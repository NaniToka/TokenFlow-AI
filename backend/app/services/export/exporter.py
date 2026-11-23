"""
Multi-Format Prompt & Analytics Exporter.

Exports compression results and session logs to Markdown, JSON, or CSV for reporting.
"""

import json
from typing import Dict, Any, List
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

## 📊 Summary Metrics
- **Original Tokens**: {response.original_tokens}
- **Compressed Tokens**: {response.compressed_tokens}
- **Tokens Saved**: {response.tokens_saved}
- **Compression Ratio**: {response.compression_ratio}%
- **Cost Saved (USD)**: ${response.cost_saved_usd:.6f}

---

## 📝 Background Context Summary
> {response.summary or "*(No background summary needed)*"}

---

## 🎯 Top-K Retained Turns
{turns_str}

---

## 🚀 Final Optimized Prompt
```text
{response.final_prompt}
```
"""

    @staticmethod
    def to_json(response: CompressResponse) -> str:
        """Exports raw JSON string."""
        return json.dumps(response.model_dump(), indent=2)
