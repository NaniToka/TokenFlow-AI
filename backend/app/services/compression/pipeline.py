"""
Production-grade compression pipeline with multi-stage processing.

Orchestrates the full prompt compression workflow:
1. Input validation, XSS sanitization, PII redaction, and Prompt Injection Firewall scan
2. Semantic deduplication of repeated/retry turns
3. Short-history bypass detection
4. Multi-strategy ranking (Linear/RRF fusion, Cross-Encoder Rerank, MMR Diversity)
5. Hierarchical Map-Reduce summarization + Knowledge Graph extraction + LRU Cache
6. Knapsack Token Budget Ceiling enforcement (`max_context_tokens`)
7. Multi-model cost savings, token salience heat-map, and Prometheus telemetry
"""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings
from app.core.guardrails import PromptInjectionFirewall
from app.core.logging import get_logger
from app.core.sanitizer import InputSanitizer
from app.schemas import (
    CompressionMetadata,
    CompressRequest,
    CompressResponse,
    FirewallReport,
    RedactionReport,
    Turn,
)
from app.services.cache.semantic_cache import summary_cache
from app.services.compression.budget_optimizer import enforce_token_budget
from app.services.compression.deduplicator import deduplicate_turns
from app.services.compression.entity_extractor import extract_structured_memory, format_knowledge_block
from app.services.compression.hierarchical import hierarchical_summarize
from app.services.evaluation.salience import compute_token_salience
from app.services.llm.client import LLMClientManager
from app.services.ranking.engine import RankingEngine
from app.services.stats_logger import StatsTracker
from app.utils.metrics import metrics_registry
from app.utils.token_counter import calculate_savings, count_tokens

logger = get_logger(__name__)


