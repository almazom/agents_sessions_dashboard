from __future__ import annotations

import unittest

from backend.api.interactive_handoff import build_replay_to_live_handoff
from backend.api.interactive_identity import resolve_runtime_identity_from_artifact_route
from backend.api.interactive_replay import (
    add_history_complete_marker,
    build_replay_event_snapshot,
)
from backend.api.interactive_status import build_interactive_runtime_status
from backend.api.session_artifacts import build_session_route
from tests.interactive.fixtures import codex_fixture_path


class Task019ReplayToLiveHandoffTests(unittest.TestCase):
    @staticmethod
    def _runtime_context() -> tuple[object, dict[str, object], dict[str, object]]:
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
        replay_snapshot = add_history_complete_marker(
            build_replay_event_snapshot(artifact_path)
        )
        runtime_status = build_interactive_runtime_status(
            thread_id=runtime_identity["runtime"]["thread_id"],
            session_id=runtime_identity["runtime"]["session_id"],
            raw_status={"type": "active", "active_flags": []},
            source="live_notification",
            transport_state="connected",
        )
        return artifact_path, runtime_identity, runtime_status

    def test_green_builds_live_attach_handoff_after_replay_boundary(self) -> None:
        artifact_path, runtime_identity, runtime_status = self._runtime_context()

        handoff = build_replay_to_live_handoff(
            replay_snapshot=add_history_complete_marker(
                build_replay_event_snapshot(artifact_path)
            ),
            runtime_identity=runtime_identity,
            runtime_status=runtime_status,
        )

        self.assertEqual(handoff["phase"], "live_attach_ready")
        self.assertTrue(handoff["ready_for_live_attach"])
        self.assertEqual(handoff["replay_event_count"], 6)
        self.assertEqual(handoff["history_boundary_event_id"], "evt-0006")
        self.assertIsNone(handoff["blocking_reason"])
        self.assertEqual(
            handoff["live_attach"],
            {
                "thread_id": "thread-fixture-codex-001",
                "session_id": "sess-fixture-codex-001",
                "transport": "codex_exec_json",
                "attach_strategy": "after_history_complete",
                "attach_after_event_id": "evt-0006",
            },
        )
        self.assertEqual(handoff["runtime_status"]["status"], "active")

    def test_red_rejects_replay_snapshot_without_history_complete_marker(self) -> None:
        artifact_path, runtime_identity, runtime_status = self._runtime_context()

        with self.assertRaises(ValueError):
            build_replay_to_live_handoff(
                replay_snapshot=build_replay_event_snapshot(artifact_path),
                runtime_identity=runtime_identity,
                runtime_status=runtime_status,
            )


if __name__ == "__main__":
    unittest.main()
