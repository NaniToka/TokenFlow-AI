"""
Production-grade compression pipeline with multi-stage processing.

Orchestrates the full prompt compression workflow:
1. Input validation and preprocessing
2. Short-history bypass detection
3. Multi-strategy ranking
4. Abstractive summarization with LLM fallback
5. Prompt assembly with section optimization
6. Cost and savings calculation
7. Metrics logging
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas import (
    CompressionMetadata,
    CompressRequest,
    CompressResponse,
    Turn,
)
from app.services.llm.client import LLMClientManager
from app.services.ranking.engine import RankingEngine
from app.services.stats_logger import StatsTracker
from app.utils.token_counter import calculate_savings, count_tokens

logger = get_logger(__name__)


class ContextSummarizer:
    """
    Generates compact summaries of evicted conversation turns.

    Uses LLM for abstractive summarization with extractive fallback
    when API is unavailable.
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

    def summarize(self, turns: list[Turn]) -> str:
        """
        Generate a compact summary of conversation turns.

        Attempts LLM-based abstractive summarization first,
        falls back to extractive method if unavailable.
        """
        if not turns:
            return ""

        formatted = "\n".join(
            f"[{t.role.capitalize()}]: {t.content}" for t in turns
        )

        # Try LLM summarization
        if self._llm.is_available:
            prompt = self.SUMMARIZATION_PROMPT.format(history=formatted)
            result = self._llm.summarize(prompt)
            if result:
                return result

        # Extractive fallback
        return self._extractive_fallback(turns)

    @staticmethod
    def _extractive_fallback(turns: list[Turn]) -> str:
        """
        Extractive summary: select key user statements.

        Prioritizes user turns and truncates long content.
        """
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
    """
    Assembles the final optimized prompt from compressed components.

    Produces a structured prompt with clear section delimiters
    that any downstream LLM can parse effectively.
    """

    @staticmethod
    def assemble(
        summary: str,
        selected_turns: list[Turn],
        current_message: str,
        system_instruction: str = "",
    ) -> str:
        """
        Build the final compressed prompt.

        Sections are included only if non-empty to minimize token overhead.
        """
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
    """
    Main orchestrator for the prompt compression workflow.

    Manages the complete pipeline from raw input to optimized output
    with comprehensive metrics collection.
    """

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
        """
        Execute the full compression pipeline.

        Pipeline stages:
        1. Deep-copy and validate input
        2. Calculate original token count
        3. Apply short-history bypass
        4. Rank turns with multi-strategy engine
        5. Summarize evicted turns
        6. Assemble optimized prompt
        7. Verify compression (fallback to original if expansion)
        8. Calculate cost savings
        9. Log metrics

        Returns:
            CompressResponse with full metrics and compressed prompt.
        """
        # Stage 1: Isolate input (stateless guarantee)
        history = [Turn(role=t.role, content=t.content) for t in (request.history or [])]
        current_msg = str(request.current_message).strip()
        system_instruction = str(request.system_instruction or "").strip()

        # Stage 2: Original token count
        history_text = "\n".join(
            f"[{t.role.capitalize()}]: {t.content}" for t in history
        )
        full_original = (
            f"{history_text}\n[User]: {current_msg}" if history_text
            else f"[User]: {current_msg}"
        )
        original_tokens = count_tokens(full_original)

        # Stage 3: Short-history bypass
        total_turns = len(history)
        history_tokens = count_tokens(history_text) if history_text else 0

        if total_turns <= request.top_k or history_tokens < 50:
            summary = ""
            selected_turns = history
            ranking_strategy = "bypass"
            alpha_used = 0.0
            drift_detected = False
            scores_meta = []
        else:
            # Stage 4: Multi-strategy ranking
            ranking = self._ranker.rank_turns(
                history=history,
                current_message=current_msg,
                top_k=request.top_k,
                alpha=request.alpha,
            )
            selected_turns = ranking.selected_turns
            unselected = ranking.unselected_turns
            ranking_strategy = ranking.ranking_strategy
            alpha_used = ranking.alpha_used
            drift_detected = ranking.drift_detected
            scores_meta = ranking.scores

            # Stage 5: Summarize evicted turns
            summary = (
                self._summarizer.summarize(unselected) if unselected else ""
            )

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
            selected_turns = history

        # Stage 8: Calculate savings
        savings = calculate_savings(original_tokens, compressed_tokens)

        # Build metadata
        metadata = CompressionMetadata(
            ranking_strategy=ranking_strategy if total_turns > request.top_k else "bypass",
            alpha_used=alpha_used,
            drift_detected=drift_detected,
            turns_evaluated=total_turns,
            turns_selected=len(selected_turns),
            turns_evicted=total_turns - len(selected_turns),
            model_used=self._settings.llm.PRIMARY_MODEL if self._summarizer._llm.is_available else "fallback_extractive",
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

        # Stage 9: Log metrics
        self._stats.log_compression(response)

        logger.info(
            "compression_complete",
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            tokens_saved=savings["tokens_saved"],
            ratio=savings["compression_ratio"],
            strategy=metadata.ranking_strategy,
        )

        return response
