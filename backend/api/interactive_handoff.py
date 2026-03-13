"""Helpers for defining the seam between replay history and live attach."""

from __future__ import annotations

from typing import Any, Dict


LIVE_ATTACH_READY_STATUSES = {"idle", "active", "waiting", "reconnect"}


def _resolve_runtime_identity_payload(runtime_identity: Dict[str, Any]) -> Dict[str, Any]:
    candidate = runtime_identity.get("runtime", runtime_identity)
    if not isinstance(candidate, dict):
        raise ValueError("interactive handoff requires a runtime identity payload")
    required_keys = ("thread_id", "session_id", "transport")
    if not all(isinstance(candidate.get(key), str) and candidate.get(key) for key in required_keys):
        raise ValueError("interactive handoff requires thread/session/transport identity")
    return candidate


def _validate_replay_boundary(replay_snapshot: Dict[str, Any]) -> str:
    items = replay_snapshot.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("interactive handoff requires a non-empty replay snapshot")
    if not replay_snapshot.get("history_complete"):
        raise ValueError("interactive handoff requires a history_complete replay marker")

    boundary_event = items[-1]
    if boundary_event.get("event_type") != "history_complete":
        raise ValueError("interactive handoff boundary must end with history_complete")

    event_id = boundary_event.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        raise ValueError("interactive handoff boundary requires a stable event_id")
    return event_id


def _validate_runtime_status(
    runtime_identity: Dict[str, Any],
    runtime_status: Dict[str, Any],
) -> str:
    required_keys = ("thread_id", "session_id", "status")
    if not all(
        isinstance(runtime_status.get(key), str) and runtime_status.get(key)
        for key in required_keys
    ):
        raise ValueError("interactive handoff requires a runtime status payload")

    if runtime_identity["thread_id"] != runtime_status["thread_id"]:
        raise ValueError("interactive handoff thread_id does not match runtime identity")
    if runtime_identity["session_id"] != runtime_status["session_id"]:
        raise ValueError("interactive handoff session_id does not match runtime identity")
    return str(runtime_status["status"])


def build_replay_to_live_handoff(
    *,
    replay_snapshot: Dict[str, Any],
    runtime_identity: Dict[str, Any],
    runtime_status: Dict[str, Any],
) -> Dict[str, Any]:
    resolved_runtime_identity = _resolve_runtime_identity_payload(runtime_identity)
    boundary_event_id = _validate_replay_boundary(replay_snapshot)
    runtime_status_value = _validate_runtime_status(
        resolved_runtime_identity,
        runtime_status,
    )

    ready_for_live_attach = runtime_status_value in LIVE_ATTACH_READY_STATUSES
    return {
        "phase": "live_attach_ready" if ready_for_live_attach else "attach_blocked",
        "ready_for_live_attach": ready_for_live_attach,
        "blocking_reason": None if ready_for_live_attach else "runtime_status_blocked",
        "replay_event_count": len(replay_snapshot["items"]),
        "history_boundary_event_id": boundary_event_id,
        "live_attach": {
            "thread_id": resolved_runtime_identity["thread_id"],
            "session_id": resolved_runtime_identity["session_id"],
            "transport": resolved_runtime_identity["transport"],
            "attach_strategy": "after_history_complete",
            "attach_after_event_id": boundary_event_id,
        },
        "runtime_status": runtime_status,
    }
