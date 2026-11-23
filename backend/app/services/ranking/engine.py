"""
Multi-Strategy Ranking Engine with BM25, Dense Vector, and hybrid scoring.

Implements a production-grade ranking pipeline:
1. BM25 sparse retrieval (lexical matching)
2. Dense vector similarity (semantic matching)
3. Recency-weighted exponential decay
4. Conversational drift detection
5. Adaptive alpha tuning
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.core.config import FeatureFlags, RankingConfig
from app.core.logging import get_logger
from app.schemas import Turn

logger = get_logger(__name__)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors using numpy."""
    if not a or not b:
        return 0.0
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.clip(np.dot(va, vb) / (norm_a * norm_b), -1.0, 1.0))


@dataclass
class ScoredTurn:
    """A conversation turn with its computed ranking scores."""

    index: int
    turn: Turn
    bm25_score: float = 0.0
    semantic_score: float = 0.0
    recency_score: float = 0.0
    drift_penalty: float = 0.0
    final_score: float = 0.0
    selected: bool = False

    def to_metadata(self) -> dict[str, Any]:
        """Export scores as API-friendly metadata dict."""
        content = self.turn.content
        snippet = content[:60] + ("..." if len(content) > 60 else "")
        return {
            "index": self.index,
            "role": self.turn.role,
            "content_snippet": snippet,
            "bm25_score": round(self.bm25_score, 4),
            "semantic_score": round(self.semantic_score, 4),
            "recency_score": round(self.recency_score, 4),
            "drift_penalty": round(self.drift_penalty, 4),
            "final_score": round(self.final_score, 4),
            "selected": self.selected,
        }


@dataclass
class RankingResult:
    """Complete result from the ranking engine."""

    selected_turns: list[Turn] = field(default_factory=list)
    unselected_turns: list[Turn] = field(default_factory=list)
    scores: list[dict[str, Any]] = field(default_factory=list)
    alpha_used: float = 0.7
    drift_detected: bool = False
    ranking_strategy: str = "hybrid"


class BM25Scorer:
    """
    Okapi BM25 sparse retrieval scorer.

    Implementation of the BM25 ranking function for lexical term matching,
    following Robertson & Zaragoza (2009).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, query: str, documents: list[str]) -> list[float]:
        """
        Compute BM25 scores for a query against a corpus of documents.

        Args:
            query: Search query string.
            documents: List of document strings to score.

        Returns:
            List of BM25 scores (one per document).
        """
        if not documents or not query.strip():
            return [0.0] * len(documents)

        # Tokenize
        query_terms = self._tokenize(query)
        doc_term_freqs = [Counter(self._tokenize(doc)) for doc in documents]
        doc_lengths = [sum(tf.values()) for tf in doc_term_freqs]
        avg_dl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0
        n_docs = len(documents)

        # Compute IDF for query terms
        idf_scores: dict[str, float] = {}
        for term in query_terms:
            df = sum(1 for dtf in doc_term_freqs if term in dtf)
            idf_scores[term] = math.log(
                (n_docs - df + 0.5) / (df + 0.5) + 1.0
            )

        # Compute BM25 for each document
        scores = []
        for i, dtf in enumerate(doc_term_freqs):
            score = 0.0
            dl = doc_lengths[i]
            for term in query_terms:
                if term not in dtf:
                    continue
                tf = dtf[term]
                idf = idf_scores.get(term, 0.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / avg_dl)
                score += idf * (numerator / denominator)
            scores.append(score)

        # Normalize to [0, 1]
        max_score = max(scores) if scores else 1.0
        if max_score > 0:
            scores = [s / max_score for s in scores]

        return scores

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lowercase tokenization."""
        return re.findall(r"\w+", text.lower())


