"""Helpers for browser-to-runtime interactive control actions."""

from __future__ import annotations

from typing import Any, Dict


def _require_non_empty_text(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"interactive action requires {label}")
    return normalized


def build_prompt_submit_action(
    *,
    thread_id: str,
    supervisor_owner_id: str,
    text: str,
    client_event_id: str,
) -> Dict[str, Any]:
    return {
        "action_type": "prompt_submit",
        "thread_id": _require_non_empty_text(thread_id, label="thread_id"),
        "supervisor_owner_id": _require_non_empty_text(
            supervisor_owner_id,
            label="supervisor_owner_id",
        ),
        "payload": {
            "text": _require_non_empty_text(text, label="prompt text"),
            "client_event_id": _require_non_empty_text(
                client_event_id,
                label="client_event_id",
            ),
        },
    }
