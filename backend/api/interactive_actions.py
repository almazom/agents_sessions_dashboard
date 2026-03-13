"""Helpers for browser-to-runtime interactive control actions."""

from __future__ import annotations

from typing import Any, Dict


INTERRUPT_MODE_VALUES = {"cancel", "interrupt"}


def _require_non_empty_text(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"interactive action requires {label}")
    return normalized


def _build_action_envelope(
    *,
    action_type: str,
    thread_id: str,
    supervisor_owner_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "action_type": action_type,
        "thread_id": _require_non_empty_text(thread_id, label="thread_id"),
        "supervisor_owner_id": _require_non_empty_text(
            supervisor_owner_id,
            label="supervisor_owner_id",
        ),
        "payload": payload,
    }


def build_prompt_submit_action(
    *,
    thread_id: str,
    supervisor_owner_id: str,
    text: str,
    client_event_id: str,
) -> Dict[str, Any]:
    return _build_action_envelope(
        action_type="prompt_submit",
        thread_id=thread_id,
        supervisor_owner_id=supervisor_owner_id,
        payload={
            "text": _require_non_empty_text(text, label="prompt text"),
            "client_event_id": _require_non_empty_text(
                client_event_id,
                label="client_event_id",
            ),
        },
    )


def build_cancel_interrupt_action(
    *,
    thread_id: str,
    supervisor_owner_id: str,
    mode: str,
    client_event_id: str,
) -> Dict[str, Any]:
    normalized_mode = _require_non_empty_text(mode, label="mode")
    if normalized_mode not in INTERRUPT_MODE_VALUES:
        raise ValueError(
            "interactive action requires mode to be one of: cancel, interrupt"
        )

    return _build_action_envelope(
        action_type="cancel_interrupt",
        thread_id=thread_id,
        supervisor_owner_id=supervisor_owner_id,
        payload={
            "mode": normalized_mode,
            "client_event_id": _require_non_empty_text(
                client_event_id,
                label="client_event_id",
            ),
        },
    )
