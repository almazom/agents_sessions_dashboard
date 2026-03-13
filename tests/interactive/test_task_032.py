from __future__ import annotations

import unittest

from backend.api.interactive_actions import build_waiting_response_action


class Task032ApprovalUserInputActionTests(unittest.TestCase):
    def test_green_builds_approval_response_action(self) -> None:
        action = build_waiting_response_action(
            thread_id="thread-fixture-codex-001",
            supervisor_owner_id="interactive-supervisor-001",
            wait_reason="approval",
            response="approve",
            client_event_id="browser-event-003",
        )

        self.assertEqual(action["action_type"], "waiting_response")
        self.assertEqual(action["payload"]["wait_reason"], "approval")
        self.assertEqual(action["payload"]["response"], "approve")
        self.assertEqual(action["payload"]["client_event_id"], "browser-event-003")

    def test_green_builds_user_input_response_action(self) -> None:
        action = build_waiting_response_action(
            thread_id="thread-fixture-codex-001",
            supervisor_owner_id="interactive-supervisor-001",
            wait_reason="user_input",
            response="Use the last three messages as context.",
            client_event_id="browser-event-004",
        )

        self.assertEqual(action["action_type"], "waiting_response")
        self.assertEqual(action["payload"]["wait_reason"], "user_input")
        self.assertEqual(
            action["payload"]["response"],
            "Use the last three messages as context.",
        )

    def test_red_rejects_unknown_approval_response(self) -> None:
        with self.assertRaises(ValueError):
            build_waiting_response_action(
                thread_id="thread-fixture-codex-001",
                supervisor_owner_id="interactive-supervisor-001",
                wait_reason="approval",
                response="later",
                client_event_id="browser-event-003",
            )


if __name__ == "__main__":
    unittest.main()
