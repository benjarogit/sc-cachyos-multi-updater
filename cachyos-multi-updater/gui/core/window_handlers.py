#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Main Window Event Handlers
Event handler methods extracted from window.py
"""

from typing import TYPE_CHECKING, Optional, Dict, Any
from pathlib import Path
import re
import subprocess
import webbrowser
import os
import shutil
import time
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QComboBox, QProgressDialog, QApplication,
    QGraphicsOpacityEffect, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor, QFontDatabase

from ..widgets import get_fa_icon, apply_fa_font, FA_ICONS, ClickableLabel
from ..ui import animate_dialog_show
from ..dialogs import ConfigDialog, SudoDialog, UpdateDialog, UpdateConfirmationDialog
from ..utils import UpdateRunner, get_logger, VersionChecker
from .i18n import t

if TYPE_CHECKING:
    from .window import MainWindow


class WindowHandlersMixin:
    """Mixin class for event handler methods"""

    def on_output_received(self: "MainWindow", text: str) -> None:
        """Handle output from update script
        
        GUI-KONSOLE: stdout + stderr direkt und ungefiltert anzeigen
        - KEINE Verarbeitung
        - KEINE Interpretation
        - KEINE Kürzung
        - KEINE Zeilenumbrüche hinzufügen (append() fügt automatisch \n hinzu!)
        - Einfach Text 1:1 einfügen, wie im Terminal
        """
        # KRITISCH: append() fügt automatisch \n hinzu - das wollen wir NICHT!
        # insertPlainText() fügt Text 1:1 ein, ohne Zeilenumbrüche
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)  # 1:1 Einfügen, keine Modifikation
        self.output_text.setTextCursor(cursor)
        
        # Auto-scroll to bottom (but user can scroll up to read old output)
        self.output_text.ensureCursorVisible()

    def on_progress_update(self: "MainWindow", percent: int, message: str) -> None:
        """Handle progress update"""
        self.progress_bar.setValue(percent)
        # Extract step info from message if available (e.g., "[5/5]")
        step_match = re.search(r"\[(\d+)/(\d+)\]", message)
        if step_match:
            current_step = step_match.group(1)
            total_steps = step_match.group(2)
            self.status_label.setText(f"{percent}% [{current_step}/{total_steps}]")
        else:
            self.status_label.setText(f"{percent}%")

    def on_error(self: "MainWindow", error_msg: str) -> None:
        """Handle error"""
        QMessageBox.critical(self, t("gui_error", "Error"), error_msg)
        self.on_update_finished(1)

    def show_settings(self: "MainWindow") -> None:
        """Show settings dialog"""
        dialog = ConfigDialog(str(self.script_dir), self)
        # Animate dialog appearance
        if animate_dialog_show is not None:
            animate_dialog_show(dialog)
        if dialog.exec():
            self.load_config()
            # Apply theme if changed
            theme_mode = self.config_manager.get("GUI_THEME", "auto")
            from ..ui import ThemeManager

            ThemeManager.apply_theme(theme_mode)

    def view_logs(self: "MainWindow"):
        """View log files with separate dropdowns for update and GUI logs"""
        logs_base_dir = Path(self.script_dir) / "logs"
        update_log_dir = logs_base_dir / "update"
        gui_log_dir = logs_base_dir / "gui"

        # Check if log directories exist
        if not logs_base_dir.exists():
            QMessageBox.information(
                self,
                t("gui_no_logs", "No Logs"),
                t("gui_log_directory_not_found", "Log directory does not exist."),
            )
            return

        # Get update log files
        update_log_files = []
        if update_log_dir.exists():
            update_log_files = sorted(
                update_log_dir.glob("*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

        # Get GUI log files
        gui_log_files = []
        if gui_log_dir.exists():
            gui_log_files = sorted(
                gui_log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True
            )

        # Check if any logs exist
        if not update_log_files and not gui_log_files:
            QMessageBox.information(
                self,
                t("gui_no_logs", "No Logs"),
                t("gui_no_logs", "No log files found."),
            )
            return

        # Show log viewer dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(t("gui_log_viewer", "Log Viewer"))
        dialog.setMinimumWidth(900)
        dialog.setMinimumHeight(700)

        layout = QVBoxLayout()

        # Log type selector (Update Logs / GUI Logs)
        type_layout = QHBoxLayout()
        type_label = QLabel(t("gui_log_type", "Log Type:"))
        type_combo = QComboBox()
        type_combo.addItem(t("gui_update_logs", "Update Logs"), "update")
        type_combo.addItem(t("gui_gui_logs", "GUI Logs"), "gui")
        type_layout.addWidget(type_label)
        type_layout.addWidget(type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # File selector
        file_layout = QHBoxLayout()
        file_label = QLabel(t("gui_log_file", "Log File:"))
        file_combo = QComboBox()
        file_layout.addWidget(file_label)
        file_layout.addWidget(file_combo)
        file_layout.addStretch()
        layout.addLayout(file_layout)

        # Log text
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setFont(QFont("Monospace", 9))
        layout.addWidget(log_text)

        def update_file_combo(log_type):
            """Update file combo box based on selected log type"""
            file_combo.clear()
            if log_type == "update":
                files = update_log_files
            else:
                files = gui_log_files

            if files:
                file_combo.addItems([f.name for f in files])
                load_log(0)
            else:
                log_text.setPlainText(
                    t("gui_no_logs_found", "No log files found for this type.")
                )

        # Info label für Log-Details (Name, Datum, Pfad)
        from datetime import datetime
        info_label = QLabel()
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 8px; background-color: rgba(128, 128, 128, 0.1); border-radius: 4px;")
        layout.insertWidget(2, info_label)  # Nach file_layout einfügen
        
        def load_log(index):
            """Load selected log file"""
            log_type = type_combo.currentData()
            if log_type == "update":
                files = update_log_files
            else:
                files = gui_log_files

            if not files or index < 0 or index >= len(files):
                log_text.setPlainText(
                    t("gui_no_logs_found", "No log files found for this type.")
                )
                info_label.setText("")
                return

            log_path = files[index]
            log_text.clear()
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    log_text.setPlainText(f.read())
                # Auto-scroll to bottom
                cursor = log_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                log_text.setTextCursor(cursor)
                
                # Update info label mit Log-Details
                from datetime import datetime
                stat_info = log_path.stat()
                mtime = datetime.fromtimestamp(stat_info.st_mtime)
                # Mehrsprachiges Datum/Zeit-Format
                current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
                if current_lang == "auto":
                    lang = os.environ.get("LANG", "en_US.UTF-8")
                    lang = lang.split("_")[0].split(".")[0].lower()
                    current_lang = "de" if lang == "de" else "en"
                
                if current_lang == "de":
                    date_str = mtime.strftime("%d.%m.%Y %H:%M:%S")
                    info_text = f"<b>{t('gui_log_name', 'Log-Name')}:</b> {log_path.name}<br>"
                    info_text += f"<b>{t('gui_log_date', 'Datum/Zeit')}:</b> {date_str}<br>"
                    info_text += f"<b>{t('gui_log_path', 'Pfad')}:</b> {log_path}"
                else:
                    date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
                    info_text = f"<b>{t('gui_log_name', 'Log Name')}:</b> {log_path.name}<br>"
                    info_text += f"<b>{t('gui_log_date', 'Date/Time')}:</b> {date_str}<br>"
                    info_text += f"<b>{t('gui_log_path', 'Path')}:</b> {log_path}"
                info_label.setText(info_text)
            except Exception as e:
                log_text.setPlainText(f"Error reading log: {e}")
                info_label.setText("")

        # Connect signals
        type_combo.currentIndexChanged.connect(
            lambda: update_file_combo(type_combo.currentData())
        )
        file_combo.currentIndexChanged.connect(load_log)

        # Initialize with update logs
        update_file_combo("update")

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Copy log button
        def copy_log():
            """Copy current log content to clipboard"""
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(log_text.toPlainText())
            QMessageBox.information(
                dialog,
                t("gui_info", "Info"),
                t("gui_log_copied", "Log content copied to clipboard"),
            )
        
        copy_btn = self._create_fa_button(
            "save",
            t("gui_copy_log", "Copy Log"),
            copy_log,
        )
        button_layout.addWidget(copy_btn)
        
        # Copy log path button
        def copy_log_path():
            """Copy current log path to clipboard"""
            from PyQt6.QtWidgets import QApplication
            log_type = type_combo.currentData()
            if log_type == "update":
                files = update_log_files
            else:
                files = gui_log_files
            if files and file_combo.currentIndex() >= 0:
                log_path = files[file_combo.currentIndex()]
                QApplication.clipboard().setText(str(log_path))
                QMessageBox.information(
                    dialog,
                    t("gui_info", "Info"),
                    t("gui_log_path_copied", "Log path copied to clipboard"),
                )
        
        copy_path_btn = self._create_fa_button(
            "file-text",
            t("gui_copy_path", "Copy Path"),
            copy_log_path,
        )
        button_layout.addWidget(copy_path_btn)

        # Open log directory button
        def open_log_directory():
            # Try different methods to open directory, suppressing Qt warnings
            try:
                env = os.environ.copy()
                env["QT_LOGGING_RULES"] = "qt.qpa.services.debug=false"
                subprocess.Popen(
                    ["xdg-open", str(logs_base_dir)],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except Exception:
                # Fallback: Show directory path in message box
                QMessageBox.information(
                    self,
                    t("gui_info", "Info"),
                    t("gui_log_directory", "Log Directory:") + f"\n{logs_base_dir}",
                )

        open_dir_btn = self._create_fa_button(
            "folder-open",
            t("gui_open_log_directory", "Open Log Directory"),
            open_log_directory,
        )
        button_layout.addWidget(open_dir_btn)

        # Close button
        close_btn = self._create_fa_button(
            "times", t("gui_close", "Close"), dialog.accept
        )
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def open_github(self: "MainWindow"):
        """Open GitHub repository in browser"""
        github_repo = self.config.get(
            "GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"
        )
        github_url = f"https://github.com/{github_repo}"

        # Try to open URL using xdg-open
        try:
            env = os.environ.copy()
            env.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            subprocess.Popen(
                ["xdg-open", github_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
        except (FileNotFoundError, OSError):
            os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            webbrowser.open(github_url)

    def open_github_releases(self: "MainWindow"):
        """Open GitHub releases page"""
        github_repo = self.config.get(
            "GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"
        )
        github_url = f"https://github.com/{github_repo}/releases"

        # Try to open URL using xdg-open
        try:
            env = os.environ.copy()
            env.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            subprocess.Popen(
                ["xdg-open", github_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True,
            )
        except (OSError, FileNotFoundError):
            os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            webbrowser.open(github_url)

    def switch_theme(self: "MainWindow"):
        """Switch theme cyclically: auto -> light -> dark -> auto"""
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        theme_cycle = {"auto": "light", "light": "dark", "dark": "auto"}
        new_theme = theme_cycle.get(current_theme, "auto")

        # Save to config
        self.config_manager.set("GUI_THEME", new_theme)
        self.config = self.config_manager.load_config()

        # Apply theme
        from ..ui.theme_manager import ThemeManager

        ThemeManager.apply_theme(new_theme)

        # Update icons
        self.update_theme_icon()
        self.update_github_icon()
        self.update_changelog_icon()
        self.update_language_icon()

    def update_changelog_icon(self: "MainWindow"):
        """Update Changelog icon color based on current theme"""
        from ..ui.theme_manager import ThemeManager

        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = current_theme

        # Choose color based on theme
        icon_color = "#000000" if actual_theme == "light" else "#ffffff"

        icon, text = get_fa_icon("list-alt", "", size=20, color=icon_color)
        if icon:
            pixmap = icon.pixmap(24, 24)
            self.changelog_label.setPixmap(pixmap)
        else:
            self.changelog_label.setText(FA_ICONS.get("list-alt", ""))
            fa_font = QFont("FontAwesome", 18)
            self.changelog_label.setFont(fa_font)
            self.changelog_label.setStyleSheet(f"color: {icon_color};")

    def update_github_icon(self: "MainWindow"):
        """Update GitHub icon color based on current theme"""
        from ..ui.theme_manager import ThemeManager

        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = current_theme

        # Choose color based on theme
        icon_color = "#24292e" if actual_theme == "light" else "#ffffff"

        icon, text = get_fa_icon("github", "", size=20, color=icon_color)
        if icon:
            pixmap = icon.pixmap(24, 24)
            self.github_label.setPixmap(pixmap)
        else:
            self.github_label.setText(FA_ICONS.get("github", ""))
            fa_font = QFont("FontAwesome", 18)
            self.github_label.setFont(fa_font)
            self.github_label.setStyleSheet(f"color: {icon_color};")

    def update_theme_icon(self: "MainWindow"):
        """Update theme icon based on current theme"""
        current_theme = self.config_manager.get("GUI_THEME", "auto")

        if current_theme == "light":
            icon_name = "sun"
            tooltip = t("gui_theme_light", "Light")
        elif current_theme == "dark":
            icon_name = "moon"
            tooltip = t("gui_theme_dark", "Dark")
        else:  # auto
            icon_name = "adjust"
            tooltip = t("gui_theme_auto", "Automatic (System)")

        # Get current theme for icon color
        from ..ui.theme_manager import ThemeManager

        theme_mode = self.config_manager.get("GUI_THEME", "auto")
        if theme_mode == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = theme_mode

        # Set icon color based on theme
        icon_color = "#ffffff" if actual_theme == "dark" else "#000000"

        icon, text = get_fa_icon(icon_name, "", size=18, color=icon_color)
        if icon:
            pixmap = icon.pixmap(20, 20)
            self.theme_label.setPixmap(pixmap)
        else:
            self.theme_label.setText(FA_ICONS.get(icon_name, ""))
            fa_font = QFont("FontAwesome", 16)
            self.theme_label.setFont(fa_font)
            self.theme_label.setStyleSheet(f"color: {icon_color};")

        self.theme_label.setToolTip(
            f"{t('gui_switch_theme', 'Switch Theme')} ({tooltip})"
        )

    def update_language_icon(self: "MainWindow"):
        """Update language icon and text based on current language"""
        # Check if widget exists
        if not hasattr(self, "language_label") or self.language_label is None:
            return

        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"

        # Get current theme for icon color
        from ..ui.theme_manager import ThemeManager

        theme_mode = self.config_manager.get("GUI_THEME", "auto")
        if theme_mode == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = theme_mode

        # Set icon color based on theme
        icon_color = "#ffffff" if actual_theme == "dark" else "#000000"

        # KRITISCH: Icon + Text aktualisieren (Icon-Label und Text-Label getrennt)
        icon, text = get_fa_icon("language", "", size=18, color=icon_color)
        lang_text = "DE" if current_lang == "de" else "EN"
        text_color = "#ffffff" if actual_theme == "dark" else "#000000"
        
        # Icon aktualisieren
        if not hasattr(self, "language_icon_label") or self.language_icon_label is None:
            return
            
        if icon:
            pixmap = icon.pixmap(20, 20)
            if not pixmap.isNull():
                self.language_icon_label.setPixmap(pixmap)
                self.language_icon_label.setScaledContents(True)
            else:
                self.language_icon_label.setText(FA_ICONS.get("language", "🌐"))
                fa_font = QFont("FontAwesome", 16)
                self.language_icon_label.setFont(fa_font)
                self.language_icon_label.setStyleSheet(f"color: {icon_color};")
        else:
            self.language_icon_label.setText(FA_ICONS.get("language", "🌐"))
            fa_font = QFont("FontAwesome", 16)
            self.language_icon_label.setFont(fa_font)
            self.language_icon_label.setStyleSheet(f"color: {icon_color};")
        
        # Text aktualisieren
        if hasattr(self, "language_text_label") and self.language_text_label is not None:
            self.language_text_label.setText(lang_text)
            self.language_text_label.setStyleSheet(f"color: {text_color};")

        # Update tooltip
        lang_name = "Deutsch" if current_lang == "de" else "English"
        if hasattr(self, "language_label") and self.language_label is not None:
            self.language_label.setToolTip(
                f"{t('gui_switch_language', 'Switch Language')} ({lang_name})"
            )

    def switch_language(self: "MainWindow"):
        """Switch language between DE and EN"""
        from .i18n import _i18n_instance, init_i18n

        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            # Detect current system language
            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"

        # Toggle between de and en
        new_lang = "en" if current_lang == "de" else "de"

        # Save to config
        self.config_manager.set("GUI_LANGUAGE", new_lang)
        self.config = self.config_manager.load_config()

        # Reload translations
        if _i18n_instance:
            _i18n_instance.set_language(new_lang)
        else:
            init_i18n(str(self.script_dir))

        # Update language icon and text first
        try:
            self.update_language_icon()
        except Exception as e:
            import traceback
            print(f"Error updating language icon: {e}")
            traceback.print_exc()

        # Update UI texts
        try:
            self.update_ui_texts()
        except Exception as e:
            import traceback
            print(f"Error updating UI texts: {e}")
            traceback.print_exc()

    def update_ui_texts(self: "MainWindow"):
        """Update all UI texts after language change"""
        # Window title
        self.setWindowTitle(t("app_name", "CachyOS Multi-Updater"))

        # Header
        if hasattr(self, "header_label"):
            self.header_label.setText(t("app_name", "CachyOS Multi-Updater"))

        # Update components group
        if hasattr(self, "components_group"):
            self.components_group.setTitle(
                t("gui_update_components", "Update Components")
            )

        # Checkboxes
        self.check_system.setText(t("system_updates", "System Updates (pacman)"))
        self.check_aur.setText(t("aur_updates", "AUR Updates (yay/paru)"))
        self.check_cursor.setText(t("cursor_editor_update", "Cursor Editor Update"))
        self.check_adguard.setText(t("adguard_home_update", "AdGuard Home Update"))
        self.check_flatpak.setText(t("flatpak_updates", "Flatpak Updates"))

        # Buttons
        icon, text = get_fa_icon(
            "search", t("gui_check_for_updates", "Check for Updates")
        )
        self.btn_check.setText(
            text if not icon else " " + t("gui_check_for_updates", "Check for Updates")
        )

        icon, text = get_fa_icon("play", t("gui_start_updates", "Start Updates"))
        self.btn_start.setText(
            text if not icon else " " + t("gui_start_updates", "Start Updates")
        )

        icon, text = get_fa_icon("stop", t("gui_stop", "Stop"))
        self.btn_stop.setText(text if not icon else " " + t("gui_stop", "Stop"))

        icon, text = get_fa_icon("cog", t("gui_settings", "Settings"))
        self.btn_settings.setText(
            text if not icon else " " + t("gui_settings", "Settings")
        )

        icon, text = get_fa_icon("file-text", t("gui_view_logs", "View Logs"))
        self.btn_logs.setText(
            text if not icon else " " + t("gui_view_logs", "View Logs")
        )

        # Status
        if self.status_label.text() in [t("gui_ready", "Ready"), "Ready"]:
            self.status_label.setText(t("gui_ready", "Ready"))

        # Output label
        if hasattr(self, "output_label"):
            self.output_label.setText(t("gui_output", "Output:"))

    def check_version_async(self: "MainWindow"):
        """Check for updates asynchronously"""
        try:
            from ..utils import VersionChecker
        except ImportError:
            return

        github_repo = self.config.get(
            "GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"
        )
        if not hasattr(self, "version_checker") or self.version_checker is None:
            self.version_checker = VersionChecker(str(self.script_dir), github_repo)

        # Check in background thread
        from .window_threads import VersionCheckThread

        self.version_thread = VersionCheckThread(
            self.version_checker, parent=self
        )
        self.version_thread.finished.connect(self.on_version_check_finished)
        self.version_thread.start()

    def on_version_check_finished(self: "MainWindow", latest_version: str, error: str):
        """Handle version check completion"""
        if error:
            self.latest_github_version = "error"
            self.update_version_label()
            if hasattr(self, "version_thread") and self.version_thread:
                self.version_thread.deleteLater()
                self.version_thread = None
            return

        if latest_version:
            self.latest_github_version = latest_version
            self.update_version_label()

            # Show toast notification if update is available (only once per session)
            if not self.update_toast_shown:
                if self.version_checker:
                    comparison = self.version_checker.compare_versions(
                        self.script_version, latest_version
                    )

                    if comparison < 0:
                        # Update available - show toast
                        self.show_update_toast()
                        self.update_toast_shown = True

        # Cleanup thread
        if hasattr(self, "version_thread") and self.version_thread:
            self.version_thread.deleteLater()
            self.version_thread = None

    def show_update_toast(self: "MainWindow"):
        """Show toast notification for available update"""
        try:
            from ..ui import show_toast
        except ImportError:
            return  # Toast not available

        message = t("gui_update_available", "Update available")
        if self.latest_github_version:
            message += f": v{self.latest_github_version}"
        message += f"\n{t('gui_version_click_to_update', 'Click to update')}"

        toast = show_toast(self, message, duration=5000)

        # Make toast clickable
        def on_toast_clicked():
            self._on_version_label_clicked_update()

        if hasattr(toast.label, "clicked"):
            toast.label.clicked.connect(on_toast_clicked)
        else:
            from ..widgets import ClickableLabel

            clickable_label = ClickableLabel(toast.label.text(), toast.label.parent())
            clickable_label.setStyleSheet(toast.label.styleSheet())
            clickable_label.setFont(toast.label.font())
            clickable_label.clicked.connect(on_toast_clicked)
            layout = toast.label.parent().layout()
            if layout:
                layout.replaceWidget(toast.label, clickable_label)
                toast.label.deleteLater()
                toast.label = clickable_label

    def check_version_manual(self: "MainWindow"):
        """Manually check for version updates"""
        self.version_label.setText(
            f"v{self.script_version} (Lokal) - {t('gui_checking', 'Checking...')}"
        )
        self.version_label.setStyleSheet("color: #666;")
        self.check_version_async()

    def check_updates(self: "MainWindow"):
        """Check for available updates - delegates to UpdateHandler"""
        self.update_handler.check_updates()

    def start_updates(self: "MainWindow", skip_confirmation: bool = False):
        """Start the update process - delegates to UpdateHandler"""
        self.update_handler.start_updates(skip_confirmation=skip_confirmation)

    def stop_updates(self: "MainWindow"):
        """Stop the running update process - delegates to UpdateHandler"""
        self.update_handler.stop_updates()

    def on_error_occurred(self: "MainWindow", error_msg: str):
        """Handle error from update runner"""
        QMessageBox.critical(
            self,
            t("gui_error", "Error"),
            t(
                "gui_update_error",
                "Error during update:\n\n{error}\n\nPlease update manually via git pull.",
            ).format(error=error_msg),
        )
        # Reset UI
        self.is_updating = False
        self.btn_check.setEnabled(True)
        self.btn_start.setEnabled(True)
        if hasattr(self, "btn_stop"):
            self.btn_stop.setEnabled(False)
            self.btn_stop.setVisible(False)

    def on_update_finished(self: "MainWindow", exit_code: int):
        """Handle update completion"""
        self.logger.info("=" * 80)
        self.logger.info(f"on_update_finished CALLED: exit_code={exit_code}")

        # Prevent multiple calls
        if hasattr(self, "_processing_finished") and self._processing_finished:
            self.logger.warning(
                "on_update_finished: Already processing, skipping duplicate call!"
            )
            return
        self._processing_finished = True

        # Reset UI state first
        self.is_updating = False
        self.btn_check.setEnabled(True)
        self.btn_start.setEnabled(True)
        if hasattr(self, "btn_stop"):
            self.btn_stop.setEnabled(False)
            self.btn_stop.setVisible(False)

        if exit_code == 0:
            if self._last_was_dry_run:
                # Dry-run completed
                # KEINE eigenen Meldungen in die Konsolen-Ausgabe - NUR stdout/stderr
                self.progress_bar.setValue(100)
                if hasattr(self, "status_label"):
                    self.status_label.setText("100%")
                # Show UpdateConfirmationDialog
                try:
                    dialog = UpdateConfirmationDialog(self)
                    QApplication.processEvents()
                    result = dialog.exec()
                    if result == QDialog.DialogCode.Accepted:
                        self.start_updates(skip_confirmation=True)
                except Exception as e:
                    self.logger.error(f"Error showing UpdateConfirmationDialog: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
                    # Fallback: just show a message
                    QMessageBox.information(
                        self,
                        t("gui_updates_available", "Updates Available"),
                        t("gui_start_updates_now", "Updates are available. Do you want to start the update process now?"),
                    )
            else:
                # Real update completed
                self.progress_bar.setValue(100)
                if hasattr(self, "status_label"):
                    self.status_label.setText("100%")
                # Show success message only once (in message box, not in output)
                QMessageBox.information(
                    self,
                    t("gui_update_success", "Update Successful"),
                    t("gui_update_completed", "Update completed successfully!"),
                )
        else:
            # KEINE eigenen Meldungen in die Konsolen-Ausgabe - NUR stdout/stderr
            # Exit-Code wird durch stderr des Prozesses angezeigt
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_failed", "Update failed with exit code: {code}").format(
                    code=exit_code
                ),
            )

        # Reset flag
        self._processing_finished = False
        self.logger.info("on_update_finished: Processing complete")

    def update_version_label(self: "MainWindow"):
        """Update version label with GitHub version and status colors"""
        if not hasattr(self, "version_label"):
            return

        if not hasattr(self, "latest_github_version"):
            self.latest_github_version = None

        # Disconnect all previous connections
        self._safe_disconnect_signal(self.version_label.clicked)

        if self.latest_github_version:
            if self.latest_github_version == "error":
                # Version check failed - GRAY
                self.version_label.setText(f"v{self.script_version} (Lokal)")
                self.version_label.setStyleSheet("color: #666;")
                self.version_label.setToolTip(
                    t("gui_version_check_failed", "Version check failed")
                )
                self._safe_connect_signal(
                    self.version_label.clicked,
                    self._on_version_label_clicked,
                    disconnect_first=False,
                )
                if hasattr(self, "update_badge"):
                    self.update_badge.setVisible(False)
            else:
                # Use VersionChecker for proper version comparison
                if self.version_checker:
                    comparison = self.version_checker.compare_versions(
                        self.script_version, self.latest_github_version
                    )
                else:
                    # Fallback: manual comparison
                    try:
                        local_parts = [int(x) for x in self.script_version.split(".")]
                        github_parts = [
                            int(x) for x in self.latest_github_version.split(".")
                        ]
                        if github_parts > local_parts:
                            comparison = -1
                        elif github_parts == local_parts:
                            comparison = 0
                        else:
                            comparison = 1
                    except Exception:
                        comparison = 0

                if comparison < 0:
                    # Update available - RED
                    self.version_label.setText(
                        f"v{self.script_version} → v{self.latest_github_version} ⬇"
                    )
                    self.version_label.setStyleSheet(
                        "color: #dc3545; font-weight: bold;"
                    )
                    tooltip_text = t("gui_version_click_to_update", "Click to update")
                    tooltip_text += (
                        f"\n{t('gui_local_version', 'Local')}: v{self.script_version}"
                    )
                    tooltip_text += f"\n{t('gui_github_version', 'GitHub')}: v{self.latest_github_version}"
                    self.version_label.setToolTip(tooltip_text)
                    self._safe_connect_signal(
                        self.version_label.clicked,
                        self._on_version_label_clicked_update,
                        disconnect_first=False,
                    )
                    if hasattr(self, "update_badge"):
                        self.update_badge.setVisible(True)
                elif comparison == 0:
                    # Up to date - GREEN
                    self.version_label.setText(f"v{self.script_version} ✓")
                    self.version_label.setStyleSheet("color: #28a745;")
                    tooltip_text = t("gui_version_up_to_date", "Version is up to date")
                    tooltip_text += (
                        f"\n{t('gui_local_version', 'Local')}: v{self.script_version}"
                    )
                    tooltip_text += f"\n{t('gui_github_version', 'GitHub')}: v{self.latest_github_version}"
                    self.version_label.setToolTip(tooltip_text)
                    self._safe_connect_signal(
                        self.version_label.clicked,
                        self._on_version_label_clicked,
                        disconnect_first=False,
                    )
                    if hasattr(self, "update_badge"):
                        self.update_badge.setVisible(False)
                else:
                    # Local is newer - GREEN
                    self.version_label.setText(f"v{self.script_version} (Dev)")
                    self.version_label.setStyleSheet("color: #28a745;")
                    tooltip_text = t(
                        "gui_version_dev", "Development version (local is newer)"
                    )
                    tooltip_text += (
                        f"\n{t('gui_local_version', 'Local')}: v{self.script_version}"
                    )
                    tooltip_text += f"\n{t('gui_github_version', 'GitHub')}: v{self.latest_github_version}"
                    self.version_label.setToolTip(tooltip_text)
                    self._safe_connect_signal(
                        self.version_label.clicked,
                        self._on_version_label_clicked,
                        disconnect_first=False,
                    )
                    if hasattr(self, "update_badge"):
                        self.update_badge.setVisible(False)
        else:
            # No version check yet - GRAY
            self.version_label.setText(f"v{self.script_version} (Lokal)")
            self.version_label.setStyleSheet("color: #666;")
            self.version_label.setToolTip(
                t("gui_version_check_tooltip", "Click to check for updates")
            )
            self._safe_connect_signal(
                self.version_label.clicked,
                self._on_version_label_clicked,
                disconnect_first=False,
            )
            if hasattr(self, "update_badge"):
                self.update_badge.setVisible(False)

    def _on_version_label_clicked(self: "MainWindow"):
        """Handle version label click - check for updates"""
        self.check_version_manual()

    def _on_version_label_clicked_update(self: "MainWindow"):
        """Handle version label click when update is available - open update dialog"""
        # UpdateDialog ist bereits in Zeile 24 importiert
        dialog = UpdateDialog(
            self.script_dir,
            self.script_version,
            self.latest_github_version,
            self.version_checker,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update was performed, refresh version check
            self.check_version_async()

    def _on_language_label_clicked(self: "MainWindow"):
        """Handle language label click with feedback effect"""
        # Get the widget that was clicked
        widget = None
        if (
            hasattr(self, "language_icon_label")
            and self.language_icon_label is not None
        ):
            widget = self.language_icon_label.parent()

        # Cancel any pending restore operation
        if self.language_feedback_timer and self.language_feedback_timer.isActive():
            self.language_feedback_timer.stop()

        # Visual feedback: briefly change opacity
        original_effect = None
        if widget and widget.isVisible():
            try:
                current_effect = widget.graphicsEffect()
                if (
                    self.language_feedback_effect
                    and current_effect == self.language_feedback_effect
                ):
                    original_effect = self.language_feedback_original_effect
                    widget.setGraphicsEffect(None)
                else:
                    original_effect = current_effect
                    self.language_feedback_original_effect = original_effect

                opacity_effect = QGraphicsOpacityEffect()
                opacity_effect.setOpacity(0.6)
                widget.setGraphicsEffect(opacity_effect)
                self.language_feedback_effect = opacity_effect
                QApplication.processEvents()
            except Exception:
                pass

        # Switch language
        try:
            self.switch_language()
        except Exception as e:
            import traceback
            print(f"Error switching language: {e}")
            traceback.print_exc()

        # Restore original effect after short delay
        def restore_effect():
            try:
                if widget and widget.isVisible():
                    current_effect = widget.graphicsEffect()
                    if current_effect == self.language_feedback_effect:
                        widget.setGraphicsEffect(original_effect)
                        self.language_feedback_effect = None
                        self.language_feedback_original_effect = None
            except Exception:
                pass

        if widget:
            if self.language_feedback_timer is None:
                self.language_feedback_timer = QTimer()
                self.language_feedback_timer.setSingleShot(True)
                self.language_feedback_timer.timeout.connect(restore_effect)
                self.language_feedback_restore_func = restore_effect
            else:
                if self.language_feedback_restore_func is not None:
                    try:
                        self.language_feedback_timer.timeout.disconnect(
                            self.language_feedback_restore_func
                        )
                    except TypeError:
                        try:
                            self.language_feedback_timer.timeout.disconnect()
                        except TypeError:
                            pass
                self.language_feedback_timer.timeout.connect(restore_effect)
                self.language_feedback_restore_func = restore_effect

            self.language_feedback_timer.start(150)

    def _on_theme_label_clicked(self: "MainWindow"):
        """Handle theme label click"""
        self.switch_theme()

    def _on_changelog_label_clicked(self: "MainWindow"):
        """Handle changelog label click"""
        self.open_github_releases()

    def _on_github_label_clicked(self: "MainWindow"):
        """Handle GitHub label click"""
        self.open_github()

    def perform_automatic_update(self: "MainWindow") -> None:
        """Perform automatic update via git pull or ZIP download"""
        # This method should be in window_threads.py or stay here as it's complex
        # For now, keeping it here as a placeholder
        QMessageBox.information(
            self,
            t("gui_info", "Info"),
            t("gui_update_feature", "Automatic update feature will be implemented here"),
        )

