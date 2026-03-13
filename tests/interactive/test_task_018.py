from __future__ import annotations

import unittest

from backend.api.interactive_status import build_interactive_runtime_status
from tests.interactive.runtime_status_schema import (
    load_runtime_status_sample,
    load_runtime_status_schema,
    validate_runtime_status_payload_against_schema,
)


class Task018RuntimeStatusContractTests(unittest.TestCase):
    def test_green_defines_runtime_status_contract_for_all_supported_states(self) -> None:
        schema = load_runtime_status_schema()
        sample = load_runtime_status_sample()
        self.assertTrue(validate_runtime_status_payload_against_schema(sample, schema))

        idle_payload = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "idle"},
            source="boot",
            transport_state="connected",
        )
        active_payload = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "active", "active_flags": []},
            source="live_notification",
            transport_state="connected",
        )
        waiting_payload = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "active", "active_flags": ["waitingOnUserInput"]},
            source="live_notification",
            transport_state="connected",
        )
        error_payload = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "systemError"},
            source="live_notification",
            transport_state="connected",
        )
        reconnect_payload = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "active", "active_flags": []},
            source="recovered",
            transport_state="reconnecting",
            reconnect_reason="transport_drop",
        )
        boot_reconnect_payload = build_interactive_runtime_status(
            thread_id="thread-fixture-codex-001",
            session_id="sess-fixture-codex-001",
            raw_status={"type": "notLoaded", "active_flags": []},
            source="boot",
            transport_state="connected",
        )

        for payload in (
            idle_payload,
            active_payload,
            waiting_payload,
            error_payload,
            reconnect_payload,
            boot_reconnect_payload,
        ):
            self.assertTrue(validate_runtime_status_payload_against_schema(payload, schema))

        self.assertEqual(idle_payload["status"], "idle")
        self.assertEqual(active_payload["status"], "active")
        self.assertEqual(waiting_payload["status"], "waiting")
        self.assertEqual(waiting_payload["wait_reason"], "user_input")
        self.assertTrue(waiting_payload["can_send_input"])
        self.assertEqual(error_payload["status"], "error")
        self.assertEqual(reconnect_payload["status"], "reconnect")
        self.assertEqual(reconnect_payload["reconnect_hint"]["reason"], "transport_drop")
        self.assertEqual(boot_reconnect_payload["status"], "reconnect")
        self.assertEqual(
            boot_reconnect_payload["reconnect_hint"]["reason"],
            "resume_after_boot",
        )

    def test_red_rejects_unknown_runtime_status_shape(self) -> None:
        with self.assertRaises(ValueError):
            build_interactive_runtime_status(
                thread_id="thread-fixture-codex-001",
                session_id="sess-fixture-codex-001",
                raw_status={"type": "mystery"},
                source="live_notification",
                transport_state="connected",
            )


if __name__ == "__main__":
    unittest.main()
