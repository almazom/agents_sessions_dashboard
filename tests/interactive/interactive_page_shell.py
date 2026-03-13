from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERACTIVE_PAGE_PATH = REPO_ROOT / "frontend" / "app" / "sessions" / "[harness]" / "[id]" / "interactive" / "page.tsx"
INTERACTIVE_LOADING_PATH = REPO_ROOT / "frontend" / "app" / "sessions" / "[harness]" / "[id]" / "interactive" / "loading.tsx"
INTERACTIVE_COMPONENT_PATH = REPO_ROOT / "frontend" / "components" / "InteractiveSessionShell.tsx"
FRONTEND_API_PATH = REPO_ROOT / "frontend" / "lib" / "api.ts"

REQUIRED_SECTION_HEADINGS = [
    "Route state",
    "Tail snapshot",
    "Replay stream",
    "Composer state",
]


class InteractivePageShellNotFound(FileNotFoundError):
    """Raised when the interactive page shell files are missing or incomplete."""


@dataclass(frozen=True)
class InteractivePageShellSnapshot:
    page_path: Path
    loading_path: Path
    component_path: Path
    api_path: Path
    route_suffix: str
    loading_copy: str
    section_headings: list[str]
    uses_boot_loader: bool


def _read_required_file(path: Path, *, label: str) -> str:
    if not path.exists():
        raise InteractivePageShellNotFound(f"{label} is missing: {path}")
    return path.read_text(encoding="utf-8")


def build_interactive_page_shell_snapshot(
    *,
    page_path: Path | None = None,
    loading_path: Path | None = None,
    component_path: Path | None = None,
    api_path: Path | None = None,
) -> InteractivePageShellSnapshot:
    resolved_page_path = (page_path or INTERACTIVE_PAGE_PATH).resolve()
    resolved_loading_path = (loading_path or INTERACTIVE_LOADING_PATH).resolve()
    resolved_component_path = (component_path or INTERACTIVE_COMPONENT_PATH).resolve()
    resolved_api_path = (api_path or FRONTEND_API_PATH).resolve()

    page_source = _read_required_file(resolved_page_path, label="interactive route page")
    loading_source = _read_required_file(resolved_loading_path, label="interactive route loading state")
    component_source = _read_required_file(resolved_component_path, label="interactive route shell component")
    api_source = _read_required_file(resolved_api_path, label="frontend api client")

    if "InteractiveSessionShell" not in page_source:
        raise InteractivePageShellNotFound(
            f"interactive route page does not mount the shell component: {resolved_page_path}"
        )
    if "Preparing interactive session" not in loading_source:
        raise InteractivePageShellNotFound(
            f"interactive route loading state is missing honest copy: {resolved_loading_path}"
        )
    if "api.getSessionArtifactInteractiveBoot" not in component_source:
        raise InteractivePageShellNotFound(
            f"interactive shell does not load the backend boot payload: {resolved_component_path}"
        )
    if "getSessionArtifactInteractiveBoot" not in api_source:
        raise InteractivePageShellNotFound(
            f"frontend api client is missing the interactive boot loader method: {resolved_api_path}"
        )

    section_headings = [
        heading for heading in REQUIRED_SECTION_HEADINGS if heading in component_source
    ]
    if section_headings != REQUIRED_SECTION_HEADINGS:
        raise InteractivePageShellNotFound(
            f"interactive shell is missing required sections: {resolved_component_path}"
        )

    return InteractivePageShellSnapshot(
        page_path=resolved_page_path,
        loading_path=resolved_loading_path,
        component_path=resolved_component_path,
        api_path=resolved_api_path,
        route_suffix="/interactive",
        loading_copy="Preparing interactive session",
        section_headings=section_headings,
        uses_boot_loader=True,
    )
