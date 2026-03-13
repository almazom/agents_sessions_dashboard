from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_STATUS_SCHEMA_PATH = REPO_ROOT / "contracts" / "interactive-runtime-status.schema.json"
RUNTIME_STATUS_SAMPLE_PATH = (
    REPO_ROOT / "contracts" / "examples" / "interactive-runtime-status.sample.json"
)


class InteractiveRuntimeStatusSchemaNotFound(FileNotFoundError):
    """Raised when the runtime status schema or sample is missing or incomplete."""


@dataclass(frozen=True)
class InteractiveRuntimeStatusSchema:
    path: Path
    version: str
    required_top_level_keys: list[str]
    status_values: list[str]
    transport_state_values: list[str]
    source_values: list[str]
    raw_status_values: list[str]
    active_flag_values: list[str]
    wait_reason_values: list[str]
    reconnect_reason_values: list[str]


def _load_json_object(path: Path, *, label: str) -> Dict[str, Any]:
    resolved_path = path.resolve()
    if not resolved_path.exists():
        raise InteractiveRuntimeStatusSchemaNotFound(f"{label} is missing: {resolved_path}")

    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InteractiveRuntimeStatusSchemaNotFound(
            f"{label} must be an object: {resolved_path}"
        )
    return payload


def load_runtime_status_schema(
    schema_path: Path | None = None,
) -> InteractiveRuntimeStatusSchema:
    payload = _load_json_object(
        schema_path or RUNTIME_STATUS_SCHEMA_PATH,
        label="interactive runtime status schema",
    )
    try:
        definitions = payload["definitions"]
        raw_status_properties = definitions["rawStatus"]["properties"]
        reconnect_properties = definitions["reconnectHint"]["properties"]
    except KeyError as error:
        raise InteractiveRuntimeStatusSchemaNotFound(
            "interactive runtime status schema is incomplete"
        ) from error

    return InteractiveRuntimeStatusSchema(
        path=(schema_path or RUNTIME_STATUS_SCHEMA_PATH).resolve(),
        version=payload["version"],
        required_top_level_keys=payload["required"],
        status_values=payload["properties"]["status"]["enum"],
        transport_state_values=payload["properties"]["transport_state"]["enum"],
        source_values=payload["properties"]["source"]["enum"],
        raw_status_values=raw_status_properties["type"]["enum"],
        active_flag_values=raw_status_properties["active_flags"]["items"]["enum"],
        wait_reason_values=payload["properties"]["wait_reason"]["enum"][:-1],
        reconnect_reason_values=reconnect_properties["reason"]["enum"],
    )


def load_runtime_status_sample(sample_path: Path | None = None) -> Dict[str, Any]:
    return _load_json_object(
        sample_path or RUNTIME_STATUS_SAMPLE_PATH,
        label="interactive runtime status sample",
    )


def validate_runtime_status_payload_against_schema(
    payload: Dict[str, Any],
    schema: InteractiveRuntimeStatusSchema,
) -> bool:
    if sorted(payload.keys()) != sorted(schema.required_top_level_keys):
        return False
    if not isinstance(payload.get("version"), int):
        return False
    if payload.get("status") not in schema.status_values:
        return False
    if payload.get("transport_state") not in schema.transport_state_values:
        return False
    if payload.get("source") not in schema.source_values:
        return False
    if not isinstance(payload.get("thread_id"), str) or not payload["thread_id"]:
        return False
    if not isinstance(payload.get("session_id"), str) or not payload["session_id"]:
        return False
    if not all(
        isinstance(payload.get(key), str) and payload.get(key)
        for key in ("label", "detail")
    ):
        return False
    if not all(
        isinstance(payload.get(key), bool)
        for key in ("can_send_input", "can_resume_stream")
    ):
        return False

    raw_status = payload.get("raw_status")
    if not isinstance(raw_status, dict):
        return False
    if raw_status.get("type") not in schema.raw_status_values:
        return False
    active_flags = raw_status.get("active_flags")
    if not isinstance(active_flags, list):
        return False
    if not all(flag in schema.active_flag_values for flag in active_flags):
        return False
    if raw_status["type"] != "active" and active_flags:
        return False

    wait_reason = payload.get("wait_reason")
    if wait_reason is not None and wait_reason not in schema.wait_reason_values:
        return False
    if payload["status"] == "waiting" and wait_reason is None:
        return False
    if payload["status"] != "waiting" and wait_reason is not None:
        return False

    reconnect_hint = payload.get("reconnect_hint")
    if reconnect_hint is not None:
        if not isinstance(reconnect_hint, dict):
            return False
        if reconnect_hint.get("reason") not in schema.reconnect_reason_values:
            return False
        if not isinstance(reconnect_hint.get("attempt"), int) or reconnect_hint["attempt"] < 1:
            return False
    if payload["status"] == "reconnect" and reconnect_hint is None:
        return False
    if payload["status"] != "reconnect" and reconnect_hint is not None:
        return False

    observed_at = payload.get("observed_at")
    if observed_at is not None and not isinstance(observed_at, str):
        return False

    return True
