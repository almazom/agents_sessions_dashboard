from __future__ import annotations

import unittest

from backend.api.interactive_handoff import build_replay_to_live_handoff
from backend.api.interactive_identity import resolve_runtime_identity_from_artifact_route
from backend.api.interactive_reconnect import build_reconnect_bootstrap_snapshot
from backend.api.interactive_replay import (
    add_history_complete_marker,
    build_replay_event_snapshot,
)
from backend.api.interactive_status import build_interactive_runtime_status
from backend.api.session_artifacts import build_session_route
from tests.interactive.fixtures import codex_fixture_path


class Task020ReconnectBootstrapSnapshotTests(unittest.TestCase):
    @staticmethod
    def _runtime_identity() -> dict[str, object]:
        artifact_path = codex_fixture_path()
        route = build_session_route(
            "codex",
            str(artifact_path),
            "sess-fixture-codex-001",
        )
        return resolve_runtime_identity_from_artifact_route(
            harness="codex",
            artifact_route_id=route["id"],
            artifact_session_id="sess-fixture-codex-001",
        )

    @staticmethod
    def _handoff_for_status(runtime_status: dict[str, object]) -> dict[str, object]:
        return build_replay_to_live_handoff(
            replay_snapshot=add_history_complete_marker(
                build_replay_event_snapshot(codex_fixture_path())
            ),
            runtime_identity=Task020ReconnectBootstrapSnapshotTests._runtime_identity(),
            runtime_status=runtime_status,
        )

    def test_green_builds_reconnect_bootstrap_snapshot(self) -> None:
        runtime_identity = self._runtime_identity()
        reconnect_status = build_interactive_runtime_status(
            thread_id=runtime_identity["runtime"]["thread_id"],
            session_id=runtime_identity["runtime"]["session_id"],
            raw_status={"type": "active", "active_flags": []},
            source="recovered",
            transport_state="reconnecting",
            reconnect_reason="transport_drop",
        )

        snapshot = build_reconnect_bootstrap_snapshot(
            self._handoff_for_status(reconnect_status)
        )

        self.assertEqual(snapshot["phase"], "reconnect_bootstrap")
        self.assertEqual(snapshot["resume_strategy"], "resume_after_bootstrap")
        self.assertEqual(snapshot["runtime_status"]["status"], "reconnect")
        self.assertTrue(snapshot["requires_replay_preservation"])
        self.assertEqual(
            snapshot["replay_summary"],
            {
                "event_count": 6,
                "history_boundary_event_id": "evt-0006",
                "history_complete": True,
            },
        )
        self.assertEqual(
            snapshot["live_attach"]["attach_after_event_id"],
            "evt-0006",
        )

    def test_red_rejects_non_reconnect_status(self) -> None:
        runtime_identity = self._runtime_identity()
        active_status = build_interactive_runtime_status(
            thread_id=runtime_identity["runtime"]["thread_id"],
            session_id=runtime_identity["runtime"]["session_id"],
            raw_status={"type": "active", "active_flags": []},
            source="live_notification",
            transport_state="connected",
        )

        with self.assertRaises(ValueError):
            build_reconnect_bootstrap_snapshot(self._handoff_for_status(active_status))


if __name__ == "__main__":
    unittest.main()
