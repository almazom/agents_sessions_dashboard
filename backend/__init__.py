"""Agent Nexus Backend - Session monitoring and API."""

from .parsers import (
    SessionParser,
    SessionSummary,
    CodexParser,
    KimiParser,
    GeminiParser,
    QwenParser,
    ClaudeParser,
    PARSER_REGISTRY,
)

# Lazy import for watcher (optional dependency)
try:
    from .watcher import SessionWatcher, WatcherConfig
    _watcher_available = True
except ImportError:
    _watcher_available = False

from .summarizer import SessionSummarizer, mask_secrets_in_dict

__version__ = "0.1.0"

_watcher_available: bool = False

__all__ = [
    "SessionParser",
    "SessionSummary",
    "CodexParser",
    "KimiParser",
    "GeminiParser",
    "QwenParser",
    "ClaudeParser",
    "PARSER_REGISTRY",
    "SessionSummarizer",
    "mask_secrets_in_dict",
]

# Conditionally export watcher
if _watcher_available:
    __all__.extend(["SessionWatcher", "WatcherConfig"])
