from __future__ import annotations

import unittest

from backend.api.interactive_observability import (
    build_interactive_lifecycle_observation,
)
from backend.api.interactive_status import build_interactive_runtime_status


class Task042LifecycleObservabilityTests(unittest.TestCase):
    @staticmethod
    def _route() -> dict[str, str]:
        return {
            "harness": "codex",
            "route_id": "rollout-interactive-fixture.jsonl",
        }

    def test_green_builds_lifecycle_logs_counters_and_failure_free_notes(self) -> None:
        active_status = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "active", "active_flags": []},
            source="live_notification",
            transport_state="connected",
            observed_at="2026-03-13T12:55:10Z",
        )
        reconnect_status = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "notLoaded", "active_flags": []},
            source="recovered",
            transport_state="reconnecting",
            observed_at="2026-03-13T12:56:10Z",
            reconnect_reason="transport_drop",
        )

        active_observation = build_interactive_lifecycle_observation(
            route=self._route(),
            previous_phase="boot_ready",
            next_phase="supervisor_ready",
            runtime_status=active_status,
            transition_at="2026-03-13T12:55:10Z",
        )
        reconnect_observation = build_interactive_lifecycle_observation(
            route=self._route(),
            previous_phase="supervisor_ready",
            next_phase="reconnect_bootstrap",
            runtime_status=reconnect_status,
            transition_at="2026-03-13T12:56:10Z",
        )

        self.assertEqual(active_observation["event"], "interactive.lifecycle.transition")
        self.assertEqual(active_observation["phase_to"], "supervisor_ready")
        self.assertEqual(
            active_observation["counter_updates"]["interactive_lifecycle_phase_supervisor_ready_total"],
            1,
        )
        self.assertEqual(
            active_observation["counter_updates"]["interactive_runtime_status_active_total"],
            1,
        )
        self.assertIsNone(active_observation["failure_note"])
        self.assertEqual(
            reconnect_observation["counter_updates"]["interactive_runtime_status_reconnect_total"],
            1,
        )
        self.assertEqual(
            reconnect_observation["counter_updates"]["interactive_reconnect_transitions_total"],
            1,
        )

    def test_red_requires_failure_note_for_failed_transition(self) -> None:
        error_status = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "systemError", "active_flags": []},
            source="live_notification",
            transport_state="connected",
            observed_at="2026-03-13T12:57:10Z",
        )

        with self.assertRaises(ValueError) as error:
            build_interactive_lifecycle_observation(
                route=self._route(),
                previous_phase="supervisor_ready",
                next_phase="failed",
                runtime_status=error_status,
                transition_at="2026-03-13T12:57:10Z",
            )

        self.assertIn("failure note", str(error.exception))


if __name__ == "__main__":
    unittest.main()
