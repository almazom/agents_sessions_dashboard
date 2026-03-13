from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.deps import User, get_current_user
from backend.api.routes.sessions import router as sessions_router
from tests.interactive.fixtures import codex_fixture_path


class Task039SessionOwnershipEnforcementTests(unittest.TestCase):
    @staticmethod
    def _app(user: User) -> FastAPI:
        app = FastAPI()
        app.include_router(sessions_router)
        app.dependency_overrides[get_current_user] = lambda: user
        return app

    @staticmethod
    def _session_payload(
        *,
        owner_id: str | None,
        allowed_actor_ids: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "session_id": "sess-fixture-codex-001",
            "agent_type": "codex",
            "agent_name": "Codex",
            "cwd": "/home/pets/zoo/agents_sessions_dashboard",
            "status": "active",
            "resume_supported": True,
            "interactive_owner_id": owner_id,
            "interactive_allowed_actor_ids": allowed_actor_ids or [],
        }

    def test_green_allows_owner_to_open_interactive_route(self) -> None:
        app = self._app(
            User(username="admin", is_authenticated=True, auth_method="test")
        )

        with patch(
            "backend.api.routes.sessions._resolve_session_artifact_source",
            return_value=(self._session_payload(owner_id="admin"), codex_fixture_path()),
        ):
            with TestClient(app) as client:
                response = client.get(
                    "/api/session-artifacts/codex/rollout-interactive-fixture.jsonl/interactive"
                )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["interactive_session"]["available"])

    def test_green_allows_explicit_allowed_actor(self) -> None:
        app = self._app(
            User(username="operator", is_authenticated=True, auth_method="test")
        )

        with patch(
            "backend.api.routes.sessions._resolve_session_artifact_source",
            return_value=(
                self._session_payload(owner_id="admin", allowed_actor_ids=["operator"]),
                codex_fixture_path(),
            ),
        ):
            with TestClient(app) as client:
                response = client.get(
                    "/api/session-artifacts/codex/rollout-interactive-fixture.jsonl/interactive"
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["runtime_identity"]["thread_id"], "thread-fixture-codex-001")

    def test_red_rejects_intruder_actor(self) -> None:
        app = self._app(
            User(username="intruder", is_authenticated=True, auth_method="test")
        )

        with patch(
            "backend.api.routes.sessions._resolve_session_artifact_source",
            return_value=(self._session_payload(owner_id="admin"), codex_fixture_path()),
        ):
            with TestClient(app) as client:
                response = client.get(
                    "/api/session-artifacts/codex/rollout-interactive-fixture.jsonl/interactive"
                )

        self.assertEqual(response.status_code, 403)
        self.assertIn("owned by another actor", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
