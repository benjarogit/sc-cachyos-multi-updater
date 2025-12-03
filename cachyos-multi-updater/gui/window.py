#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Main Window
Main GUI window for the updater
"""

from pathlib import Path
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QTextEdit, QProgressBar, QGroupBox,
    QMessageBox, QFileDialog, QDialog, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QAbstractAnimation
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QMovie, QPixmap, QPainter

# Import Font Awesome icon helper
try:
    from .fa_icons import get_fa_icon, apply_fa_font, FA_ICONS
except ImportError:
    from fa_icons import get_fa_icon, apply_fa_font, FA_ICONS

# Import animation helpers
try:
    from .animations import AnimationHelper, animate_button_hover, animate_dialog_show, animate_dialog_hide
except ImportError:
    try:
        from animations import AnimationHelper, animate_button_hover, animate_dialog_show, animate_dialog_hide
    except ImportError:
        # Fallback if animations not available
        AnimationHelper = None
        animate_button_hover = None
        animate_dialog_show = None
        animate_dialog_hide = None

# Handle imports for both direct execution and module import
try:
    from .config_dialog import ConfigDialog
    from .update_runner import UpdateRunner
    from .config_manager import ConfigManager
    from .i18n import t
    from .sudo_dialog import SudoDialog
    from .update_confirmation_dialog import UpdateConfirmationDialog
except ImportError:
    from config_dialog import ConfigDialog
    from update_runner import UpdateRunner
    from config_manager import ConfigManager
    from i18n import t
    from sudo_dialog import SudoDialog
    from update_confirmation_dialog import UpdateConfirmationDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, script_dir: str):
        super().__init__()
        self.script_dir = Path(script_dir)
        self.config_manager = ConfigManager(str(self.script_dir))
        self.config = self.config_manager.load_config()
        self.update_runner = None
        self.script_version = self.get_script_version()
        self.is_updating = False
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(self.update_spinner)
        self.spinner_frame = 0
        self.version_checker = None
        self.latest_version = None
        self.latest_github_version = None
        self.version_thread = None
        
        self.setWindowTitle(t("app_name", "CachyOS Multi-Updater"))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        self.init_ui()
        self.load_config()
        
        # Check for updates in background
        self.check_version_async()
    
    def get_script_version(self):
        """Read script version from update-all.sh"""
        script_path = self.script_dir / "update-all.sh"
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'readonly SCRIPT_VERSION=' in line:
                        version = line.split('"')[1] if '"' in line else line.split("'")[1]
                        return version
        except Exception:
            pass
        return "unknown"
    
    def update_spinner(self):
        """Update spinner animation"""
        self.spinner_frame = (self.spinner_frame + 1) % 10
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        if self.is_updating:
            wait_text = t("gui_please_wait_updating", "Please wait, updating system...")
        else:
            wait_text = t("gui_please_wait_checking", "Please wait, checking for updates...")
        self.wait_label.setText(f"{spinner_chars[self.spinner_frame]} {wait_text}")
    
    def init_ui(self):
        """Initialize UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Header with GitHub icon and version
        header_layout = QHBoxLayout()
        
        # Title with modern styling
        self.header_label = QLabel(t("app_name", "CachyOS Multi-Updater"))
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_label.setFont(header_font)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # Add subtle gradient effect via stylesheet
        self.header_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 120, 212, 0.1),
                    stop:1 transparent);
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        header_layout.addWidget(self.header_label)
        
        # Version label (will be updated after version check)
        self.version_label = QLabel(f"v{self.script_version} (Lokal)")
        version_font = QFont()
        version_font.setPointSize(10)
        version_font.setItalic(True)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet("color: #666;")
        self.version_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.version_label.setToolTip(t("gui_version_check_tooltip", "Click to check for updates"))
        self.version_label.mousePressEvent = self._on_version_label_clicked
        header_layout.addWidget(self.version_label)
        
        header_layout.addStretch()
        
        # Language switcher icon
        self.language_label = QLabel("DE")
        language_font = QFont()
        language_font.setPointSize(12)
        language_font.setBold(True)
        self.language_label.setFont(language_font)
        self.language_label.setStyleSheet("color: #666; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px;")
        self.language_label.setToolTip(t("gui_switch_language", "Switch Language"))
        self.language_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.language_label.mousePressEvent = self._on_language_label_clicked
        header_layout.addWidget(self.language_label)
        
        # Theme switcher icon
        self.theme_label = QLabel()
        self.update_theme_icon()
        self.theme_label.setToolTip(t("gui_switch_theme", "Switch Theme"))
        self.theme_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_label.mousePressEvent = self._on_theme_label_clicked
        header_layout.addWidget(self.theme_label)
        
        # Changelog/Release icon as clickable label
        self.changelog_label = QLabel()
        self.update_changelog_icon()
        self.changelog_label.setToolTip(t("gui_open_changelog", "Open Changelog/Releases"))
        self.changelog_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.changelog_label.mousePressEvent = self._on_changelog_label_clicked
        header_layout.addWidget(self.changelog_label)
        
        # GitHub icon as clickable label (not button)
        self.github_label = QLabel()
        self.update_github_icon()
        self.github_label.setToolTip(t("gui_open_github", "Open GitHub repository"))
        self.github_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_label.mousePressEvent = self._on_github_label_clicked
        header_layout.addWidget(self.github_label)
        
        layout.addLayout(header_layout)
        
        # Update components group
        self.components_group = QGroupBox(t("gui_update_components", "Update Components"))
        components_layout = QVBoxLayout()
        
        # Try to use Font Awesome checkboxes, fallback to regular checkboxes
        try:
            from .fa_checkbox import FACheckBox
            USE_FA_CHECKBOX = True
        except ImportError:
            try:
                from fa_checkbox import FACheckBox
                USE_FA_CHECKBOX = True
            except ImportError:
                USE_FA_CHECKBOX = False
        
        if USE_FA_CHECKBOX:
            self.check_system = FACheckBox(t("system_updates", "System Updates (pacman)"))
            self.check_aur = FACheckBox(t("aur_updates", "AUR Updates (yay/paru)"))
            self.check_cursor = FACheckBox(t("cursor_editor_update", "Cursor Editor Update"))
            self.check_adguard = FACheckBox(t("adguard_home_update", "AdGuard Home Update"))
            self.check_flatpak = FACheckBox(t("flatpak_updates", "Flatpak Updates"))
        else:
            self.check_system = QCheckBox(t("system_updates", "System Updates (pacman)"))
            self.check_aur = QCheckBox(t("aur_updates", "AUR Updates (yay/paru)"))
            self.check_cursor = QCheckBox(t("cursor_editor_update", "Cursor Editor Update"))
            self.check_adguard = QCheckBox(t("adguard_home_update", "AdGuard Home Update"))
            self.check_flatpak = QCheckBox(t("flatpak_updates", "Flatpak Updates"))
        
        components_layout.addWidget(self.check_system)
        components_layout.addWidget(self.check_aur)
        components_layout.addWidget(self.check_cursor)
        components_layout.addWidget(self.check_adguard)
        components_layout.addWidget(self.check_flatpak)
        
        self.components_group.setLayout(components_layout)
        layout.addWidget(self.components_group)
        
        # Progress bar (without text format to avoid duplication)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")  # No text format - status_label shows the info
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel(t("gui_ready", "Ready"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Output area
        self.output_label = QLabel(t("gui_output", "Output:"))
        layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Monospace", 9))
        # Add syntax highlighting
        try:
            from .syntax_highlighter import ConsoleSyntaxHighlighter
            self.highlighter = ConsoleSyntaxHighlighter(self.output_text.document())
        except ImportError:
            try:
                from syntax_highlighter import ConsoleSyntaxHighlighter
                self.highlighter = ConsoleSyntaxHighlighter(self.output_text.document())
            except ImportError:
                self.highlighter = None
        layout.addWidget(self.output_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Check for Updates button
        icon, text = get_fa_icon('search', t("gui_check_for_updates", "Check for Updates"))
        self.btn_check = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(self.btn_check)
        self.btn_check.clicked.connect(self.check_updates)
        button_layout.addWidget(self.btn_check)
        
        # Start Updates button
        icon, text = get_fa_icon('play', t("gui_start_updates", "Start Updates"))
        self.btn_start = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(self.btn_start)
        self.btn_start.clicked.connect(self.start_updates)
        button_layout.addWidget(self.btn_start)
        
        # Stop button
        icon, text = get_fa_icon('stop', t("gui_stop", "Stop"))
        self.btn_stop = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(self.btn_stop)
        self.btn_stop.clicked.connect(self.stop_updates)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setVisible(False)  # Hidden by default
        button_layout.addWidget(self.btn_stop)
        
        # Wait label with spinner (shown during updates)
        self.wait_label = QLabel()
        self.wait_label.setMaximumHeight(32)
        self.wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wait_font = QFont()
        wait_font.setPointSize(10)
        self.wait_label.setFont(wait_font)
        self.wait_label.setStyleSheet("color: #666; font-style: italic;")
        self.wait_label.setVisible(False)
        button_layout.addWidget(self.wait_label)
        
        button_layout.addStretch()
        
        # Settings button
        icon, text = get_fa_icon('cog', t("gui_settings", "Settings"))
        self.btn_settings = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(self.btn_settings)
        self.btn_settings.clicked.connect(self.show_settings)
        button_layout.addWidget(self.btn_settings)
        
        # View Logs button
        icon, text = get_fa_icon('file-text', t("gui_view_logs", "View Logs"))
        self.btn_logs = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(self.btn_logs)
        self.btn_logs.clicked.connect(self.view_logs)
        button_layout.addWidget(self.btn_logs)
        
        layout.addLayout(button_layout)
        
        # Copyright footer
        copyright_layout = QHBoxLayout()
        copyright_layout.addStretch()
        copyright_label = QLabel("© 2025 Sunny C. - <a href='https://benjaro.info'>benjaro.info</a>")
        copyright_label.setOpenExternalLinks(True)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_font = QFont()
        copyright_font.setPointSize(8)
        copyright_label.setFont(copyright_font)
        copyright_layout.addWidget(copyright_label)
        copyright_layout.addStretch()
        layout.addLayout(copyright_layout)
    
    def load_config(self):
        """Load config and update UI"""
        self.config = self.config_manager.load_config()
        
        # Update language label
        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            import os
            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"
        if hasattr(self, 'language_label'):
            self.language_label.setText("EN" if current_lang == "en" else "DE")
        
        # Update theme icon
        if hasattr(self, 'theme_label'):
            self.update_theme_icon()
        
        # Update checkboxes
        self.check_system.setChecked(self.config.get("ENABLE_SYSTEM_UPDATE", "true") == "true")
        self.check_aur.setChecked(self.config.get("ENABLE_AUR_UPDATE", "true") == "true")
        self.check_cursor.setChecked(self.config.get("ENABLE_CURSOR_UPDATE", "true") == "true")
        self.check_adguard.setChecked(self.config.get("ENABLE_ADGUARD_UPDATE", "true") == "true")
        self.check_flatpak.setChecked(self.config.get("ENABLE_FLATPAK_UPDATE", "true") == "true")
    
    def save_component_settings(self):
        """Save component settings to config"""
        # Works for both QCheckBox and FACheckBox
        self.config["ENABLE_SYSTEM_UPDATE"] = str(self.check_system.isChecked()).lower()
        self.config["ENABLE_AUR_UPDATE"] = str(self.check_aur.isChecked()).lower()
        self.config["ENABLE_CURSOR_UPDATE"] = str(self.check_cursor.isChecked()).lower()
        self.config["ENABLE_ADGUARD_UPDATE"] = str(self.check_adguard.isChecked()).lower()
        self.config["ENABLE_FLATPAK_UPDATE"] = str(self.check_flatpak.isChecked()).lower()
        self.config_manager.save_config(self.config)
    
    def show_update_confirmation_dialog(self):
        """Show update confirmation dialog after check"""
        dialog = UpdateConfirmationDialog(self)
        # Animate dialog appearance
        if animate_dialog_show is not None:
            animate_dialog_show(dialog)
        if dialog.exec():
            # User clicked "Yes" - start updates
            self.start_updates(dry_run=False)
        # If user clicked "No" or "Close", dialog just closes, nothing happens
    
    def get_sudo_password(self):
        """Get sudo password from secure storage or prompt user"""
        # Try to get from secure storage first
        try:
            from .password_manager import PasswordManager
        except ImportError:
            try:
                from password_manager import PasswordManager
            except ImportError:
                PasswordManager = None
        
        if PasswordManager:
            password_manager = PasswordManager(str(self.script_dir))
            stored_password = password_manager.get_password()
            if stored_password:
                return stored_password
        
        # Fallback: Check config (for backward compatibility with old unencrypted passwords)
        stored_password = self.config_manager.get("SUDO_PASSWORD")
        if stored_password:
            # Migrate to secure storage
            if PasswordManager:
                password_manager = PasswordManager(str(self.script_dir))
                if password_manager.is_available():
                    password_manager.save_password(stored_password)
                    # Remove from config
                    config = self.config_manager.load_config()
                    config.pop("SUDO_PASSWORD", None)
                    self.config_manager.save_config(config)
            return stored_password
        
        # If not stored, show dialog
        dialog = SudoDialog(self, save_to_config=True)
        if dialog.exec():
            password = dialog.get_password()
            # Save securely if user wants
            if dialog.should_save_password():
                if PasswordManager:
                    password_manager = PasswordManager(str(self.script_dir))
                    if password_manager.is_available():
                        password_manager.save_password(password)
                    else:
                        # Fallback to config (with warning)
                        self.logger.warning("Secure password storage not available, storing in config (not recommended)")
                        self.config_manager.set("SUDO_PASSWORD", password)
                else:
                    # Fallback to config
                    self.config_manager.set("SUDO_PASSWORD", password)
            return password
        return None
    
    def check_updates(self):
        """Check for available updates (dry-run)"""
        self.save_component_settings()
        self.start_updates(dry_run=True)
    
    def start_updates(self, dry_run=False):
        """Start update process"""
        if self.update_runner and self.update_runner.process:
            from PyQt6.QtCore import QProcess
            if self.update_runner.process.state() == QProcess.ProcessState.Running:
                QMessageBox.warning(self, t("gui_update_running", "Update Running"), t("gui_update_running", "An update is already running!"))
                return
        
        self.save_component_settings()
        
        # Get sudo password if needed (not for dry-run)
        sudo_password = None
        if not dry_run:
            sudo_password = self.get_sudo_password()
            if sudo_password is None:
                # User cancelled password dialog
                return
        
        # Create runner
        self.update_runner = UpdateRunner(str(self.script_dir), self.config)
        self.update_runner.output_received.connect(self.on_output_received)
        self.update_runner.progress_update.connect(self.on_progress_update)
        self.update_runner.finished.connect(self.on_update_finished)
        self.update_runner.error_occurred.connect(self.on_error)
        
        # Clear output
        self.output_text.clear()
        
        # Show "Please wait" message immediately
        if dry_run:
            wait_msg = t("gui_please_wait_checking", "Please wait, checking for updates...")
            self.on_output_received(wait_msg)
        else:
            wait_msg = t("gui_please_wait_updating", "Please wait, updating system...")
            self.on_output_received(wait_msg)
        
        # Update UI - show spinner and wait label
        self.is_updating = not dry_run
        self.btn_start.setEnabled(False)
        self.btn_check.setEnabled(False)
        self.wait_label.setVisible(True)
        self.btn_stop.setVisible(True)
        self.btn_stop.setEnabled(True)
        
        # Start spinner animation
        self.spinner_frame = 0
        self.spinner_timer.start(100)  # Update every 100ms
        self.update_spinner()
        
        self.progress_bar.setValue(0)
        self.status_label.setText(t("gui_updating", "Updating...") if not dry_run else t("gui_checking", "Checking for updates..."))
        
        # Store if this is a dry-run for later check
        self._last_was_dry_run = dry_run
        
        # Start update (pass dry_run parameter correctly)
        self.update_runner.start_update(dry_run=dry_run, interactive=False, sudo_password=sudo_password)
    
    def stop_updates(self):
        """Stop update process"""
        if self.update_runner:
            self.update_runner.stop_update()
            self.status_label.setText(t("gui_update_stopped", "Update stopped"))
            # Stop spinner and hide wait label
            self.spinner_timer.stop()
            self.wait_label.setVisible(False)
            self.btn_stop.setVisible(False)
            self.is_updating = False
            self.on_update_finished(1)
    
    def on_output_received(self, text: str):
        """Handle output from update script"""
        # Filter out progress bar lines that show percentage (to avoid duplication)
        # These lines come from lib/progress.sh and are meant for console output.
        # In the GUI, we already have a progress bar widget, so we filter these lines
        # to avoid showing the same information twice.
        # Format: "[████████████████████████████████████████] 100% [5/5]"
        # Also filter lines with just percentage: "100%"
        if re.search(r'\[.*\]\s+\d+%\s+\[\d+/\d+\]', text) or re.search(r'^\s*\d+%\s*$', text):
            # This is a progress bar line - skip it, we already show it in the progress bar widget
            return
        
        # Color coding
        format_normal = QTextCharFormat()
        format_normal.setForeground(QColor("black"))
        
        format_success = QTextCharFormat()
        format_success.setForeground(QColor("green"))
        
        format_error = QTextCharFormat()
        format_error.setForeground(QColor("red"))
        
        format_warning = QTextCharFormat()
        format_warning.setForeground(QColor("orange"))
        
        # Determine format
        text_lower = text.lower()
        if "error" in text_lower or "failed" in text_lower or "❌" in text:
            fmt = format_error
        elif "success" in text_lower or "✅" in text or "completed" in text_lower:
            fmt = format_success
        elif "warning" in text_lower or "⚠️" in text:
            fmt = format_warning
        else:
            fmt = format_normal
        
        # Append text
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
    
    def on_progress_update(self, percent: int, message: str):
        """Handle progress update"""
        self.progress_bar.setValue(percent)
        # Extract step info from message if available (e.g., "[5/5]")
        step_match = re.search(r'\[(\d+)/(\d+)\]', message)
        if step_match:
            current_step = step_match.group(1)
            total_steps = step_match.group(2)
            self.status_label.setText(f"{percent}% [{current_step}/{total_steps}]")
        else:
            self.status_label.setText(f"{percent}%")
    
    def on_update_finished(self, exit_code: int):
        """Handle update finished"""
        # Stop spinner
        self.spinner_timer.stop()
        self.wait_label.setVisible(False)
        self.btn_stop.setVisible(False)
        self.is_updating = False
        
        self.btn_start.setEnabled(True)
        self.btn_check.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        if exit_code == 0:
            self.status_label.setText(t("gui_update_complete", "Update complete"))
            self.progress_bar.setValue(100)
            # Show success toast
            try:
                from .toast_notification import show_toast
                show_toast(self, t("gui_update_completed", "Update completed successfully"), 3000)
            except ImportError:
                try:
                    from toast_notification import show_toast
                    show_toast(self, t("gui_update_completed", "Update completed successfully"), 3000)
                except ImportError:
                    pass
            
            # If this was a dry-run (check), ask if user wants to update now
            if hasattr(self, '_last_was_dry_run') and self._last_was_dry_run:
                # Show dialog immediately after check finishes
                # Use QTimer to ensure GUI is responsive and dialog appears quickly
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.show_update_confirmation_dialog())
        else:
            self.status_label.setText(t("gui_update_failed", "Update failed"))
            # Show error toast
            try:
                from .toast_notification import show_toast
                show_toast(self, t("gui_update_failed", "Update failed"), 4000)
            except ImportError:
                try:
                    from toast_notification import show_toast
                    show_toast(self, t("gui_update_failed", "Update failed"), 4000)
                except ImportError:
                    pass
        
        self.update_runner = None
        self._last_was_dry_run = False
    
    def on_error(self, error_msg: str):
        """Handle error"""
        QMessageBox.critical(self, t("gui_error", "Error"), error_msg)
        self.on_update_finished(1)
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = ConfigDialog(str(self.script_dir), self)
        # Animate dialog appearance
        if animate_dialog_show is not None:
            animate_dialog_show(dialog)
        if dialog.exec():
            self.load_config()
            # Apply theme if changed
            from theme_manager import ThemeManager
            theme_mode = self.config_manager.get("GUI_THEME", "auto")
            ThemeManager.apply_theme(theme_mode)
    
    def view_logs(self):
        """View log files"""
        log_dir = Path(self.script_dir) / "logs"
        if not log_dir.exists():
            QMessageBox.information(self, t("gui_no_logs", "No Logs"), t("gui_log_directory_not_found", "Log directory does not exist."))
            return
        
        # Get latest log file
        log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            QMessageBox.information(self, t("gui_no_logs", "No Logs"), t("gui_no_logs", "No log files found."))
            return
        
        # Show log viewer dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(t("gui_log_viewer", "Log Viewer"))
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        
        # File selector
        file_layout = QHBoxLayout()
        file_label = QLabel("Log File:")
        file_combo = QComboBox()
        file_combo.addItems([f.name for f in log_files])
        
        def load_log(index):
            log_path = log_files[index]
            log_text.clear()
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    log_text.setPlainText(f.read())
            except Exception as e:
                log_text.setPlainText(f"Error reading log: {e}")
        
        file_combo.currentIndexChanged.connect(load_log)
        file_layout.addWidget(file_label)
        file_layout.addWidget(file_combo)
        file_layout.addStretch()
        layout.addLayout(file_layout)
        
        # Log text
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setFont(QFont("Monospace", 9))
        layout.addWidget(log_text)
        
        # Load first log
        load_log(0)
        
        # Close button
        icon, text = get_fa_icon('times', t("gui_close", "Close"))
        close_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(close_btn)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def open_github(self):
        """Open GitHub repository in browser"""
        import webbrowser
        import subprocess
        import os
        github_repo = self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater")
        github_url = f"https://github.com/{github_repo}"
        
        # Try to open URL using xdg-open (more reliable on Linux, avoids QDBus warnings)
        try:
            # Suppress QDBus warnings by setting environment variable
            env = os.environ.copy()
            env.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            subprocess.Popen(['xdg-open', github_url], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           env=env)
        except (FileNotFoundError, OSError):
            # Fallback to webbrowser module (also suppress warnings)
            os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            webbrowser.open(github_url)
    
    def open_github_releases(self):
        """Open GitHub releases page"""
        import subprocess
        import webbrowser
        import os
        github_repo = self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater")
        github_url = f"https://github.com/{github_repo}/releases"
        
        # Try to open URL using xdg-open (more reliable on Linux, avoids QDBus warnings)
        try:
            # Suppress QDBus warnings by setting environment variable
            env = os.environ.copy()
            env.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            # Suppress stderr to avoid QDBus warnings
            subprocess.Popen(['xdg-open', github_url], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           env=env,
                           start_new_session=True)
        except (OSError, FileNotFoundError):
            # Fallback to webbrowser module (also suppress warnings)
            os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")
            webbrowser.open(github_url)
    
    def switch_theme(self):
        """Switch theme cyclically: auto -> light -> dark -> auto"""
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        theme_cycle = {"auto": "light", "light": "dark", "dark": "auto"}
        new_theme = theme_cycle.get(current_theme, "auto")
        
        # Save to config
        self.config_manager.set("GUI_THEME", new_theme)
        self.config = self.config_manager.load_config()
        
        # Apply theme
        from theme_manager import ThemeManager
        ThemeManager.apply_theme(new_theme)
        
        # Update icons
        self.update_theme_icon()
        self.update_github_icon()
    
    def update_changelog_icon(self):
        """Update Changelog icon color based on current theme"""
        from theme_manager import ThemeManager
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = current_theme
        
        # Choose color based on theme
        icon_color = '#24292e' if actual_theme == "light" else '#ffffff'
        
        icon, text = get_fa_icon('list-alt', "", size=20, color=icon_color)
        if icon:
            pixmap = icon.pixmap(24, 24)
            self.changelog_label.setPixmap(pixmap)
        else:
            self.changelog_label.setText(FA_ICONS.get('list-alt', ''))
            fa_font = QFont("FontAwesome", 18)
            self.changelog_label.setFont(fa_font)
            self.changelog_label.setStyleSheet(f"color: {icon_color};")
    
    def update_github_icon(self):
        """Update GitHub icon color based on current theme"""
        from theme_manager import ThemeManager
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = current_theme
        
        # Choose color based on theme
        icon_color = '#24292e' if actual_theme == "light" else '#ffffff'
        
        icon, text = get_fa_icon('github', "", size=20, color=icon_color)
        if icon:
            pixmap = icon.pixmap(24, 24)
            self.github_label.setPixmap(pixmap)
        else:
            self.github_label.setText(FA_ICONS.get('github', ''))
            fa_font = QFont("FontAwesome", 18)
            self.github_label.setFont(fa_font)
            self.github_label.setStyleSheet(f"color: {icon_color};")
    
    def update_theme_icon(self):
        """Update theme icon based on current theme"""
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        
        if current_theme == "light":
            icon_name = 'sun'
            tooltip = t("gui_theme_light", "Light")
        elif current_theme == "dark":
            icon_name = 'moon'
            tooltip = t("gui_theme_dark", "Dark")
        else:  # auto
            icon_name = 'adjust'
            tooltip = t("gui_theme_auto", "Automatic (System)")
        
        icon, text = get_fa_icon(icon_name, "", size=18)
        if icon:
            pixmap = icon.pixmap(20, 20)
            self.theme_label.setPixmap(pixmap)
        else:
            self.theme_label.setText(FA_ICONS.get(icon_name, ''))
            fa_font = QFont("FontAwesome", 16)
            self.theme_label.setFont(fa_font)
            self.theme_label.setStyleSheet("color: #666;")
        
        self.theme_label.setToolTip(f"{t('gui_switch_theme', 'Switch Theme')} ({tooltip})")
    
    def switch_language(self):
        """Switch language between DE and EN"""
        from i18n import _i18n_instance, init_i18n
        
        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            # Detect current system language
            import os
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
        
        # Update UI texts
        self.update_ui_texts()
        
        # Update language label
        self.language_label.setText("EN" if new_lang == "en" else "DE")
    
    def update_ui_texts(self):
        """Update all UI texts after language change"""
        # Window title
        self.setWindowTitle(t("app_name", "CachyOS Multi-Updater"))
        
        # Header
        if hasattr(self, 'header_label'):
            self.header_label.setText(t("app_name", "CachyOS Multi-Updater"))
        
        # Update components group
        if hasattr(self, 'components_group'):
            self.components_group.setTitle(t("gui_update_components", "Update Components"))
        
        # Checkboxes
        self.check_system.setText(t("system_updates", "System Updates (pacman)"))
        self.check_aur.setText(t("aur_updates", "AUR Updates (yay/paru)"))
        self.check_cursor.setText(t("cursor_editor_update", "Cursor Editor Update"))
        self.check_adguard.setText(t("adguard_home_update", "AdGuard Home Update"))
        self.check_flatpak.setText(t("flatpak_updates", "Flatpak Updates"))
        
        # Buttons
        icon, text = get_fa_icon('search', t("gui_check_for_updates", "Check for Updates"))
        self.btn_check.setText(text if not icon else " " + t("gui_check_for_updates", "Check for Updates"))
        
        icon, text = get_fa_icon('play', t("gui_start_updates", "Start Updates"))
        self.btn_start.setText(text if not icon else " " + t("gui_start_updates", "Start Updates"))
        
        icon, text = get_fa_icon('stop', t("gui_stop", "Stop"))
        self.btn_stop.setText(text if not icon else " " + t("gui_stop", "Stop"))
        
        icon, text = get_fa_icon('cog', t("gui_settings", "Settings"))
        self.btn_settings.setText(text if not icon else " " + t("gui_settings", "Settings"))
        
        icon, text = get_fa_icon('file-text', t("gui_view_logs", "View Logs"))
        self.btn_logs.setText(text if not icon else " " + t("gui_view_logs", "View Logs"))
        
        # Status
        if self.status_label.text() in [t("gui_ready", "Ready"), "Ready"]:
            self.status_label.setText(t("gui_ready", "Ready"))
        
        # Output label
        if hasattr(self, 'output_label'):
            self.output_label.setText(t("gui_output", "Output:"))
        
        # Tooltips
        self.language_label.setToolTip(t("gui_switch_language", "Switch Language"))
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "light":
            tooltip = t("gui_theme_light", "Light")
        elif current_theme == "dark":
            tooltip = t("gui_theme_dark", "Dark")
        else:
            tooltip = t("gui_theme_auto", "Automatic (System)")
        self.theme_label.setToolTip(f"{t('gui_switch_theme', 'Switch Theme')} ({tooltip})")
        self.github_label.setToolTip(t("gui_open_github", "Open GitHub repository"))
        
        # Update version label if available
        if hasattr(self, 'version_checker') and self.version_checker and self.latest_version:
            self.update_version_display()
    
    def check_version_async(self):
        """Check for updates asynchronously"""
        try:
            from .version_checker import VersionChecker
        except ImportError:
            try:
                from version_checker import VersionChecker
            except ImportError:
                return
        
        github_repo = self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater")
        if not hasattr(self, 'version_checker') or self.version_checker is None:
            self.version_checker = VersionChecker(str(self.script_dir), github_repo)
        
        # Check in background thread to avoid blocking UI
        class VersionCheckThread(QThread):
            finished = pyqtSignal(str, str)  # latest_version, error
            
            def __init__(self, checker):
                super().__init__()
                self.checker = checker
            
            def run(self):
                latest, error = self.checker.check_latest_version()
                self.finished.emit(latest or "", error or "")
        
        self.version_thread = VersionCheckThread(self.version_checker)
        self.version_thread.finished.connect(self.on_version_check_finished)
        self.version_thread.start()
    
    def on_version_check_finished(self, latest_version: str, error: str):
        """Handle version check completion"""
        if error:
            # Keep showing local version only
            self.latest_github_version = "error"
            self.update_version_label()
            # Cleanup thread
            if hasattr(self, 'version_thread') and self.version_thread:
                self.version_thread.deleteLater()
                self.version_thread = None
            return
        
        if latest_version:
            self.latest_github_version = latest_version
            self.update_version_label()
        
        # Cleanup thread
        if hasattr(self, 'version_thread') and self.version_thread:
            self.version_thread.deleteLater()
            self.version_thread = None
    
    def check_version_manual(self):
        """Manually check for version updates"""
        self.version_label.setText(f"v{self.script_version} (Lokal) - {t('gui_checking', 'Checking...')}")
        self.version_label.setStyleSheet("color: #666;")
        self.check_version_async()
    
    def update_version_label(self):
        """Update version label with GitHub version"""
        if not hasattr(self, 'version_label'):
            return
        
        if not hasattr(self, 'latest_github_version'):
            self.latest_github_version = None
        
        if self.latest_github_version:
            if self.latest_github_version == "error":
                self.version_label.setText(f"v{self.script_version} (Lokal)")
                self.version_label.setStyleSheet("color: #666;")
                self.version_label.setToolTip(t("gui_version_check_failed", "Version check failed"))
            else:
                # Compare versions (simple string comparison for now)
                try:
                    local_parts = [int(x) for x in self.script_version.split('.')]
                    github_parts = [int(x) for x in self.latest_github_version.split('.')]
                    
                    if github_parts > local_parts:
                        # Update available - RED
                        self.version_label.setText(f"v{self.script_version} (Lokal) → v{self.latest_github_version} (GitHub) ⬇")
                        self.version_label.setStyleSheet("color: #dc3545; font-weight: bold;")
                        self.version_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        self.version_label.setToolTip(t("gui_version_click_to_update", "Click to update"))
                        self.version_label.mousePressEvent = self._on_version_label_clicked_update
                    elif github_parts == local_parts:
                        # Up to date - GREEN
                        self.version_label.setText(f"v{self.script_version} (Lokal) → v{self.latest_github_version} (GitHub)")
                        self.version_label.setStyleSheet("color: #28a745;")
                        self.version_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        self.version_label.setToolTip(t("gui_version_up_to_date", "Version is up to date"))
                        self.version_label.mousePressEvent = self._on_version_label_clicked
                    else:
                        # Local is newer (shouldn't happen) - GREEN
                        self.version_label.setText(f"v{self.script_version} (Lokal) → v{self.latest_github_version} (GitHub)")
                        self.version_label.setStyleSheet("color: #28a745;")
                        self.version_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        self.version_label.setToolTip(t("gui_version_up_to_date", "Version is up to date"))
                        self.version_label.mousePressEvent = self._on_version_label_clicked
                except Exception as e:
                    self.version_label.setText(f"v{self.script_version} (Lokal)")
                    self.version_label.setStyleSheet("color: #666;")
                    self.version_label.setToolTip(f"Error: {e}")
        else:
            self.version_label.setText(f"v{self.script_version} (Lokal)")
            self.version_label.setStyleSheet("color: #666;")
            self.version_label.setToolTip(t("gui_version_check_tooltip", "Click to check for updates"))
            self.version_label.mousePressEvent = self._on_version_label_clicked
    
    def download_update(self):
        """Open download page for update"""
        self.open_github_releases()
    
    def _on_version_label_clicked(self, event):
        """Handle version label click - check for updates"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.check_version_manual()
        event.accept()
    
    def _on_version_label_clicked_update(self, event):
        """Handle version label click when update is available - open releases page"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_github_releases()
        event.accept()
    
    def _on_language_label_clicked(self, event):
        """Handle language label click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.switch_language()
        event.accept()
    
    def _on_theme_label_clicked(self, event):
        """Handle theme label click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.switch_theme()
        event.accept()
    
    def _on_changelog_label_clicked(self, event):
        """Handle changelog label click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_github_releases()
        event.accept()
    
    def _on_github_label_clicked(self, event):
        """Handle GitHub label click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_github()
        event.accept()

