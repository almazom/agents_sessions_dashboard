from __future__ import annotations

import unittest

from tests.interactive.route_security_bundle import (
    InteractiveRouteSecurityMilestoneBundleBroken,
    build_route_security_milestone_bundle,
)


class Task050RouteAndSecurityMilestoneReproductionTests(unittest.TestCase):
    def test_route_security_bundle_green(self) -> None:
        bundle = build_route_security_milestone_bundle()

        self.assertEqual(
            bundle.backend_path,
            "/api/session-artifacts/codex/rollout-interactive-fixture.jsonl/interactive",
        )
        self.assertEqual(
            bundle.interactive_href,
            "/sessions/codex/rollout-interactive-fixture.jsonl/interactive",
        )
        self.assertEqual(bundle.transport, "codex_app_server")
        self.assertEqual(bundle.thread_id, "thread-fixture-codex-001")
        self.assertEqual(
            bundle.security_headers,
            (
                "same-origin",
                "session-cookie",
                "same-origin",
                "cookie-bound-http",
            ),
        )
        self.assertEqual(bundle.ownership_status_code, 403)
        self.assertEqual(bundle.prompt_disposition, "enqueue")
        self.assertEqual(bundle.control_disposition, "dispatch_now")
        self.assertEqual(bundle.observability_event, "interactive.lifecycle.transition")
        self.assertIn(
            "interactive_lifecycle_phase_supervisor_ready_total",
            bundle.observability_counter_keys,
        )

    def test_route_security_bundle_broken(self) -> None:
        with self.assertRaises(InteractiveRouteSecurityMilestoneBundleBroken) as error:
            build_route_security_milestone_bundle(force_cross_origin=True)

        self.assertIn("same-origin", str(error.exception))


if __name__ == "__main__":
    unittest.main()
