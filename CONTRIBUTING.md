# Contributing to TokenFlow-AI

Thank you for your interest in contributing to **TokenFlow-AI**! We welcome bug reports, documentation improvements, algorithmic optimizations, and feature pull requests.

---

## 1. Development Environment Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- `git`
- (Optional) Docker for containerized testing

### Initial Setup
```bash
# Clone repository
git clone https://github.com/NaniToka/TokenFlow-AI.git
cd TokenFlow-AI

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (runtime + testing)
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio httpx ruff black
```

---

## 2. Running Tests & Benchmarks

Before submitting any code, verify that all tests pass:

```bash
# Run full unit and integration test suite
pytest backend/tests/ -v

# Run performance and latency benchmarks
python benchmarks/benchmark_suite.py
```

All new features and bug fixes MUST include corresponding unit tests in `backend/tests/`.

---

## 3. Code Style & Standards

We enforce modern, clean Python conventions:
- **Type Annotations**: Use Python type hints on all public functions and methods (`from typing import List, Dict, Optional`).
- **Formatting**: Format code with `black` (88 character line limit).
- **Linting**: Clean linting with `ruff check backend/`.
- **Validation**: Use Pydantic v2 models for all API request and response data structures.

---

## 4. Conventional Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification to keep the changelog structured and reproducible:

```
<type>(<scope>): <short description>
```

### Types:
- `feat`: A new feature or algorithm improvement.
- `fix`: A bug fix.
- `test`: Adding or updating test suites.
- `docs`: Documentation updates or additions.
- `perf`: A code change that improves performance or latency.
- `ci`: GitHub Actions or CI configuration changes.
- `refactor`: Code restructuring without behavioral changes.

### Examples:
- `feat(compressor): add configurable exponential recency decay tuner`
- `test(api): add payload validation edge case unit tests`
- `docs(api): add comprehensive API specification and schema documentation`

---

## 5. Pull Request Workflow

1. **Create a branch**: Branch off `main` with a descriptive name:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Implement changes**: Keep commits modular and self-contained.
3. **Verify tests**: Run `pytest backend/tests/ -v`.
4. **Push branch**:
   ```bash
   git push origin feat/your-feature-name
   ```
5. **Open Pull Request**: Describe your change, motivation, and link any related issues.
