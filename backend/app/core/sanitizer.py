"""
Input Sanitizer, XSS Defense, and PII/Secret Redaction Guard.

Sanitizes prompt inputs, strips dangerous script injections, enforces strict
UTF-8 normalization, and optionally redacts sensitive secrets/PII before
prompts reach external LLM providers.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class SanitizationResult:
    """Result of sanitizing and redacting input text."""

    sanitized_text: str
    xss_stripped: int = 0
    redactions_count: int = 0
    redacted_types: list[str] = field(default_factory=list)


class InputSanitizer:
    """Sanitizes text inputs to protect downstream LLMs and web UIs."""

    INJECTION_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"onload\s*=", re.IGNORECASE),
        re.compile(r"onerror\s*=", re.IGNORECASE),
    ]

    PII_PATTERNS: ClassVar[list[tuple[str, re.Pattern[str], str]]] = [
        ("GEMINI_API_KEY", re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"), "[REDACTED_API_KEY]"),
        ("OPENAI_KEY", re.compile(r"\bsk-[A-Za-z0-9\-_]{20,}\b"), "[REDACTED_API_KEY]"),
        ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[REDACTED_TOKEN]"),
        ("JWT_TOKEN", re.compile(r"\beyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b"), "[REDACTED_JWT]"),
        ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
        ("IPV4_ADDR", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
        ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    ]

    @classmethod
    def sanitize(cls, text: str | None) -> str:
        """Sanitizes XSS vectors, control characters, and normalizes Unicode."""
        if not text:
            return ""

        normalized = unicodedata.normalize("NFKC", text)

        for pattern in cls.INJECTION_PATTERNS:
            normalized = pattern.sub("", normalized)

        cleaned = "".join(
            ch for ch in normalized if ch in "\n\r\t" or unicodedata.category(ch)[0] != "C"
        )
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        return cleaned.strip()

    @classmethod
    def sanitize_and_redact(cls, text: str | None, redact_pii: bool = False) -> SanitizationResult:
        """Sanitizes text and optionally masks sensitive PII/credentials."""
        if not text:
            return SanitizationResult(sanitized_text="")

        normalized = unicodedata.normalize("NFKC", text)
        xss_count = 0
        for pattern in cls.INJECTION_PATTERNS:
            normalized, n = pattern.subn("", normalized)
            xss_count += n

        cleaned = "".join(
            ch for ch in normalized if ch in "\n\r\t" or unicodedata.category(ch)[0] != "C"
        )
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()

        redactions = 0
        redacted_types: list[str] = []
        if redact_pii:
            for pii_label, pattern, replacement in cls.PII_PATTERNS:
                cleaned, count = pattern.subn(replacement, cleaned)
                if count > 0:
                    redactions += count
                    if pii_label not in redacted_types:
                        redacted_types.append(pii_label)

        return SanitizationResult(
            sanitized_text=cleaned,
            xss_stripped=xss_count,
            redactions_count=redactions,
            redacted_types=redacted_types,
        )
