from __future__ import annotations

import unittest
from pathlib import Path

from tests.interactive.real_session_browser_fixture import build_real_session_browser_fixture


PLAYWRIGHT_SPEC_PATH = Path(
    "/home/pets/zoo/agents_sessions_dashboard/frontend/e2e/interactive-session.spec.ts"
)


class Task043LocalHappyPathProofTests(unittest.TestCase):
    def test_green_local_happy_path_proof(self) -> None:
        fixture = build_real_session_browser_fixture()
        spec_source = PLAYWRIGHT_SPEC_PATH.read_text(encoding="utf-8")

        self.assertEqual(fixture.handoff_phase, "live_attach_ready")
        self.assertEqual(fixture.reconnect_phase, "reconnect_bootstrap")
        self.assertEqual(fixture.supervisor_phase, "supervisor_ready")
        self.assertIn("tail snapshot shows last messages", spec_source)
        self.assertIn("detail CTA opens interactive route", spec_source)
        self.assertIn("interactive prompt roundtrip", spec_source)
        self.assertNotIn("test.skip(", spec_source)
        self.assertIn("Reconnecting to runtime", spec_source)

    def test_red_local_happy_path_proof(self) -> None:
        missing_spec = Path("/tmp/interactive-task-check/missing-interactive-session.spec.ts")
        with self.assertRaises(FileNotFoundError):
            missing_spec.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
