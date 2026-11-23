import pytest
from app.schemas import Turn, CompressResponse, CompressionMetadata
from app.services.export.exporter import PromptExporter


def test_exporter_markdown_and_json():
    response = CompressResponse(
        summary="User is asking about EKS setup.",
        selected_turns=[Turn(role="user", content="Setup EKS cluster.")],
        final_prompt="Final optimized prompt content",
        original_tokens=80,
        compressed_tokens=40,
        tokens_saved=40,
        cost_before_usd=0.000006,
        cost_after_usd=0.000003,
        cost_saved_usd=0.000003,
        compression_ratio=50.0,
        metadata=CompressionMetadata(),
    )

    md = PromptExporter.to_markdown(response)
    assert "# TokenFlow AI" in md
    assert "Tokens Saved" in md
    assert "Final optimized prompt content" in md

    js = PromptExporter.to_json(response)
    assert "compressed_tokens" in js
    assert "50.0" in js
