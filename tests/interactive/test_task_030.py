from __future__ import annotations

import unittest

from backend.api.interactive_actions import build_prompt_submit_action


class Task030PromptSubmitActionTests(unittest.TestCase):
    def test_green_builds_prompt_submit_action_from_browser_input(self) -> None:
        prompt_text = "Continue with the browser session."
        action = build_prompt_submit_action(
            thread_id="thread-fixture-codex-001",
            supervisor_owner_id="interactive-supervisor-001",
            text=prompt_text,
            client_event_id="browser-event-001",
        )

        self.assertEqual(action["action_type"], "prompt_submit")
        self.assertEqual(action["thread_id"], "thread-fixture-codex-001")
        self.assertEqual(action["supervisor_owner_id"], "interactive-supervisor-001")
        self.assertEqual(action["payload"]["text"], prompt_text)
        self.assertEqual(action["payload"]["client_event_id"], "browser-event-001")

    def test_red_rejects_empty_prompt_submit_text(self) -> None:
        with self.assertRaises(ValueError):
            build_prompt_submit_action(
                thread_id="thread-fixture-codex-001",
                supervisor_owner_id="interactive-supervisor-001",
                text="   ",
                client_event_id="browser-event-001",
            )


if __name__ == "__main__":
    unittest.main()
