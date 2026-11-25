"""
Production-grade compression pipeline with multi-stage processing.

Orchestrates the full prompt compression workflow:
1. Input validation, XSS sanitization, and optional PII redaction
2. Short-history bypass detection
3. Multi-strategy ranking (with compression modes)
4. Abstractive summarization with Semantic LRU cache & fallback
5. Prompt assembly with section optimization
6. Multi-model cost and savings calculation
7. Metrics & Prometheus telemetry logging
"""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.sanitizer import InputSanitizer
from app.schemas import (
    CompressionMetadata,
    CompressRequest,
    CompressResponse,
    RedactionReport,
    Turn,
)
from app.services.cache.semantic_cache import summary_cache
from app.services.llm.client import LLMClientManager
from app.services.ranking.engine import RankingEngine
from app.services.stats_logger import StatsTracker
from app.utils.metrics import metrics_registry
from app.utils.token_counter import calculate_savings, count_tokens

logger = get_logger(__name__)


class ContextSummarizer:
    """
    Generates compact summaries of evicted conversation turns.

    Uses LLM for abstractive summarization with Semantic LRU Caching
    and extractive fallback when API is unavailable.
    """

    SUMMARIZATION_PROMPT = (
        "You are a precise context compression engine. "
        "Summarize the following prior conversation background in 2-3 concise sentences. "
        "Focus ONLY on: key facts, decisions made, entities mentioned, user preferences, "
        "technical constraints, and action items. "
        "OMIT: greetings, pleasantries, off-topic tangents, and filler. "
        "Output ONLY the summary, nothing else.\n\n"
        "Conversation History:\n{history}"
    )

    def __init__(self, llm_client: LLMClientManager):
        self._llm = llm_client

    def summarize(self, turns: list[Turn], use_cache: bool = True) -> tuple[str, bool]:
        """
        Generate a compact summary of conversation turns.

        Returns:
            Tuple of (summary_text, cache_hit_bool).
        """
        if not turns:
            return "", False

        formatted = "\n".join(
            f"[{t.role.capitalize()}]: {t.content}" for t in turns
        )
        cache_key = summary_cache.hash_key(formatted)

        if use_cache:
            cached = summary_cache.get(cache_key)
            if isinstance(cached, str):
                return cached, True

        summary_text = ""
        if self._llm.is_available:
            prompt = self.SUMMARIZATION_PROMPT.format(history=formatted)
            summary_text = self._llm.summarize(prompt)

        if not summary_text:
            summary_text = self._extractive_fallback(turns)

        if use_cache and summary_text:
            summary_cache.set(cache_key, summary_text)

        return summary_text, False

    @staticmethod
    def _extractive_fallback(turns: list[Turn]) -> str:
        """Extractive summary: select key user statements."""
        user_turns = [t.content.strip() for t in turns if t.role == "user"]
        if not user_turns:
            user_turns = [t.content.strip() for t in turns]

        if not user_turns:
            return ""

        points = user_turns[:3]
        lines = []
        for pt in points:
            if len(pt) > 100:
                pt = pt[:97] + "..."
            lines.append(f"• {pt}")

        return "Prior context summary:\n" + "\n".join(lines)


class PromptAssembler:
    """Assembles the final optimized prompt from compressed components."""

    @staticmethod
    def assemble(
        summary: str,
        selected_turns: list[Turn],
        current_message: str,
        system_instruction: str = "",
    ) -> str:
        """Build the final compressed prompt with zero unnecessary overhead."""
        sections = []

        if system_instruction and system_instruction.strip():
            sections.append(f"[SYSTEM INSTRUCTION]\n{system_instruction.strip()}")

        if summary and summary.strip() and summary.strip() != "No prior background summary needed.":
            sections.append(f"[BACKGROUND CONTEXT SUMMARY]\n{summary.strip()}")

        if selected_turns:
            history_str = "\n".join(
                f"[{t.role.capitalize()}]: {t.content}" for t in selected_turns
            )
            sections.append(f"[RELEVANT RECENT HISTORY]\n{history_str}")

        sections.append(f"[CURRENT USER MESSAGE]\n{current_message.strip()}")

        return "\n\n".join(sections)


