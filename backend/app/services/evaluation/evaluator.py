"""
LLM-as-a-Judge and Context Quality Evaluation Framework.

Computes benchmark evaluation metrics for compressed prompts:
1. Lexical Recall (retained entities & key facts)
2. Token Reduction Efficiency
3. Semantic Preservation Score
4. Hallucination Risk Metric
"""

import re
from dataclasses import dataclass

from app.schemas import CompressResponse, Turn


@dataclass
class QualityBenchmarkReport:
    """Benchmark evaluation report for a compression run."""
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float
    lexical_recall: float
    entity_coverage: float
    semantic_fidelity: float
    hallucination_risk: float
    composite_grade: str


class ContextQualityEvaluator:
    """
    Evaluates compression fidelity comparing raw conversation history
    against the optimized output prompt.
    """

    KEYWORD_PATTERN = re.compile(r"\b[A-Za-z0-9_]{3,}\b")

    def evaluate(self, original_history: list[Turn], response: CompressResponse) -> QualityBenchmarkReport:
        """Generates comprehensive quality score across factual retention and efficiency."""
        # 1. Extract vocabulary & entities from original user/model turns
        orig_text = " ".join([t.content for t in original_history])
        comp_text = response.final_prompt + " " + response.summary

        orig_words = set(w.lower() for w in self.KEYWORD_PATTERN.findall(orig_text))
        comp_words = set(w.lower() for w in self.KEYWORD_PATTERN.findall(comp_text))

        # Filter out common stop words
        stopwords = {
            "the", "and", "is", "in", "to", "of", "it", "you", "that", "he", "was",
            "for", "on", "are", "as", "with", "his", "they", "at", "be", "this", "have", "from"
        }
        filtered_orig = orig_words - stopwords
        filtered_comp = comp_words - stopwords

        # Recall ratio of important terms
        overlap = filtered_orig.intersection(filtered_comp)
        lexical_recall = len(overlap) / len(filtered_orig) if filtered_orig else 1.0

        # Technical/capitalized entity coverage
        orig_entities = set(re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", orig_text))
        comp_entities = set(re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", comp_text))
        entity_coverage = len(orig_entities.intersection(comp_entities)) / len(orig_entities) if orig_entities else 1.0

        # Semantic fidelity approximation
        semantic_fidelity = min(1.0, 0.5 * lexical_recall + 0.5 * entity_coverage)

        # Hallucination risk: novel words in summary that never appeared in history
        summary_words = set(w.lower() for w in self.KEYWORD_PATTERN.findall(response.summary)) - stopwords
        novel_words = summary_words - orig_words
        hallucination_risk = min(1.0, len(novel_words) / max(1, len(summary_words))) if summary_words else 0.0

        # Determine composite grade
        composite_score = (semantic_fidelity * 0.6) + ((1.0 - hallucination_risk) * 0.4)
        if composite_score >= 0.75:
            grade = "A+ (Production Elite)"
        elif composite_score >= 0.60:
            grade = "A (High Retention)"
        elif composite_score >= 0.45:
            grade = "B (Acceptable)"
        else:
            grade = "C (Needs Tuning)"

        return QualityBenchmarkReport(
            original_tokens=response.original_tokens,
            compressed_tokens=response.compressed_tokens,
            tokens_saved=response.tokens_saved,
            compression_ratio=response.compression_ratio,
            lexical_recall=round(lexical_recall * 100.0, 2),
            entity_coverage=round(entity_coverage * 100.0, 2),
            semantic_fidelity=round(semantic_fidelity * 100.0, 2),
            hallucination_risk=round(hallucination_risk * 100.0, 2),
            composite_grade=grade,
        )
