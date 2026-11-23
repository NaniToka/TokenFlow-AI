"""
Token counting and cost estimation utilities with offline fallback.

Uses tiktoken when encodings are cached/available locally,
and falls back to calibrated character/word-level estimation
when network is unreachable or tiktoken is unavailable.
"""

import re
from typing import Any

_TIKTOKEN_ENCODING = None
_TIKTOKEN_INITIALIZED = False


def _get_encoding():
    """Lazily load tiktoken encoding, catching any network/cache errors."""
    global _TIKTOKEN_ENCODING, _TIKTOKEN_INITIALIZED
    if _TIKTOKEN_INITIALIZED:
        return _TIKTOKEN_ENCODING

    try:
        import tiktoken
        _TIKTOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _TIKTOKEN_ENCODING = None

    _TIKTOKEN_INITIALIZED = True
    return _TIKTOKEN_ENCODING


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Counts the number of tokens for a given text.
    Uses tiktoken encoding if available; falls back to calibrated token estimation.
    """
    if not text:
        return 0

    encoding = _get_encoding()
    if encoding is not None:
        try:
            return len(encoding.encode(text))
        except Exception:
            pass

    # Calibrated offline fallback:
    # Standard English text averages ~4 characters per token or ~1.3 tokens per whitespace word.
    # We use a regex splitting on words, punctuation, and whitespace sequences.
    tokens = re.findall(r"\w+|[^\w\s]|\s+", text)
    # Calibrate: raw regex tokens correlate closely with BPE subwords
    est_count = max(1, int(len(tokens) * 0.85)) if tokens else 0
    return max(1, est_count) if text.strip() else 0


def calculate_gemini_cost(tokens: int, is_input: bool = True, model: str = "gemini-1.5-flash") -> float:
    """
    Calculates USD cost based on standard Gemini pricing:
    - Gemini 1.5 Flash: $0.075 input / $0.30 output per 1M tokens
    - Gemini 1.5 Pro: $1.25 input / $5.00 output per 1M tokens
    """
    if tokens <= 0:
        return 0.0

    if "pro" in model.lower():
        rate_per_million = 1.25 if is_input else 5.0
    else:
        rate_per_million = 0.075 if is_input else 0.30

    cost = (tokens / 1_000_000.0) * rate_per_million
    return round(cost, 8)


def calculate_savings(original_tokens: int, compressed_tokens: int) -> dict[str, Any]:
    """Calculates token reduction and cost savings metrics."""
    tokens_saved = max(0, original_tokens - compressed_tokens)

    if original_tokens > 0:
        compression_ratio = round((1.0 - (compressed_tokens / original_tokens)) * 100.0, 2)
    else:
        compression_ratio = 0.0

    cost_before_usd = calculate_gemini_cost(original_tokens, is_input=True)
    cost_after_usd = calculate_gemini_cost(compressed_tokens, is_input=True)
    cost_saved_usd = round(max(0.0, cost_before_usd - cost_after_usd), 8)

    return {
        "tokens_saved": tokens_saved,
        "compression_ratio": compression_ratio,
        "cost_before_usd": cost_before_usd,
        "cost_after_usd": cost_after_usd,
        "cost_saved_usd": cost_saved_usd,
    }
