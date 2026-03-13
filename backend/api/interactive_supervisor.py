"""Helpers for supervisor-driven start/resume orchestration."""

from __future__ import annotations

from typing import Any, Dict

from .interactive_store import (
    acquire_operational_store_lock,
    release_operational_store_lock,
)


def _operation_for_runtime_status(runtime_status: Dict[str, Any]) -> str:
    return "reconnect" if runtime_status.get("status") == "reconnect" else "resume"


def start_supervisor_resume_flow(
    *,
    handoff: Dict[str, Any],
    store_record: Dict[str, Any],
    owner_id: str,
    lease_id: str,
    heartbeat_at: str,
    lock_expires_at: str,
) -> Dict[str, Any]:
    runtime_status = handoff.get("runtime_status")
    live_attach = handoff.get("live_attach")
    if not isinstance(runtime_status, dict):
        raise ValueError("supervisor start requires runtime status payload")
    if not isinstance(live_attach, dict):
        raise ValueError("supervisor start requires live attach metadata")

    locked_record = acquire_operational_store_lock(
        store_record,
        owner_id=owner_id,
        lease_id=lease_id,
        heartbeat_at=heartbeat_at,
        lock_expires_at=lock_expires_at,
    )

    return {
        "phase": "supervisor_ready",
        "operation": _operation_for_runtime_status(runtime_status),
        "live_attach": live_attach,
        "runtime_status": runtime_status,
        "supervisor": locked_record["supervisor"],
    }


def stop_supervisor_flow(
    plan: Dict[str, Any],
    *,
    owner_id: str,
    stopped_at: str,
    reason: str,
) -> Dict[str, Any]:
    supervisor = plan.get("supervisor")
    if not isinstance(supervisor, dict):
        raise ValueError("supervisor stop requires supervisor ownership payload")

    released_supervisor = release_operational_store_lock(
        {"supervisor": supervisor},
        owner_id=owner_id,
        released_at=stopped_at,
    )["supervisor"]

    return {
        **plan,
        "phase": "supervisor_stopped",
        "operation": "cancel",
        "reason": reason,
        "supervisor": released_supervisor,
    }
