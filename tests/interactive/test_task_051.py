from __future__ import annotations

import unittest
from pathlib import Path

from tests.interactive.real_session_browser_fixture import (
    RealSessionBrowserFixtureBroken,
    build_real_session_browser_fixture,
)


class Task051RealSessionBrowserFixtureTests(unittest.TestCase):
    def test_real_session_fixture_green(self) -> None:
        fixture = build_real_session_browser_fixture()

        self.assertEqual(
            fixture.artifact_path,
            Path(
                "/home/pets/zoo/agents_sessions_dashboard/tests/fixtures/interactive/codex/rollout-interactive-fixture.jsonl"
            ),
        )
        self.assertEqual(
            fixture.detail_route,
            "/sessions/codex/rollout-interactive-fixture.jsonl",
        )
        self.assertEqual(
            fixture.interactive_route,
            "/sessions/codex/rollout-interactive-fixture.jsonl/interactive",
        )
        self.assertEqual(fixture.thread_id, "thread-fixture-codex-001")
        self.assertEqual(fixture.session_id, "sess-fixture-codex-001")
        self.assertIn("Build deterministic fixture for interactive mode", fixture.tail_texts)
        self.assertEqual(
            fixture.replay_event_types,
            (
                "user_message",
                "tool_call",
                "tool_call",
                "tool_call",
                "task_complete",
                "history_complete",
            ),
        )
        self.assertEqual(fixture.history_boundary_event_id, "evt-0006")
        self.assertEqual(fixture.handoff_phase, "live_attach_ready")
        self.assertEqual(fixture.reconnect_phase, "reconnect_bootstrap")
        self.assertEqual(fixture.supervisor_phase, "supervisor_ready")
        self.assertEqual(
            fixture.playwright_command,
            "cd frontend && npx playwright test e2e/interactive-session.spec.ts",
        )
        self.assertEqual(fixture.sdk_status, "adopt_with_scope")

    def test_broken_real_session_fixture(self) -> None:
        with self.assertRaises(RealSessionBrowserFixtureBroken):
            build_real_session_browser_fixture(
                artifact_path=Path("/tmp/interactive-task-check/missing-real-session-fixture.jsonl")
            )


if __name__ == "__main__":
    unittest.main()
