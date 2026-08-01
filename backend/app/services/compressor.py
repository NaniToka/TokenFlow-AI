import logging
from typing import List
from google import genai
from app.schemas import Turn
from app.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client | None:
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY is not set or using default placeholder.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Client: {e}")
        return None


def _local_fallback_summary(unselected_turns: List[Turn]) -> str:
    """
    Extractive fallback summary when Gemini API key is missing or call fails.
    """
    if not unselected_turns:
        return ""

    user_turns = [t.content.strip() for t in unselected_turns if t.role == "user"]
    if not user_turns:
        user_turns = [t.content.strip() for t in unselected_turns]
    
    if not user_turns:
        return ""

    selected_points = user_turns[:3]
    summary_lines = []
    for pt in selected_points:
        if len(pt) > 80:
            pt = pt[:77] + "..."
        summary_lines.append(f"• {pt}")
    
    return "Prior context summary:\n" + "\n".join(summary_lines)


def summarize_turns(unselected_turns: List[Turn], model: str = "gemini-1.5-flash") -> str:
    """
    Summarizes unselected/older conversation turns into a compact 2-3 sentence memory summary using Gemini Flash.
    Returns an empty string if unselected_turns is empty.
    """
    if not unselected_turns:
        return ""

    # Format turns into a structured text log
    formatted_log = "\n".join(
        [f"[{turn.role.capitalize()}]: {turn.content}" for turn in unselected_turns]
    )

    client = _get_client()
    if not client:
        return _local_fallback_summary(unselected_turns)

    prompt = (
        "Summarize the following prior conversation background in 2-3 concise sentences. "
        "Focus strictly on key facts, decisions, entities, user preferences, and constraints. "
        "Do NOT include fluff, greetings, or irrelevant detail.\n\n"
        f"Conversation History:\n{formatted_log}"
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        if response and response.text:
            return response.text.strip()
        return _local_fallback_summary(unselected_turns)
    except Exception as e:
        logger.error(f"Error generating summary from Gemini Flash ({model}): {e}")
        return _local_fallback_summary(unselected_turns)
