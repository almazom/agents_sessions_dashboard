from __future__ import annotations

import unittest

from backend.api.interactive_handoff import build_replay_to_live_handoff
from backend.api.interactive_identity import resolve_runtime_identity_from_artifact_route
from backend.api.interactive_replay import (
    add_history_complete_marker,
    build_replay_event_snapshot,
)
from backend.api.interactive_status import build_interactive_runtime_status
from backend.api.interactive_store import build_operational_store_snapshot
from backend.api.interactive_supervisor import (
    start_supervisor_resume_flow,
    stop_supervisor_flow,
)
from backend.api.session_artifacts import build_session_route
from tests.interactive.fixtures import codex_fixture_path


class Task026SupervisorStopCancelFlowTests(unittest.TestCase):
    @staticmethod
    def _supervisor_store() -> dict[str, str]:
        return {
            "owner_id": "interactive-supervisor-001",
            "lease_id": "lease-fixture-001",
            "lock_status": "released",
            "heartbeat_at": "2026-03-13T12:17:20Z",
            "lock_expires_at": "2026-03-13T12:22:20Z",
        }

    @staticmethod
    def _started_plan() -> dict[str, object]:
        artifact_path = codex_fixture_path()
        route = build_session_route(
            "codex",
            str(artifact_path),
            "sess-fixture-codex-001",
        )
        runtime_identity = resolve_runtime_identity_from_artifact_route(
            harness="codex",
            artifact_route_id=route["id"],
            artifact_session_id="sess-fixture-codex-001",
        )
        runtime_status = build_interactive_runtime_status(
            thread_id=runtime_identity["runtime"]["thread_id"],
            session_id=runtime_identity["runtime"]["session_id"],
            raw_status={"type": "active", "active_flags": []},
            source="live_notification",
            transport_state="connected",
        )
        handoff = build_replay_to_live_handoff(
            replay_snapshot=add_history_complete_marker(
                build_replay_event_snapshot(artifact_path)
            ),
            runtime_identity=runtime_identity,
            runtime_status=runtime_status,
        )
        store_snapshot = build_operational_store_snapshot(
            route=route,
            runtime_identity=runtime_identity["runtime"],
            runtime_status=runtime_status,
            supervisor=Task026SupervisorStopCancelFlowTests._supervisor_store(),
            updated_at="2026-03-13T12:17:20Z",
        )
        return start_supervisor_resume_flow(
            handoff=handoff,
            store_record=store_snapshot["records"][0],
            owner_id="interactive-supervisor-001",
            lease_id="lease-fixture-002",
            heartbeat_at="2026-03-13T12:18:20Z",
            lock_expires_at="2026-03-13T12:23:20Z",
        )

    def test_green_stops_supervisor_and_releases_lock(self) -> None:
        stopped = stop_supervisor_flow(
            self._started_plan(),
            owner_id="interactive-supervisor-001",
            stopped_at="2026-03-13T12:19:20Z",
            reason="cancelled_by_user",
        )

        self.assertEqual(stopped["phase"], "supervisor_stopped")
        self.assertEqual(stopped["operation"], "cancel")
        self.assertEqual(stopped["reason"], "cancelled_by_user")
        self.assertEqual(stopped["supervisor"]["lock_status"], "released")
        self.assertEqual(stopped["supervisor"]["heartbeat_at"], "2026-03-13T12:19:20Z")

    def test_red_rejects_stop_from_non_owner(self) -> None:
        with self.assertRaises(PermissionError):
            stop_supervisor_flow(
                self._started_plan(),
                owner_id="interactive-supervisor-999",
                stopped_at="2026-03-13T12:19:20Z",
                reason="cancelled_by_user",
            )


if __name__ == "__main__":
    unittest.main()
