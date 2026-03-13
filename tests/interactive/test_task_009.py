from __future__ import annotations

import unittest
from pathlib import Path

from tests.interactive.runtime_identity_schema import (
    InteractiveRuntimeIdentitySchemaNotFound,
    load_runtime_identity_schema,
    validate_runtime_identity_fixture_against_schema,
)
from tests.interactive.fixtures import load_codex_runtime_identity


class Task009RuntimeIdentitySchemaTests(unittest.TestCase):
    def test_green_runtime_identity_schema_accepts_fixture(self) -> None:
        schema = load_runtime_identity_schema()
        fixture = load_codex_runtime_identity()

        self.assertEqual(
            schema.path,
            Path("/home/pets/zoo/agents_sessions_dashboard/contracts/interactive-runtime-identity.schema.json"),
        )
        self.assertEqual(schema.version, "1.0.0")
        self.assertEqual(schema.required_top_level_keys, ["version", "mappings"])
        self.assertEqual(
            schema.runtime_transport_values,
            ["codex_app_server", "codex_exec_json", "codex_sdk_ts"],
        )
        self.assertEqual(
            schema.runtime_source_values,
            ["fixture", "operational_live", "recovered"],
        )
        self.assertTrue(validate_runtime_identity_fixture_against_schema(fixture, schema))

    def test_red_missing_runtime_identity_schema_fails_honestly(self) -> None:
        with self.assertRaises(InteractiveRuntimeIdentitySchemaNotFound):
            load_runtime_identity_schema(
                schema_path=Path("/tmp/interactive-task-check/missing-interactive-runtime-identity.schema.json")
            )


if __name__ == "__main__":
    unittest.main()
