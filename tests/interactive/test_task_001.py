from __future__ import annotations

import unittest
from pathlib import Path

from backend.api.session_artifacts import build_session_route
from backend.parsers.base import SessionStatus
from backend.parsers.codex_parser import CodexParser
from tests.interactive.fixtures import codex_fixture_path, load_codex_fixture_records


class Task001CodexFixtureTests(unittest.TestCase):
    def test_fixture_artifact(self) -> None:
        fixture_path = codex_fixture_path()
        self.assertTrue(fixture_path.exists(), f"missing fixture: {fixture_path}")

        records = load_codex_fixture_records()
        self.assertGreaterEqual(len(records), 6)
        self.assertEqual(records[0]["type"], "session_meta")
        self.assertEqual(records[1]["type"], "response_item")

        summary = CodexParser().parse_file(fixture_path)

        self.assertEqual(summary.agent_type.value, "codex")
        self.assertEqual(summary.session_id, "sess-fixture-codex-001")
        self.assertEqual(summary.cwd, "/home/pets/zoo/agents_sessions_dashboard")
        self.assertEqual(summary.status, SessionStatus.COMPLETED)
        self.assertEqual(summary.first_user_message, "Build deterministic fixture for interactive mode")
        self.assertEqual(summary.last_user_message, "Build deterministic fixture for interactive mode")
        self.assertIn("exec_command", summary.tool_calls)
        self.assertIn("apply_patch", summary.tool_calls)
        self.assertEqual(summary.token_usage["input_tokens"], 42)
        self.assertEqual(summary.token_usage["output_tokens"], 17)
        self.assertEqual(summary.token_usage["total_tokens"], 59)
        self.assertIn("tests/interactive/test_task_001.py", summary.files_modified)
        self.assertEqual(summary.plan_steps[0]["step"], "Create fixture artifact")
        self.assertEqual(summary.plan_steps[0]["status"], "completed")
        self.assertEqual([event.event_type for event in summary.timeline], [
            "function_call",
            "task_complete",
        ])

        route = build_session_route("codex", str(fixture_path), summary.session_id)
        self.assertEqual(route["id"], fixture_path.name)
        self.assertEqual(route["href"], f"/sessions/codex/{fixture_path.name}")

    def test_missing_fixture(self) -> None:
        missing_path = Path("/tmp/interactive-task-check/missing-rollout.jsonl")
        self.assertFalse(missing_path.exists())
        with self.assertRaises(FileNotFoundError):
            CodexParser().parse_file(missing_path)


if __name__ == "__main__":
    unittest.main()
