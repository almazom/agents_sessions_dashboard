from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.api.interactive_handoff import build_replay_to_live_handoff
from backend.api.interactive_reconnect import build_reconnect_bootstrap_snapshot
from backend.api.interactive_replay import add_history_complete_marker, build_replay_event_snapshot
from backend.api.interactive_status import build_interactive_runtime_status
from backend.api.interactive_store import build_operational_store_snapshot
from backend.api.interactive_supervisor import start_supervisor_resume_flow
from tests.interactive.backend_harness import build_interactive_backend_harness
from tests.interactive.sdk_sidecar_probe import build_codex_sdk_sidecar_probe

from .fixtures import codex_fixture_path


REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:8888"
DEFAULT_PUBLISHED_BASE_URL = "http://107.174.231.22:8888"


class RealSessionBrowserFixtureBroken(RuntimeError):
    """Raised when the real-session browser fixture cannot be composed honestly."""


@dataclass(frozen=True)
class RealSessionBrowserFixture:
    artifact_path: Path
    detail_route: str
    interactive_route: str
    thread_id: str
    session_id: str
    tail_texts: tuple[str, ...]
    replay_event_types: tuple[str, ...]
    history_boundary_event_id: str
    handoff_phase: str
    reconnect_phase: str
    supervisor_phase: str
    local_base_url: str
    published_base_url: str
    playwright_command: str
    sdk_status: str


def _read_env_value(name: str) -> str:
    if not ENV_PATH.exists():
        return ""

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()
    return ""


def _released_supervisor() -> dict[str, str]:
    return {
        "owner_id": "interactive-supervisor-001",
        "lease_id": "lease-fixture-browser-001",
        "lock_status": "released",
        "heartbeat_at": "2026-03-14T00:10:00Z",
        "lock_expires_at": "2026-03-14T00:15:00Z",
    }


def build_real_session_browser_fixture(
    *,
    artifact_path: Path | None = None,
) -> RealSessionBrowserFixture:
    resolved_artifact_path = (artifact_path or codex_fixture_path()).resolve()
    if not resolved_artifact_path.exists():
        raise RealSessionBrowserFixtureBroken(
            f"real-session browser fixture is missing: {resolved_artifact_path}"
        )

    try:
        harness = build_interactive_backend_harness(artifact_path=resolved_artifact_path)
        tail_snapshot = harness.summary.last_user_message
        replay_snapshot = add_history_complete_marker(
            build_replay_event_snapshot(resolved_artifact_path)
        )
        runtime_status = build_interactive_runtime_status(
            thread_id=harness.runtime_identity["runtime"]["thread_id"],
            session_id=harness.runtime_identity["runtime"]["session_id"],
            raw_status={"type": "idle", "active_flags": []},
            source="live_notification",
            transport_state="connected",
        )
        handoff = build_replay_to_live_handoff(
            replay_snapshot=replay_snapshot,
            runtime_identity=harness.runtime_identity,
            runtime_status=runtime_status,
        )
        reconnect_status = build_interactive_runtime_status(
            thread_id=harness.runtime_identity["runtime"]["thread_id"],
            session_id=harness.runtime_identity["runtime"]["session_id"],
            raw_status={"type": "active", "active_flags": []},
            source="recovered",
            transport_state="reconnecting",
            reconnect_reason="page_reload",
        )
        reconnect_snapshot = build_reconnect_bootstrap_snapshot(
            build_replay_to_live_handoff(
                replay_snapshot=replay_snapshot,
                runtime_identity=harness.runtime_identity,
                runtime_status=reconnect_status,
            )
        )
        store_snapshot = build_operational_store_snapshot(
            route=harness.route,
            runtime_identity=harness.runtime_identity["runtime"],
            runtime_status=runtime_status,
            supervisor=_released_supervisor(),
            updated_at="2026-03-14T00:10:00Z",
        )
        supervisor_plan = start_supervisor_resume_flow(
            handoff=handoff,
            store_record=store_snapshot["records"][0],
            owner_id="interactive-supervisor-001",
            lease_id="lease-fixture-browser-002",
            heartbeat_at="2026-03-14T00:11:00Z",
            lock_expires_at="2026-03-14T00:16:00Z",
        )
        sdk_probe = build_codex_sdk_sidecar_probe()
    except (LookupError, PermissionError, ValueError, RuntimeError) as error:
        raise RealSessionBrowserFixtureBroken(str(error)) from error

    if not sdk_probe.fit_for_fixture_seeding:
        raise RealSessionBrowserFixtureBroken(
            "Codex SDK probe no longer supports fixture seeding"
        )

    local_base_url = f"http://127.0.0.1:{_read_env_value('NEXUS_PUBLIC_PORT') or '8888'}"
    published_base_url = (
        _read_env_value("NEXUS_PUBLIC_URL")
        or DEFAULT_PUBLISHED_BASE_URL
    )

    return RealSessionBrowserFixture(
        artifact_path=resolved_artifact_path,
        detail_route=harness.route["href"],
        interactive_route=f"{harness.route['href']}/interactive",
        thread_id=harness.runtime_identity["runtime"]["thread_id"],
        session_id=harness.runtime_identity["runtime"]["session_id"],
        tail_texts=(
            str(tail_snapshot),
            "Latest observed event: task_complete.",
            f"Session {harness.summary.session_id} maps to thread {harness.runtime_identity['runtime']['thread_id']}.",
        ),
        replay_event_types=tuple(
            str(item["event_type"]) for item in replay_snapshot["items"]
        ),
        history_boundary_event_id=str(handoff["history_boundary_event_id"]),
        handoff_phase=str(handoff["phase"]),
        reconnect_phase=str(reconnect_snapshot["phase"]),
        supervisor_phase=str(supervisor_plan["phase"]),
        local_base_url=local_base_url or DEFAULT_LOCAL_BASE_URL,
        published_base_url=published_base_url,
        playwright_command="cd frontend && npx playwright test e2e/interactive-session.spec.ts",
        sdk_status=str(sdk_probe.status),
    )
