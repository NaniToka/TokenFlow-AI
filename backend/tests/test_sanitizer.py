import pytest
from app.core.sanitizer import InputSanitizer


def test_input_sanitizer():
    dirty = "Hello <script>alert('xss')</script> world! \x00 testing"
    clean = InputSanitizer.sanitize(dirty)
    assert "<script>" not in clean
    assert "alert" not in clean
    assert "\x00" not in clean
    assert "Hello world! testing" in clean


def test_input_sanitizer_empty():
    assert InputSanitizer.sanitize("") == ""
    assert InputSanitizer.sanitize(None) == ""
