#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Main Window
Main GUI window for the updater
"""

from pathlib import Path
import re
import shutil
import time
import logging
from typing import Optional, Dict, Any, Callable
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QMessageBox,
    QDialog,
    QComboBox,
    QProgressDialog,
    QApplication,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, QThread, QSettings, QEvent
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor, QResizeEvent, QCloseEvent

# Import from new structure
from ..widgets import ClickableLabel
from ..ui import animate_dialog_show
from ..dialogs import ConfigDialog, SudoDialog
from ..utils import UpdateRunner, get_logger, DebugLogger
from .config_manager import ConfigManager
from .i18n import t
from .update_handler import UpdateHandler
from .window_ui import WindowUIMixin
from .window_handlers import WindowHandlersMixin
from .constants import (
    MAX_DOWNLOAD_RETRIES,
    DOWNLOAD_RETRY_DELAY_SECONDS,
    MAX_BACKUP_DIRS,
    BACKUP_RETENTION_SECONDS,
    EXECUTABLE_PERMISSIONS,
    EXECUTABLE_FILES,
    CRITICAL_INSTALLATION_FILES,
    SCRIPT_DIRECTORIES,
    NETWORK_CHECK_HOST,
    NETWORK_CHECK_PORT,
    NETWORK_CHECK_TIMEOUT,
    SPINNER_FRAME_COUNT,
    MAX_LOG_FILES_DEFAULT,
)


class MainWindow(WindowUIMixin, WindowHandlersMixin, QMainWindow):
    """Main application window"""

    def __init__(self, script_dir: str) -> None:
        super().__init__()
        self.script_dir: Path = Path(script_dir)

        # Set script directory for debug logger (so logs go to logs/gui/)
        # Initialize logger immediately to ensure GUI logs are always created
        # Initialize logger
        try:
            DebugLogger.set_script_dir(str(self.script_dir))
            # Force logger initialization by getting it
            self.logger: logging.Logger = get_logger()
            self.logger.info("GUI started")
            # Best Practice: Cleanup old update logs on startup
            self._cleanup_update_logs()
        except Exception:
            # Create dummy logger if real one fails
            class DummyLogger:
                def debug(self, *args: Any, **kwargs: Any) -> None:
                    pass

                def info(self, *args: Any, **kwargs: Any) -> None:
                    pass

                def warning(self, *args: Any, **kwargs: Any) -> None:
                    pass

                def error(self, *args: Any, **kwargs: Any) -> None:
                    pass

                def exception(self, *args: Any, **kwargs: Any) -> None:
                    pass

                def get_log_file(self) -> Optional[str]:
                    return None

            self.logger: Any = DummyLogger()

        self.config_manager: ConfigManager = ConfigManager(str(self.script_dir))
        self.config: Dict[str, str] = self.config_manager.load_config()
        self.update_runner: Optional[UpdateRunner] = None
        self._last_was_dry_run: bool = False  # Track if last operation was dry-run

        # Initialize update handler
        self.update_handler: UpdateHandler = UpdateHandler(self)

        # Migrate VERSION file from script dir to root if needed
        self._migrate_version_file()

        self.script_version: str = self.get_script_version()
        self.is_updating: bool = False
        self.spinner_frame: int = 0
        self.spinner_timer: Optional[QTimer] = None
        self.latest_github_version: Optional[str] = None
        self.version_checker: Optional[Any] = None
        self.version_thread: Optional[QThread] = None

        # Feedback effects for language/theme switching
        self.language_feedback_effect: Optional[QGraphicsOpacityEffect] = None
        self.language_feedback_timer: Optional[QTimer] = None
        self.language_feedback_restore_func: Optional[Callable] = None
        self.language_feedback_original_effect: Optional[QGraphicsOpacityEffect] = (
            None  # Store original effect before feedback
        )
        self.update_toast_shown: bool = (
            False  # Track if update toast was shown this session
        )

        self.setWindowTitle(t("app_name", "CachyOS Multi-Updater"))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        # KRITISCH: Vollständig skalierbar in alle Richtungen
        # Keine maximale Größe - Window kann frei skaliert werden

        self.init_ui()
        self._connect_signals()
        self.load_config()
        
        # KRITISCH: Fenstergröße laden und speichern
        self._load_window_geometry()

        # Check for updates in background
        self.check_version_async()

        # Start spinner timer
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.update_spinner)
        self.spinner_timer.start(100)  # Update every 100ms

    def _connect_signals(self) -> None:
        """Connect all signal-slot connections"""
        # Version label connections are handled in update_version_label()
        # Other connections are set up in init_ui() via _create_header() etc.
        
        # Connect component checkboxes to save config when toggled
        if hasattr(self, "check_system"):
            self.check_system.toggled.connect(
                lambda checked: self.config_manager.set("ENABLE_SYSTEM_UPDATE", str(checked).lower())
            )
        if hasattr(self, "check_aur"):
            self.check_aur.toggled.connect(
                lambda checked: self.config_manager.set("ENABLE_AUR_UPDATE", str(checked).lower())
            )
        if hasattr(self, "check_cursor"):
            self.check_cursor.toggled.connect(
                lambda checked: self.config_manager.set("ENABLE_CURSOR_UPDATE", str(checked).lower())
            )
        if hasattr(self, "check_adguard"):
            self.check_adguard.toggled.connect(
                lambda checked: self.config_manager.set("ENABLE_ADGUARD_UPDATE", str(checked).lower())
            )
        if hasattr(self, "check_flatpak"):
            self.check_flatpak.toggled.connect(
                lambda checked: self.config_manager.set("ENABLE_FLATPAK_UPDATE", str(checked).lower())
            )
        if hasattr(self, "check_proton_ge"):
            self.check_proton_ge.toggled.connect(
                lambda checked: self.config_manager.set("ENABLE_PROTON_GE_UPDATE", str(checked).lower())
            )

    def _migrate_version_file(self) -> None:
        """Migrate VERSION file from script_dir to root if needed"""
        version_file_old = self.script_dir / "VERSION"
        version_file_new = self.script_dir.parent / "VERSION"

        if version_file_old.exists() and not version_file_new.exists():
            try:
                shutil.copy2(version_file_old, version_file_new)
                self.logger.info(f"Migrated VERSION file from {version_file_old} to {version_file_new}")
            except Exception as e:
                self.logger.warning(f"Failed to migrate VERSION file: {e}")

    def _update_version_file_with_retry(self, version_file: Path, version: str) -> bool:
        """Update VERSION file with retry logic

        Args:
            version_file: Path to VERSION file
            version: Version string to write

        Returns:
            True if successful, False otherwise
        """
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                # Use atomic write: write to temp file, then rename
                temp_file = version_file.with_suffix(version_file.suffix + ".tmp")
                with open(temp_file, "w") as f:
                    f.write(version)
                temp_file.replace(version_file)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.error(f"Failed to update VERSION file after {max_retries} attempts: {e}")
                    return False

        return False

    def update_spinner(self) -> None:
        """Update spinner animation"""
        self.spinner_frame = (self.spinner_frame + 1) % SPINNER_FRAME_COUNT
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        if self.is_updating:
            wait_text = t("gui_please_wait_updating", "Please wait, updating system...")
        else:
            wait_text = t(
                "gui_please_wait_checking", "Please wait, checking for updates..."
            )
        if hasattr(self, "wait_label") and self.wait_label:
            self.wait_label.setText(f"{spinner_chars[self.spinner_frame]} {wait_text}")

    def _safe_disconnect_signal(self, signal, slot=None):
        """Safely disconnect a signal from a slot

        Best Practice: Helper method to prevent TypeError when disconnecting

        Args:
            signal: Qt signal object
            slot: Optional slot to disconnect. If None, disconnects all slots.
        """
        try:
            if slot is not None:
                signal.disconnect(slot)
            else:
                signal.disconnect()
        except TypeError:
            # No connections to disconnect
            pass

    def _safe_connect_signal(self, signal, slot, disconnect_first: bool = True):
        """Safely connect a signal to a slot, optionally disconnecting first

        Best Practice: Helper method to prevent duplicate connections

        Args:
            signal: Qt signal object
            slot: Slot function to connect
            disconnect_first: If True, disconnect existing connections first
        """
        if disconnect_first:
            self._safe_disconnect_signal(signal)
        signal.connect(slot)

    def _cleanup_update_logs(self, keep_last: int = MAX_LOG_FILES_DEFAULT):
        """Clean up old update log files

        Best Practice: Helper method to prevent log directory from growing too large

        Args:
            keep_last: Number of recent log files to keep (default: 10)
        """
        try:
            update_log_dir = self.script_dir / "logs" / "update"
            if not update_log_dir.exists():
                return

            log_files = sorted(
                update_log_dir.glob("update-*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            if len(log_files) > keep_last:
                deleted_count = 0
                for old_log in log_files[keep_last:]:
                    try:
                        old_log.unlink()
                        deleted_count += 1
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to delete old update log {old_log}: {e}"
                        )

                if deleted_count > 0:
                    self.logger.info(
                        f"Cleaned up {deleted_count} old update log files (kept {keep_last} most recent)"
                    )
        except Exception as e:
            self.logger.warning(f"Failed to cleanup update logs: {e}")

    def load_config(self) -> None:
        """Load config and update UI"""
        self.config = self.config_manager.load_config()

        # Load component checkbox states from config (default: all enabled)
        if hasattr(self, "check_system"):
            self.check_system.setChecked(
                self.config.get("ENABLE_SYSTEM_UPDATE", "true") == "true"
            )
        if hasattr(self, "check_aur"):
            self.check_aur.setChecked(
                self.config.get("ENABLE_AUR_UPDATE", "true") == "true"
            )
        if hasattr(self, "check_cursor"):
            self.check_cursor.setChecked(
                self.config.get("ENABLE_CURSOR_UPDATE", "true") == "true"
            )
        if hasattr(self, "check_adguard"):
            self.check_adguard.setChecked(
                self.config.get("ENABLE_ADGUARD_UPDATE", "true") == "true"
            )
        if hasattr(self, "check_flatpak"):
            self.check_flatpak.setChecked(
                self.config.get("ENABLE_FLATPAK_UPDATE", "true") == "true"
            )
        if hasattr(self, "check_proton_ge"):
            self.check_proton_ge.setChecked(
                self.config.get("ENABLE_PROTON_GE_UPDATE", "true") == "true"
            )

        # Update language icon and text
        if hasattr(self, "update_language_icon"):
            self.update_language_icon()

        # Update theme icon
        if hasattr(self, "theme_label"):
            self.update_theme_icon()

    def save_component_settings(self) -> None:
        """Save component checkbox states to config"""
        # Component settings are saved automatically when checkboxes are toggled
        # This method is kept for compatibility but does nothing
        pass

    def get_sudo_password(self) -> Optional[str]:
        """Get sudo password from user

        Returns:
            Sudo password or None if cancelled
        """
        from ..dialogs import SudoDialog

        dialog = SudoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_password()
        return None

    def get_script_version(self) -> str:
        """Get script version from VERSION file

        Returns:
            Version string (e.g., "2.3.0")
        """
        # Try root directory first (new location)
        version_file = self.script_dir.parent / "VERSION"
        if not version_file.exists():
            # Fallback to script_dir (old location)
            version_file = self.script_dir / "VERSION"

        if version_file.exists():
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
                    if version:
                        return version
            except Exception as e:
                self.logger.warning(f"Failed to read VERSION file: {e}")

        # Fallback: return default version
        return "2.3.0"

    def parse_update_output(self, text: str) -> None:
        """Parse update output and update info display

        Args:
            text: Output text from update script
        """
        self.update_handler.parse_update_output(text)

    def update_info_display(self) -> None:
        """Update the update info display panel
        
        Shows current versions and available updates for all components.
        Update-Info Panel: Summary of what's current and what can be updated.
        """
        if not hasattr(self, "update_info_text"):
            return

        lines = []
        info_data = self.update_info_data

        # System updates - kompakte eine Zeile pro Komponente
        if info_data["status"]["system"]["found"] > 0:
            package_names = info_data["status"]["system"].get("packages", [])
            if package_names:
                # Show first 3-4 packages, then "... und X weitere"
                shown_count = min(3, len(package_names))
                shown_packages = package_names[:shown_count]
                package_list = ", ".join(shown_packages)
                if len(package_names) > shown_count:
                    package_list += f", ... und {len(package_names) - shown_count} weitere"
                lines.append(
                    f"📦 System: {info_data['status']['system']['found']} Update{'s' if info_data['status']['system']['found'] > 1 else ''} ({package_list})"
                )
            else:
                lines.append(
                    f"📦 System: {info_data['status']['system']['found']} Update{'s' if info_data['status']['system']['found'] > 1 else ''} verfügbar"
                )
        elif info_data["status"]["system"]["current"]:
            lines.append("📦 System: aktuell")
        else:
            lines.append("📦 System: Prüfe...")

        # AUR updates - kompakte eine Zeile pro Komponente
        if info_data["status"]["aur"]["found"] > 0:
            package_names = info_data["status"]["aur"].get("packages", [])
            if package_names:
                # Show first 3-4 packages, then "... und X weitere"
                shown_count = min(3, len(package_names))
                shown_packages = package_names[:shown_count]
                package_list = ", ".join(shown_packages)
                if len(package_names) > shown_count:
                    package_list += f", ... und {len(package_names) - shown_count} weitere"
                lines.append(
                    f"🔧 AUR: {info_data['status']['aur']['found']} Update{'s' if info_data['status']['aur']['found'] > 1 else ''} ({package_list})"
                )
            else:
                lines.append(
                    f"🔧 AUR: {info_data['status']['aur']['found']} Update{'s' if info_data['status']['aur']['found'] > 1 else ''} verfügbar"
                )
        elif info_data["status"]["aur"]["current"]:
            lines.append("🔧 AUR: aktuell")
        else:
            lines.append("🔧 AUR: Prüfe...")

        # Cursor updates - kompakte eine Zeile
        cursor_version = info_data["status"]["cursor"].get("current_version", "")
        if info_data["status"]["cursor"]["update_available"]:
            available_version = info_data["status"]["cursor"].get("available_version", "")
            if available_version:
                lines.append(
                    f"🖱️ Cursor: {cursor_version} → {available_version} verfügbar"
                )
            else:
                lines.append(
                    f"🖱️ Cursor: {cursor_version} → Update verfügbar"
                )
        elif cursor_version:
            lines.append(f"🖱️ Cursor: aktuell ({cursor_version})")
        else:
            lines.append("🖱️ Cursor: Prüfe...")

        # AdGuard updates - kompakte eine Zeile
        adguard_version = info_data["status"]["adguard"].get("current_version", "")
        if info_data["status"]["adguard"]["update_available"]:
            available_version = info_data["status"]["adguard"].get("available_version", "")
            if available_version:
                lines.append(
                    f"🛡️ AdGuard: {adguard_version} → {available_version} verfügbar"
                )
            else:
                lines.append(
                    f"🛡️ AdGuard: {adguard_version} → Update verfügbar"
                )
        elif adguard_version:
            lines.append(f"🛡️ AdGuard: aktuell ({adguard_version})")
        else:
            lines.append("🛡️ AdGuard: Prüfe...")

        # Flatpak updates - kompakte eine Zeile pro Komponente
        if info_data["status"]["flatpak"]["found"] > 0:
            package_names = info_data["status"]["flatpak"].get("packages", [])
            if package_names:
                # Show first 3-4 packages, then "... und X weitere"
                shown_count = min(3, len(package_names))
                shown_packages = package_names[:shown_count]
                package_list = ", ".join(shown_packages)
                if len(package_names) > shown_count:
                    package_list += f", ... und {len(package_names) - shown_count} weitere"
                lines.append(
                    f"📱 Flatpak: {info_data['status']['flatpak']['found']} Update{'s' if info_data['status']['flatpak']['found'] > 1 else ''} ({package_list})"
                )
            else:
                lines.append(
                    f"📱 Flatpak: {info_data['status']['flatpak']['found']} Update{'s' if info_data['status']['flatpak']['found'] > 1 else ''} verfügbar"
                )
        elif info_data["status"]["flatpak"]["current"]:
            lines.append("📱 Flatpak: aktuell")
        else:
            lines.append("📱 Flatpak: Prüfe...")

        # Proton-GE updates - kompakte eine Zeile
        proton_ge_current = info_data["status"]["proton_ge"].get("current_version", "")
        proton_ge_available = info_data["status"]["proton_ge"].get("available_version", "")
        if info_data["status"]["proton_ge"]["update_available"]:
            lines.append(
                f"🎮 Proton-GE: {proton_ge_current} → {proton_ge_available} verfügbar"
            )
        elif proton_ge_current:
            lines.append(f"🎮 Proton-GE: aktuell ({proton_ge_current})")
        else:
            lines.append("🎮 Proton-GE: Prüfe...")

        # Summary - show total count or "alle aktuell"
        total_updates = sum([
            info_data["status"]["system"]["found"],
            info_data["status"]["aur"]["found"],
            info_data["status"]["flatpak"]["found"],
            1 if info_data["status"]["cursor"]["update_available"] else 0,
            1 if info_data["status"]["adguard"]["update_available"] else 0,
            1 if info_data["status"]["proton_ge"]["update_available"] else 0,
        ])
        
        lines.append("")  # Empty line before summary
        if total_updates > 0:
            lines.append(
                f"✓ {total_updates} Update{'s' if total_updates > 1 else ''} verfügbar"
            )
        else:
            # Check if all components are checked and current
            all_checked = (
                info_data["status"]["system"]["current"]
                and info_data["status"]["aur"]["current"]
                and info_data["status"]["flatpak"]["current"]
                and not info_data["status"]["cursor"]["update_available"]
                and not info_data["status"]["adguard"]["update_available"]
                and not info_data["status"]["proton_ge"]["update_available"]
            )
            if all_checked:
                lines.append("○ Alle Komponenten aktuell")

        # Build tooltip with all package names for hover
        tooltip_lines = []
        if info_data["status"]["system"]["found"] > 0:
            system_packages = info_data["status"]["system"].get("packages", [])
            if system_packages:
                tooltip_lines.append(f"System: {', '.join(system_packages)}")
        if info_data["status"]["aur"]["found"] > 0:
            aur_packages = info_data["status"]["aur"].get("packages", [])
            if aur_packages:
                tooltip_lines.append(f"AUR: {', '.join(aur_packages)}")
        if info_data["status"]["flatpak"]["found"] > 0:
            flatpak_packages = info_data["status"]["flatpak"].get("packages", [])
            if flatpak_packages:
                tooltip_lines.append(f"Flatpak: {', '.join(flatpak_packages)}")
        
        tooltip_text = "\n".join(tooltip_lines) if tooltip_lines else ""
        self.update_info_text.setToolTip(tooltip_text)
        
        # Save scroll position before updating text
        scrollbar = self.update_info_text.verticalScrollBar()
        saved_scroll_value = scrollbar.value()
        was_at_bottom = (
            saved_scroll_value >= scrollbar.maximum() - 10
        )  # Within 10px of bottom

        # Update text
        self.update_info_text.setPlainText("\n".join(lines))

        # Restore scroll position: only auto-scroll to bottom if user was already at bottom
        if was_at_bottom:
            cursor = self.update_info_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.update_info_text.setTextCursor(cursor)
            self.update_info_text.ensureCursorVisible()
        else:
            # Restore previous scroll position (after text update, max might have changed)
            QApplication.processEvents()  # Ensure text is rendered
            scrollbar.setValue(min(saved_scroll_value, scrollbar.maximum()))
    
    def _load_window_geometry(self) -> None:
        """Load and restore window geometry from QSettings"""
        settings = QSettings("CachyOS", "Multi-Updater")
        geometry = settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size if no saved geometry
            self.resize(1000, 700)
    
    def _save_window_geometry(self) -> None:
        """Save window geometry to QSettings"""
        settings = QSettings("CachyOS", "Multi-Updater")
        settings.setValue("window_geometry", self.saveGeometry())
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - save geometry"""
        self._save_window_geometry()
        super().closeEvent(event)
