"""
Input Sanitizer & XSS Defense.

Sanitizes prompt inputs, strips dangerous script injections, and enforces strict UTF-8 normalization.
"""

import re
import html
import unicodedata


class InputSanitizer:
    """Sanitizes text inputs to protect downstream LLMs and web UIs."""

    INJECTION_PATTERNS = [
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"onload\s*=", re.IGNORECASE),
        re.compile(r"onerror\s*=", re.IGNORECASE),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return ""

        # Normalize unicode to NFKC
        normalized = unicodedata.normalize("NFKC", text)

        # Neutralize malicious tags
        for pattern in cls.INJECTION_PATTERNS:
            normalized = pattern.sub("", normalized)

        # Strip null bytes and control chars (except standard newlines/tabs)
        cleaned = "".join(ch for ch in normalized if ch in "\n\r\t" or unicodedata.category(ch)[0] != "C")

        # Collapse multiple spaces
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        return cleaned.strip()
