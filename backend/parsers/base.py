"""Base parser class and common data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"
    UNKNOWN = "unknown"


class AgentType(str, Enum):
    CODEX = "codex"
    KIMI = "kimi"
    GEMINI = "gemini"
    QWEN = "qwen"
    CLAUDE = "claude"
    PI = "pi"


@dataclass
class TimelineEvent:
    """Single event in session timeline."""
    timestamp: str
    event_type: str
    description: str
    icon: str = "📝"
    details: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SessionSummary:
    """Compressed session summary (~1KB target)."""
    session_id: str
    agent_type: AgentType
    agent_name: str
    cwd: str
    timestamp_start: str
    timestamp_end: Optional[str]
    status: SessionStatus
    user_intent: str  # Truncated first user message
    timeline: List[TimelineEvent] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    files_modified: List[str] = field(default_factory=list)
    git_branch: Optional[str] = None
    plan_steps: List[Dict[str, str]] = field(default_factory=list)
    source_file: str = ""
    error_message: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["agent_type"] = self.agent_type.value
        data["status"] = self.status.value
        data["timeline"] = [e.to_dict() if hasattr(e, 'to_dict') else e for e in self.timeline]
        return json.dumps(data, ensure_ascii=False, default=str)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["agent_type"] = self.agent_type.value
        data["status"] = self.status.value
        return data


class SessionParser(ABC):
    """Abstract base class for agent session parsers."""

    AGENT_TYPE: AgentType = None
    WATCH_PATHS: List[str] = []

    @abstractmethod
    def parse_file(self, file_path: Path) -> SessionSummary:
        """Parse a session file and return summary."""
        pass

    @abstractmethod
    def parse_line(self, line: str, context: Dict) -> Optional[Dict]:
        """Parse a single JSONL line. Returns event dict or None."""
        pass

    def extract_user_intent(self, text: str, max_length: int = 150) -> str:
        """Extract and truncate user intent from first message."""
        if not text:
            return ""
        # Clean up the text
        text = text.strip()
        # Remove newlines for display
        text = " ".join(text.split())
        # Truncate
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

    def detect_status(self, events: List[Dict]) -> SessionStatus:
        """Detect session status from events."""
        if not events:
            return SessionStatus.UNKNOWN

        last_event = events[-1]
        event_type = last_event.get("type", "")

        # Check for completion markers
        completion_types = ["task_complete", "task_completed", "session_end"]
        if event_type in completion_types:
            return SessionStatus.COMPLETED

        # Check for error markers
        if "error" in event_type.lower() or last_event.get("error"):
            return SessionStatus.ERROR

        # Default to active if recent events
        return SessionStatus.ACTIVE

    def build_timeline(self, events: List[Dict], max_events: int = 20) -> List[TimelineEvent]:
        """Build compressed timeline from events."""
        timeline = []
        seen_types = set()

        for event in events[-max_events:]:
            event_type = event.get("type", "unknown")

            # Skip duplicate consecutive events
            if event_type in seen_types and len(timeline) > 0:
                continue

            timeline.append(TimelineEvent(
                timestamp=event.get("timestamp", ""),
                event_type=event_type,
                description=event.get("description", event_type),
                icon=event.get("icon", "📝"),
                details=event.get("details")
            ))
            seen_types.add(event_type)

        return timeline

    def calculate_token_usage(self, events: List[Dict]) -> Dict[str, int]:
        """Aggregate token usage from events."""
        total = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

        for event in events:
            usage = event.get("token_usage", {})
            total["input_tokens"] += usage.get("input_tokens", 0)
            total["output_tokens"] += usage.get("output_tokens", 0)
            total["total_tokens"] += usage.get("total_tokens", 0)

        return total
