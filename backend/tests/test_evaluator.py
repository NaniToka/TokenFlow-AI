import pytest
from app.schemas import Turn, CompressResponse, CompressionMetadata
from app.services.evaluation.evaluator import ContextQualityEvaluator


def test_evaluator_basic():
    evaluator = ContextQualityEvaluator()
    history = [
        Turn(role="user", content="Deploy PostgreSQL database with connection pooling and SSL."),
        Turn(role="model", content="Configured PostgreSQL with PgBouncer connection pool."),
    ]
    response = CompressResponse(
        summary="Prior context summary: Configured PostgreSQL with PgBouncer.",
        selected_turns=[history[1]],
        final_prompt="[RELEVANT RECENT HISTORY]\n[Model]: Configured PostgreSQL with PgBouncer.\n\n[CURRENT USER MESSAGE]\nEnable SSL",
        original_tokens=100,
        compressed_tokens=50,
        tokens_saved=50,
        cost_before_usd=0.0001,
        cost_after_usd=0.00005,
        cost_saved_usd=0.00005,
        compression_ratio=50.0,
        metadata=CompressionMetadata(),
    )

    report = evaluator.evaluate(history, response)
    assert report.tokens_saved == 50
    assert report.compression_ratio == 50.0
    assert report.lexical_recall > 0.0
    assert "A" in report.composite_grade or "B" in report.composite_grade
