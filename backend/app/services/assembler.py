"""
Prompt assembler and compression processor.

Maintains backward-compatible interfaces while delegating to
the modern multi-strategy compression pipeline.
"""

import logging

from app.core.dependencies import get_container
from app.schemas import CompressRequest, CompressResponse, Turn
from app.services.compression.pipeline import (
    PromptAssembler,
)

logger = logging.getLogger(__name__)


def assemble_optimized_prompt(
    summary: str,
    selected_turns: list[Turn],
    current_message: str,
    system_instruction: str = "",
) -> str:
    """Assembles a structured prompt using compressed summary, top-K turns, and user message."""
    return PromptAssembler.assemble(
        summary=summary,
        selected_turns=selected_turns,
        current_message=current_message,
        system_instruction=system_instruction,
    )


def process_compression(request: CompressRequest) -> CompressResponse:
    """Orchestrates the prompt compression pipeline using the service container."""
    pipeline = get_container().compression_pipeline
    return pipeline.compress(request)
