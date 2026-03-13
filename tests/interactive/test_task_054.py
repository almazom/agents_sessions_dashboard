from __future__ import annotations

import unittest

from tests.interactive.sdk_sidecar_probe import build_codex_sdk_sidecar_probe


class Task054CodexSdkSidecarProbeTests(unittest.TestCase):
    def test_sdk_sidecar_probe_green(self) -> None:
        verdict = build_codex_sdk_sidecar_probe()

        self.assertEqual(verdict.package_name, "@openai/codex-sdk")
        self.assertEqual(verdict.node_requirement, ">=18")
        self.assertEqual(verdict.status, "adopt_with_scope")
        self.assertEqual(verdict.primary_browser_transport, "codex_app_server")
        self.assertTrue(verdict.supports_run_streamed)
        self.assertTrue(verdict.supports_resume_thread)
        self.assertTrue(verdict.supports_event_capture)
        self.assertTrue(verdict.fit_for_fixture_seeding)
        self.assertTrue(verdict.fit_for_python_backend_sidecar)
        self.assertFalse(verdict.fit_for_browser_transport)
        self.assertIn("backend_sidecar_adapter", verdict.recommended_roles)
        self.assertIn("browser_transport", verdict.rejected_roles)
        self.assertIn("runStreamed", " ".join(verdict.capabilities))

    def test_sdk_sidecar_rejected(self) -> None:
        verdict = build_codex_sdk_sidecar_probe(requested_surface="browser_transport")

        self.assertEqual(verdict.status, "rejected")
        self.assertFalse(verdict.fit_for_requested_surface)
        self.assertIn("browser transport", verdict.summary)
        self.assertIn("codex_app_server", verdict.summary)


if __name__ == "__main__":
    unittest.main()
