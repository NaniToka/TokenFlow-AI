import logging
from typing import List
from google import genai
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


def get_embedding(text: str, model: str = "text-embedding-004") -> List[float]:
    """
    Generates a vector embedding for a single text using Gemini text-embedding-004.
    Returns a list of floats, or an empty list if an error occurs.
    """
    if not text or not text.strip():
        return []

    client = _get_client()
    if not client:
        return []

    try:
        response = client.models.embed_content(
            model=model,
            contents=text
        )
        if response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0].values or []
        return []
    except Exception as e:
        logger.error(f"Error fetching embedding from Gemini API ({model}): {e}")
        return []


def get_batch_embeddings(texts: List[str], model: str = "text-embedding-004") -> List[List[float]]:
    """
    Generates vector embeddings for a list of text strings efficiently using Gemini text-embedding-004.
    Returns a list of float vectors matching the order of input texts.
    """
    if not texts:
        return []

    client = _get_client()
    if not client:
        return [[] for _ in texts]

    try:
        response = client.models.embed_content(
            model=model,
            contents=texts
        )
        if response.embeddings and len(response.embeddings) == len(texts):
            return [emb.values or [] for emb in response.embeddings]
        
        # Fallback if structure varies
        embeddings = []
        if response.embeddings:
            for emb in response.embeddings:
                embeddings.append(emb.values or [])
        while len(embeddings) < len(texts):
            embeddings.append([])
        return embeddings
    except Exception as e:
        logger.error(f"Error fetching batch embeddings from Gemini API: {e}")
        # Graceful fallback to individual requests or empty lists
        results = []
        for text in texts:
            results.append(get_embedding(text, model=model))
        return results
