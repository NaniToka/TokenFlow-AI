import logging
from typing import List
from app.schemas import Turn, CompressRequest, CompressResponse
from app.services.memory_ranker import rank_turns
from app.services.compressor import summarize_turns
from app.services.stats_logger import stats_tracker
from app.utils.token_counter import count_tokens, calculate_savings

logger = logging.getLogger(__name__)


def assemble_optimized_prompt(summary: str, selected_turns: List[Turn], current_message: str) -> str:
    """
    Assembles a structured optimized prompt using the compressed summary, top-K selected turns, and current user message.
    Includes sections ONLY if non-empty to ensure zero token overhead.
    """
    sections = []

    if summary and summary.strip() and summary.strip() != "No prior background summary needed.":
        sections.append(f"[BACKGROUND CONTEXT SUMMARY]\n{summary.strip()}")

    if selected_turns:
        history_str = "\n".join([f"[{turn.role.capitalize()}]: {turn.content}" for turn in selected_turns])
        sections.append(f"[RELEVANT RECENT HISTORY]\n{history_str}")

    sections.append(f"[CURRENT USER MESSAGE]\n{current_message.strip()}")

    return "\n\n".join(sections)


def process_compression(request: CompressRequest) -> CompressResponse:
    """
    Orchestrates the prompt compression pipeline with 100% stateless execution per request.
    Extracts history exclusively from request.history and clears any transient references.
    """
    # Guarantee 100% stateless execution by deep-copying history turns from request
    history_turns = [Turn(role=t.role, content=t.content) for t in (request.history or [])]
    current_msg = str(request.current_message).strip()

    # 1. Calculate original tokens
    history_text = "\n".join([f"[{t.role.capitalize()}]: {t.content}" for t in history_turns])
    if history_text:
        full_original_text = f"{history_text}\n[User]: {current_msg}"
    else:
        full_original_text = f"[User]: {current_msg}"

    original_tokens = count_tokens(full_original_text)

    # 2. Smart Bypass / Short History Guard
    total_turns = len(history_turns)
    history_tokens = count_tokens(history_text) if history_text else 0

    if total_turns <= request.top_k or history_tokens < 50:
        summary = ""
        selected_turns = history_turns
        unselected_turns = []
    else:
        # Memory Ranker on isolated history_turns
        ranking = rank_turns(
            history=history_turns,
            current_message=current_msg,
            top_k=request.top_k
        )
        selected_turns = ranking["selected_turns"]
        unselected_turns = ranking["unselected_turns"]

        # Context Compressor (only on unselected turns)
        summary = summarize_turns(unselected_turns) if unselected_turns else ""

    # 3. Assemble Final Prompt
    final_prompt = assemble_optimized_prompt(
        summary=summary,
        selected_turns=selected_turns,
        current_message=current_msg
    )
    compressed_tokens = count_tokens(final_prompt)

    # 4. Fallback Cost Protection
    if compressed_tokens > original_tokens:
        final_prompt = full_original_text
        compressed_tokens = original_tokens
        summary = ""
        selected_turns = history_turns

    # 5. Calculate Savings
    savings = calculate_savings(original_tokens, compressed_tokens)

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
        compression_ratio=savings["compression_ratio"]
    )

    # 6. Log numerical metrics ONLY
    stats_tracker.log_compression(response)

    return response
