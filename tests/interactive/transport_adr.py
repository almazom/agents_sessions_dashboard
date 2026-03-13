from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_ADR_PATH = REPO_ROOT / "docs" / "adr" / "interactive-transport-v1.md"


class InteractiveTransportAdrNotFound(FileNotFoundError):
    """Raised when the interactive transport ADR file is missing or incomplete."""


@dataclass(frozen=True)
class InteractiveTransportAdr:
    path: Path
    primary_browser_transport: str
    fallback_policy: str
    sdk_role: str
    non_goals: list[str]
    interactive_route: str


def _extract_single_value(text: str, key: str) -> str:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise InteractiveTransportAdrNotFound(f"interactive transport ADR key is missing: {key}")


def _extract_list_value(text: str, key: str) -> list[str]:
    raw_value = _extract_single_value(text, key)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def load_transport_adr(adr_path: Path | None = None) -> InteractiveTransportAdr:
    resolved_path = (adr_path or TRANSPORT_ADR_PATH).resolve()
    if not resolved_path.exists():
        raise InteractiveTransportAdrNotFound(
            f"interactive transport ADR is missing: {resolved_path}"
        )

    text = resolved_path.read_text(encoding="utf-8")
    return InteractiveTransportAdr(
        path=resolved_path,
        primary_browser_transport=_extract_single_value(text, "primary_browser_transport"),
        fallback_policy=_extract_single_value(text, "fallback_policy"),
        sdk_role=_extract_single_value(text, "sdk_role"),
        non_goals=_extract_list_value(text, "non_goals"),
        interactive_route=_extract_single_value(text, "interactive_route"),
    )
