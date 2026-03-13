"""Resource limits and backpressure rules for interactive runtime actions."""

from __future__ import annotations

from typing import Any, Dict


CONTROL_ACTION_TYPES = {"cancel_interrupt", "waiting_response"}
PROMPT_ACTION_TYPE = "prompt_submit"
MAX_INFLIGHT_PROMPTS = 1
MAX_QUEUED_PROMPTS = 2
MAX_RECENT_PROMPTS = 4


def evaluate_interactive_backpressure(
    action: Dict[str, Any],
    *,
    inflight_prompts: int,
    queued_prompts: int,
    recent_prompt_count: int,
) -> Dict[str, Any]:
    action_type = _require_action_type(action)
    _require_non_negative(inflight_prompts, label="inflight_prompts")
    _require_non_negative(queued_prompts, label="queued_prompts")
    _require_non_negative(recent_prompt_count, label="recent_prompt_count")

    if action_type in CONTROL_ACTION_TYPES:
        return {
            "action_type": action_type,
            "queue_lane": "control",
            "disposition": "dispatch_now",
            "overloaded": False,
            "accepted_queue_depth": queued_prompts,
            "remaining_queue_slots": max(0, MAX_QUEUED_PROMPTS - queued_prompts),
        }

    if recent_prompt_count >= MAX_RECENT_PROMPTS:
        raise PermissionError("interactive runtime rate limit exceeded for prompt submit")

    if queued_prompts >= MAX_QUEUED_PROMPTS:
        raise OverflowError("interactive runtime queue is full")

    is_ready_now = inflight_prompts < MAX_INFLIGHT_PROMPTS and queued_prompts == 0
    next_queue_depth = queued_prompts if is_ready_now else queued_prompts + 1

    return {
        "action_type": action_type,
        "queue_lane": "prompt",
        "disposition": "dispatch_now" if is_ready_now else "enqueue",
        "overloaded": not is_ready_now,
        "accepted_queue_depth": next_queue_depth,
        "remaining_queue_slots": max(0, MAX_QUEUED_PROMPTS - next_queue_depth),
    }


def _require_action_type(action: Dict[str, Any]) -> str:
    if not isinstance(action, dict):
        raise ValueError("interactive backpressure requires action object")

    action_type = action.get("action_type")
    if action_type not in CONTROL_ACTION_TYPES | {PROMPT_ACTION_TYPE}:
        raise ValueError("interactive backpressure received unsupported action type")
    return str(action_type)


def _require_non_negative(value: int, *, label: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"interactive backpressure requires non-negative {label}")
    return value
