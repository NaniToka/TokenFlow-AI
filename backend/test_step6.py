import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app


def test_stats_api():
    print("\n--- Testing Session Stats API Endpoints ---")
    client = TestClient(app)

    # 1. Reset stats first
    reset_res = client.post("/api/v1/stats/reset")
    assert reset_res.status_code == 200

    # Verify initial stats are zero
    stats_res = client.get("/api/v1/stats")
    initial_stats = stats_res.json()
    assert initial_stats["total_requests"] == 0
    assert initial_stats["total_tokens_saved"] == 0

    print("Initial stats verified (0 requests).")

    # 2. Send multi-turn request 1
    req1 = {
        "history": [
            {"role": "user", "content": "I am working on Python backend performance optimization for our microservices."},
            {"role": "model", "content": "Python code performance can be profiled using tools like cProfile and py-spy."},
            {"role": "user", "content": "We noticed high memory consumption during peak traffic hours."},
            {"role": "model", "content": "Memory leaks in Python often stem from global references or unclosed file/db handles."},
            {"role": "user", "content": "We are considering switching our server framework from Flask to FastAPI."},
            {"role": "model", "content": "FastAPI leverages async event loops with Starlette and Pydantic validation for lower latency."},
            {"role": "user", "content": "What database ORM works best with async FastAPI?"},
            {"role": "model", "content": "SQLAlchemy 2.0 with async engine driver or Tortoise ORM are recommended options."}
        ],
        "current_message": "Can you show how to setup SQLAlchemy 2.0 async sessionmaker in FastAPI?",
        "top_k": 2
    }
    res1 = client.post("/api/v1/compress", json=req1)
    assert res1.status_code == 200

    # 3. Send multi-turn request 2
    req2 = {
        "history": [
            {"role": "user", "content": "We are deploying a Kubernetes cluster on AWS EKS with Terraform."},
            {"role": "model", "content": "AWS EKS with Terraform module terraform-aws-modules/eks is a standard pattern."},
            {"role": "user", "content": "How do we manage ingress controllers and SSL certificates automatically?"},
            {"role": "model", "content": "AWS Load Balancer Controller combined with cert-manager and Let's Encrypt works great."},
            {"role": "user", "content": "What node group instances are cost effective for production worker nodes?"},
            {"role": "model", "content": "AWS Graviton (m6g/c6g) ARM instance families offer ~20% better price performance."},
            {"role": "user", "content": "How do we configure cluster autoscaling for spike traffic?"},
            {"role": "model", "content": "Karpenter provides much faster node provisioning than standard Cluster Autoscaler."}
        ],
        "current_message": "Can you provide a minimal Karpenter NodePool manifest for AWS EKS?",
        "top_k": 2
    }
    res2 = client.post("/api/v1/compress", json=req2)
    assert res2.status_code == 200

    # 4. Fetch cumulative stats
    stats_res2 = client.get("/api/v1/stats")
    stats_data = stats_res2.json()

    print("\n--- Cumulative Session Statistics ---")
    print(f"Total Requests:           {stats_data['total_requests']}")
    print(f"Total Original Tokens:    {stats_data['total_original_tokens']}")
    print(f"Total Compressed Tokens:  {stats_data['total_compressed_tokens']}")
    print(f"Total Tokens Saved:       {stats_data['total_tokens_saved']}")
    print(f"Avg Compression Ratio:    {stats_data['avg_compression_ratio']}%")
    print(f"Total Cost Saved:         ${stats_data['total_cost_saved_usd']:.8f}")
    print(f"Request History Logs:     {len(stats_data['request_history'])} entries")

    assert stats_data["total_requests"] == 2
    assert stats_data["total_original_tokens"] > 0
    assert stats_data["total_tokens_saved"] > 0
    assert len(stats_data["request_history"]) == 2
    assert stats_data["avg_compression_ratio"] > 0

    # 5. Reset stats and verify cleanup
    print("\nResetting session statistics...")
    reset_res2 = client.post("/api/v1/stats/reset")
    assert reset_res2.status_code == 200

    stats_res3 = client.get("/api/v1/stats")
    reset_data = stats_res3.json()
    assert reset_data["total_requests"] == 0
    assert reset_data["total_tokens_saved"] == 0
    assert len(reset_data["request_history"]) == 0

    print("✅ Stats reset verified! All metrics reset to zero.")
    print("\n✅ Session Stats API test passed successfully!")


if __name__ == "__main__":
    test_stats_api()
