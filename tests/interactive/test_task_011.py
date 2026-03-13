from __future__ import annotations

import unittest

from backend.api.interactive_identity import (
    InteractiveIdentityMismatch,
    InteractiveIdentityNotFound,
    InteractiveIdentityStale,
    evaluate_runtime_identity_mapping,
    load_runtime_identity_fixture,
)


class Task011IdentityMismatchHandlingTests(unittest.TestCase):
    def test_green_covers_missing_stale_and_mismatched_identity_cases(self) -> None:
        fixture = load_runtime_identity_fixture()
        mapping = fixture["mappings"][0]

        self.assertEqual(
            evaluate_runtime_identity_mapping(
                mapping,
                harness="codex",
                artifact_route_id="rollout-interactive-fixture.jsonl",
                artifact_session_id="sess-fixture-codex-001",
            )["runtime"]["thread_id"],
            "thread-fixture-codex-001",
        )

        with self.assertRaises(InteractiveIdentityStale):
            evaluate_runtime_identity_mapping(
                mapping,
                harness="codex",
                artifact_route_id="rollout-interactive-fixture.jsonl",
                artifact_session_id="sess-fixture-codex-stale",
            )

        with self.assertRaises(InteractiveIdentityMismatch):
            evaluate_runtime_identity_mapping(
                mapping,
                harness="qwen",
                artifact_route_id="rollout-interactive-fixture.jsonl",
                artifact_session_id="sess-fixture-codex-001",
            )

    def test_red_missing_mapping_raises_not_found(self) -> None:
        fixture = load_runtime_identity_fixture()
        with self.assertRaises(InteractiveIdentityNotFound):
            evaluate_runtime_identity_mapping(
                fixture["mappings"][0],
                harness="codex",
                artifact_route_id="missing-rollout.jsonl",
                artifact_session_id="sess-fixture-codex-001",
            )


if __name__ == "__main__":
    unittest.main()
