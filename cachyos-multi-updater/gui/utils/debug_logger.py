#!/usr/bin/env python3
"""
Debug Logger for CachyOS Multi-Updater GUI
Provides comprehensive logging and debugging capabilities
"""

import logging
import traceback
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Any, Callable


class DebugLogger:
    """Centralized debug logger for GUI"""

    _instance: Optional["DebugLogger"] = None
    _initialized = False
    _script_dir: Optional[Path] = None

    def __new__(cls) -> "DebugLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_script_dir(cls, script_dir: str) -> None:
        """Set the script directory for log file location"""
        cls._script_dir = Path(script_dir)

    def __init__(self) -> None:
        if self._initialized:
            return

        self.logger = logging.getLogger("CachyOSMultiUpdaterGUI")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create logs directory (ensure it exists before any logging)
        # Use script_dir/logs/gui/ if script_dir is set, otherwise fallback to ~/.cache
        if self._script_dir:
            self.log_dir = self._script_dir / "logs" / "gui"
        else:
            self.log_dir = Path.home() / ".cache" / "cachyos-multi-updater" / "gui-logs"
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # If we can't create the log directory, log to stderr
            # sys is already imported at the top of the file
            print(
                f"WARNING: Cannot create log directory {self.log_dir}: {e}",
                file=sys.stderr,
            )
            # Use a fallback location in /tmp
            self.log_dir = Path("/tmp") / "cachyos-multi-updater-gui-logs"
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e2:
                # Last resort: use current directory
                print(
                    f"WARNING: Cannot create fallback log directory {self.log_dir}: {e2}",
                    file=sys.stderr,
                )
                self.log_dir = Path.cwd() / "gui-logs"
                try:
                    self.log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e3:
                    # Final fallback: use /tmp directly
                    print(
                        f"WARNING: Cannot create final fallback log directory {self.log_dir}: {e3}",
                        file=sys.stderr,
                    )
                    self.log_dir = Path("/tmp")

        # Log file with timestamp
        try:
            log_file = (
                self.log_dir
                / f"gui-debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
            )

            # File handler
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            # If we can't create the log file, log to stderr and continue
            print(
                f"WARNING: Cannot create log file in {self.log_dir}: {e}",
                file=sys.stderr,
            )
            # Create a fallback log file in /tmp
            log_file = (
                Path("/tmp")
                / f"cachyos-multi-updater-gui-debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
            )
            try:
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception as e2:
                # Last resort: only console logging
                print(f"ERROR: Cannot create any log file: {e2}", file=sys.stderr)
                log_file = None

        # Console handler (only for errors and warnings)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter("[GUI DEBUG] %(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        self._initialized = True
        self.log_file = log_file

        # Best Practice: Cleanup old logs on initialization
        try:
            self.cleanup_old_logs(keep_last=5)
        except Exception:
            pass  # Don't fail if cleanup fails

        if log_file:
            try:
                self.logger.info("=" * 80)
                self.logger.info("GUI Debug Logger initialized")
                self.logger.info(f"Log file: {log_file}")
                self.logger.info("=" * 80)
            except Exception:
                # If logging fails, at least print to stderr
                print(
                    f"GUI Debug Logger initialized (log file: {log_file})",
                    file=sys.stderr,
                )
        else:
            print(
                "GUI Debug Logger initialized (no log file available)", file=sys.stderr
            )

    def debug(self, message: str, exc_info: bool = False) -> None:
        """Log debug message"""
        self.logger.debug(message, exc_info=exc_info)

    def info(self, message: str, exc_info: bool = False) -> None:
        """Log info message"""
        self.logger.info(message, exc_info=exc_info)

    def warning(self, message: str, exc_info: bool = False) -> None:
        """Log warning message"""
        self.logger.warning(message, exc_info=exc_info)

    def error(self, message: str, exc_info: bool = True) -> None:
        """Log error message with exception info"""
        self.logger.error(message, exc_info=exc_info)

    def exception(self, message: str) -> None:
        """Log exception with full traceback"""
        self.logger.exception(message)

    def log_function_call(
        self, func_name: str, args: Optional[Dict[str, Any]] = None, kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log function call with parameters"""
        params = []
        if args:
            params.append(f"args={args}")
        if kwargs:
            params.append(f"kwargs={kwargs}")
        param_str = ", ".join(params) if params else "no parameters"
        self.debug(f"Calling {func_name}({param_str})")

    def log_exception_details(self, exc: Exception, context: str = "") -> None:
        """Log detailed exception information"""
        exc_type = type(exc).__name__
        exc_message = str(exc)
        exc_traceback = traceback.format_exc()

        self.error(f"Exception in {context}: {exc_type}: {exc_message}")
        self.debug(f"Traceback:\n{exc_traceback}")

    def get_log_file(self) -> Path:
        """Get current log file path"""
        if not hasattr(self, "log_file") or self.log_file is None:
            # Fallback: return default log directory
            return self.log_dir / "gui-debug.log"
        return self.log_file

    def cleanup_old_logs(self, keep_last: int = 5) -> None:
        """Clean up old log files, keeping only the last N"""
        try:
            log_files = sorted(
                self.log_dir.glob("gui-debug-*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if len(log_files) > keep_last:
                for old_log in log_files[keep_last:]:
                    try:
                        old_log.unlink()
                        self.debug(f"Deleted old log file: {old_log}")
                    except Exception as e:
                        self.warning(f"Failed to delete old log file {old_log}: {e}")
        except Exception as e:
            self.warning(f"Failed to cleanup old logs: {e}")


def get_logger() -> DebugLogger:
    """Get singleton logger instance"""
    return DebugLogger()


def log_exception(func: Callable) -> Callable:
    """Decorator to automatically log exceptions"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger()
        func_name = f"{func.__module__}.{func.__qualname__}"
        logger.log_function_call(func_name, args=args, kwargs=kwargs)
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func_name} completed successfully")
            return result
        except Exception as e:
            logger.log_exception_details(e, context=func_name)
            raise

    return wrapper
