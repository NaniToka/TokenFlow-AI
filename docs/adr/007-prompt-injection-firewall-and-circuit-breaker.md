# ADR-007: Zero-Trust Prompt Injection Firewall & 3-State LLM Circuit Breaker

- **Status**: Accepted
- **Date**: 2026-11-26

## Context

Compression middleware proxies untrusted user turns directly toward downstream LLMs, creating two reliability and security hazards:
1. Prompt injection & delimiter spoofing attacks embedded in older turns can survive summarization or selection if undetected.
2. Upstream embedding/generation API outages cause cascading request timeouts across synchronous and streaming workers.

## Decision

1. **Prompt Injection Firewall (`backend/app/core/guardrails.py`)**: Compiled deterministic signatures `INJ-001` through `INJ-005` detect instruction overrides, system prompt exfiltration probes, role boundary spoofing (`<|im_start|>system`, `[SYSTEM OVERRIDE]`), jailbreak persona activation, and suspicious Base64/eval smuggling. Results surface in `CompressResponse.metadata.firewall` and `/api/v1/guard/scan`.
2. **3-State Circuit Breaker (`backend/app/services/llm/circuit_breaker.py`)**: Tracks consecutive upstream failures (`CLOSED -> OPEN -> HALF_OPEN`), failing fast to local offline fallback modes once `failure_threshold=3` is hit and exposing Prometheus gauge `tokenflow_llm_circuit_breaker_state` plus `/api/v1/circuit-breaker/reset`.

## Consequences

- Security findings never mutate user audit logs cleanly (`audit_log_buffer.py` records telemetry metadata only, zero raw prompts).
- Latency stays bounded during external API outages without operator intervention.
