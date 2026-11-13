import pytest
from app.utils.resilience import retry_with_backoff


def test_retry_with_backoff_success_on_first_try():
    calls = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def dummy_func():
        nonlocal calls
        calls += 1
        return "success"

    result = dummy_func()
    assert result == "success"
    assert calls == 1


def test_retry_with_backoff_eventual_success():
    calls = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def flaky_func():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise ConnectionError("Temporary network hiccup")
        return "recovered"

    result = flaky_func()
    assert result == "recovered"
    assert calls == 2


def test_retry_with_backoff_exhausts_retries():
    calls = 0

    @retry_with_backoff(max_retries=2, initial_delay=0.01, retryable_exceptions=(ValueError,))
    def always_fails():
        nonlocal calls
        calls += 1
        raise ValueError("Persistent bad input")

    with pytest.raises(ValueError):
        always_fails()

    assert calls == 2
