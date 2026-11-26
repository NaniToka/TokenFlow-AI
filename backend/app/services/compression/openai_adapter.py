"""
OpenAI Chat Completions Compatibility Adapter.

Translates standard OpenAI / Anthropic `messages: [{role, content}]` payloads
into TokenFlow `CompressRequest`, executes compression, and formats the result
back as drop-in `messages` ready for `openai.chat.completions.create()`.
"""

from __future__ import annotations

from typing import Any

from app.schemas import CompressionMode, CompressRequest, Turn


def openai_messages_to_compress_request(
    messages: list[dict[str, str]],
    top_k: int = 3,
    target_model: str = "gpt-4o",
    compression_mode: str = "balanced",
    max_context_tokens: int | None = None,
    sanitize_pii: bool = False,
) -> CompressRequest:
    """Convert standard OpenAI message list into a CompressRequest."""
    system_parts: list[str] = []
    dialogue_turns: list[Turn] = []

    for msg in messages:
        role = str(msg.get("role", "user")).lower()
        content = str(msg.get("content", "")).strip()
        if not content:
            continue

        if role == "system":
            system_parts.append(content)
        elif role in {"assistant", "model", "tool"}:
            dialogue_turns.append(Turn(role="model", content=content))
        else:
            dialogue_turns.append(Turn(role="user", content=content))

    if not dialogue_turns:
        raise ValueError("At least one non-system user message is required.")

    current_msg = dialogue_turns[-1].content
    history = dialogue_turns[:-1]

    try:
        mode = CompressionMode(compression_mode)
    except ValueError:
        mode = CompressionMode.BALANCED

    return CompressRequest(
        history=history,
        current_message=current_msg,
        system_instruction="\n".join(system_parts),
        top_k=top_k,
        target_model=target_model,
        compression_mode=mode,
        max_context_tokens=max_context_tokens,
        sanitize_pii=sanitize_pii,
    )


def compress_response_to_openai_messages(
    response: Any,
    system_instruction: str = "",
    current_message: str = "",
) -> list[dict[str, str]]:
    """Format a CompressResponse back into standard OpenAI chat completion messages."""
    out: list[dict[str, str]] = []

    sys_content_parts: list[str] = []
    if system_instruction.strip():
        sys_content_parts.append(system_instruction.strip())
    if response.summary and response.summary.strip():
        sys_content_parts.append(f"[Prior Context Memory]\n{response.summary.strip()}")

    if sys_content_parts:
        out.append({"role": "system", "content": "\n\n".join(sys_content_parts)})

    for turn in response.selected_turns:
        role = "assistant" if turn.role == "model" else "user"
        out.append({"role": role, "content": turn.content})

    if current_message.strip():
        out.append({"role": "user", "content": current_message.strip()})

    return out
