"""
Utility classes for CachyOS Multi-Updater GUI
"""

from .update_runner import UpdateRunner
from .bash_wrapper import BashWrapper, UpdateCheckResult
from .version_checker import VersionChecker
from .password_manager import PasswordManager
from .debug_logger import DebugLogger, get_logger

# SyntaxHighlighter may not exist or have different name
try:
    from .syntax_highlighter import ConsoleSyntaxHighlighter as SyntaxHighlighter
except ImportError:
    SyntaxHighlighter = None

__all__ = [
    "UpdateRunner",
    "BashWrapper",
    "UpdateCheckResult",
    "VersionChecker",
    "PasswordManager",
    "DebugLogger",
    "get_logger",
    "SyntaxHighlighter",
]