class ContextSummarizer:
    """
    Generates compact summaries of evicted conversation turns.

    Uses Hierarchical Map-Reduce LLM summarization, Knowledge Graph extraction,
    and Semantic LRU Caching with deterministic extractive fallback.
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

    def summarize(
        self,
        turns: list[Turn],
        use_cache: bool = True,
        use_hierarchical: bool = True,
    ) -> tuple[str, bool, int]:
        """
        Generate a compact summary of evicted turns.

        Returns:
            Tuple of (summary_text, cache_hit_bool, epochs_count).
        """
        if not turns:
            return "", False, 0

        formatted = "\n".join(
            f"[{t.role.capitalize()}]: {t.content}" for t in turns
        )
        cache_key = summary_cache.hash_key(f"{use_hierarchical}:{formatted}")

        if use_cache:
            cached = summary_cache.get(cache_key)
            if isinstance(cached, str):
                return cached, True, 1

        epochs = 1
        summary_text = ""

        if use_hierarchical and len(turns) > 12:
            summary_text, epochs = hierarchical_summarize(turns, llm_client=self._llm)
        elif self._llm.is_available:
            prompt = self.SUMMARIZATION_PROMPT.format(history=formatted)
            summary_text = self._llm.summarize(prompt)

        if not summary_text:
            summary_text = self._extractive_fallback(turns)

        if use_cache and summary_text:
            summary_cache.set(cache_key, summary_text)

        return summary_text, False, epochs

    @staticmethod
    def _extractive_fallback(turns: list[Turn]) -> str:
        """Extractive summary enhanced with structured entity/decision graph."""
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

        graph = extract_structured_memory(turns)
        kg_block = format_knowledge_block(graph)
        base = "Prior context summary:\n" + "\n".join(lines)
        return f"{base}\n{kg_block}" if kg_block else base


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

        # Firewall Scan
        if request.scan_prompt_injection:
            fw = PromptInjectionFirewall.scan([t.content for t in sanitized_history] + [current_msg])
            firewall_report = FirewallReport(
                is_safe=fw.is_safe,
                risk_score=fw.risk_score,
                highest_severity=fw.highest_severity,
                findings=[
                    {
                        "rule_id": f.rule_id,
                        "severity": f.severity,
                        "description": f.description,
                        "matched_excerpt": f.matched_excerpt,
                    }
                    for f in fw.findings
                ],
            )
        else:
            firewall_report = FirewallReport()

        # Stage 2: Original token count BEFORE deduplication
        history_text = "\n".join(
            f"[{t.role.capitalize()}]: {t.content}" for t in sanitized_history
        )
        full_original = (
            f"{history_text}\n[User]: {current_msg}" if history_text
            else f"[User]: {current_msg}"
        )
        original_tokens = count_tokens(full_original)

        # Stage 2b: Semantic Deduplication
        duplicates_removed = 0
        working_history = sanitized_history
        if request.use_dedup and len(sanitized_history) > 1:
            dedup_res = deduplicate_turns(sanitized_history)
            working_history = dedup_res.deduplicated_turns
            duplicates_removed = dedup_res.duplicates_removed

        # Stage 3: Short-history bypass
        total_turns = len(working_history)
        working_text = "\n".join(f"[{t.role.capitalize()}]: {t.content}" for t in working_history)
        working_tokens = count_tokens(working_text) if working_text else 0
        cache_hit = False
        epochs_summarized = 0
        mode_value = request.compression_mode.value
        dropped_for_budget = 0

        if total_turns <= request.top_k or working_tokens < 50:
            summary = ""
            selected_turns = working_history
            unselected: list[Turn] = []
            ranking_strategy = "bypass"
            alpha_used = 0.0
            drift_detected = False
            scores_meta: list[dict[str, Any]] = []
            scored_triplets = [(i, t, 1.0) for i, t in enumerate(selected_turns)]
        else:
            # Stage 4: Multi-strategy ranking
            ranking = self._ranker.rank_turns(
                history=working_history,
                current_message=current_msg,
                top_k=request.top_k,
                alpha=request.alpha,
                compression_mode=mode_value,
                fusion_method=request.fusion_method,
                use_mmr=request.use_mmr,
                mmr_lambda=request.mmr_lambda,
                use_reranker=request.use_reranker,
            )
            selected_turns = ranking.selected_turns
            unselected = ranking.unselected_turns
            ranking_strategy = ranking.ranking_strategy
            alpha_used = ranking.alpha_used
            drift_detected = ranking.drift_detected
            scores_meta = ranking.scores

            scored_triplets = [
                (int(s["index"]), working_history[int(s["index"])], float(s["final_score"]))
                for s in scores_meta
                if s.get("selected")
            ]

            # Stage 5: Summarize evicted turns
            if unselected:
                summary, cache_hit, epochs_summarized = self._summarizer.summarize(
                    unselected,
                    use_cache=request.use_cache,
                    use_hierarchical=request.use_hierarchical,
                )
            else:
                summary = ""

        # Stage 5b: Optional Hard Token Budget Knapsack Packing
        if request.max_context_tokens is not None:
            pack = enforce_token_budget(
                scored_selected=scored_triplets,
                current_message=current_msg,
                summary=summary,
                system_instruction=system_instruction,
                max_context_tokens=request.max_context_tokens,
            )
            selected_turns = pack.packed_turns
            dropped_for_budget = pack.dropped_for_budget

        # Extract Knowledge Graph over evicted turns for diagnostics
        kg = extract_structured_memory(unselected if unselected else working_history)

        # Stage 6: Assemble final prompt
        final_prompt = self._assembler.assemble(
            summary=summary,
            selected_turns=selected_turns,
            current_message=current_msg,
            system_instruction=system_instruction,
        )
        compressed_tokens = count_tokens(final_prompt)

        # Stage 7: Fallback protection (never expand unless hard budget forced smaller)
        if compressed_tokens > original_tokens and request.max_context_tokens is None:
            logger.warning(
                "compression_expansion_detected",
                original=original_tokens,
                compressed=compressed_tokens,
            )
            final_prompt = full_original
            compressed_tokens = original_tokens
            summary = ""
            selected_turns = working_history

        # Stage 8: Multi-model cost savings & Token Salience Heat-Map
        savings = calculate_savings(
            original_tokens,
            compressed_tokens,
            model=request.target_model,
        )
        salience = compute_token_salience(final_prompt, query=current_msg)

        elapsed_sec = time.perf_counter() - start_time
        latency_ms = round(elapsed_sec * 1000, 2)

        metadata = CompressionMetadata(
            ranking_strategy=ranking_strategy if total_turns > request.top_k else "bypass",
            compression_mode=mode_value,
            fusion_method=request.fusion_method,
            target_model=request.target_model,
            alpha_used=alpha_used,
            drift_detected=drift_detected,
            turns_evaluated=total_turns,
            turns_selected=len(selected_turns),
            turns_evicted=total_turns - len(selected_turns),
            duplicates_removed=duplicates_removed,
            dropped_for_budget=dropped_for_budget,
            epochs_summarized=epochs_summarized,
            model_used=self._settings.llm.PRIMARY_MODEL if self._summarizer._llm.is_available else "fallback_extractive",
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            redaction=RedactionReport(
                enabled=request.sanitize_pii,
                redactions_count=total_redactions,
                xss_stripped=total_xss,
                redacted_types=redacted_types,
            ),
            firewall=firewall_report,
            knowledge_graph=kg,
            salience_tokens=salience,
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
