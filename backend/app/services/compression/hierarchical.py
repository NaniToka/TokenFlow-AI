"""
Hierarchical Multi-Pass Map-Reduce Summarizer.

For ultra-long evicted histories (>12 turns), partitions turns into thematic epochs,
summarizes each epoch in Stage 1 (Map), and merges epoch digests into a single
compact global memory block in Stage 2 (Reduce).
"""

from __future__ import annotations

from typing import Any

from app.schemas import Turn
from app.services.compression.entity_extractor import extract_structured_memory, format_knowledge_block


def hierarchical_summarize(
    turns: list[Turn],
    llm_client: Any = None,
    epoch_size: int = 8,
) -> tuple[str, int]:
    """
    Summarize arbitrarily long evicted turn histories using Map-Reduce epochs.

    Returns:
        Tuple of (compact_summary, epochs_processed).
    """
    if not turns:
        return "", 0

    if len(turns) <= epoch_size:
        graph = extract_structured_memory(turns)
        block = format_knowledge_block(graph)
        if llm_client and llm_client.is_available:
            formatted = "\n".join(f"[{t.role.capitalize()}]: {t.content}" for t in turns)
            llm_out = llm_client.summarize(
                "Compress this dialogue segment into 2 concise technical sentences:\n" + formatted
            )
            if llm_out:
                return llm_out, 1
        return block or f"Prior context ({len(turns)} turns compressed).", 1

    # Stage 1 (Map): Chunk into thematic epochs
    epochs = [turns[i : i + epoch_size] for i in range(0, len(turns), epoch_size)]
    epoch_digests: list[str] = []

    for idx, epoch in enumerate(epochs):
        if llm_client and llm_client.is_available:
            formatted = "\n".join(f"[{t.role.capitalize()}]: {t.content}" for t in epoch)
            digest = llm_client.summarize(
                f"Summarize Epoch {idx + 1} in 1-2 crisp sentences preserving technical facts:\n{formatted}"
            )
            if digest:
                epoch_digests.append(f"[Epoch {idx + 1}] {digest}")
                continue

        graph = extract_structured_memory(epoch)
        note = format_knowledge_block(graph)
        if note:
            epoch_digests.append(f"[Epoch {idx + 1}] {note}")

    # Stage 2 (Reduce): Fuse epoch digests
    combined = "\n".join(epoch_digests)
    if llm_client and llm_client.is_available and len(epoch_digests) > 1:
        reduced = llm_client.summarize(
            "Synthesize these chronological memory epochs into 3 crisp non-redundant sentences:\n" + combined
        )
        if reduced:
            return reduced, len(epochs)

    return combined[:600], len(epochs)
