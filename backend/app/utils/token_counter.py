import tiktoken
from typing import Dict, Any


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Counts the exact number of tokens for a given text using tiktoken encoding.
    """
    if not text:
        return 0
    try:
        encoding = tiktoken.get_encoding(model)
    except KeyError:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def calculate_gemini_cost(tokens: int, is_input: bool = True) -> float:
    """
    Calculates USD cost based on standard Gemini 1.5 Flash pricing:
    - Input tokens: $0.075 per 1,000,000 tokens
    - Output tokens: $0.30 per 1,000,000 tokens
    """
    if tokens <= 0:
        return 0.0
    
    rate_per_million = 0.075 if is_input else 0.30
    cost = (tokens / 1_000_000.0) * rate_per_million
    return round(cost, 8)


def calculate_savings(original_tokens: int, compressed_tokens: int) -> Dict[str, Any]:
    """
    Calculates token reduction and cost savings metrics.
    """
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
