# Contributing to TokenFlow AI

First off, thank you for considering contributing to TokenFlow AI! We welcome community contributions.

## How Can I Contribute?

### Reporting Bugs
- Ensure the bug was not already reported by searching on GitHub under [Issues].
- If you're unable to find an open issue addressing the problem, open a new one. Be sure to include a title and clear description, as much relevant information as possible, and a code sample or an executable test case demonstrating the expected behavior that is not occurring.

### Suggesting Enhancements
- Open a new issue with a clear title and description.
- Explain why this enhancement would be useful to most users.

### Pull Requests
1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes (run `pytest`).
5. Make sure your code lints.
6. Issue that pull request!

## Local Development Setup

1. Clone the repository.
2. Install Python dependencies: `cd backend && pip install -r requirements.txt`.
3. Set up the environment: `cp backend/.env.example backend/.env`.
4. Run the API: `uvicorn app.main:app --reload`.

## Styleguides
### Git Commit Messages
* Use the present tense ("Add feature" not "Added feature").
* Limit the first line to 72 characters or less.
* Reference issues and pull requests liberally after the first line.
