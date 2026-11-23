# ADR-002: Stateless Memory Middleware Architecture

## Context
Enterprise deployments in healthcare (HIPAA) and finance (SOC 2, GDPR) strictly restrict persisting user chat logs, prompts, and confidential PII to disk or external databases.

## Decision
TokenFlow AI operates as a **100% stateless middleware**:
- Ingests raw conversation history strictly in-memory per HTTP/WebSocket request.
- Performs ranking, extraction, and summarization in ephemeral RAM buffers.
- Only numerical telemetric aggregates (tokens saved, cost saved, latencies) are logged for dashboard analytics; zero prompt text is ever retained or written to databases.

## Consequences
- **Positive**: Zero regulatory risk for GDPR Right-to-be-Forgotten or HIPAA ePHI compliance.
- **Positive**: Enables instant multi-region horizontal scaling without state synchronization or database locks.
- **Trade-off**: Client must supply conversation history with each turn, though TokenFlow immediately reduces downstream LLM payload size by 35–45%.
