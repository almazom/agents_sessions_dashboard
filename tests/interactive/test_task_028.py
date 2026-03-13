from __future__ import annotations

import unittest

from backend.api.interactive_events import build_tool_fallback_event


class Task028ToolFallbackRenderingEventTests(unittest.TestCase):
    def test_green_builds_fallback_rendering_for_unknown_tool_shape(self) -> None:
        event = build_tool_fallback_event(
            {
                "event_id": "tool-1",
                "kind": "tool_call",
                "status": "completed",
                "summary": "weird_tool",
                "payload": {
                    "server": "custom",
                    "tool": "weird_tool",
                    "arguments": {"path": "/tmp/demo"},
                    "result": None,
                    "error": None,
                },
                "source_event_type": "item.completed",
            }
        )

        self.assertEqual(event["kind"], "tool_fallback")
        self.assertEqual(event["status"], "completed")
        self.assertEqual(event["summary"], "Tool call: weird_tool")
        self.assertEqual(event["payload"]["display_mode"], "fallback")
        self.assertIn("server", event["payload"]["details"])

    def test_red_rejects_non_tool_event_for_fallback_rendering(self) -> None:
        with self.assertRaises(ValueError):
            build_tool_fallback_event(
                {
                    "event_id": "msg-1",
                    "kind": "agent_message",
                    "status": "completed",
                    "summary": "hello",
                    "payload": {"text": "hello"},
                    "source_event_type": "item.completed",
                }
            )


if __name__ == "__main__":
    unittest.main()