class DriftDetector:
    """
    Detects conversational topic drift to penalize off-topic turns.

    Uses windowed Jaccard similarity to identify topic shifts
    in the conversation history.
    """

    def __init__(self, window_size: int = 5, threshold: float = 0.3):
        self.window_size = window_size
        self.threshold = threshold

    def detect_drift_points(self, turns: list[Turn]) -> list[float]:
        """
        Compute drift penalty for each turn.

        Returns a list of penalty values [0.0, 1.0] where higher
        values indicate the turn is part of an off-topic drift.
        """
        if len(turns) <= 2:
            return [0.0] * len(turns)

        penalties = [0.0] * len(turns)
        texts = [t.content.lower() for t in turns]

        for i in range(1, len(turns)):
            # Compare current turn to preceding window
            window_start = max(0, i - self.window_size)
            window_text = " ".join(texts[window_start:i])
            current_text = texts[i]

            similarity = self._jaccard(window_text, current_text)

            if similarity < self.threshold:
                # Low similarity → likely off-topic drift
                penalties[i] = 1.0 - similarity

        return penalties

    @staticmethod
    def _jaccard(text1: str, text2: str) -> float:
        """Jaccard similarity between two texts."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0


class AdaptiveAlpha:
    """
    Dynamically tunes the alpha (semantic vs recency) weight.

    Uses conversation characteristics to determine optimal weighting:
    - Short conversations → favor recency (lower alpha)
    - Long, topic-consistent conversations → favor semantics (higher alpha)
    - Multi-topic conversations → moderate alpha with drift penalty
    """

    @staticmethod
    def compute(
        turns: list[Turn],
        drift_penalties: list[float],
        base_alpha: float = 0.7,
    ) -> float:
        """
        Compute adaptive alpha based on conversation characteristics.

        Returns alpha in [0.3, 0.9] range.
        """
        n = len(turns)

        if n <= 3:
            return 0.4  # Favor recency for short conversations

        # Measure topic consistency
        drift_count = sum(1 for d in drift_penalties if d > 0.3)
        drift_ratio = drift_count / n

        # Length factor: longer conversations benefit more from semantics
        length_factor = min(1.0, n / 20.0)

        # Compute adaptive alpha
        alpha = base_alpha

        # Increase alpha (more semantic) for long, focused conversations
        alpha += length_factor * 0.1

        # Decrease alpha (more recency) for conversations with lots of drift
        alpha -= drift_ratio * 0.2

        # Clamp to valid range
        return max(0.3, min(0.9, alpha))


class RankingEngine:
    """
    Production-grade multi-strategy ranking engine.

    Combines:
    - BM25 sparse retrieval
    - Dense vector semantic similarity
    - Exponential recency decay
    - Conversational drift detection
    - Adaptive alpha tuning
    """

    def __init__(
        self,
        config: RankingConfig,
        features: FeatureFlags,
        llm_client: Any = None,
    ):
        self._config = config
        self._features = features
        self._llm_client = llm_client
        self._bm25 = BM25Scorer(k1=config.BM25_K1, b=config.BM25_B)
        self._drift_detector = DriftDetector(
            window_size=config.DRIFT_WINDOW_SIZE,
            threshold=config.DRIFT_THRESHOLD,
        )

    def rank_turns(
        self,
        history: list[Turn],
        current_message: str,
        top_k: int = 3,
        alpha: float | None = None,
    ) -> RankingResult:
        """
        Rank conversation history using multi-strategy scoring.

        Args:
            history: Conversation history turns.
            current_message: Current user query.
            top_k: Number of turns to select.
            alpha: Override for semantic vs recency weight (auto if None).

        Returns:
            RankingResult with selected/unselected turns and metadata.
        """
        if not history:
            return RankingResult()

        total = len(history)
        texts = [t.content for t in history]

        # --- Step 1: Compute drift penalties ---
        drift_penalties = [0.0] * total
        drift_detected = False
        if self._features.ENABLE_DRIFT_DETECTION:
            drift_penalties = self._drift_detector.detect_drift_points(history)
            drift_detected = any(d > 0.3 for d in drift_penalties)

        # --- Step 2: Determine alpha ---
        if alpha is not None:
            effective_alpha = alpha
        elif self._features.ENABLE_ADAPTIVE_ALPHA:
            effective_alpha = AdaptiveAlpha.compute(
                history, drift_penalties, self._config.DEFAULT_ALPHA
            )
        else:
            effective_alpha = self._config.DEFAULT_ALPHA

        # --- Step 3: Compute BM25 scores ---
        bm25_scores = [0.0] * total
        if self._features.ENABLE_BM25_RANKING:
            bm25_scores = self._bm25.score(current_message, texts)

        # --- Step 4: Compute dense vector similarity ---
        semantic_scores = self._compute_semantic_scores(current_message, texts)

        # --- Step 5: Compute recency weights ---
        recency_scores = [
            self._recency_weight(i, total) for i in range(total)
        ]

        # --- Step 6: Build scored turns ---
        scored = []
        for i, turn in enumerate(history):
            # Combine BM25 and semantic into a unified similarity score
            sim = 0.6 * semantic_scores[i] + 0.4 * bm25_scores[i]

            # Apply drift penalty
            drift_pen = drift_penalties[i] * 0.3 if drift_detected else 0.0

            # Final hybrid score
            final = (
                effective_alpha * sim
                + (1.0 - effective_alpha) * recency_scores[i]
                - drift_pen
            )

            scored.append(ScoredTurn(
                index=i,
                turn=Turn(role=turn.role, content=turn.content),
                bm25_score=bm25_scores[i],
                semantic_score=semantic_scores[i],
                recency_score=recency_scores[i],
                drift_penalty=drift_pen,
                final_score=max(0.0, final),
            ))

        # --- Step 7: Select top-k ---
        ranked = sorted(scored, key=lambda x: x.final_score, reverse=True)
        k = min(top_k, total)
        selected_indices = set()
        for item in ranked[:k]:
            item.selected = True
            selected_indices.add(item.index)

        # Maintain chronological order
        selected = [s.turn for s in sorted(
            [x for x in scored if x.index in selected_indices],
            key=lambda x: x.index,
        )]
        unselected = [s.turn for s in sorted(
            [x for x in scored if x.index not in selected_indices],
            key=lambda x: x.index,
        )]

        strategy_parts = ["recency"]
        if self._features.ENABLE_BM25_RANKING:
            strategy_parts.append("bm25")
        if any(s > 0 for s in semantic_scores):
            strategy_parts.append("dense_vector")
        if drift_detected:
            strategy_parts.append("drift_penalty")

        return RankingResult(
            selected_turns=selected,
            unselected_turns=unselected,
            scores=[s.to_metadata() for s in scored],
            alpha_used=round(effective_alpha, 4),
            drift_detected=drift_detected,
            ranking_strategy="+".join(strategy_parts),
        )

    def _compute_semantic_scores(
        self, query: str, texts: list[str]
    ) -> list[float]:
        """Compute semantic similarity scores using embeddings or fallback."""
        if not self._llm_client or not self._llm_client.is_available:
            return self._lexical_fallback(query, texts)

        query_vec = self._llm_client.get_embedding(query)
        turn_vecs = self._llm_client.get_batch_embeddings(texts)

        if not query_vec:
            return self._lexical_fallback(query, texts)

        scores = []
        for vec in turn_vecs:
            if vec:
                scores.append(self._cosine_similarity(query_vec, vec))
            else:
                scores.append(self._jaccard_similarity(query, texts[len(scores)]))
        return scores

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b:
            return 0.0
        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        norm_a = np.linalg.norm(va)
        norm_b = np.linalg.norm(vb)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.clip(np.dot(va, vb) / (norm_a * norm_b), -1.0, 1.0))

    @staticmethod
    def _jaccard_similarity(text1: str, text2: str) -> float:
        """Jaccard token-level similarity."""
        w1 = set(text1.lower().split())
        w2 = set(text2.lower().split())
        if not w1 or not w2:
            return 0.0
        return len(w1 & w2) / len(w1 | w2)

    def _lexical_fallback(self, query: str, texts: list[str]) -> list[float]:
        """Fallback to Jaccard similarity when embeddings unavailable."""
        return [self._jaccard_similarity(query, t) for t in texts]

    def _recency_weight(self, index: int, total: int) -> float:
        """Exponential recency decay weight."""
        if total <= 0 or index < 0:
            return 0.0
        distance = total - 1 - index
        return math.exp(-self._config.RECENCY_DECAY_FACTOR * distance)
