from __future__ import annotations

import unittest
from pathlib import Path

from backend.api.interactive_identity import (
    InteractiveIdentityNotFound,
    load_runtime_identity_fixture,
    resolve_runtime_identity,
)
from tests.interactive.fixtures import codex_fixture_path


class Task002InteractiveIdentityTests(unittest.TestCase):
    def test_green_runtime_identity_mapping(self) -> None:
        fixture_path = codex_fixture_path()
        identity_fixture = load_runtime_identity_fixture()

        resolved = resolve_runtime_identity(
            identity_fixture,
            harness="codex",
            artifact_route_id=fixture_path.name,
        )

        self.assertEqual(resolved["artifact"]["route_id"], fixture_path.name)
        self.assertEqual(resolved["artifact"]["session_id"], "sess-fixture-codex-001")
        self.assertEqual(resolved["runtime"]["thread_id"], "thread-fixture-codex-001")
        self.assertEqual(resolved["runtime"]["transport"], "codex_exec_json")
        self.assertEqual(resolved["runtime"]["source"], "fixture")

    def test_red_missing_runtime_identity_mapping(self) -> None:
        identity_fixture = load_runtime_identity_fixture()

        with self.assertRaises(InteractiveIdentityNotFound):
            resolve_runtime_identity(
                identity_fixture,
                harness="codex",
                artifact_route_id="missing-rollout.jsonl",
            )


if __name__ == "__main__":
    unittest.main()
