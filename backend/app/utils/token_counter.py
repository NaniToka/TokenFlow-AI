"""
Token counting and multi-model cost estimation utilities with offline fallback.

Uses tiktoken when encodings are cached/available locally,
and falls back to calibrated character/word-level estimation
when network is unreachable or tiktoken is unavailable.
"""

import re
from typing import Any

_TIKTOKEN_ENCODING = None
_TIKTOKEN_INITIALIZED = False

MODEL_PRICING: dict[str, dict[str, Any]] = {
    "gemini-2.0-flash": {
        "display_name": "Gemini 2.0 Flash",
        "provider": "Google",
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
        "context_window": 1_000_000,
    },
    "gemini-1.5-flash": {
        "display_name": "Gemini 1.5 Flash",
        "provider": "Google",
        "input_per_1m": 0.075,
        "output_per_1m": 0.30,
        "context_window": 1_000_000,
    },
    "gemini-1.5-pro": {
        "display_name": "Gemini 1.5 Pro",
        "provider": "Google",
        "input_per_1m": 1.25,
        "output_per_1m": 5.00,
        "context_window": 2_000_000,
    },
    "gpt-4o": {
        "display_name": "GPT-4o",
        "provider": "OpenAI",
        "input_per_1m": 2.50,
        "output_per_1m": 10.00,
        "context_window": 128_000,
    },
    "gpt-4o-mini": {
        "display_name": "GPT-4o Mini",
        "provider": "OpenAI",
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
        "context_window": 128_000,
    },
    "claude-3-5-sonnet": {
        "display_name": "Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
        "context_window": 200_000,
    },
}


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

    tokens = re.findall(r"\w+|[^\w\s]|\s+", text)
    est_count = max(1, int(len(tokens) * 0.85)) if tokens else 0
    return max(1, est_count) if text.strip() else 0


def calculate_gemini_cost(tokens: int, is_input: bool = True, model: str = "gemini-1.5-flash") -> float:
    """Calculates USD cost based on target model pricing table."""
    if tokens <= 0:
        return 0.0

    key = model.lower()
    if key in MODEL_PRICING:
        pricing = MODEL_PRICING[key]
        rate_per_million = float(pricing["input_per_1m"] if is_input else pricing["output_per_1m"])
    elif "pro" in key:
        rate_per_million = 1.25 if is_input else 5.0
    else:
        rate_per_million = 0.075 if is_input else 0.30

    cost = (tokens / 1_000_000.0) * rate_per_million
    return round(cost, 8)


def calculate_savings(
    original_tokens: int,
    compressed_tokens: int,
    model: str = "gemini-1.5-flash",
) -> dict[str, Any]:
    """Calculates token reduction and cost savings metrics for a given target model."""
    tokens_saved = max(0, original_tokens - compressed_tokens)

    if original_tokens > 0:
        compression_ratio = round((1.0 - (compressed_tokens / original_tokens)) * 100.0, 2)
    else:
        compression_ratio = 0.0

    cost_before_usd = calculate_gemini_cost(original_tokens, is_input=True, model=model)
    cost_after_usd = calculate_gemini_cost(compressed_tokens, is_input=True, model=model)
    cost_saved_usd = round(max(0.0, cost_before_usd - cost_after_usd), 8)

    return {
        "tokens_saved": tokens_saved,
        "compression_ratio": compression_ratio,
        "cost_before_usd": cost_before_usd,
        "cost_after_usd": cost_after_usd,
        "cost_saved_usd": cost_saved_usd,
    }


def list_supported_models() -> list[dict[str, Any]]:
    """Returns structured pricing metadata for all supported target LLMs."""
    return [
        {"id": model_id, **info}
        for model_id, info in MODEL_PRICING.items()
    ]
