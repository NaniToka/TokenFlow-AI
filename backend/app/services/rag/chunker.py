"""
Recursive Semantic Document Chunker for RAG and Long-Context Ingestion.

Splits long conversational texts, documents, and code snippets into semantically
coherent chunks while preserving paragraph, sentence, and word boundaries.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunked segment of text with position metadata."""
    chunk_id: int
    text: str
    token_count: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]


class SemanticChunker:
    """
    Splits text recursively using hierarchical separators:
    1. Double newlines (paragraphs)
    2. Single newlines (lines / code blocks)
    3. Sentence terminators (. ! ?)
    4. Clauses (, ; :)
    5. Whitespace
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """Splits input text into overlapping semantic chunks."""
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        raw_chunks = self._recursive_split(text, self.DEFAULT_SEPARATORS)
        
        # Merge small splits up to chunk_size with overlap
        merged: List[TextChunk] = []
        current_text = ""
        chunk_idx = 0
        current_start = 0

        for segment in raw_chunks:
            if len(current_text) + len(segment) <= self.chunk_size:
                current_text += segment
            else:
                if current_text.strip():
                    merged.append(
                        TextChunk(
                            chunk_id=chunk_idx,
                            text=current_text.strip(),
                            token_count=max(1, len(current_text) // 4),
                            start_char=current_start,
                            end_char=current_start + len(current_text),
                            metadata=dict(metadata),
                        )
                    )
                    chunk_idx += 1
                    
                    # Compute overlap
                    overlap_len = min(len(current_text), self.chunk_overlap)
                    overlap_text = current_text[-overlap_len:] if overlap_len > 0 else ""
                    current_start = current_start + len(current_text) - overlap_len
                    current_text = overlap_text + segment
                else:
                    current_text = segment

        if current_text.strip():
            merged.append(
                TextChunk(
                    chunk_id=chunk_idx,
                    text=current_text.strip(),
                    token_count=max(1, len(current_text) // 4),
                    start_char=current_start,
                    end_char=current_start + len(current_text),
                    metadata=dict(metadata),
                )
            )

        return merged

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Recursively partitions text along the highest available separator."""
        if not separators or len(text) <= self.chunk_size:
            return [text]

        sep = separators[0]
        remaining_seps = separators[1:]

        if sep not in text:
            return self._recursive_split(text, remaining_seps)

        parts = text.split(sep)
        splits = []
        for i, part in enumerate(parts):
            # re-attach separator to preserve structure
            chunk_part = part + (sep if i < len(parts) - 1 else "")
            if len(chunk_part) > self.chunk_size and remaining_seps:
                splits.extend(self._recursive_split(chunk_part, remaining_seps))
            else:
                splits.append(chunk_part)

        return splits
