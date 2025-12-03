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
from typing import Optional


class DebugLogger:
    """Centralized debug logger for GUI"""
    
    _instance: Optional['DebugLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger('CachyOSMultiUpdaterGUI')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create logs directory
        self.log_dir = Path.home() / ".cache" / "cachyos-multi-updater" / "gui-logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log file with timestamp
        log_file = self.log_dir / f"gui-debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (only for errors and warnings)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter('[GUI DEBUG] %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        self._initialized = True
        self.log_file = log_file
        self.logger.info("=" * 80)
        self.logger.info("GUI Debug Logger initialized")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info("=" * 80)
    
    def debug(self, message: str, exc_info=False):
        """Log debug message"""
        self.logger.debug(message, exc_info=exc_info)
    
    def info(self, message: str, exc_info=False):
        """Log info message"""
        self.logger.info(message, exc_info=exc_info)
    
    def warning(self, message: str, exc_info=False):
        """Log warning message"""
        self.logger.warning(message, exc_info=exc_info)
    
    def error(self, message: str, exc_info=True):
        """Log error message with exception info"""
        self.logger.error(message, exc_info=exc_info)
    
    def exception(self, message: str):
        """Log exception with full traceback"""
        self.logger.exception(message)
    
    def log_function_call(self, func_name: str, args: dict = None, kwargs: dict = None):
        """Log function call with parameters"""
        params = []
        if args:
            params.append(f"args={args}")
        if kwargs:
            params.append(f"kwargs={kwargs}")
        param_str = ", ".join(params) if params else "no parameters"
        self.debug(f"Calling {func_name}({param_str})")
    
    def log_exception_details(self, exc: Exception, context: str = ""):
        """Log detailed exception information"""
        exc_type = type(exc).__name__
        exc_message = str(exc)
        exc_traceback = traceback.format_exc()
        
        self.error(f"Exception in {context}: {exc_type}: {exc_message}")
        self.debug(f"Traceback:\n{exc_traceback}")
    
    def get_log_file(self) -> Path:
        """Get current log file path"""
        if not hasattr(self, 'log_file') or self.log_file is None:
            # Fallback: return default log directory
            return self.log_dir / "gui-debug.log"
        return self.log_file
    
    def cleanup_old_logs(self, keep_last: int = 5):
        """Clean up old log files, keeping only the last N"""
        try:
            log_files = sorted(self.log_dir.glob("gui-debug-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
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


def log_exception(func):
    """Decorator to automatically log exceptions"""
    def wrapper(*args, **kwargs):
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

