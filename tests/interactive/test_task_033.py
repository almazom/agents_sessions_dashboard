from __future__ import annotations

import unittest

from backend.api.interactive_actions import validate_inbound_action


class Task033InboundActionValidationTests(unittest.TestCase):
    @staticmethod
    def _validation_kwargs() -> dict[str, str]:
        return {
            "authenticated_actor_id": "interactive-supervisor-001",
            "expected_thread_id": "thread-fixture-codex-001",
            "expected_supervisor_owner_id": "interactive-supervisor-001",
        }

    def test_green_accepts_prompt_submit_action_for_owner(self) -> None:
        action = validate_inbound_action(
            action={
                "action_type": "prompt_submit",
                "thread_id": "thread-fixture-codex-001",
                "supervisor_owner_id": "interactive-supervisor-001",
                "payload": {
                    "text": "Continue from the last replayed message.",
                    "client_event_id": "browser-event-010",
                },
            },
            **self._validation_kwargs(),
        )

        self.assertEqual(action["action_type"], "prompt_submit")
        self.assertEqual(
            action["payload"]["text"],
            "Continue from the last replayed message.",
        )

    def test_green_accepts_cancel_interrupt_action_for_owner(self) -> None:
        action = validate_inbound_action(
            action={
                "action_type": "cancel_interrupt",
                "thread_id": "thread-fixture-codex-001",
                "supervisor_owner_id": "interactive-supervisor-001",
                "payload": {
                    "mode": "cancel",
                    "client_event_id": "browser-event-011",
                },
            },
            **self._validation_kwargs(),
        )

        self.assertEqual(action["payload"]["mode"], "cancel")

    def test_green_accepts_waiting_response_action_for_owner(self) -> None:
        action = validate_inbound_action(
            action={
                "action_type": "waiting_response",
                "thread_id": "thread-fixture-codex-001",
                "supervisor_owner_id": "interactive-supervisor-001",
                "payload": {
                    "wait_reason": "approval",
                    "response": "approve",
                    "client_event_id": "browser-event-012",
                },
            },
            **self._validation_kwargs(),
        )

        self.assertEqual(action["payload"]["wait_reason"], "approval")
        self.assertEqual(action["payload"]["response"], "approve")

    def test_red_rejects_actor_that_does_not_own_supervisor(self) -> None:
        with self.assertRaises(PermissionError):
            validate_inbound_action(
                action={
                    "action_type": "prompt_submit",
                    "thread_id": "thread-fixture-codex-001",
                    "supervisor_owner_id": "interactive-supervisor-001",
                    "payload": {
                        "text": "Continue from the last replayed message.",
                        "client_event_id": "browser-event-010",
                    },
                },
                authenticated_actor_id="interactive-supervisor-999",
                expected_thread_id="thread-fixture-codex-001",
                expected_supervisor_owner_id="interactive-supervisor-001",
            )

    def test_red_rejects_unknown_action_type(self) -> None:
        with self.assertRaises(ValueError):
            validate_inbound_action(
                action={
                    "action_type": "resume_stream",
                    "thread_id": "thread-fixture-codex-001",
                    "supervisor_owner_id": "interactive-supervisor-001",
                    "payload": {"client_event_id": "browser-event-013"},
                },
                **self._validation_kwargs(),
            )


if __name__ == "__main__":
    unittest.main()
