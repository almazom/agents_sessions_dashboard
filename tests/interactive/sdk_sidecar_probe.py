from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .transport_matrix import (
    SSOT_KANBAN_PATH,
    build_codex_transport_matrix,
)


class CodexSdkSidecarProbeNotFound(FileNotFoundError):
    """Raised when the local SDK probe references are missing or incomplete."""


@dataclass(frozen=True)
class CodexSdkSidecarProbeVerdict:
    package_name: str
    node_requirement: str
    status: str
    requested_surface: str
    fit_for_requested_surface: bool
    primary_browser_transport: str
    supports_run_streamed: bool
    supports_resume_thread: bool
    supports_event_capture: bool
    fit_for_fixture_seeding: bool
    fit_for_python_backend_sidecar: bool
    fit_for_browser_transport: bool
    capabilities: tuple[str, ...]
    recommended_roles: tuple[str, ...]
    rejected_roles: tuple[str, ...]
    summary: str
    evidence_paths: tuple[str, ...]


def _load_reference_inputs(board_path: Path) -> dict[str, str]:
    payload = json.loads(board_path.read_text(encoding="utf-8"))
    return {
        item["id"]: item["path"]
        for item in payload["session"]["reference_inputs"]
        if "path" in item
    }


def _require_reference_path(reference_inputs: Mapping[str, str], reference_id: str) -> Path:
    raw_path = reference_inputs.get(reference_id)
    if not raw_path:
        raise CodexSdkSidecarProbeNotFound(
            f"Codex SDK sidecar probe reference is missing: {reference_id}"
        )

    resolved_path = Path(raw_path).resolve()
    if not resolved_path.exists():
        raise CodexSdkSidecarProbeNotFound(
            f"Codex SDK sidecar probe file is missing: {resolved_path}"
        )
    return resolved_path


def _require_reference_text(path: Path, needle: str) -> None:
    if needle not in path.read_text(encoding="utf-8"):
        raise CodexSdkSidecarProbeNotFound(
            f"Codex SDK sidecar evidence is missing in: {path}"
        )


def build_codex_sdk_sidecar_probe(
    *,
    requested_surface: str = "backend_sidecar_adapter",
    board_path: Path | None = None,
    reference_overrides: Mapping[str, str] | None = None,
) -> CodexSdkSidecarProbeVerdict:
    resolved_board_path = (board_path or SSOT_KANBAN_PATH).resolve()
    reference_inputs = _load_reference_inputs(resolved_board_path)
    if reference_overrides:
        reference_inputs.update(reference_overrides)

    sdk_root = _require_reference_path(reference_inputs, "local-codex-sdk-typescript")
    sdk_readme = _require_reference_path(reference_inputs, "local-codex-sdk-readme")
    sdk_thread = _require_reference_path(reference_inputs, "local-codex-sdk-thread")
    sdk_events = _require_reference_path(reference_inputs, "local-codex-sdk-events")
    sdk_items = _require_reference_path(reference_inputs, "local-codex-sdk-items")
    sdk_package = sdk_root / "package.json"
    sdk_exec = sdk_root / "src" / "exec.ts"
    sdk_codex = sdk_root / "src" / "codex.ts"

    for path in (sdk_package, sdk_exec, sdk_codex):
        if not path.exists():
            raise CodexSdkSidecarProbeNotFound(
                f"Codex SDK sidecar probe file is missing: {path.resolve()}"
            )

    _require_reference_text(sdk_readme, "spawns the CLI and exchanges JSONL events over stdin/stdout")
    _require_reference_text(sdk_readme, "runStreamed()")
    _require_reference_text(sdk_readme, "resumeThread()")
    _require_reference_text(sdk_thread, "runStreamed")
    _require_reference_text(sdk_events, 'type: "thread.started"')
    _require_reference_text(sdk_items, 'type: "command_execution"')
    _require_reference_text(sdk_exec, "spawn(")
    _require_reference_text(sdk_exec, "--experimental-json")
    _require_reference_text(sdk_exec, "codex_sdk_ts")
    _require_reference_text(sdk_codex, "resumeThread")

    package_payload = json.loads(sdk_package.read_text(encoding="utf-8"))
    matrix = build_codex_transport_matrix(
        board_path=resolved_board_path,
        reference_overrides=reference_overrides,
    )
    sdk_entry = matrix.entries["codex_sdk_ts"]

    package_name = str(package_payload.get("name") or "")
    node_requirement = str((package_payload.get("engines") or {}).get("node") or "")

    if package_name != "@openai/codex-sdk":
        raise CodexSdkSidecarProbeNotFound(
            f"unexpected Codex SDK package name: {package_name or '<missing>'}"
        )
    if not node_requirement:
        raise CodexSdkSidecarProbeNotFound(
            "Codex SDK package is missing the Node engine requirement"
        )

    supports_run_streamed = True
    supports_resume_thread = True
    supports_event_capture = True
    fit_for_fixture_seeding = True
    fit_for_python_backend_sidecar = True
    fit_for_browser_transport = False

    capabilities = (
        "runStreamed async event generator",
        "resumeThread from persisted thread id",
        "typed ThreadEvent and ThreadItem capture",
        "spawned codex exec --experimental-json bridge",
        "working-directory and output-schema controls for backend helpers",
    )
    recommended_roles = (
        "backend_sidecar_adapter",
        "fixture_seeding",
        "event_capture",
        "event_normalization",
    )
    rejected_roles = (
        "browser_transport",
        "app_server_replacement",
        "client_side_sdk",
    )

    if requested_surface == "browser_transport":
        status = "rejected"
        fit_for_requested_surface = False
        summary = (
            "Codex SDK should not be used as the browser transport; "
            "it is a Node wrapper over spawned codex exec, while "
            f"{matrix.primary_transport} remains the primary browser continuation contract."
        )
    else:
        status = "adopt_with_scope"
        fit_for_requested_surface = True
        summary = (
            "Codex SDK is a good backend sidecar adapter for runStreamed, resumeThread, "
            "fixture seeding, and event capture, but it should stay behind the backend owner "
            f"because {matrix.primary_transport} remains the browser-facing transport."
        )

    return CodexSdkSidecarProbeVerdict(
        package_name=package_name,
        node_requirement=node_requirement,
        status=status,
        requested_surface=requested_surface,
        fit_for_requested_surface=fit_for_requested_surface,
        primary_browser_transport=matrix.primary_transport,
        supports_run_streamed=supports_run_streamed,
        supports_resume_thread=supports_resume_thread,
        supports_event_capture=supports_event_capture,
        fit_for_fixture_seeding=fit_for_fixture_seeding,
        fit_for_python_backend_sidecar=fit_for_python_backend_sidecar,
        fit_for_browser_transport=fit_for_browser_transport,
        capabilities=capabilities,
        recommended_roles=recommended_roles,
        rejected_roles=rejected_roles,
        summary=summary,
        evidence_paths=(
            str(sdk_package.resolve()),
            str(sdk_readme),
            str(sdk_codex.resolve()),
            str(sdk_thread),
            str(sdk_exec.resolve()),
            str(sdk_events),
            str(sdk_items),
        ) + sdk_entry.evidence_paths,
    )
