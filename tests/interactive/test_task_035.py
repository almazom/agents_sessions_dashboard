from __future__ import annotations

import unittest
from pathlib import Path

from tests.interactive.interactive_page_shell import (
    InteractivePageShellNotFound,
    build_interactive_page_shell_snapshot,
)


class Task035InteractivePageShellTests(unittest.TestCase):
    def test_green_builds_interactive_page_shell_with_loading_state(self) -> None:
        snapshot = build_interactive_page_shell_snapshot()

        self.assertEqual(
            snapshot.page_path,
            Path(
                "/home/pets/zoo/agents_sessions_dashboard/frontend/app/sessions/[harness]/[id]/interactive/page.tsx"
            ),
        )
        self.assertEqual(
            snapshot.loading_path,
            Path(
                "/home/pets/zoo/agents_sessions_dashboard/frontend/app/sessions/[harness]/[id]/interactive/loading.tsx"
            ),
        )
        self.assertEqual(snapshot.route_suffix, "/interactive")
        self.assertEqual(snapshot.loading_copy, "Preparing interactive session")
        self.assertEqual(
            snapshot.section_headings,
            [
                "Route state",
                "Tail snapshot",
                "Replay stream",
                "Composer state",
            ],
        )
        self.assertTrue(snapshot.uses_boot_loader)

    def test_red_missing_shell_component_fails_honestly(self) -> None:
        missing_component = Path("/tmp/interactive-task-check/missing-InteractiveSessionShell.tsx")
        with self.assertRaises(InteractivePageShellNotFound):
            build_interactive_page_shell_snapshot(component_path=missing_component)


if __name__ == "__main__":
    unittest.main()
