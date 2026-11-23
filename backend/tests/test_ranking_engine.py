import pytest
from app.schemas import Turn
from app.core.config import RankingConfig, FeatureFlags
from app.services.ranking.engine import (
    BM25Scorer,
    DriftDetector,
    AdaptiveAlpha,
    RankingEngine,
)


def test_bm25_scorer():
    scorer = BM25Scorer()
    corpus = [
        "Kubernetes pods and ingress controllers routing traffic.",
        "Python FastAPI database scripts with SQLAlchemy.",
        "Deep learning model quantization using TensorRT.",
    ]
    scores = scorer.score("How do I configure Kubernetes ingress?", corpus)
    assert len(scores) == 3
    # Top score should be the Kubernetes document
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]


def test_drift_detector():
    detector = DriftDetector(window_size=2, threshold=0.2)
    turns = [
        Turn(role="user", content="Let's discuss database migrations in Postgres."),
        Turn(role="model", content="We can use Alembic for PostgreSQL migrations."),
        Turn(role="user", content="What did you eat for breakfast today?"),
        Turn(role="model", content="I am an AI, I don't eat food!"),
    ]
    penalties = detector.detect_drift_points(turns)
    assert len(penalties) == 4
    # The off-topic breakfast turn should receive a higher penalty
    assert penalties[2] > 0.0


def test_adaptive_alpha():
    turns = [
        Turn(role="user", content="Turn " + str(i)) for i in range(10)
    ]
    penalties = [0.0] * 10
    alpha = AdaptiveAlpha.compute(turns, penalties, base_alpha=0.7)
    assert 0.3 <= alpha <= 0.9


def test_ranking_engine_execution():
    config = RankingConfig()
    features = FeatureFlags()
    engine = RankingEngine(config, features)

    history = [
        Turn(role="user", content="How do I configure AWS EKS?"),
        Turn(role="model", content="Use eksctl or Terraform modules."),
        Turn(role="user", content="What about S3 state locking?"),
        Turn(role="model", content="Use DynamoDB table with LockID key."),
    ]
    result = engine.rank_turns(
        history=history,
        current_message="How do I resolve DynamoDB lock conflict?",
        top_k=2,
    )
    assert len(result.selected_turns) == 2
    assert len(result.unselected_turns) == 2
    assert result.alpha_used > 0
    assert "bm25" in result.ranking_strategy
