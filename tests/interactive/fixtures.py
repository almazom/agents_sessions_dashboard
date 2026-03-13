from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "interactive"
CODEX_FIXTURE_DIR = FIXTURE_ROOT / "codex"
CODEX_FIXTURE_PATH = CODEX_FIXTURE_DIR / "rollout-interactive-fixture.jsonl"
CODEX_RUNTIME_IDENTITY_PATH = CODEX_FIXTURE_DIR / "runtime_identity.json"


def fixture_root() -> Path:
    return FIXTURE_ROOT


def codex_fixture_path() -> Path:
    return CODEX_FIXTURE_PATH


def codex_runtime_identity_path() -> Path:
    return CODEX_RUNTIME_IDENTITY_PATH


def load_codex_fixture_records() -> list[Dict[str, Any]]:
    records: list[Dict[str, Any]] = []
    with CODEX_FIXTURE_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def load_codex_runtime_identity() -> Dict[str, Any]:
    with CODEX_RUNTIME_IDENTITY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)
