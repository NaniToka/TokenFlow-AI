"""
Multi-turn dialogue simulation test harness.
Provides deterministic scenario generators for evaluating context compression fidelity.
"""

from typing import List, Dict, Any
from app.schemas import Turn


class DialogueSimulator:
    """Simulates multi-turn conversations across varied technical domains."""

    SCENARIOS = {
        "devops": [
            ("user", "We are seeing high memory usage in our Kubernetes pods."),
            ("model", "Check kubectl top pods and review container memory limits in your deployment spec."),
            ("user", "The OOMKilled count is increasing on worker-node-3."),
            ("model", "Increase resources.limits.memory or profile heap allocation for memory leaks."),
            ("user", "We suspect the Python garbage collector is not freeing tensor buffers."),
            ("model", "Try calling gc.collect() explicitly and verify if tracemalloc reveals uncollected buffers."),
            ("user", "How do we add automated memory alerts in Prometheus?"),
            ("model", "Create a PrometheusRule checking container_memory_working_set_bytes exceeding 85% of limit."),
        ],
        "database": [
            ("user", "Our PostgreSQL query on the orders table is taking 4.2 seconds."),
            ("model", "Run EXPLAIN ANALYZE to check if a sequential scan is happening."),
            ("user", "The query planner shows Seq Scan on orders filter created_at > now() - interval '7 days'."),
            ("model", "Add a B-tree index on created_at: CREATE INDEX idx_orders_created_at ON orders (created_at)."),
            ("user", "The index scan dropped latency to 12ms. Now connection count is maxing out."),
            ("model", "Deploy PgBouncer in transaction pooling mode to multiplex client connections."),
        ],
    }

    @classmethod
    def generate_turns(cls, scenario: str = "devops", repeat: int = 1) -> List[Turn]:
        raw_turns = cls.SCENARIOS.get(scenario, cls.SCENARIOS["devops"])
        turns = []
        for r in range(repeat):
            for role, text in raw_turns:
                suffix = f" (cycle {r+1})" if r > 0 else ""
                turns.append(Turn(role=role, content=f"{text}{suffix}"))
        return turns

    @classmethod
    def get_summary_stats(cls, turns: List[Turn]) -> Dict[str, Any]:
        user_count = sum(1 for t in turns if t.role == "user")
        model_count = sum(1 for t in turns if t.role == "model")
        total_chars = sum(len(t.content) for t in turns)
        return {
            "total_turns": len(turns),
            "user_turns": user_count,
            "model_turns": model_count,
            "total_characters": total_chars,
        }
