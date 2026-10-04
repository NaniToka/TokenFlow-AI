# TokenFlow AI - 90 Second Demo Script

## Preparation
- Have the local server running: `docker compose up -d`
- Open `http://localhost:8000` in your browser to the Dashboard.
- Open your terminal side-by-side with the browser.

## Shot List & Commands

**0:00 - 0:15 | Intro & The Problem**
*(Screen: Terminal with a massive JSON payload visible)*
- **Voiceover**: "When building LLM apps, sending long chat histories over and over inflates your token costs and eats up context windows."
- **Action**: Scroll through a massive 15-turn JSON conversation history payload.

**0:15 - 0:40 | The Solution in Action**
*(Screen: TokenFlow Dashboard - Custom Prompt Tester)*
- **Voiceover**: "TokenFlow is a stateless middleware that fixes this. Watch."
- **Action**: Paste the payload into the Dashboard, click "Compress Prompt".
- **Action**: Highlight the result visually. "It automatically drops irrelevant turns, creates a background memory note using Gemini Flash, and returns an optimized prompt."

**0:40 - 0:60 | The Savings**
*(Screen: Dashboard Analytics View)*
- **Voiceover**: "Because it counts tokens precisely, you can see the exact savings."
- **Action**: Click to the Analytics tab. Hover over the 74% reduction bar and the estimated USD savings.
- **Voiceover**: "We cut token payloads by up to 75% with zero database state required."

**1:00 - 1:30 | Easy Integration**
*(Screen: Terminal)*
- **Voiceover**: "It runs completely locally in a Docker container or mounts to your existing FastAPI app."
- **Action**: Run `curl -X POST http://localhost:8000/api/v1/compress -d '{"current_message": "..."}'` and show the fast JSON response.
- **Voiceover**: "TokenFlow. Save tokens, speed up responses. Check out the repo on GitHub."

## Required Screenshots for README/Repo
1. `prompt-visualizer.png`: The side-by-side view of a compressed vs original prompt.
2. `analytics-dashboard.png`: The token reduction graph and USD savings.
3. `api-docs.png`: The FastAPI Swagger UI at `/docs`.
