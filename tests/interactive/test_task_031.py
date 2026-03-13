from __future__ import annotations

import unittest

from backend.api.interactive_actions import build_cancel_interrupt_action


class Task031CancelInterruptActionTests(unittest.TestCase):
    def test_green_builds_interrupt_action_from_browser_input(self) -> None:
        action = build_cancel_interrupt_action(
            thread_id="thread-fixture-codex-001",
            supervisor_owner_id="interactive-supervisor-001",
            mode="interrupt",
            client_event_id="browser-event-002",
        )

        self.assertEqual(action["action_type"], "cancel_interrupt")
        self.assertEqual(action["thread_id"], "thread-fixture-codex-001")
        self.assertEqual(action["supervisor_owner_id"], "interactive-supervisor-001")
        self.assertEqual(action["payload"]["mode"], "interrupt")
        self.assertEqual(action["payload"]["client_event_id"], "browser-event-002")

    def test_red_rejects_unknown_interrupt_mode(self) -> None:
        with self.assertRaises(ValueError):
            build_cancel_interrupt_action(
                thread_id="thread-fixture-codex-001",
                supervisor_owner_id="interactive-supervisor-001",
                mode="pause",
                client_event_id="browser-event-002",
            )


if __name__ == "__main__":
    unittest.main()
