from __future__ import annotations

import unittest
from pathlib import Path

from tests.interactive.real_session_browser_fixture import build_real_session_browser_fixture
from tests.interactive.route_security_bundle import build_route_security_milestone_bundle


START_PUBLISHED_SCRIPT = Path("/home/pets/zoo/agents_sessions_dashboard/scripts/start_published.sh")


class Task045PublishedInteractiveProofTests(unittest.TestCase):
    def test_published_interactive_proof(self) -> None:
        fixture = build_real_session_browser_fixture()
        security_bundle = build_route_security_milestone_bundle()

        self.assertTrue(START_PUBLISHED_SCRIPT.exists())
        self.assertTrue(fixture.published_base_url.startswith("http://"))
        self.assertEqual(
            fixture.interactive_route,
            "/sessions/codex/rollout-interactive-fixture.jsonl/interactive",
        )
        self.assertEqual(security_bundle.ownership_status_code, 403)
        self.assertIn("cookie-bound-http", security_bundle.security_headers)

    def test_unauthorized_published_interactive_proof(self) -> None:
        security_bundle = build_route_security_milestone_bundle()

        self.assertEqual(security_bundle.ownership_status_code, 403)


if __name__ == "__main__":
    unittest.main()
