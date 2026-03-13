"""Helpers for mapping an artifact route to a resumable runtime identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "interactive" / "codex" / "runtime_identity.json"


class InteractiveIdentityNotFound(LookupError):
    """Raised when no runtime identity mapping exists for the artifact route."""


def load_runtime_identity_fixture(path: Path | None = None) -> Dict[str, Any]:
    fixture_path = path or DEFAULT_FIXTURE_PATH
    with fixture_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict) or not isinstance(payload.get("mappings"), list):
        raise ValueError("runtime identity fixture must be an object with a mappings list")

    return payload


def resolve_runtime_identity(
    fixture_payload: Dict[str, Any],
    *,
    harness: str,
    artifact_route_id: str,
) -> Dict[str, Any]:
    for mapping in fixture_payload.get("mappings", []):
        artifact = mapping.get("artifact") or {}
        if artifact.get("harness") != harness:
            continue
        if artifact.get("route_id") != artifact_route_id:
            continue
        return mapping

    raise InteractiveIdentityNotFound(
        f"missing runtime identity mapping for {harness}/{artifact_route_id}"
    )

