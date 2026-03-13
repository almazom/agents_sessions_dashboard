"""Helpers for route-level interactive ownership enforcement."""

from __future__ import annotations

from typing import Any, Dict

from .deps import User


def resolve_interactive_actor_id(user: User) -> str:
    if isinstance(user.telegram_id, str) and user.telegram_id:
        return user.telegram_id
    if isinstance(user.username, str) and user.username:
        return user.username
    raise PermissionError("interactive route requires an authenticated actor identity")


def enforce_interactive_session_ownership(
    session: Dict[str, Any],
    *,
    actor_id: str,
) -> Dict[str, Any]:
    if not isinstance(actor_id, str) or not actor_id:
        raise PermissionError("interactive route requires a non-empty actor id")

    owner_id = session.get("interactive_owner_id") or session.get("owner_id")
    allowed_actor_ids = session.get("interactive_allowed_actor_ids") or []
    if allowed_actor_ids is None:
        allowed_actor_ids = []
    if not isinstance(allowed_actor_ids, list):
        raise ValueError("interactive route allowed actors must be a list")

    normalized_allowed_actor_ids = [
        actor
        for actor in allowed_actor_ids
        if isinstance(actor, str) and actor
    ]

    if not owner_id:
        return {
            "owner_id": None,
            "actor_id": actor_id,
            "access": "unrestricted",
            "allowed_actor_ids": normalized_allowed_actor_ids,
        }

    if not isinstance(owner_id, str) or not owner_id:
        raise ValueError("interactive route owner must be a non-empty string")

    if actor_id != owner_id and actor_id not in normalized_allowed_actor_ids:
        raise PermissionError("interactive route is owned by another actor")

    return {
        "owner_id": owner_id,
        "actor_id": actor_id,
        "access": "owner" if actor_id == owner_id else "allowed_actor",
        "allowed_actor_ids": normalized_allowed_actor_ids,
    }
