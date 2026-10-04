# Good First Issues

These are curated "good first issues" for new contributors looking to get familiar with the TokenFlow codebase.

## Issue 1: Add a `/api/v1/metrics/prometheus` endpoint
**Description**: Currently, we have a `/api/v1/stats` endpoint returning JSON stats. It would be highly useful for enterprise users to have a `/api/v1/metrics/prometheus` endpoint that formats the in-memory stats tracker into Prometheus-compatible plaintext metrics.
**Where to start**: `backend/app/main.py` and `backend/app/services/stats_logger.py`.

## Issue 2: Support for `top_p` semantic filtering
**Description**: The API currently accepts `top_k` (an integer) to blindly pick the top K ranked turns. We should also accept an optional `top_p` (float between 0-1) that acts as a threshold. If a turn's final score is below `top_p`, it is discarded even if it's within the top K.
**Where to start**: Add `top_p` to `CompressRequest` in `backend/app/schemas.py`, and implement the filter logic in `backend/app/services/memory_ranker.py`.

## Issue 3: Standardize structured JSON logging
**Description**: Right now we use standard Python logging. To be truly production-ready, we should use a library like `python-json-logger` or `structlog` to output our logs in JSON format, making them easier to ingest into Datadog or ELK stacks.
**Where to start**: Modify `logger` initialization in `backend/app/main.py` and `backend/app/services/compressor.py`.

## Issue 4: Add Docker compose volume for persistence (Optional)
**Description**: If a user runs TokenFlow via Docker Compose, they lose session stats on restart. Add an optional SQLite integration or local volume mount for the stats tracker to persist data across container reboots.
**Where to start**: Look at `backend/app/services/stats_logger.py` and update `docker-compose.yml`.

## Issue 5: Expand test coverage for edge cases
**Description**: We have unit tests for core ranking and API routes, but we are missing tests for extreme edge cases: what if the system instruction is 50,000 tokens long? What if the history contains non-UTF8 characters? 
**Where to start**: Add a new test file `backend/tests/test_edge_cases.py` and write 3-4 pytest cases demonstrating the API handles these gracefully without crashing.
