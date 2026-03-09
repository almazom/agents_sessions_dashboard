"""Unified parser system for AI agent session logs.

Supports: Codex, Kimi, Gemini, Qwen, Claude, Pi
"""

from .base import SessionParser, SessionSummary
from .codex_parser import CodexParser
from .kimi_parser import KimiParser
from .gemini_parser import GeminiParser
from .qwen_parser import QwenParser
from .claude_parser import ClaudeParser
from .pi_parser import PiParser

__all__ = [
    "SessionParser",
    "SessionSummary",
    "CodexParser",
    "KimiParser",
    "GeminiParser",
    "QwenParser",
    "ClaudeParser",
    "PiParser",
]

# Registry of all parsers
PARSER_REGISTRY = {
    "codex": CodexParser,
    "kimi": KimiParser,
    "gemini": GeminiParser,
    "qwen": QwenParser,
    "claude": ClaudeParser,
    "pi": PiParser,
}