class CompressionPipeline:
    """Main orchestrator for the prompt compression workflow."""

    def __init__(
        self,
        ranking_engine: RankingEngine,
        llm_client: LLMClientManager,
        stats_tracker: StatsTracker,
        settings: Settings,
    ):
        self._ranker = ranking_engine
        self._summarizer = ContextSummarizer(llm_client)
        self._assembler = PromptAssembler()
        self._stats = stats_tracker
        self._settings = settings

    def compress(self, request: CompressRequest) -> CompressResponse:
        """Execute the full multi-stage compression pipeline."""
        start_time = time.perf_counter()

        # Stage 1: Isolate, sanitize, and optionally redact PII
        total_redactions = 0
        total_xss = 0
        redacted_types: list[str] = []

        sanitized_history: list[Turn] = []
        for t in (request.history or []):
            res = InputSanitizer.sanitize_and_redact(t.content, redact_pii=request.sanitize_pii)
            total_redactions += res.redactions_count
            total_xss += res.xss_stripped
            for rtype in res.redacted_types:
                if rtype not in redacted_types:
                    redacted_types.append(rtype)
            if res.sanitized_text:
                sanitized_history.append(Turn(role=t.role, content=res.sanitized_text))

        msg_res = InputSanitizer.sanitize_and_redact(request.current_message, redact_pii=request.sanitize_pii)
        total_redactions += msg_res.redactions_count
        total_xss += msg_res.xss_stripped
        for rtype in msg_res.redacted_types:
            if rtype not in redacted_types:
                redacted_types.append(rtype)

        current_msg = msg_res.sanitized_text or str(request.current_message).strip()
        system_instruction = InputSanitizer.sanitize(request.system_instruction)

        # Stage 2: Original token count
        history_text = "\n".join(
            f"[{t.role.capitalize()}]: {t.content}" for t in sanitized_history
        )
        full_original = (
            f"{history_text}\n[User]: {current_msg}" if history_text
            else f"[User]: {current_msg}"
        )
        original_tokens = count_tokens(full_original)

        # Stage 3: Short-history bypass
        total_turns = len(sanitized_history)
        history_tokens = count_tokens(history_text) if history_text else 0
        cache_hit = False
        mode_value = request.compression_mode.value

        if total_turns <= request.top_k or history_tokens < 50:
            summary = ""
            selected_turns = sanitized_history
            ranking_strategy = "bypass"
            alpha_used = 0.0
            drift_detected = False
            scores_meta: list[dict[str, Any]] = []
        else:
            # Stage 4: Multi-strategy ranking
            ranking = self._ranker.rank_turns(
                history=sanitized_history,
                current_message=current_msg,
                top_k=request.top_k,
                alpha=request.alpha,
                compression_mode=mode_value,
            )
            selected_turns = ranking.selected_turns
            unselected = ranking.unselected_turns
            ranking_strategy = ranking.ranking_strategy
            alpha_used = ranking.alpha_used
            drift_detected = ranking.drift_detected
            scores_meta = ranking.scores

            # Stage 5: Summarize evicted turns
            if unselected:
                summary, cache_hit = self._summarizer.summarize(
                    unselected, use_cache=request.use_cache
                )
            else:
                summary = ""

        # Stage 6: Assemble final prompt
        final_prompt = self._assembler.assemble(
            summary=summary,
            selected_turns=selected_turns,
            current_message=current_msg,
            system_instruction=system_instruction,
        )
        compressed_tokens = count_tokens(final_prompt)

        # Stage 7: Fallback protection (never expand)
        if compressed_tokens > original_tokens:
            logger.warning(
                "compression_expansion_detected",
                original=original_tokens,
                compressed=compressed_tokens,
            )
            final_prompt = full_original
            compressed_tokens = original_tokens
            summary = ""
            selected_turns = sanitized_history

        # Stage 8: Multi-model cost savings calculation
        savings = calculate_savings(
            original_tokens,
            compressed_tokens,
            model=request.target_model,
        )

        elapsed_sec = time.perf_counter() - start_time
        latency_ms = round(elapsed_sec * 1000, 2)

        metadata = CompressionMetadata(
            ranking_strategy=ranking_strategy if total_turns > request.top_k else "bypass",
            compression_mode=mode_value,
            target_model=request.target_model,
            alpha_used=alpha_used,
            drift_detected=drift_detected,
            turns_evaluated=total_turns,
            turns_selected=len(selected_turns),
            turns_evicted=total_turns - len(selected_turns),
            model_used=self._settings.llm.PRIMARY_MODEL if self._summarizer._llm.is_available else "fallback_extractive",
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            redaction=RedactionReport(
                enabled=request.sanitize_pii,
                redactions_count=total_redactions,
                xss_stripped=total_xss,
                redacted_types=redacted_types,
            ),
            scores=scores_meta,
        )

        response = CompressResponse(
            summary=summary,
            selected_turns=selected_turns,
            final_prompt=final_prompt,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            tokens_saved=savings["tokens_saved"],
            cost_before_usd=savings["cost_before_usd"],
            cost_after_usd=savings["cost_after_usd"],
            cost_saved_usd=savings["cost_saved_usd"],
            compression_ratio=savings["compression_ratio"],
            metadata=metadata,
        )

        # Stage 9: Log metrics & Prometheus telemetry
        self._stats.log_compression(response, latency_ms=latency_ms)
        metrics_registry.record_request(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            duration_seconds=elapsed_sec,
            success=True,
        )

        logger.info(
            "compression_complete",
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            tokens_saved=savings["tokens_saved"],
            ratio=savings["compression_ratio"],
            strategy=metadata.ranking_strategy,
            cache_hit=cache_hit,
        )

        return response
