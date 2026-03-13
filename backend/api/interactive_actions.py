"""Helpers for browser-to-runtime interactive control actions."""

from __future__ import annotations

from typing import Any, Dict


INTERRUPT_MODE_VALUES = {"cancel", "interrupt"}
WAIT_REASON_VALUES = {"approval", "user_input"}
APPROVAL_RESPONSE_VALUES = {"approve", "reject"}
ACTION_TYPE_VALUES = {
    "prompt_submit",
    "cancel_interrupt",
    "waiting_response",
}


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


def _require_payload_dict(action: Dict[str, Any]) -> Dict[str, Any]:
    payload = action.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("interactive action requires payload object")
    return payload


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


def build_waiting_response_action(
    *,
    thread_id: str,
    supervisor_owner_id: str,
    wait_reason: str,
    response: str,
    client_event_id: str,
) -> Dict[str, Any]:
    normalized_wait_reason = _require_non_empty_text(
        wait_reason,
        label="wait_reason",
    )
    if normalized_wait_reason not in WAIT_REASON_VALUES:
        raise ValueError(
            "interactive action requires wait_reason to be one of: approval, user_input"
        )

    normalized_response = _require_non_empty_text(response, label="response")
    if (
        normalized_wait_reason == "approval"
        and normalized_response not in APPROVAL_RESPONSE_VALUES
    ):
        raise ValueError(
            "interactive action requires approval response to be one of: "
            "approve, reject"
        )

    return _build_action_envelope(
        action_type="waiting_response",
        thread_id=thread_id,
        supervisor_owner_id=supervisor_owner_id,
        payload={
            "wait_reason": normalized_wait_reason,
            "response": normalized_response,
            "client_event_id": _require_non_empty_text(
                client_event_id,
                label="client_event_id",
            ),
        },
    )


def validate_inbound_action(
    *,
    action: Dict[str, Any],
    authenticated_actor_id: str,
    expected_thread_id: str,
    expected_supervisor_owner_id: str,
) -> Dict[str, Any]:
    if not isinstance(action, dict):
        raise ValueError("interactive action validation requires action object")

    actor_id = _require_non_empty_text(
        authenticated_actor_id,
        label="authenticated_actor_id",
    )
    thread_id = _require_non_empty_text(
        expected_thread_id,
        label="expected_thread_id",
    )
    owner_id = _require_non_empty_text(
        expected_supervisor_owner_id,
        label="expected_supervisor_owner_id",
    )

    if actor_id != owner_id:
        raise PermissionError("interactive action actor is not allowed to control owner")

    action_type = _require_non_empty_text(
        str(action.get("action_type", "")),
        label="action_type",
    )
    if action_type not in ACTION_TYPE_VALUES:
        raise ValueError(f"interactive action does not support type: {action_type}")

    action_thread_id = _require_non_empty_text(
        str(action.get("thread_id", "")),
        label="thread_id",
    )
    if action_thread_id != thread_id:
        raise PermissionError("interactive action thread does not match active session")

    action_owner_id = _require_non_empty_text(
        str(action.get("supervisor_owner_id", "")),
        label="supervisor_owner_id",
    )
    if action_owner_id != owner_id:
        raise PermissionError("interactive action owner does not match active supervisor")

    payload = _require_payload_dict(action)

    if action_type == "prompt_submit":
        return build_prompt_submit_action(
            thread_id=action_thread_id,
            supervisor_owner_id=action_owner_id,
            text=str(payload.get("text", "")),
            client_event_id=str(payload.get("client_event_id", "")),
        )

    if action_type == "cancel_interrupt":
        return build_cancel_interrupt_action(
            thread_id=action_thread_id,
            supervisor_owner_id=action_owner_id,
            mode=str(payload.get("mode", "")),
            client_event_id=str(payload.get("client_event_id", "")),
        )

    return build_waiting_response_action(
        thread_id=action_thread_id,
        supervisor_owner_id=action_owner_id,
        wait_reason=str(payload.get("wait_reason", "")),
        response=str(payload.get("response", "")),
        client_event_id=str(payload.get("client_event_id", "")),
    )
