from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
START_PUBLISHED_SCRIPT = REPO_ROOT / "scripts" / "start_published.sh"
FRONTEND_DIR = REPO_ROOT / "frontend"
PLAYWRIGHT_COMMAND = [
    "npx",
    "playwright",
    "test",
    "e2e/interactive-session.spec.ts",
]
DEFAULT_TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class InteractiveBrowserE2EResult:
    base_url: str
    returncode: int
    stdout: str
    stderr: str


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )


def ensure_published_stack() -> None:
    env = os.environ.copy()
    env["NEXUS_PLAYWRIGHT_CHECK_ENABLED"] = "0"
    completed = _run_command(
        [str(START_PUBLISHED_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"failed to start published stack: {detail}")


def run_interactive_browser_e2e(
    *,
    base_url: str,
    ensure_stack: bool = True,
) -> InteractiveBrowserE2EResult:
    if ensure_stack:
        ensure_published_stack()

    env = os.environ.copy()
    env["NEXUS_PUBLIC_URL"] = base_url
    completed = _run_command(
        PLAYWRIGHT_COMMAND,
        cwd=FRONTEND_DIR,
        env=env,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )

    return InteractiveBrowserE2EResult(
        base_url=base_url,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
