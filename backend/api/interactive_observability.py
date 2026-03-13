"""Structured lifecycle observability helpers for interactive runtime."""

from __future__ import annotations

from typing import Any, Dict


LIFECYCLE_PHASE_VALUES = {
    "boot_ready",
    "supervisor_ready",
    "reconnect_bootstrap",
    "supervisor_stopped",
    "failed",
}


def build_interactive_lifecycle_observation(
    *,
    route: Dict[str, Any],
    previous_phase: str | None,
    next_phase: str,
    runtime_status: Dict[str, Any],
    transition_at: str,
    failure_note: str | None = None,
) -> Dict[str, Any]:
    phase_to = _require_phase(next_phase, label="next_phase")
    phase_from = _optional_phase(previous_phase)
    route_payload = _normalize_route(route)
    runtime_status_payload = _normalize_runtime_status(runtime_status)
    observed_at = _require_non_empty_text(transition_at, label="transition_at")
    normalized_failure_note = _normalize_failure_note(failure_note)

    if phase_to == "failed" and normalized_failure_note is None:
        raise ValueError("interactive lifecycle failed transition requires failure note")

    counter_updates = {
        "interactive_lifecycle_transitions_total": 1,
        f"interactive_lifecycle_phase_{phase_to}_total": 1,
        f"interactive_runtime_status_{runtime_status_payload['status']}_total": 1,
    }
    if runtime_status_payload["status"] == "reconnect":
        counter_updates["interactive_reconnect_transitions_total"] = 1
    if normalized_failure_note is not None:
        counter_updates["interactive_lifecycle_failures_total"] = 1

    return {
        "event": "interactive.lifecycle.transition",
        "harness": route_payload["harness"],
        "route_id": route_payload["route_id"],
        "phase_from": phase_from,
        "phase_to": phase_to,
        "runtime_status": runtime_status_payload["status"],
        "transport_state": runtime_status_payload["transport_state"],
        "source": runtime_status_payload["source"],
        "observed_at": observed_at,
        "failure_note": normalized_failure_note,
        "counter_updates": counter_updates,
    }


def _normalize_route(route: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(route, dict):
        raise ValueError("interactive lifecycle observability requires route object")
    return {
        "harness": _require_non_empty_text(route.get("harness"), label="route harness"),
        "route_id": _require_non_empty_text(
            route.get("route_id") or route.get("id"),
            label="route id",
        ),
    }


def _normalize_runtime_status(runtime_status: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(runtime_status, dict):
        raise ValueError("interactive lifecycle observability requires runtime status object")
    return {
        "status": _require_non_empty_text(runtime_status.get("status"), label="runtime status"),
        "transport_state": _require_non_empty_text(
            runtime_status.get("transport_state"),
            label="transport_state",
        ),
        "source": _require_non_empty_text(runtime_status.get("source"), label="source"),
    }


def _normalize_failure_note(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _require_non_empty_text(value, label="failure note")
    return normalized[:200]


def _optional_phase(value: str | None) -> str | None:
    if value is None:
        return None
    return _require_phase(value, label="previous_phase")


def _require_phase(value: str, *, label: str) -> str:
    normalized = _require_non_empty_text(value, label=label)
    if normalized not in LIFECYCLE_PHASE_VALUES:
        raise ValueError(f"interactive lifecycle observability does not support {label}")
    return normalized


def _require_non_empty_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"interactive lifecycle observability requires {label}")
    return value
