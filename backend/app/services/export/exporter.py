"""
Multi-Format Prompt & Analytics Exporter.

Exports compression results and turn-scoring audits to Markdown, JSON, or CSV.
"""

import csv
import io
import json

from app.schemas import CompressResponse


class PromptExporter:
    """Serializes compression outputs into structured files."""

    @staticmethod
    def to_markdown(response: CompressResponse) -> str:
        """Renders an executive summary Markdown report."""
        turns_str = "\n".join(
            f"- **{t.role.upper()}**: {t.content}" for t in response.selected_turns
        )
        return f"""# TokenFlow AI - Context Compression Report

## Summary Metrics
- **Original Tokens**: {response.original_tokens}
- **Compressed Tokens**: {response.compressed_tokens}
- **Tokens Saved**: {response.tokens_saved}
- **Compression Ratio**: {response.compression_ratio}%
- **Cost Saved (USD)**: ${response.cost_saved_usd:.6f}
- **Strategy**: {response.metadata.ranking_strategy} ({response.metadata.compression_mode})

---

## Background Context Summary
> {response.summary or "*(No background summary needed)*"}

---

## Top-K Retained Turns
{turns_str}

---

## Final Optimized Prompt
```text
{response.final_prompt}
```
"""

    @staticmethod
    def to_json(response: CompressResponse) -> str:
        """Exports raw JSON string."""
        return json.dumps(response.model_dump(), indent=2)

    @staticmethod
    def to_csv(response: CompressResponse) -> str:
        """Exports per-turn scoring breakdown as RFC 4180 CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Turn Index",
            "Role",
            "Snippet",
            "BM25 Score",
            "Semantic Score",
            "Recency Score",
            "Drift Penalty",
            "Final Score",
            "Selected",
        ])
        for s in response.metadata.scores:
            writer.writerow([
                s.get("index", 0),
                s.get("role", ""),
                s.get("content_snippet", ""),
                s.get("bm25_score", 0.0),
                s.get("semantic_score", 0.0),
                s.get("recency_score", 0.0),
                s.get("drift_penalty", 0.0),
                s.get("final_score", 0.0),
                s.get("selected", False),
            ])
        return output.getvalue()
