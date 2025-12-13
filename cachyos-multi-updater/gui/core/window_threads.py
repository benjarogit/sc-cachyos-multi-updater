#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Main Window Threading
Thread and worker classes extracted from window.py
"""

from typing import TYPE_CHECKING, Optional, Any
from PyQt6.QtCore import QThread, pyqtSignal, QObject

if TYPE_CHECKING:
    from .window import MainWindow


class VersionCheckWorker(QObject):
    """Worker for checking version updates in background thread"""

    finished = pyqtSignal(str, str)  # latest_version, error

    def __init__(self, checker: Any, parent: Optional[QObject] = None) -> None:
        """Initialize version check worker

        Args:
            checker: VersionChecker instance
            parent: Parent QObject for proper memory management
        """
        super().__init__(parent)
        self.checker = checker

    def run(self) -> None:
        """Run version check in background thread"""
        latest, error = self.checker.check_latest_version()
        self.finished.emit(latest or "", error or "")


class VersionCheckThread(QThread):
    """Thread wrapper for VersionCheckWorker"""

    finished = pyqtSignal(str, str)  # latest_version, error

    def __init__(self, checker: Any, parent: Optional[QObject] = None) -> None:
        """Initialize version check thread

        Args:
            checker: VersionChecker instance
            parent: Parent QObject for proper memory management
        """
        super().__init__(parent)
        self.checker = checker
        self.worker: Optional[VersionCheckWorker] = None

    def run(self) -> None:
        """Run version check in background thread"""
        latest, error = self.checker.check_latest_version()
        self.finished.emit(latest or "", error or "")
