from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.deps import User, get_current_user
from backend.api.interactive_actions import (
    build_cancel_interrupt_action,
    build_prompt_submit_action,
)
from backend.api.interactive_backpressure import evaluate_interactive_backpressure
from backend.api.interactive_observability import (
    build_interactive_lifecycle_observation,
)
from backend.api.interactive_status import build_interactive_runtime_status
from backend.api.routes.sessions import router as sessions_router
from tests.interactive.fixtures import codex_fixture_path
from tests.interactive.interactive_route_integration import (
    InteractiveRouteIntegrationBroken,
    build_interactive_route_integration_snapshot,
)


class InteractiveRouteSecurityMilestoneBundleBroken(RuntimeError):
    """Raised when the route/security milestone bundle is incomplete."""


@dataclass(frozen=True)
class InteractiveRouteSecurityMilestoneBundle:
    backend_path: str
    interactive_href: str
    transport: str
    thread_id: str
    security_headers: tuple[str, ...]
    ownership_status_code: int
    prompt_disposition: str
    control_disposition: str
    observability_event: str
    observability_counter_keys: tuple[str, ...]


def _app(username: str) -> FastAPI:
    app = FastAPI()
    app.include_router(sessions_router)
    app.dependency_overrides[get_current_user] = lambda: User(
        username=username,
        is_authenticated=True,
        auth_method="test",
    )
    return app


def _session_payload(*, owner_id: str) -> dict[str, object]:
    return {
        "session_id": "sess-fixture-codex-001",
        "agent_type": "codex",
        "agent_name": "Codex",
        "cwd": "/home/pets/zoo/agents_sessions_dashboard",
        "status": "active",
        "resume_supported": True,
        "interactive_owner_id": owner_id,
    }


def build_route_security_milestone_bundle(
    *,
    force_cross_origin: bool = False,
) -> InteractiveRouteSecurityMilestoneBundle:
    try:
        integration_snapshot = build_interactive_route_integration_snapshot()
    except InteractiveRouteIntegrationBroken as error:
        raise InteractiveRouteSecurityMilestoneBundleBroken(str(error)) from error

    owner_app = _app("admin")
    intruder_app = _app("intruder")
    backend_path = integration_snapshot.backend_path

    same_origin_headers = {
        "origin": "https://dashboard.test",
        "host": "dashboard.test",
        "x-forwarded-proto": "https",
        "sec-fetch-site": "same-origin",
    }
    if force_cross_origin:
        same_origin_headers = {
            **same_origin_headers,
            "origin": "https://evil.example",
            "sec-fetch-site": "cross-site",
        }

    with patch(
        "backend.api.routes.sessions._resolve_session_artifact_source",
        return_value=(_session_payload(owner_id="admin"), codex_fixture_path()),
    ):
        with TestClient(owner_app) as client:
            owner_response = client.get(backend_path, headers=same_origin_headers)

        with TestClient(intruder_app) as client:
            intruder_response = client.get(backend_path, headers={
                "origin": "https://dashboard.test",
                "host": "dashboard.test",
                "x-forwarded-proto": "https",
                "sec-fetch-site": "same-origin",
            })

    if owner_response.status_code != 200:
        raise InteractiveRouteSecurityMilestoneBundleBroken(
            f"interactive security boot returned {owner_response.status_code}: "
            f"{owner_response.json().get('detail', '')}"
        )
    if intruder_response.status_code != 403:
        raise InteractiveRouteSecurityMilestoneBundleBroken(
            f"interactive ownership guard returned {intruder_response.status_code} instead of 403"
        )

    security_headers = tuple(
        owner_response.headers.get(header_name, "")
        for header_name in (
            "cross-origin-resource-policy",
            "x-interactive-auth-token",
            "x-interactive-origin-policy",
            "x-interactive-transport-security",
        )
    )
    if security_headers != (
        "same-origin",
        "session-cookie",
        "same-origin",
        "cookie-bound-http",
    ):
        raise InteractiveRouteSecurityMilestoneBundleBroken(
            "interactive security headers are incomplete"
        )

    prompt_verdict = evaluate_interactive_backpressure(
        build_prompt_submit_action(
            thread_id=integration_snapshot.thread_id,
            supervisor_owner_id="interactive-supervisor-001",
            text="Continue from the browser.",
            client_event_id="browser-event-040",
        ),
        inflight_prompts=1,
        queued_prompts=1,
        recent_prompt_count=2,
    )
    control_verdict = evaluate_interactive_backpressure(
        build_cancel_interrupt_action(
            thread_id=integration_snapshot.thread_id,
            supervisor_owner_id="interactive-supervisor-001",
            mode="cancel",
            client_event_id="browser-event-041",
        ),
        inflight_prompts=1,
        queued_prompts=2,
        recent_prompt_count=4,
    )
    runtime_status = build_interactive_runtime_status(
        thread_id=integration_snapshot.thread_id,
        session_id="sess-fixture-codex-001",
        raw_status={"type": "active", "active_flags": []},
        source="live_notification",
        transport_state="connected",
        observed_at="2026-03-13T13:05:10Z",
    )
    observation = build_interactive_lifecycle_observation(
        route={
            "harness": "codex",
            "route_id": "rollout-interactive-fixture.jsonl",
        },
        previous_phase="boot_ready",
        next_phase="supervisor_ready",
        runtime_status=runtime_status,
        transition_at="2026-03-13T13:05:10Z",
    )

    return InteractiveRouteSecurityMilestoneBundle(
        backend_path=integration_snapshot.backend_path,
        interactive_href=integration_snapshot.interactive_href,
        transport=integration_snapshot.transport,
        thread_id=integration_snapshot.thread_id,
        security_headers=security_headers,
        ownership_status_code=intruder_response.status_code,
        prompt_disposition=str(prompt_verdict["disposition"]),
        control_disposition=str(control_verdict["disposition"]),
        observability_event=str(observation["event"]),
        observability_counter_keys=tuple(sorted(observation["counter_updates"].keys())),
    )
