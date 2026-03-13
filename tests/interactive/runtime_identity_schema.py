from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_IDENTITY_SCHEMA_PATH = REPO_ROOT / "contracts" / "interactive-runtime-identity.schema.json"
ARTIFACT_IDENTITY_KEYS = ("harness", "route_id", "session_id", "source_file")
RUNTIME_IDENTITY_KEYS = ("thread_id", "session_id", "transport", "source")


class InteractiveRuntimeIdentitySchemaNotFound(FileNotFoundError):
    """Raised when the runtime identity schema file is missing or incomplete."""


@dataclass(frozen=True)
class InteractiveRuntimeIdentitySchema:
    path: Path
    version: str
    required_top_level_keys: list[str]
    runtime_transport_values: list[str]
    runtime_source_values: list[str]


def load_runtime_identity_schema(
    schema_path: Path | None = None,
) -> InteractiveRuntimeIdentitySchema:
    resolved_path = (schema_path or RUNTIME_IDENTITY_SCHEMA_PATH).resolve()
    if not resolved_path.exists():
        raise InteractiveRuntimeIdentitySchemaNotFound(
            f"interactive runtime identity schema is missing: {resolved_path}"
        )

    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    try:
        runtime_properties = payload["definitions"]["runtimeIdentity"]["properties"]
        runtime_transport_values = runtime_properties["transport"]["enum"]
        runtime_source_values = runtime_properties["source"]["enum"]
    except KeyError as error:
        raise InteractiveRuntimeIdentitySchemaNotFound(
            f"interactive runtime identity schema is incomplete: {resolved_path}"
        ) from error

    return InteractiveRuntimeIdentitySchema(
        path=resolved_path,
        version=payload["version"],
        required_top_level_keys=payload["required"],
        runtime_transport_values=runtime_transport_values,
        runtime_source_values=runtime_source_values,
    )


def validate_runtime_identity_fixture_against_schema(
    fixture_payload: Dict[str, Any],
    schema: InteractiveRuntimeIdentitySchema,
) -> bool:
    if sorted(fixture_payload.keys()) != sorted(schema.required_top_level_keys):
        return False
    if not isinstance(fixture_payload.get("version"), int):
        return False

    mappings = fixture_payload.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        return False

    for mapping in mappings:
        artifact = mapping.get("artifact")
        runtime = mapping.get("runtime")
        if not isinstance(artifact, dict) or not isinstance(runtime, dict):
            return False
        if not all(isinstance(artifact.get(key), str) for key in ARTIFACT_IDENTITY_KEYS):
            return False
        if not all(isinstance(runtime.get(key), str) for key in RUNTIME_IDENTITY_KEYS):
            return False
        if runtime["transport"] not in schema.runtime_transport_values:
            return False
        if runtime["source"] not in schema.runtime_source_values:
            return False

    return True
