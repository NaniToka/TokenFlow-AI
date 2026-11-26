"""
Prompt Injection & Jailbreak Security Firewall.

Scans user inputs and conversation turns for adversarial prompt injections:
- Instruction override attempts ("ignore all previous instructions")
- System prompt exfiltration ("reveal your system prompt")
- Delimiter spoofing & role hijacking ("[SYSTEM]:", "<|im_start|>system")
- Base64/Hex encoded smuggling hints
- Jailbreak personas ("DAN", "developer mode", "bypass safety")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class FirewallFinding:
    rule_id: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    description: str
    matched_excerpt: str


@dataclass
class FirewallScanResult:
    is_safe: bool
    risk_score: float
    highest_severity: str
    findings: list[FirewallFinding] = field(default_factory=list)


class PromptInjectionFirewall:
    """Zero-latency deterministic prompt injection & jailbreak detector."""

    RULES: ClassVar[list[tuple[str, str, str, re.Pattern[str], float]]] = [
        (
            "INJ-001",
            "CRITICAL",
            "Direct instruction override attempt detected",
            re.compile(r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:previous|prior|above|system)\s+(?:instructions?|prompts?|rules?)\b", re.IGNORECASE),
            0.95,
        ),
        (
            "INJ-002",
            "HIGH",
            "System prompt exfiltration or extraction probe",
            re.compile(r"\b(?:reveal|print|dump|output|show|repeat)\s+(?:your\s+|the\s+)?(?:system\s+prompt|hidden\s+instructions|initial\s+prompt)\b", re.IGNORECASE),
            0.85,
        ),
        (
            "INJ-003",
            "CRITICAL",
            "Token delimiter / role boundary spoofing",
            re.compile(r"(?:<\|im_start\|>system|<\|endoftext\|>|\[SYSTEM\s*OVERRIDE\]|###\s*SYSTEM\s*PROMPT)", re.IGNORECASE),
            0.95,
        ),
        (
            "INJ-004",
            "HIGH",
            "Adversarial jailbreak persona activation",
            re.compile(r"\b(?:DAN\s+mode|do\s+anything\s+now|enable\s+developer\s+mode|bypass\s+(?:safety|guardrails?|filters?))\b", re.IGNORECASE),
            0.80,
        ),
        (
            "INJ-005",
            "MEDIUM",
            "Suspicious long Base64 payload smuggling",
            re.compile(r"\b(?:decode\s+this\s+base64|eval\(|exec\(|__import__)\b", re.IGNORECASE),
            0.60,
        ),
    ]

    @classmethod
    def scan(cls, texts: list[str] | str) -> FirewallScanResult:
        """Scan one or more strings and aggregate security findings."""
        if isinstance(texts, str):
            corpus = [texts]
        else:
            corpus = texts

        findings: list[FirewallFinding] = []
        max_risk = 0.0
        sev_rank = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        highest_sev = "NONE"

        for text in corpus:
            if not text:
                continue
            for rule_id, severity, desc, pattern, weight in cls.RULES:
                match = pattern.search(text)
                if match:
                    findings.append(
                        FirewallFinding(
                            rule_id=rule_id,
                            severity=severity,
                            description=desc,
                            matched_excerpt=match.group(0)[:80],
                        )
                    )
                    max_risk = max(max_risk, weight)
                    if sev_rank[severity] > sev_rank[highest_sev]:
                        highest_sev = severity

        return FirewallScanResult(
            is_safe=len(findings) == 0,
            risk_score=round(max_risk, 2),
            highest_severity=highest_sev,
            findings=findings,
        )
