"""
Extractive Decision, Entity & Action-Item Graph Extractor.

Parses evicted conversation turns deterministically to extract structured memory nodes:
- Technical entities & identifiers (e.g., PostgreSQL, Kubernetes, `LockID`)
- Explicit architectural decisions ("decided to", "using", "configured")
- Unresolved constraints & error codes (HTTP 502, OOM, timeouts)
"""

from __future__ import annotations

import re
from typing import Any

from app.schemas import Turn

ENTITY_PATTERN = re.compile(r"\b(?:[A-Z][a-zA-Z0-9_-]{2,}|[a-z]+_[a-z0-9_]+|v?\d+\.\d+(?:\.\d+)?)\b")
CODE_INLINE_PATTERN = re.compile(r"`([^`]{2,40})`")
DECISION_MARKERS = ("decided", "using", "configured", "require", "must", "enabled", "deployed", "selected")


def extract_structured_memory(turns: list[Turn]) -> dict[str, Any]:
    """
    Extract entities, inline symbols, decisions, and pending questions from turns.
    Works 100% deterministically offline with zero LLM latency.
    """
    if not turns:
        return {
            "entities": [],
            "code_symbols": [],
            "decisions": [],
            "open_questions": [],
        }

    entities: list[str] = []
    seen_ent: set[str] = set()
    code_symbols: list[str] = []
    seen_sym: set[str] = set()
    decisions: list[str] = []
    questions: list[str] = []

    stop_entities = {"The", "This", "That", "What", "How", "Why", "When", "Where", "Yes", "Great", "Sure", "Back"}

    for turn in turns:
        text = turn.content.strip()

        for sym in CODE_INLINE_PATTERN.findall(text):
            if sym not in seen_sym and len(code_symbols) < 12:
                seen_sym.add(sym)
                code_symbols.append(sym)

        for ent in ENTITY_PATTERN.findall(text):
            if ent not in stop_entities and ent not in seen_ent and len(entities) < 15:
                seen_ent.add(ent)
                entities.append(ent)

        # Sentence-level decision/question extraction
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        for sent in sentences:
            low = sent.lower()
            if sent.endswith("?") and turn.role == "user" and len(questions) < 3:
                questions.append(sent[:120])
            elif any(marker in low for marker in DECISION_MARKERS) and len(decisions) < 4:
                decisions.append(sent[:130])

    return {
        "entities": entities,
        "code_symbols": code_symbols,
        "decisions": decisions,
        "open_questions": questions,
    }


def format_knowledge_block(graph: dict[str, Any]) -> str:
    """Format extracted knowledge graph into a compact prompt-ready memory note."""
    lines: list[str] = []
    if graph.get("entities"):
        lines.append(f"Entities: {', '.join(graph['entities'][:10])}")
    if graph.get("code_symbols"):
        lines.append(f"Symbols: {', '.join(graph['code_symbols'][:8])}")
    if graph.get("decisions"):
        lines.append("Key Facts: " + " | ".join(graph["decisions"][:3]))
    return "\n".join(lines)
