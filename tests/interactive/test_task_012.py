from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api.session_artifacts import build_session_detail_payload


class Task012InteractiveCapabilityPayloadTests(unittest.TestCase):
    def test_green_adds_interactive_capability_for_supported_codex_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "rollout-interactive-fixture.jsonl"
            file_path.write_text(json.dumps({"type": "session_meta"}), encoding="utf-8")

            with patch("backend.api.session_artifacts.build_session_git_commit_context", return_value={
                "repository_root": None,
                "commits": [],
            }):
                payload = build_session_detail_payload(
                    {
                        "session_id": "sess-fixture-codex-001",
                        "agent_type": "codex",
                        "agent_name": "Codex",
                        "cwd": "/home/pets/zoo/agents_sessions_dashboard",
                        "timestamp_start": "2026-03-12T08:00:00+00:00",
                        "timestamp_end": "2026-03-12T08:05:00+00:00",
                        "status": "active",
                        "resume_supported": True,
                    },
                    file_path,
                )

        capability = payload["session"]["state_model"]["interactive_session"]
        self.assertTrue(capability["available"])
        self.assertEqual(capability["transport"], "codex_app_server")
        self.assertEqual(capability["href"], "/sessions/codex/rollout-interactive-fixture.jsonl/interactive")
        self.assertIn("Interactive mode", capability["label"])

    def test_red_reports_honest_disabled_reason_for_unsupported_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "rollout-gemini.json"
            file_path.write_text(json.dumps({"type": "session_meta"}), encoding="utf-8")

            with patch("backend.api.session_artifacts.build_session_git_commit_context", return_value={
                "repository_root": None,
                "commits": [],
            }):
                payload = build_session_detail_payload(
                    {
                        "session_id": "sess-gemini-001",
                        "agent_type": "gemini",
                        "agent_name": "Gemini",
                        "cwd": "/home/pets/zoo/agents_sessions_dashboard",
                        "timestamp_start": "2026-03-12T08:00:00+00:00",
                        "timestamp_end": "2026-03-12T08:05:00+00:00",
                        "status": "completed",
                    },
                    file_path,
                )

        capability = payload["session"]["state_model"]["interactive_session"]
        self.assertFalse(capability["available"])
        self.assertIsNone(capability["href"])
        self.assertIn("not supported", capability["detail"])


if __name__ == "__main__":
    unittest.main()
