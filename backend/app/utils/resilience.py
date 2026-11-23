"""
Resilience utilities for external API integrations.
Provides exponential backoff with full jitter to avoid thundering herd problems.
"""

import time
import random
import logging
from typing import Callable, Any, Type, Tuple

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator that retries a synchronous function using exponential backoff with jitter.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            delay = initial_delay

            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    attempt += 1
                    if attempt >= max_retries:
                        logger.error(f"Function {func.__name__} exhausted {max_retries} retries: {e}")
                        raise

                    jitter = random.uniform(0.8, 1.2)
                    sleep_time = delay * jitter
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} for {func.__name__} failed with {type(e).__name__}: {e}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor

        return wrapper
    return decorator
