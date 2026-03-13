from __future__ import annotations

import unittest

from backend.api.interactive_actions import (
    build_cancel_interrupt_action,
    build_prompt_submit_action,
)
from backend.api.interactive_backpressure import evaluate_interactive_backpressure


class Task041ResourceLimitsAndBackpressureTests(unittest.TestCase):
    @staticmethod
    def _prompt_action() -> dict[str, object]:
        return build_prompt_submit_action(
            thread_id="thread-fixture-codex-001",
            supervisor_owner_id="interactive-supervisor-001",
            text="Continue from the browser.",
            client_event_id="browser-event-030",
        )

    @staticmethod
    def _cancel_action() -> dict[str, object]:
        return build_cancel_interrupt_action(
            thread_id="thread-fixture-codex-001",
            supervisor_owner_id="interactive-supervisor-001",
            mode="cancel",
            client_event_id="browser-event-031",
        )

    def test_green_queues_prompt_work_but_keeps_control_actions_unblocked(self) -> None:
        prompt_verdict = evaluate_interactive_backpressure(
            self._prompt_action(),
            inflight_prompts=1,
            queued_prompts=1,
            recent_prompt_count=2,
        )
        cancel_verdict = evaluate_interactive_backpressure(
            self._cancel_action(),
            inflight_prompts=1,
            queued_prompts=2,
            recent_prompt_count=4,
        )

        self.assertEqual(prompt_verdict["queue_lane"], "prompt")
        self.assertEqual(prompt_verdict["disposition"], "enqueue")
        self.assertTrue(prompt_verdict["overloaded"])
        self.assertEqual(prompt_verdict["accepted_queue_depth"], 2)
        self.assertEqual(prompt_verdict["remaining_queue_slots"], 0)
        self.assertEqual(cancel_verdict["queue_lane"], "control")
        self.assertEqual(cancel_verdict["disposition"], "dispatch_now")
        self.assertFalse(cancel_verdict["overloaded"])

    def test_red_rejects_prompt_submit_when_rate_limited_or_queue_is_full(self) -> None:
        with self.assertRaises(PermissionError) as rate_error:
            evaluate_interactive_backpressure(
                self._prompt_action(),
                inflight_prompts=0,
                queued_prompts=0,
                recent_prompt_count=4,
            )
        self.assertIn("rate limit", str(rate_error.exception))

        with self.assertRaises(OverflowError) as queue_error:
            evaluate_interactive_backpressure(
                self._prompt_action(),
                inflight_prompts=1,
                queued_prompts=2,
                recent_prompt_count=1,
            )
        self.assertIn("queue is full", str(queue_error.exception))


if __name__ == "__main__":
    unittest.main()
