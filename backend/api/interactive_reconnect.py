"""Helpers for preparing reconnect-specific interactive bootstrap payloads."""

from __future__ import annotations

from typing import Any, Dict


def build_reconnect_bootstrap_snapshot(
    handoff: Dict[str, Any],
) -> Dict[str, Any]:
    runtime_status = handoff.get("runtime_status")
    live_attach = handoff.get("live_attach")
    boundary_event_id = handoff.get("history_boundary_event_id")
    replay_event_count = handoff.get("replay_event_count")

    if not isinstance(runtime_status, dict):
        raise ValueError("reconnect bootstrap requires a runtime status payload")
    if runtime_status.get("status") != "reconnect":
        raise ValueError("reconnect bootstrap requires reconnect runtime status")
    if not isinstance(live_attach, dict):
        raise ValueError("reconnect bootstrap requires live attach metadata")
    if not isinstance(boundary_event_id, str) or not boundary_event_id:
        raise ValueError("reconnect bootstrap requires a history boundary event id")
    if not isinstance(replay_event_count, int) or replay_event_count < 1:
        raise ValueError("reconnect bootstrap requires replay event count")

    return {
        "phase": "reconnect_bootstrap",
        "resume_strategy": "resume_after_bootstrap",
        "requires_replay_preservation": True,
        "runtime_status": runtime_status,
        "live_attach": live_attach,
        "replay_summary": {
            "event_count": replay_event_count,
            "history_boundary_event_id": boundary_event_id,
            "history_complete": True,
        },
    }
