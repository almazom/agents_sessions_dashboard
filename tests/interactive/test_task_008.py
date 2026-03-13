from __future__ import annotations

import unittest
from pathlib import Path

from tests.interactive.transport_adr import (
    InteractiveTransportAdrNotFound,
    load_transport_adr,
)


class Task008TransportAdrTests(unittest.TestCase):
    def test_green_loads_transport_adr_decision(self) -> None:
        adr = load_transport_adr()

        self.assertEqual(
            adr.path,
            Path("/home/pets/zoo/agents_sessions_dashboard/docs/adr/interactive-transport-v1.md"),
        )
        self.assertEqual(adr.primary_browser_transport, "codex_app_server")
        self.assertEqual(adr.fallback_policy, "raw_exec_and_sdk_are_backend_only_fallbacks")
        self.assertEqual(adr.sdk_role, "node_sidecar_adapter")
        self.assertEqual(
            adr.non_goals,
            [
                "direct_browser_sdk",
                "pty_scraping",
                "qemu_or_browser_vm",
            ],
        )
        self.assertIn("/sessions/[harness]/[id]/interactive", adr.interactive_route)

    def test_red_missing_transport_adr_fails_honestly(self) -> None:
        with self.assertRaises(InteractiveTransportAdrNotFound):
            load_transport_adr(
                adr_path=Path("/tmp/interactive-task-check/missing-interactive-transport-v1.md")
            )


if __name__ == "__main__":
    unittest.main()
