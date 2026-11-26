"""
RAG Citation & Grounding Attribution Engine.

Maps query sentences or retrieved claims back to exact source chunk IDs
and computes per-citation grounding confidence scores.
"""

from __future__ import annotations

import re
from typing import Any


def build_rag_citations(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate inline grounded citations and matched key terms per retrieved chunk.

    Returns:
        Dict with attributed_summary, citations list, and overall_confidence.
    """
    if not retrieved_chunks:
        return {
            "attributed_summary": "",
            "citations": [],
            "overall_confidence": 0.0,
        }

    query_terms = set(re.findall(r"[a-z0-9_]{3,}", query.lower()))
    citations: list[dict[str, Any]] = []
    attributed_lines: list[str] = []

    for chunk in retrieved_chunks:
        cid = chunk.get("chunk_id", 0)
        text = str(chunk.get("text", ""))
        hybrid = float(chunk.get("hybrid_score", 0.0))

        chunk_terms = set(re.findall(r"[a-z0-9_]{3,}", text.lower()))
        matched_terms = sorted(query_terms & chunk_terms)

        # Extract the highest-signal sentence in the chunk
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        best_sentence = sentences[0] if sentences else text[:160]
        if sentences and query_terms:
            best_sentence = max(
                sentences,
                key=lambda s: len(set(re.findall(r"[a-z0-9_]{3,}", s.lower())) & query_terms),
            )

        confidence = round(min(1.0, 0.65 * hybrid + 0.35 * (len(matched_terms) / max(1, len(query_terms)))), 4)
        citations.append({
            "citation_tag": f"[Chunk #{cid}]",
            "chunk_id": cid,
            "confidence": confidence,
            "matched_terms": matched_terms[:10],
            "excerpt": best_sentence[:220],
            "source": chunk.get("metadata", {}).get("source", "workspace_document"),
        })
        attributed_lines.append(f"{best_sentence} [Chunk #{cid}]")

    avg_conf = round(sum(c["confidence"] for c in citations) / len(citations), 4)
    return {
        "attributed_summary": " ".join(attributed_lines),
        "citations": citations,
        "overall_confidence": avg_conf,
    }
