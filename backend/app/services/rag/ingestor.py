"""
Multi-Format Document File Ingestor for RAG Pipeline.

Parses uploaded text, Markdown, JSON, Python, CSV, and log files safely
into normalized text blocks with file extension metadata.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

ALLOWED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".log", ".csv", ".yaml", ".yml"}
MAX_FILE_BYTES = 1_000_000  # 1 MB safety limit


@dataclass
class IngestedDocument:
    filename: str
    extension: str
    normalized_text: str
    byte_size: int
    line_count: int


def parse_uploaded_file(filename: str, raw_bytes: bytes) -> IngestedDocument:
    """
    Validate and decode uploaded file bytes into normalized text.

    Raises:
        ValueError: If file exceeds MAX_FILE_BYTES, has unsupported extension, or is empty.
    """
    if not filename:
        raise ValueError("Filename cannot be empty.")

    if len(raw_bytes) > MAX_FILE_BYTES:
        raise ValueError(f"File exceeds maximum allowed size of {MAX_FILE_BYTES} bytes.")

    _, ext = os.path.splitext(filename.lower())
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    decoded = raw_bytes.decode("utf-8", errors="replace").strip()
    if not decoded:
        raise ValueError("Uploaded file contains no readable text.")

    # Pretty-normalize JSON if valid so chunk boundaries split cleanly
    if ext == ".json":
        try:
            parsed = json.loads(decoded)
            decoded = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass

    return IngestedDocument(
        filename=os.path.basename(filename),
        extension=ext or ".txt",
        normalized_text=decoded,
        byte_size=len(raw_bytes),
        line_count=len(decoded.splitlines()),
    )
