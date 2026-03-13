"""Helpers for building an honest runtime status payload for interactive mode."""

from __future__ import annotations

from typing import Any, Dict


STATUS_VALUES = {"idle", "active", "waiting", "error", "reconnect"}
TRANSPORT_STATE_VALUES = {"connected", "reconnecting", "disconnected"}
SOURCE_VALUES = {"boot", "live_notification", "recovered"}
RAW_STATUS_VALUES = {"notLoaded", "idle", "systemError", "active"}
ACTIVE_FLAG_VALUES = {"waitingOnApproval", "waitingOnUserInput"}
WAIT_REASON_BY_ACTIVE_FLAG = {
    "waitingOnApproval": "approval",
    "waitingOnUserInput": "user_input",
}
RECONNECT_REASON_VALUES = {"transport_drop", "page_reload", "resume_after_boot"}


def _normalize_raw_status(raw_status: Dict[str, Any]) -> Dict[str, Any]:
    raw_type = raw_status.get("type")
    if raw_type not in RAW_STATUS_VALUES:
        raise ValueError(f"interactive runtime status does not support raw type: {raw_type}")

    active_flags = raw_status.get("active_flags", [])
    if active_flags is None:
        active_flags = []
    if not isinstance(active_flags, list):
        raise ValueError("interactive runtime status requires active_flags to be a list")
    if raw_type != "active" and active_flags:
        raise ValueError("only active raw status may carry active flags")
    if not all(flag in ACTIVE_FLAG_VALUES for flag in active_flags):
        raise ValueError("interactive runtime status received an unknown active flag")

    return {
        "type": raw_type,
        "active_flags": active_flags,
    }


def _derive_wait_reason(active_flags: list[str]) -> str | None:
    for flag in ("waitingOnUserInput", "waitingOnApproval"):
        wait_reason = WAIT_REASON_BY_ACTIVE_FLAG.get(flag)
        if flag in active_flags and wait_reason is not None:
            return wait_reason
    return None


def _status_copy(
    *,
    status: str,
    label: str,
    detail: str,
    can_send_input: bool,
    can_resume_stream: bool,
    wait_reason: str | None = None,
    reconnect_hint: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "label": label,
        "detail": detail,
        "can_send_input": can_send_input,
        "can_resume_stream": can_resume_stream,
        "wait_reason": wait_reason,
        "reconnect_hint": reconnect_hint,
    }


def _derive_ui_status(
    *,
    raw_status: Dict[str, Any],
    transport_state: str,
    reconnect_reason: str | None,
) -> Dict[str, Any]:
    if transport_state not in TRANSPORT_STATE_VALUES:
        raise ValueError(
            f"interactive runtime status does not support transport state: {transport_state}"
        )
    if reconnect_reason is not None and reconnect_reason not in RECONNECT_REASON_VALUES:
        raise ValueError(
            f"interactive runtime status does not support reconnect reason: {reconnect_reason}"
        )

    raw_type = raw_status["type"]
    default_reconnect_reason = (
        "resume_after_boot" if raw_type == "notLoaded" else "transport_drop"
    )

    if transport_state in {"reconnecting", "disconnected"} or raw_type == "notLoaded":
        return _status_copy(
            status="reconnect",
            label="Reconnecting",
            detail=(
                "The browser transport is recovering the session and will resume "
                "the runtime when the thread is loaded again."
            ),
            can_send_input=False,
            can_resume_stream=True,
            reconnect_hint={
                "attempt": 1,
                "reason": reconnect_reason or default_reconnect_reason,
            },
        )
    active_flags = raw_status["active_flags"]

    if raw_type == "systemError":
        return _status_copy(
            status="error",
            label="Runtime error",
            detail="The runtime reported a system-level error and cannot continue normally.",
            can_send_input=False,
            can_resume_stream=False,
        )

    if raw_type == "idle":
        return _status_copy(
            status="idle",
            label="Idle",
            detail="The thread is loaded and ready for the next user action.",
            can_send_input=True,
            can_resume_stream=True,
        )

    if raw_type == "active":
        wait_reason = _derive_wait_reason(active_flags)
        if wait_reason is not None:
            detail = (
                "The runtime is waiting for user input before it can continue."
                if wait_reason == "user_input"
                else "The runtime is waiting for explicit approval before it can continue."
            )
            return _status_copy(
                status="waiting",
                label="Waiting",
                detail=detail,
                can_send_input=wait_reason == "user_input",
                can_resume_stream=False,
                wait_reason=wait_reason,
            )

        return _status_copy(
            status="active",
            label="Active",
            detail="The runtime is actively processing or streaming work for this thread.",
            can_send_input=False,
            can_resume_stream=False,
        )
    raise ValueError(f"interactive runtime status cannot derive ui state from raw type: {raw_type}")


def build_interactive_runtime_status(
    *,
    thread_id: str,
    session_id: str,
    raw_status: Dict[str, Any],
    source: str,
    transport_state: str,
    observed_at: str | None = None,
    reconnect_reason: str | None = None,
) -> Dict[str, Any]:
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("interactive runtime status requires a non-empty thread_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("interactive runtime status requires a non-empty session_id")
    if source not in SOURCE_VALUES:
        raise ValueError(f"interactive runtime status does not support source: {source}")

    normalized_raw_status = _normalize_raw_status(raw_status)
    derived_status = _derive_ui_status(
        raw_status=normalized_raw_status,
        transport_state=transport_state,
        reconnect_reason=reconnect_reason,
    )

    payload = {
        "version": 1,
        "thread_id": thread_id,
        "session_id": session_id,
        "status": derived_status["status"],
        "label": derived_status["label"],
        "detail": derived_status["detail"],
        "source": source,
        "transport_state": transport_state,
        "can_send_input": derived_status["can_send_input"],
        "can_resume_stream": derived_status["can_resume_stream"],
        "raw_status": normalized_raw_status,
        "wait_reason": derived_status["wait_reason"],
        "reconnect_hint": derived_status["reconnect_hint"],
        "observed_at": observed_at,
    }
    if payload["status"] not in STATUS_VALUES:
        raise ValueError(
            "interactive runtime status produced unsupported status: "
            f"{payload['status']}"
        )
    return payload
