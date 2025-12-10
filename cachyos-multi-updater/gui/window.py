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
    QMessageBox, QFileDialog, QDialog, QComboBox, QSizePolicy, QProgressDialog, QApplication,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QAbstractAnimation
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QMovie, QPixmap, QPainter, QTextCursor

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
        
        # Set script directory for debug logger (so logs go to logs/gui/)
        # Initialize logger immediately to ensure GUI logs are always created
        try:
            from .debug_logger import DebugLogger, get_logger
            DebugLogger.set_script_dir(str(self.script_dir))
            # Force logger initialization by getting it
            logger = get_logger()
            logger.info("GUI started")
        except Exception:
            pass  # Logger not critical
        
        self.config_manager = ConfigManager(str(self.script_dir))
        self.config = self.config_manager.load_config()
        self.update_runner = None
        self._last_was_dry_run = False  # Track if last operation was dry-run
        
        # Migrate VERSION file from script dir to root if needed
        self._migrate_version_file()
        
        self.script_version = self.get_script_version()
        self.is_updating = False
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(self.update_spinner)
        self.spinner_frame = 0
        self.version_checker = None
        self.latest_version = None
        self.latest_github_version = None
        self.version_thread = None
        self.language_feedback_timer = None  # Timer for language switcher feedback effect
        self.language_feedback_effect = None  # Current opacity effect for feedback
        self.language_feedback_restore_func = None  # Store restore function for disconnect
        self.language_feedback_original_effect = None  # Store original effect before feedback
        
        self.setWindowTitle(t("app_name", "CachyOS Multi-Updater"))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        self.init_ui()
        self.load_config()
        
        # Check for updates in background
        self.check_version_async()
    
    def _migrate_version_file(self):
        """Migrate VERSION file from script directory to root directory"""
        try:
            root_dir = self.script_dir.parent
            old_version_file = self.script_dir / "VERSION"
            new_version_file = root_dir / "VERSION"
            
            # If VERSION exists in script dir, move it to root
            if old_version_file.exists() and not new_version_file.exists():
                import shutil
                shutil.move(str(old_version_file), str(new_version_file))
                # Set permissions: 644
                new_version_file.chmod(0o644)
            
            # If VERSION doesn't exist in root, create it from update-all.sh
            if not new_version_file.exists():
                script_path = self.script_dir / "update-all.sh"
                if script_path.exists():
                    try:
                        import re
                        with open(script_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if 'readonly SCRIPT_VERSION=' in line:
                                    match = re.search(r'["\']([0-9.]+)["\']', line)
                                    if match:
                                        version = match.group(1)
                                        # Validate version format
                                        if re.match(r'^\d+\.\d+\.\d+$', version):
                                            with open(new_version_file, 'w', encoding='utf-8') as vf:
                                                vf.write(version + '\n')
                                            new_version_file.chmod(0o644)
                                            break
                    except Exception:
                        pass
        except Exception:
            # Migration failed, but don't crash - fallback to reading from update-all.sh
            pass
    
    def get_script_version(self):
        """Read script version from VERSION file (root), fallback to update-all.sh"""
        import re
        # First try: Read from VERSION file (root directory)
        root_dir = self.script_dir.parent
        version_file = root_dir / "VERSION"
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    # Validate version format (should be like "1.0.15")
                    if re.match(r'^\d+\.\d+\.\d+$', version):
                        return version
            except Exception:
                pass
        
        # Fallback: Read from update-all.sh
        script_path = self.script_dir / "update-all.sh"
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'readonly SCRIPT_VERSION=' in line:
                        match = re.search(r'["\']([0-9.]+)["\']', line)
                        if match:
                            version = match.group(1)
                            # Validate version format
                            if re.match(r'^\d+\.\d+\.\d+$', version):
                                return version
        except Exception:
            pass
        return "unknown"
    
    def _update_version_file_with_retry(self, version_file, version):
        """Update VERSION file with retry logic (3 attempts with exponential backoff)"""
        import time
        delays = [0.1, 0.2, 0.4]  # Exponential backoff: 100ms, 200ms, 400ms
        
        for attempt, delay in enumerate(delays, 1):
            try:
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(version + '\n')
                # Set permissions: 644
                version_file.chmod(0o644)
                return True
            except Exception as e:
                if attempt < len(delays):
                    # Wait before retry
                    time.sleep(delay)
                else:
                    # All attempts failed - log warning but don't fail update
                    try:
                        from .debug_logger import get_logger
                        logger = get_logger()
                        logger.warning(f"Failed to update VERSION file after {attempt} attempts: {e}")
                    except:
                        pass
                    QMessageBox.warning(
                        self,
                        t("gui_update_success", "Update Successful"),
                        t("gui_update_success_msg", "Script updated successfully!\n\nWarning: Failed to update VERSION file after multiple attempts. Please restart the application manually.")
                    )
                    return False
        return False
    
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
        
        # Language switcher with icon and text (horizontal layout)
        language_widget = QWidget()
        language_layout = QHBoxLayout()
        language_layout.setContentsMargins(6, 4, 6, 4)
        language_layout.setSpacing(6)
        language_widget.setLayout(language_layout)
        
        # Language icon
        self.language_icon_label = QLabel()
        self.language_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        language_layout.addWidget(self.language_icon_label)
        
        # Language text (pixel font style) - right of icon
        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            import os
            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"
        
        self.language_text_label = QLabel("DE" if current_lang == "de" else "EN")
        language_text_font = QFont("Courier", 9)
        language_text_font.setBold(True)
        self.language_text_label.setFont(language_text_font)
        self.language_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        language_layout.addWidget(self.language_text_label)
        
        # Update language icon and text colors (must be called after both labels are created)
        self.update_language_icon()
        
        # Make entire widget clickable
        language_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        language_widget.mousePressEvent = self._on_language_label_clicked
        language_widget.setToolTip(t("gui_switch_language", "Switch Language"))
        header_layout.addWidget(language_widget)
        
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
        # Use HTML entity for heart and style only the heart red
        copyright_text = "© 2025 Sunny C. - <a href='https://benjaro.info'>benjaro.info</a> | I <span style='color: #d32f2f;'>❤️</span> <a href='https://www.woltlab.com/en/'>WoltLab Suite</a>"
        copyright_label = QLabel(copyright_text)
        copyright_label.setOpenExternalLinks(True)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_font = QFont()
        copyright_font.setPointSize(8)
        copyright_label.setFont(copyright_font)
        # Don't set link color to red - only the heart should be red
        copyright_layout.addWidget(copyright_label)
        copyright_layout.addStretch()
        layout.addLayout(copyright_layout)
    
    def load_config(self):
        """Load config and update UI"""
        self.config = self.config_manager.load_config()
        
        # Update language icon and text
        if hasattr(self, 'update_language_icon'):
            self.update_language_icon()
        
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
        """View log files with separate dropdowns for update and GUI logs"""
        logs_base_dir = Path(self.script_dir) / "logs"
        update_log_dir = logs_base_dir / "update"
        gui_log_dir = logs_base_dir / "gui"
        
        # Check if log directories exist
        if not logs_base_dir.exists():
            QMessageBox.information(self, t("gui_no_logs", "No Logs"), t("gui_log_directory_not_found", "Log directory does not exist."))
            return
        
        # Get update log files
        update_log_files = []
        if update_log_dir.exists():
            update_log_files = sorted(update_log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Get GUI log files
        gui_log_files = []
        if gui_log_dir.exists():
            gui_log_files = sorted(gui_log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Check if any logs exist
        if not update_log_files and not gui_log_files:
            QMessageBox.information(self, t("gui_no_logs", "No Logs"), t("gui_no_logs", "No log files found."))
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
                log_text.setPlainText(t("gui_no_logs_found", "No log files found for this type."))
        
        def load_log(index):
            """Load selected log file"""
            log_type = type_combo.currentData()
            if log_type == "update":
                files = update_log_files
            else:
                files = gui_log_files
            
            if not files or index < 0 or index >= len(files):
                log_text.setPlainText(t("gui_no_logs_found", "No log files found for this type."))
                return
            
            log_path = files[index]
            log_text.clear()
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    log_text.setPlainText(f.read())
                # Auto-scroll to bottom
                cursor = log_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                log_text.setTextCursor(cursor)
            except Exception as e:
                log_text.setPlainText(f"Error reading log: {e}")
        
        # Connect signals
        type_combo.currentIndexChanged.connect(lambda: update_file_combo(type_combo.currentData()))
        file_combo.currentIndexChanged.connect(load_log)
        
        # Initialize with update logs
        update_file_combo("update")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Open log directory button
        icon, text = get_fa_icon('folder-open', t("gui_open_log_directory", "Open Log Directory"))
        open_dir_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(open_dir_btn)
        def open_log_directory():
            import subprocess
            import os
            # Try different methods to open directory, suppressing Qt warnings
            try:
                # Method 1: Use subprocess with environment that suppresses Qt warnings
                env = os.environ.copy()
                env['QT_LOGGING_RULES'] = 'qt.qpa.services.debug=false'
                # Use Popen with detached process to avoid Qt portal warnings
                subprocess.Popen(
                    ['xdg-open', str(logs_base_dir)],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            except Exception:
                # Fallback: Show directory path in message box
                QMessageBox.information(
                    self,
                    t("gui_info", "Info"),
                    t("gui_log_directory", "Log Directory:") + f"\n{logs_base_dir}"
                )
        open_dir_btn.clicked.connect(open_log_directory)
        button_layout.addWidget(open_dir_btn)
        
        # Close button
        icon, text = get_fa_icon('times', t("gui_close", "Close"))
        close_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(close_btn)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
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
        self.update_changelog_icon()
        self.update_language_icon()
    
    def update_changelog_icon(self):
        """Update Changelog icon color based on current theme"""
        from theme_manager import ThemeManager
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = current_theme
        
        # Choose color based on theme (CachyOS colors - white for dark, black for light)
        icon_color = "#000000" if actual_theme == "light" else "#ffffff"
        
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
        
        # Get current theme for icon color
        try:
            from .theme_manager import ThemeManager
        except ImportError:
            from theme_manager import ThemeManager
        
        theme_mode = self.config_manager.get("GUI_THEME", "auto")
        if theme_mode == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = theme_mode
        
        # Set icon color based on theme (CachyOS colors)
        icon_color = "#ffffff" if actual_theme == "dark" else "#000000"
        
        icon, text = get_fa_icon(icon_name, "", size=18, color=icon_color)
        if icon:
            pixmap = icon.pixmap(20, 20)
            self.theme_label.setPixmap(pixmap)
        else:
            self.theme_label.setText(FA_ICONS.get(icon_name, ''))
            fa_font = QFont("FontAwesome", 16)
            self.theme_label.setFont(fa_font)
            self.theme_label.setStyleSheet(f"color: {icon_color};")
        
        self.theme_label.setToolTip(f"{t('gui_switch_theme', 'Switch Theme')} ({tooltip})")
    
    def update_language_icon(self):
        """Update language icon and text based on current language"""
        # Check if widgets exist
        if not hasattr(self, 'language_icon_label') or self.language_icon_label is None:
            return
        
        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            import os
            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"
        
        # Get current theme for icon color
        try:
            from .theme_manager import ThemeManager
        except ImportError:
            from theme_manager import ThemeManager
        
        theme_mode = self.config_manager.get("GUI_THEME", "auto")
        if theme_mode == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = theme_mode
        
        # Set icon color based on theme (CachyOS colors)
        icon_color = "#ffffff" if actual_theme == "dark" else "#000000"
        text_color = "#ffffff" if actual_theme == "dark" else "#000000"
        
        # Use language icon
        icon, text = get_fa_icon('language', "", size=18, color=icon_color)
        if icon:
            pixmap = icon.pixmap(20, 20)
            self.language_icon_label.setPixmap(pixmap)
        else:
            self.language_icon_label.setText(FA_ICONS.get('language', '🌐'))
            fa_font = QFont("FontAwesome", 16)
            self.language_icon_label.setFont(fa_font)
            self.language_icon_label.setStyleSheet(f"color: {icon_color};")
        
        # Update text label with explicit color
        if hasattr(self, 'language_text_label') and self.language_text_label is not None:
            self.language_text_label.setText("DE" if current_lang == "de" else "EN")
            self.language_text_label.setStyleSheet(f"color: {text_color};")
        
        # Update tooltip
        lang_name = "Deutsch" if current_lang == "de" else "English"
        parent = self.language_icon_label.parent()
        if parent:
            parent.setToolTip(f"{t('gui_switch_language', 'Switch Language')} ({lang_name})")
    
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
        
        # Update language icon and text first (before UI update to avoid conflicts)
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
        # Language switcher tooltip is updated in update_language_icon()
        if hasattr(self, 'language_icon_label') and self.language_icon_label is not None:
            parent = self.language_icon_label.parent()
            if parent:
                current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
                if current_lang == "auto":
                    import os
                    lang = os.environ.get("LANG", "en_US.UTF-8")
                    lang = lang.split("_")[0].split(".")[0].lower()
                    current_lang = "de" if lang == "de" else "en"
                lang_name = "Deutsch" if current_lang == "de" else "English"
                parent.setToolTip(f"{t('gui_switch_language', 'Switch Language')} ({lang_name})")
        
        current_theme = self.config_manager.get("GUI_THEME", "auto")
        if current_theme == "light":
            tooltip = t("gui_theme_light", "Light")
        elif current_theme == "dark":
            tooltip = t("gui_theme_dark", "Dark")
        else:
            tooltip = t("gui_theme_auto", "Automatic (System)")
        if hasattr(self, 'theme_label') and self.theme_label is not None:
            self.theme_label.setToolTip(f"{t('gui_switch_theme', 'Switch Theme')} ({tooltip})")
        if hasattr(self, 'github_label') and self.github_label is not None:
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
    
    def check_updates(self):
        """Check for available updates (dry-run mode)"""
        # Initialize debug logger to ensure it's available
        try:
            from .debug_logger import get_logger
            logger = get_logger()
            logger.info("=" * 80)
            logger.info("Starting update check (dry-run)")
            logger.info(f"Script directory: {self.script_dir}")
            logger.info(f"Log file: {logger.get_log_file()}")
            logger.info("=" * 80)
        except Exception:
            pass  # Logger not critical
        
        if self.is_updating:
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_already_running", "Another update is already in progress.\n\nPlease wait for it to complete.")
            )
            return
        
        # Check if update-all.sh exists
        script_path = self.script_dir / "update-all.sh"
        if not script_path.exists():
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_script_not_found", "update-all.sh not found in:\n{script_dir}").format(script_dir=self.script_dir)
            )
            return
        
        # Start update runner in dry-run mode
        try:
            # Import UpdateRunner with fallback for relative/absolute imports
            try:
                from .update_runner import UpdateRunner
            except ImportError:
                from update_runner import UpdateRunner
            
            from PyQt6.QtCore import QProcess
            
            # Create or reuse UpdateRunner
            if self.update_runner is None:
                # Create UpdateRunner as child of MainWindow to ensure proper Qt lifecycle
                self.update_runner = UpdateRunner(str(self.script_dir), self.config, parent=self)
                self.update_runner.output_received.connect(self.on_output_received)
                self.update_runner.progress_update.connect(self.on_progress_update)
                self.update_runner.error_occurred.connect(self.on_error_occurred)
                self.update_runner.finished.connect(self.on_update_finished)
            else:
                # Reuse existing runner - stop process if running
                if hasattr(self.update_runner, 'process') and self.update_runner.process:
                    if self.update_runner.process.state() != QProcess.ProcessState.NotRunning:
                        self.update_runner.process.kill()
                        self.update_runner.process.waitForFinished(1000)
            
            # Clear output and reset progress bar
            self.output_text.clear()
            self.output_text.append(t("gui_checking_updates", "Checking for updates..."))
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            if hasattr(self, 'status_label'):
                self.status_label.setText("0%")
                self.status_label.setVisible(True)
            
            # Start in dry-run mode (no sudo password needed for dry-run)
            self._last_was_dry_run = True  # Mark as dry-run
            self.update_runner.start_update(dry_run=True, interactive=False, sudo_password=None)
            
            # Update UI
            self.is_updating = True
            self.btn_check.setEnabled(False)
            self.btn_start.setEnabled(False)
            if hasattr(self, 'btn_stop'):
                self.btn_stop.setEnabled(True)
                self.btn_stop.setVisible(True)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(e))
            )
    
    def start_updates(self):
        """Start the update process"""
        if self.is_updating:
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_already_running", "Another update is already in progress.\n\nPlease wait for it to complete.")
            )
            return
        
        # Check if update-all.sh exists
        script_path = self.script_dir / "update-all.sh"
        if not script_path.exists():
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_script_not_found", "update-all.sh not found in:\n{script_dir}").format(script_dir=self.script_dir)
            )
            return
        
        # Show confirmation dialog
        try:
            try:
                from .update_confirmation_dialog import UpdateConfirmationDialog
            except ImportError:
                from update_confirmation_dialog import UpdateConfirmationDialog
            dialog = UpdateConfirmationDialog(self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
        except ImportError:
            # Fallback if dialog not available
            reply = QMessageBox.question(
                self,
                t("gui_start_updates", "Start Updates"),
                t("gui_start_updates_now", "Updates are available. Do you want to start the update process now?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Ask for sudo password if needed
        try:
            from .sudo_dialog import SudoDialog
        except ImportError:
            from sudo_dialog import SudoDialog
        
        sudo_dialog = SudoDialog(self)
        if sudo_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        sudo_password = sudo_dialog.get_password()
        if not sudo_password:
            return
        
        # Start update runner
        try:
            # Import UpdateRunner with fallback for relative/absolute imports
            try:
                from .update_runner import UpdateRunner
            except ImportError:
                from update_runner import UpdateRunner
            
            from PyQt6.QtCore import QProcess
            
            # Create or reuse UpdateRunner
            if self.update_runner is None:
                # Create UpdateRunner as child of MainWindow to ensure proper Qt lifecycle
                self.update_runner = UpdateRunner(str(self.script_dir), self.config, parent=self)
                self.update_runner.output_received.connect(self.on_output_received)
                self.update_runner.progress_update.connect(self.on_progress_update)
                self.update_runner.error_occurred.connect(self.on_error_occurred)
                self.update_runner.finished.connect(self.on_update_finished)
            else:
                # Reuse existing runner - stop process if running
                if hasattr(self.update_runner, 'process') and self.update_runner.process:
                    if self.update_runner.process.state() != QProcess.ProcessState.NotRunning:
                        self.update_runner.process.kill()
                        self.update_runner.process.waitForFinished(1000)
            
            # Clear output and reset progress bar
            self.output_text.clear()
            self.output_text.append(t("gui_starting_updates", "Starting updates..."))
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            if hasattr(self, 'status_label'):
                self.status_label.setText("0%")
                self.status_label.setVisible(True)
            
            # Start update
            self._last_was_dry_run = False  # Mark as real update
            self.update_runner.start_update(dry_run=False, interactive=False, sudo_password=sudo_password)
            
            # Update UI
            self.is_updating = True
            self.btn_check.setEnabled(False)
            self.btn_start.setEnabled(False)
            if hasattr(self, 'btn_stop'):
                self.btn_stop.setEnabled(True)
                self.btn_stop.setVisible(True)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(e))
            )
    
    def stop_updates(self):
        """Stop the running update process"""
        if self.update_runner and self.update_runner.process:
            self.update_runner.process.kill()
            self.update_runner.process.waitForFinished(1000)
            self.output_text.append("\n" + t("gui_update_stopped", "Update stopped by user."))
        
        # Reset UI
        self.is_updating = False
        self.btn_check.setEnabled(True)
        self.btn_start.setEnabled(True)
        if hasattr(self, 'btn_stop'):
            self.btn_stop.setEnabled(False)
            self.btn_stop.setVisible(False)
    
    def on_output_received(self, text: str):
        """Handle output from update runner"""
        # Filter out console-specific prompts that are confusing in GUI
        # These are only relevant for console version
        filtered_patterns = [
            "Drücke Enter",
            "Press Enter",
            "Enter um das Fenster",
            "Enter to close",
            "zum Beenden",
            "to close",
            "read -r -p",
        ]
        
        # Check if line contains any of the filtered patterns
        should_filter = any(pattern.lower() in text.lower() for pattern in filtered_patterns)
        
        if not should_filter:
            self.output_text.append(text)
            # Auto-scroll to bottom
            cursor = self.output_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.output_text.setTextCursor(cursor)
    
    def on_error_occurred(self, error_msg: str):
        """Handle error from update runner"""
        QMessageBox.critical(
            self,
            t("gui_error", "Error"),
            t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=error_msg)
        )
        # Reset UI
        self.is_updating = False
        self.btn_check.setEnabled(True)
        self.btn_start.setEnabled(True)
        if hasattr(self, 'btn_stop'):
            self.btn_stop.setEnabled(False)
            self.btn_stop.setVisible(False)
    
    def on_update_finished(self, exit_code: int):
        """Handle update completion"""
        # Reset UI state first (before showing dialog)
        self.is_updating = False
        self.btn_check.setEnabled(True)
        self.btn_start.setEnabled(True)
        if hasattr(self, 'btn_stop'):
            self.btn_stop.setEnabled(False)
            self.btn_stop.setVisible(False)
        
        if exit_code == 0:
            if self._last_was_dry_run:
                # Dry-run completed - show different message
                self.output_text.append("\n" + t("gui_check_completed", "Update check completed successfully!"))
                # Set progress to 100% on success
                self.progress_bar.setValue(100)
                if hasattr(self, 'status_label'):
                    self.status_label.setText("100%")
                # Show success message dialog for dry-run with option to start update
                reply = QMessageBox.question(
                    self,
                    t("gui_check_success", "Update Check Completed"),
                    t("gui_check_completed", "Update check completed successfully!") + "\n\n" +
                    t("gui_start_updates_now", "Updates are available. Do you want to start the update process now?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # User wants to start update - call start_updates()
                    # Note: UI state is already reset, so start_updates() can proceed
                    self.start_updates()
            else:
                # Real update completed
                self.output_text.append("\n" + t("gui_update_completed", "Update completed successfully!"))
                # Set progress to 100% on success
                self.progress_bar.setValue(100)
                if hasattr(self, 'status_label'):
                    self.status_label.setText("100%")
                # Show success message dialog
                QMessageBox.information(
                    self,
                    t("gui_update_success", "Update Successful"),
                    t("gui_update_completed", "Update completed successfully!")
                )
        else:
            self.output_text.append("\n" + t("gui_update_failed", "Update failed with exit code: {code}").format(code=exit_code))
            # Show error message dialog
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_failed", "Update failed with exit code: {code}").format(code=exit_code)
            )
    
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
        """Handle version label click when update is available - perform automatic update"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Ask user for confirmation
            reply = QMessageBox.question(
                self,
                t("gui_update_available", "Update Available"),
                t("gui_update_confirm", "Update to version {version} is available.\n\nDo you want to update now?").format(version=self.latest_github_version),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.perform_automatic_update()
        event.accept()
    
    def perform_automatic_update(self):
        """Perform automatic update via git pull or ZIP download"""
        # Get root directory (parent of cachyos-multi-updater/)
        # script_dir is cachyos-multi-updater/, so parent is root
        root_dir = self.script_dir.parent
        
        # HIGH-1 FIX: Atomically create lock file to prevent race conditions
        # Use same mechanism as update-all.sh: create lock directory atomically
        import os
        lock_file = self.script_dir / ".update-all.lock"
        lock_dir = self.script_dir / ".update-all.lock.d"
        
        # Try to create lock directory atomically (mkdir is atomic)
        try:
            lock_dir.mkdir(exist_ok=False)
            # Success: We got the lock atomically
            try:
                # Write our PID to lock file
                with open(lock_file, 'w') as f:
                    f.write(str(os.getpid()))
                # Remove lock directory (lock file is now the indicator)
                lock_dir.rmdir()
                # Bug 1 FIX: Store lock file path immediately after successful creation
                # This ensures cleanup works even if early returns occur
                self.update_lock_file = lock_file
            except Exception as lock_error:
                # Cleanup on error
                try:
                    if lock_file.exists():
                        lock_file.unlink()
                except Exception:
                    pass
                try:
                    if lock_dir.exists():
                        lock_dir.rmdir()
                except Exception:
                    pass
                QMessageBox.warning(
                    self,
                    t("gui_update_failed", "Update Failed"),
                    t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(lock_error))
                )
                return
        except FileExistsError:
            # Lock directory exists - another process is updating
            # Check if lock file exists and process is still running
            if lock_file.exists():
                try:
                    with open(lock_file, 'r') as f:
                        lock_pid = f.read().strip()
                    if lock_pid:
                        try:
                            # Check if process is still running (signal 0 = check only)
                            os.kill(int(lock_pid), 0)
                            # Process is running - update already in progress
                            QMessageBox.warning(
                                self,
                                t("gui_update_failed", "Update Failed"),
                                t("gui_update_already_running", "Another update is already in progress.\n\nPlease wait for it to complete.")
                            )
                            return
                        except (OSError, ValueError, ProcessLookupError):
                            # Process not running - stale lock file, remove and retry
                            try:
                                lock_file.unlink()
                            except Exception:
                                pass
                            try:
                                if lock_dir.exists():
                                    lock_dir.rmdir()
                            except Exception:
                                pass
                            # Retry lock creation
                            try:
                                lock_dir.mkdir(exist_ok=False)
                                with open(lock_file, 'w') as f:
                                    f.write(str(os.getpid()))
                                # Bug 1 FIX: Store lock file path BEFORE rmdir() to ensure cleanup
                                # If rmdir() fails, we still need to clean up the lock file
                                self.update_lock_file = lock_file
                                lock_dir.rmdir()
                            except FileExistsError:
                                # Another process was faster - give up
                                # Cleanup lock file if it was created
                                if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                                    try:
                                        self.update_lock_file.unlink()
                                    except Exception:
                                        pass
                                QMessageBox.warning(
                                    self,
                                    t("gui_update_failed", "Update Failed"),
                                    t("gui_update_already_running", "Another update is already in progress.\n\nPlease wait for it to complete.")
                                )
                                return
                            except Exception as retry_error:
                                # Bug 1 FIX: Cleanup lock file if creation partially succeeded
                                # lock_file was written but rmdir() failed - clean up orphaned file
                                if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                                    try:
                                        self.update_lock_file.unlink()
                                    except Exception:
                                        pass
                                QMessageBox.warning(
                                    self,
                                    t("gui_update_failed", "Update Failed"),
                                    t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(retry_error))
                                )
                                return
                except Exception:
                    # Can't read lock file - assume stale, remove and retry
                    try:
                        if lock_file.exists():
                            lock_file.unlink()
                    except Exception:
                        pass
                    try:
                        if lock_dir.exists():
                            lock_dir.rmdir()
                    except Exception:
                        pass
                    # Retry lock creation
                    try:
                        lock_dir.mkdir(exist_ok=False)
                        with open(lock_file, 'w') as f:
                            f.write(str(os.getpid()))
                        # Bug 1 FIX: Store lock file path BEFORE rmdir() to ensure cleanup
                        # If rmdir() fails, we still need to clean up the lock file
                        self.update_lock_file = lock_file
                        lock_dir.rmdir()
                    except FileExistsError:
                        # Another process was faster - give up
                        # Cleanup lock file if it was created
                        if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                            try:
                                self.update_lock_file.unlink()
                            except Exception:
                                pass
                        QMessageBox.warning(
                            self,
                            t("gui_update_failed", "Update Failed"),
                            t("gui_update_already_running", "Another update is already in progress.\n\nPlease wait for it to complete.")
                        )
                        return
                    except Exception as retry_error:
                        # Bug 1 FIX: Cleanup lock file if creation partially succeeded
                        # lock_file was written but rmdir() failed - clean up orphaned file
                        if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                            try:
                                self.update_lock_file.unlink()
                            except Exception:
                                pass
                        QMessageBox.warning(
                            self,
                            t("gui_update_failed", "Update Failed"),
                            t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(retry_error))
                        )
                        return
            else:
                # Lock directory exists but no lock file - remove directory and retry
                try:
                    lock_dir.rmdir()
                except Exception:
                    pass
                # Retry lock creation
                try:
                    lock_dir.mkdir(exist_ok=False)
                    with open(lock_file, 'w') as f:
                        f.write(str(os.getpid()))
                    # Bug 1 FIX: Store lock file path BEFORE rmdir() to ensure cleanup
                    # If rmdir() fails, we still need to clean up the lock file
                    self.update_lock_file = lock_file
                    lock_dir.rmdir()
                except FileExistsError:
                    # Another process was faster - give up
                    # Cleanup lock file if it was created
                    if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                        try:
                            self.update_lock_file.unlink()
                        except Exception:
                            pass
                    QMessageBox.warning(
                        self,
                        t("gui_update_failed", "Update Failed"),
                        t("gui_update_already_running", "Another update is already in progress.\n\nPlease wait for it to complete.")
                    )
                    return
                except Exception as retry_error:
                    # Bug 1 FIX: Cleanup lock file if creation partially succeeded
                    # lock_file was written but rmdir() failed - clean up orphaned file
                    if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                        try:
                            self.update_lock_file.unlink()
                        except Exception:
                            pass
                    QMessageBox.warning(
                        self,
                        t("gui_update_failed", "Update Failed"),
                        t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(retry_error))
                    )
                    return
        except Exception as lock_error:
            # Unexpected error creating lock
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(lock_error))
            )
            return
        
        # Bug 1 FIX: Lock file path is already stored during creation (see above)
        # This line is kept for clarity, but the assignment happens earlier
        if not hasattr(self, 'update_lock_file'):
            self.update_lock_file = lock_file
        
        # Check if .git exists in root - use git pull if available
        if (root_dir / ".git").exists():
            self.perform_git_update(root_dir)
        else:
            # No git repo - download ZIP and extract
            self.perform_zip_update(root_dir)
    
    def perform_git_update(self, root_dir):
        """Perform update via git pull"""
        import subprocess
        
        # Create progress dialog with cancel button
        progress = QProgressDialog(
            t("gui_update_in_progress", "Updating script...\n\nPlease wait..."),
            t("gui_cancel", "Cancel"),  # Cancel button
            0, 0,  # Indeterminate progress
            self
        )
        progress.setWindowTitle(t("gui_updating", "Updating"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)  # Show immediately
        progress.setValue(0)
        progress.show()
        
        # Track if update was cancelled
        update_cancelled = False
        
        def on_cancel():
            nonlocal update_cancelled
            update_cancelled = True
            progress.setLabelText(t("gui_update_cancelling", "Cancelling update..."))
        
        progress.canceled.connect(on_cancel)
        
        # Force update to show dialog
        QApplication.processEvents()
        
        try:
            # Check for cancellation before starting
            if update_cancelled:
                progress.close()
                QMessageBox.information(
                    self,
                    t("gui_update_cancelled", "Update Cancelled"),
                    t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                )
                return
            
            # Get current commit hash before pull (locale-independent method)
            before_hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(root_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            before_hash = before_hash_result.stdout.strip() if before_hash_result.returncode == 0 else None
            
            # MED-2: Fallback if hash check fails (e.g., detached HEAD)
            if before_hash is None:
                # Try to get current branch and commit
                branch_result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=str(root_dir),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if branch_result.returncode == 0:
                    # We have a branch, but hash failed - use branch name as identifier
                    before_hash = branch_result.stdout.strip()
            
            # Change to root directory and run git pull
            # Check for cancellation during operation
            if update_cancelled:
                progress.close()
                QMessageBox.information(
                    self,
                    t("gui_update_cancelled", "Update Cancelled"),
                    t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                )
                return
            
            result = subprocess.run(
                ['git', 'pull'],
                cwd=str(root_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check for cancellation after pull
            if update_cancelled:
                progress.close()
                # Git pull is idempotent, but we should inform user
                QMessageBox.information(
                    self,
                    t("gui_update_cancelled", "Update Cancelled"),
                    t("gui_update_cancelled_after_pull", "Update was cancelled after git pull completed.\n\nChanges may have been applied. Please check manually.")
                )
                return
            
            # Get commit hash after pull
            after_hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(root_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            after_hash = after_hash_result.stdout.strip() if after_hash_result.returncode == 0 else None
            
            # MED-2: Fallback if hash check fails
            if after_hash is None:
                branch_result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=str(root_dir),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if branch_result.returncode == 0:
                    after_hash = branch_result.stdout.strip()
            
            # Check if anything was actually updated by comparing commit hashes
            # This is locale-independent and works regardless of git language
            was_updated = (before_hash is not None and after_hash is not None and before_hash != after_hash)
            
            # MED-2: If hash comparison fails, check git pull output for changes
            if not was_updated and result.returncode == 0 and result.stdout:
                pull_output = result.stdout.strip()
                # Look for indicators of changes (works in any language)
                was_updated = any(keyword in pull_output.lower() for keyword in [
                    "updating", "fast-forward", "merge", "changed", "insertion", "deletion"
                ]) and "already up to date" not in pull_output.lower()
            
            # Close progress dialog
            progress.close()
            
            # Show output in message
            output_lines = []
            if result.stdout:
                output_lines.append("Output:")
                output_lines.append(result.stdout)
            if result.stderr:
                output_lines.append("\nErrors:")
                output_lines.append(result.stderr)
            
            output_text = "\n".join(output_lines) if output_lines else t("gui_no_output", "No output")
            
            if result.returncode == 0:
                
                # Update script_version and version label if update was successful
                if was_updated:
                    github_version = self.latest_github_version
                    if github_version:
                        # Update script_version
                        self.script_version = github_version
                        # Update version label
                        self.update_version_label()
                
                success_msg = t("gui_update_success_msg", "Script updated successfully!\n\nPlease restart the application to use the new version.")
                if output_text and output_text != t("gui_no_output", "No output"):
                    success_msg += f"\n\n{output_text}"
                
                # Ask if user wants to restart now
                if was_updated:
                    reply = QMessageBox.question(
                        self,
                        t("gui_update_success", "Update Successful"),
                        success_msg + "\n\n" + t("gui_restart_now", "Do you want to restart the application now?"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.restart_application()
                    else:
                        QMessageBox.information(
                            self,
                            t("gui_update_success", "Update Successful"),
                            success_msg
                        )
                else:
                    QMessageBox.information(
                        self,
                        t("gui_update_success", "Update Successful"),
                        t("gui_already_up_to_date", "Script is already up to date.\n\nNo changes were made.")
                    )
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                if not error_msg:
                    error_msg = t("gui_update_unknown_error", "Unknown error occurred")
                
                QMessageBox.warning(
                    self,
                    t("gui_update_failed", "Update Failed"),
                    t("gui_update_failed_msg", "Failed to update script:\n\n{error}\n\nPlease update manually via git pull.").format(error=error_msg)
                )
        except subprocess.TimeoutExpired:
            progress.close()
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_timeout", "Update timed out. Please try again or update manually.")
            )
        except Exception as e:
            progress.close()
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_error", "Error during update:\n\n{error}\n\nPlease update manually via git pull.").format(error=str(e))
            )
        finally:
            # HIGH-1 FIX: Always cleanup lock file
            if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                try:
                    self.update_lock_file.unlink()
                except Exception:
                    pass
    
    def perform_zip_update(self, root_dir):
        """Perform update by downloading ZIP from GitHub"""
        import subprocess
        import tempfile
        import shutil
        import zipfile
        import time
        import os
        from urllib.request import urlretrieve
        from pathlib import Path
        
        progress = None
        progress_closed = False  # Track if progress dialog was closed
        
        try:
            # Get latest version
            if not self.latest_github_version:
                QMessageBox.warning(
                    self,
                    t("gui_update_failed", "Update Failed"),
                    t("gui_zip_version_check_failed", "Could not determine latest version.\n\nPlease update manually.")
                )
                return
            
            # Create progress dialog with cancel button
            progress = QProgressDialog(
                t("gui_downloading_update", "Downloading update...\n\nPlease wait..."),
                t("gui_cancel", "Cancel"),  # Cancel button
                0, 0,  # Indeterminate progress
                self
            )
            progress.setWindowTitle(t("gui_updating", "Updating"))
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            # Track if update was cancelled
            update_cancelled = False
            
            def on_cancel():
                nonlocal update_cancelled
                update_cancelled = True
                progress.setLabelText(t("gui_update_cancelling", "Cancelling update..."))
            
            # Bug 1 FIX: Connect signal handler BEFORE processEvents() to ensure
            # cancellation clicks are handled immediately when dialog is shown
            progress.canceled.connect(on_cancel)
            
            # Force update to show dialog (after signal connection)
            QApplication.processEvents()
            
            # MED-1: Check network availability before downloading
            try:
                import socket
                # Bug 1 FIX: Close socket after connection check to prevent resource leak
                sock = socket.create_connection(("8.8.8.8", 53), timeout=3)
                sock.close()
            except (OSError, socket.error):
                QMessageBox.warning(
                    self,
                    t("gui_update_failed", "Update Failed"),
                    t("gui_no_network", "No network connection available.\n\nPlease check your internet connection and try again.")
                )
                progress.close()
                return
            
            # Download ZIP from GitHub
            github_repo = self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater")
            zip_url = f"https://github.com/{github_repo}/archive/refs/heads/main.zip"
            
            # Create temp directory (initialize to None for cleanup tracking)
            temp_dir = None
            zip_file = None
            backup_dir = None  # Track backup directory for rollback
            old_target_dir = None  # Track old directory after atomic swap
            
            try:
                # Create temp directory
                temp_dir = Path(tempfile.mkdtemp(prefix="cachyos-updater-"))
                zip_file = temp_dir / "update.zip"
            except Exception as temp_error:
                # If temp directory creation fails, show error and return
                QMessageBox.warning(
                    self,
                    t("gui_update_failed", "Update Failed"),
                    t("gui_zip_update_failed", "Failed to update via ZIP download:\n\n{error}\n\nPlease update manually from GitHub.").format(error=str(temp_error))
                )
                return
            
            try:
                # Check for cancellation before starting download
                if update_cancelled:
                    progress.close()
                    # Bug 1: Cleanup temp_dir before returning
                    if temp_dir and temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    QMessageBox.information(
                        self,
                        t("gui_update_cancelled", "Update Cancelled"),
                        t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                    )
                    return
                
                # Download ZIP with retry logic (MED-1)
                progress.setLabelText(t("gui_downloading_zip", "Downloading ZIP archive..."))
                QApplication.processEvents()
                
                max_retries = 3
                retry_count = 0
                download_success = False
                
                while retry_count < max_retries and not download_success:
                    if update_cancelled:
                        progress.close()
                        # Bug 1: Cleanup temp_dir before returning
                        if temp_dir and temp_dir.exists():
                            shutil.rmtree(temp_dir, ignore_errors=True)
                        QMessageBox.information(
                            self,
                            t("gui_update_cancelled", "Update Cancelled"),
                            t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                        )
                        return
                    
                    try:
                        urlretrieve(zip_url, str(zip_file))
                        download_success = True
                    except Exception as download_error:
                        retry_count += 1
                        if retry_count < max_retries:
                            progress.setLabelText(
                                t("gui_download_retry", "Download failed, retrying... ({retry}/{max})").format(
                                    retry=retry_count, max=max_retries
                                )
                            )
                            QApplication.processEvents()
                            import time
                            time.sleep(2)  # Wait 2 seconds before retry
                        else:
                            raise download_error
                
                # Check for cancellation before extraction
                if update_cancelled:
                    progress.close()
                    # Cleanup downloaded file
                    if zip_file and zip_file.exists():
                        zip_file.unlink()
                    # Bug 1: Cleanup temp_dir before returning
                    if temp_dir and temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    QMessageBox.information(
                        self,
                        t("gui_update_cancelled", "Update Cancelled"),
                        t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                    )
                    return
                
                # Extract ZIP
                progress.setLabelText(t("gui_extracting_zip", "Extracting files..."))
                QApplication.processEvents()
                
                extract_dir = temp_dir / "extracted"
                with zipfile.ZipFile(str(zip_file), 'r') as zip_ref:
                    zip_ref.extractall(str(extract_dir))
                
                # Check for cancellation after extraction
                if update_cancelled:
                    progress.close()
                    # Cleanup extracted files
                    if extract_dir.exists():
                        shutil.rmtree(extract_dir, ignore_errors=True)
                    # Bug 1: Cleanup temp_dir before returning
                    if temp_dir and temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    QMessageBox.information(
                        self,
                        t("gui_update_cancelled", "Update Cancelled"),
                        t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                    )
                    return
                
                # Find the extracted directory (usually repo-name-main)
                extracted_dirs = list(extract_dir.iterdir())
                if not extracted_dirs:
                    raise Exception("No files extracted from ZIP")
                
                source_dir = extracted_dirs[0]  # Should be sc-cachyos-multi-updater-main
                
                # Copy files from extracted ZIP to current directory
                progress.setLabelText(t("gui_copying_files", "Copying files..."))
                QApplication.processEvents()
                
                # Copy cachyos-multi-updater directory
                source_project_dir = source_dir / "cachyos-multi-updater"
                if source_project_dir.exists():
                    target_dir = root_dir / "cachyos-multi-updater"
                    
                    # Bug 1 FIX: Initialize temp_target_dir before inner try block
                    # This ensures it's always defined for exception handlers
                    temp_target_dir = None
                    old_target_dir = None  # Also initialize for consistency
                    
                    # CRIT-1: Use atomic swap instead of delete + copy to avoid file locking issues
                    # Create new directory with temporary name first
                    temp_target_dir = root_dir / f"cachyos-multi-updater.new.{int(time.time())}"
                    
                    # Backup current directory before making changes
                    if target_dir.exists():
                        backup_dir = root_dir / f"cachyos-multi-updater.backup.{int(time.time())}"
                        shutil.copytree(target_dir, backup_dir, dirs_exist_ok=True)
                    
                    try:
                        # Check for cancellation before copying
                        if update_cancelled:
                            progress.close()
                            # Bug 2 FIX: Rollback behavior depends on whether backup exists
                            # If backup exists: restore from backup (update scenario)
                            # If no backup: no restoration needed (fresh installation scenario)
                            if backup_dir and backup_dir.exists():
                                # Update scenario: restore from backup
                                if target_dir.exists():
                                    shutil.rmtree(target_dir, ignore_errors=True)
                                shutil.copytree(backup_dir, target_dir)
                                shutil.rmtree(backup_dir, ignore_errors=True)
                                cancel_msg = t("gui_update_cancelled_rollback", "Update was cancelled.\n\nOriginal installation has been restored.")
                            else:
                                # Fresh installation scenario: no backup to restore
                                cancel_msg = t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                            # Bug 1: Cleanup temp_dir before returning
                            if temp_dir and temp_dir.exists():
                                shutil.rmtree(temp_dir, ignore_errors=True)
                            QMessageBox.information(
                                self,
                                t("gui_update_cancelled", "Update Cancelled"),
                                cancel_msg
                            )
                            return
                        
                        # Copy new files to temporary directory
                        shutil.copytree(source_project_dir, temp_target_dir)
                        
                        # Check for cancellation after copying
                        if update_cancelled:
                            progress.close()
                            # Rollback: restore backup if it exists
                            if backup_dir and backup_dir.exists():
                                if target_dir.exists():
                                    shutil.rmtree(target_dir, ignore_errors=True)
                                shutil.copytree(backup_dir, target_dir)
                                shutil.rmtree(backup_dir, ignore_errors=True)
                                cancel_msg = t("gui_update_cancelled_rollback", "Update was cancelled.\n\nOriginal installation has been restored.")
                            else:
                                # Fresh installation scenario: no backup to restore
                                cancel_msg = t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                            # Bug 2 FIX: Always cleanup temp_target_dir regardless of backup_dir existence
                            if temp_target_dir and temp_target_dir.exists():
                                shutil.rmtree(temp_target_dir, ignore_errors=True)
                            # Bug 1: Cleanup temp_dir before returning
                            if temp_dir and temp_dir.exists():
                                shutil.rmtree(temp_dir, ignore_errors=True)
                            QMessageBox.information(
                                self,
                                t("gui_update_cancelled", "Update Cancelled"),
                                cancel_msg
                            )
                            return
                        
                        # HIGH-2: Set correct permissions for executable files
                        executable_files = [
                            "update-all.sh",
                            "setup.sh",
                            "cachyos-update",
                            "cachyos-update-gui",
                            "run-update.sh"
                        ]
                        for exec_file in executable_files:
                            exec_path = temp_target_dir / exec_file
                            if exec_path.exists():
                                os.chmod(exec_path, 0o755)
                        
                        # Also set permissions for scripts in subdirectories
                        for script_dir_name in ["lib", "gui"]:
                            script_dir_path = temp_target_dir / script_dir_name
                            if script_dir_path.exists():
                                for item in script_dir_path.rglob("*.sh"):
                                    if item.is_file():
                                        os.chmod(item, 0o755)
                                for item in script_dir_path.rglob("*.py"):
                                    if item.is_file():
                                        # Python scripts should be readable and executable
                                        os.chmod(item, 0o755)
                        
                        # Copy root files (README, LICENSE, etc.) to temp directory's parent
                        # These will be copied to root_dir after atomic swap
                        root_files_to_copy = []
                        for item in source_dir.iterdir():
                            if item.is_file() and item.name not in ['.gitignore', 'README.md', 'README.de.md']:
                                # Skip files that might overwrite user configs
                                if item.name == 'config.conf':
                                    continue
                                root_files_to_copy.append(item)
                        
                        # Check for cancellation before atomic swap
                        if update_cancelled:
                            progress.close()
                            # Rollback: restore backup if it exists
                            if backup_dir and backup_dir.exists():
                                if target_dir.exists():
                                    shutil.rmtree(target_dir, ignore_errors=True)
                                shutil.copytree(backup_dir, target_dir)
                                shutil.rmtree(backup_dir, ignore_errors=True)
                                cancel_msg = t("gui_update_cancelled_rollback", "Update was cancelled.\n\nOriginal installation has been restored.")
                            else:
                                # Fresh installation scenario: no backup to restore
                                cancel_msg = t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                            # Bug 2 FIX: Always cleanup temp_target_dir regardless of backup_dir existence
                            if temp_target_dir and temp_target_dir.exists():
                                shutil.rmtree(temp_target_dir, ignore_errors=True)
                            # Bug 1: Cleanup temp_dir before returning
                            if temp_dir and temp_dir.exists():
                                shutil.rmtree(temp_dir, ignore_errors=True)
                            QMessageBox.information(
                                self,
                                t("gui_update_cancelled", "Update Cancelled"),
                                cancel_msg
                            )
                            return
                        
                        # CRIT-1: Atomic swap - rename old to temp, then new to target
                        # This minimizes the time window where target_dir doesn't exist
                        old_target_dir = root_dir / f"cachyos-multi-updater.old.{int(time.time())}"
                        if target_dir.exists():
                            target_dir.rename(old_target_dir)
                        
                        # Atomic move: temp -> target
                        temp_target_dir.rename(target_dir)
                        
                        # Check for cancellation after swap (before cleanup)
                        if update_cancelled:
                            progress.close()
                            # Bug 2 FIX: Rollback behavior depends on whether backup exists
                            # If backup exists: restore from backup (update scenario)
                            # If no backup: remove new installation (fresh installation scenario)
                            if backup_dir and backup_dir.exists():
                                # Update scenario: restore from backup
                                if target_dir.exists():
                                    target_dir.rename(root_dir / f"cachyos-multi-updater.cancelled.{int(time.time())}")
                                shutil.copytree(backup_dir, target_dir)
                                shutil.rmtree(backup_dir, ignore_errors=True)
                                cancel_msg = t("gui_update_cancelled_rollback", "Update was cancelled.\n\nOriginal installation has been restored.")
                            else:
                                # Fresh installation scenario: remove incomplete installation
                                if target_dir.exists():
                                    shutil.rmtree(target_dir, ignore_errors=True)
                                cancel_msg = t("gui_update_cancelled_msg", "Update was cancelled. No changes were made.")
                            # Bug 2: Cleanup old_target_dir before returning
                            if old_target_dir and old_target_dir.exists():
                                shutil.rmtree(old_target_dir, ignore_errors=True)
                            # Bug 1: Cleanup temp_dir before returning
                            if temp_dir and temp_dir.exists():
                                shutil.rmtree(temp_dir, ignore_errors=True)
                            QMessageBox.information(
                                self,
                                t("gui_update_cancelled", "Update Cancelled"),
                                cancel_msg
                            )
                            return
                        
                        # Copy root files after successful swap
                        for item in root_files_to_copy:
                            shutil.copy2(item, root_dir / item.name)
                            # HIGH-2: Set permissions for root executable files
                            if item.name in executable_files:
                                os.chmod(root_dir / item.name, 0o755)
                        
                        # Remove old directory after successful swap
                        if old_target_dir and old_target_dir.exists():
                            shutil.rmtree(old_target_dir, ignore_errors=True)
                        
                        # HIGH-1: Verify installation is complete - check critical files
                        critical_files = [
                            "update-all.sh",
                            "gui/main.py",
                            "gui/window.py",
                            "lib/i18n.sh"
                        ]
                        missing_files = []
                        for critical_file in critical_files:
                            if not (target_dir / critical_file).exists():
                                missing_files.append(critical_file)
                        
                        if missing_files:
                            raise Exception(f"Installation verification failed: Missing critical files: {', '.join(missing_files)}")
                        
                    except Exception as copy_error:
                        # Rollback: restore backup if it exists
                        if backup_dir and backup_dir.exists():
                            # Remove broken/incomplete installation
                            if target_dir.exists():
                                shutil.rmtree(target_dir, ignore_errors=True)
                            # Bug 1 FIX: Check if temp_target_dir is defined before accessing it
                            if temp_target_dir and temp_target_dir.exists():
                                shutil.rmtree(temp_target_dir, ignore_errors=True)
                            # Bug 1: Check if old_target_dir exists before accessing it
                            if old_target_dir and old_target_dir.exists():
                                shutil.rmtree(old_target_dir, ignore_errors=True)
                            # Restore from backup
                            shutil.copytree(backup_dir, target_dir)
                        raise copy_error
                    
                    # Cleanup backup only after successful installation
                    if backup_dir and backup_dir.exists():
                        shutil.rmtree(backup_dir)
                        backup_dir = None
                    
                    # HIGH-3: Cleanup old backup directories (keep max 3, remove older than 7 days)
                    import glob
                    backup_pattern = str(root_dir / "cachyos-multi-updater.backup.*")
                    backup_dirs = sorted(glob.glob(backup_pattern), reverse=True)
                    current_time = time.time()
                    seven_days_ago = current_time - (7 * 24 * 60 * 60)
                    
                    # Remove backups older than 7 days
                    for backup_path_str in backup_dirs:
                        backup_path = Path(backup_path_str)
                        try:
                            backup_time = backup_path.stat().st_mtime
                            if backup_time < seven_days_ago:
                                shutil.rmtree(backup_path, ignore_errors=True)
                        except Exception:
                            pass
                    
                    # Keep only the 3 most recent backups
                    remaining_backups = sorted([Path(p) for p in glob.glob(backup_pattern) if Path(p).exists()], 
                                               key=lambda p: p.stat().st_mtime, reverse=True)
                    for old_backup in remaining_backups[3:]:  # Keep first 3, remove rest
                        shutil.rmtree(old_backup, ignore_errors=True)
                else:
                    raise Exception("cachyos-multi-updater directory not found in ZIP")
                
                # Cleanup temp files
                progress.close()
                progress_closed = True
                shutil.rmtree(temp_dir)
                
                # Update VERSION file after successful ZIP update
                github_version = self.latest_github_version
                if github_version:
                    root_version_file = self.script_dir.parent / "VERSION"
                    
                    # Check if VERSION file already has the correct version (skip if so)
                    if root_version_file.exists():
                        try:
                            with open(root_version_file, 'r', encoding='utf-8') as f:
                                existing_version = f.read().strip()
                                if existing_version == github_version:
                                    # Already correct, skip writing
                                    pass
                                else:
                                    # Need to update
                                    self._update_version_file_with_retry(root_version_file, github_version)
                        except Exception:
                            # Failed to read, try to update anyway
                            self._update_version_file_with_retry(root_version_file, github_version)
                    else:
                        # File doesn't exist, create it
                        self._update_version_file_with_retry(root_version_file, github_version)
                    
                    # Update script_version and version label
                    self.script_version = github_version
                    self.update_version_label()
                
                # Success
                QMessageBox.information(
                    self,
                    t("gui_update_success", "Update Successful"),
                    t("gui_update_success_msg", "Script updated successfully!\n\nPlease restart the application to use the new version.")
                )
                
                # Ask if user wants to restart
                reply = QMessageBox.question(
                    self,
                    t("gui_update_success", "Update Successful"),
                    t("gui_restart_now", "Do you want to restart the application now?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.restart_application()
                    
            except Exception as e:
                # Close progress dialog only if not already closed
                if not progress_closed:
                    progress.close()
                    progress_closed = True
                
                # Rollback: restore backup if installation was partially completed
                target_dir = root_dir / "cachyos-multi-updater"
                if backup_dir and backup_dir.exists():
                    try:
                        # Check if target is missing or incomplete
                        needs_restore = (
                            not target_dir.exists() or
                            not (target_dir / "update-all.sh").exists()
                        )
                        
                        if needs_restore:
                            # Remove incomplete/broken installation
                            if target_dir.exists():
                                shutil.rmtree(target_dir, ignore_errors=True)
                            # Restore from backup
                            shutil.copytree(backup_dir, target_dir)
                            # Bug 2 FIX: Cleanup backup after successful restore
                            # Use ignore_errors=True to ensure backup_dir is set to None even if cleanup fails
                            shutil.rmtree(backup_dir, ignore_errors=True)
                            backup_dir = None
                    except Exception as restore_error:
                        # If restore fails, at least keep the backup for manual recovery
                        # Bug 2 FIX: Ensure backup_dir is set to None even if restore fails
                        # This prevents orphaned backup directories
                        try:
                            if backup_dir and backup_dir.exists():
                                shutil.rmtree(backup_dir, ignore_errors=True)
                        except Exception:
                            pass
                        backup_dir = None
                        pass
                
                # Bug 2: Cleanup temp_dir and old_target_dir
                if temp_dir and temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                if old_target_dir and old_target_dir.exists():
                    shutil.rmtree(old_target_dir, ignore_errors=True)
                
                raise
                
        except Exception as e:
            # Cleanup progress dialog if it exists and wasn't already closed
            if progress is not None and not progress_closed:
                progress.close()
            
            # Cleanup temp directory if it was created but error occurred before inner try block
            if temp_dir is not None and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass  # Ignore cleanup errors
            
            # Show error message
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_zip_update_failed", "Failed to update via ZIP download:\n\n{error}\n\nPlease update manually from GitHub.").format(error=str(e))
            )
        finally:
            # HIGH-1 FIX: Always cleanup lock file
            if hasattr(self, 'update_lock_file') and self.update_lock_file.exists():
                try:
                    self.update_lock_file.unlink()
                except Exception:
                    pass
    
    def restart_application(self):
        """Restart the application"""
        import subprocess
        import sys
        import os
        
        try:
            # Get the script path that started this application
            # Try to find cachyos-update-gui in parent directory
            root_dir = self.script_dir.parent
            launcher_script = root_dir / "cachyos-update-gui"
            
            new_process = None
            if launcher_script.exists():
                # Use launcher script
                new_process = subprocess.Popen([str(launcher_script)], cwd=str(root_dir))
            else:
                # Fallback: use gui/main.py directly
                gui_script = self.script_dir / "gui" / "main.py"
                if gui_script.exists():
                    new_process = subprocess.Popen(['python3', str(gui_script)], cwd=str(self.script_dir))
                else:
                    QMessageBox.warning(
                        self,
                        t("gui_restart_failed", "Restart Failed"),
                        t("gui_restart_manual", "Could not restart automatically.\n\nPlease restart the application manually.")
                    )
                    return
            
            # Bug 3: Verify new process was spawned successfully before quitting
            # new_process is guaranteed to be a Popen object here because:
            # - If launcher_script exists: new_process = subprocess.Popen(...)
            # - Else if gui_script exists: new_process = subprocess.Popen(...)
            # - Else: return (early exit, never reaches this point)
            # subprocess.Popen() either returns a Popen object or raises an exception
            if new_process.poll() is None:
                # Process is running - safe to quit
                app = QApplication.instance()
                if app is not None:
                    app.quit()
                else:
                    # Fallback: sys.exit if no QApplication instance
                    import sys
                    sys.exit(0)
            else:
                # Process failed to start (exited immediately)
                QMessageBox.warning(
                    self,
                    t("gui_restart_failed", "Restart Failed"),
                    t("gui_restart_error", "Error restarting application:\n\nFailed to start new process.\n\nPlease restart manually.")
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                t("gui_restart_failed", "Restart Failed"),
                t("gui_restart_error", "Error restarting application:\n\n{error}\n\nPlease restart manually.").format(error=str(e))
            )
    
    def _on_language_label_clicked(self, event):
        """Handle language label click with feedback effect"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the widget that was clicked (the parent widget)
            widget = None
            if hasattr(self, 'language_icon_label') and self.language_icon_label is not None:
                widget = self.language_icon_label.parent()
            
            # Cancel any pending restore operation from previous clicks
            if self.language_feedback_timer and self.language_feedback_timer.isActive():
                self.language_feedback_timer.stop()
            
            # Visual feedback: briefly change opacity using QGraphicsOpacityEffect
            original_effect = None
            if widget and widget.isVisible():
                try:
                    # Store original effect BEFORE clearing any existing feedback effect
                    # This ensures we can restore it later
                    current_effect = widget.graphicsEffect()
                    
                    # If there's already a feedback effect active, use the stored original effect
                    if self.language_feedback_effect and current_effect == self.language_feedback_effect:
                        # Restore the original effect that was stored before the first feedback
                        original_effect = self.language_feedback_original_effect
                        # Clear the current feedback effect
                        widget.setGraphicsEffect(None)
                    else:
                        # No feedback effect active, store the current effect as original
                        original_effect = current_effect
                        # Save it for future clicks
                        self.language_feedback_original_effect = original_effect
                    
                    # Create and apply opacity effect
                    opacity_effect = QGraphicsOpacityEffect()
                    opacity_effect.setOpacity(0.6)
                    widget.setGraphicsEffect(opacity_effect)
                    self.language_feedback_effect = opacity_effect  # Store reference
                    QApplication.processEvents()
                except Exception:
                    pass  # Ignore effect errors
            
            # Switch language
            try:
                self.switch_language()
            except Exception as e:
                # Log error but don't crash
                import traceback
                print(f"Error switching language: {e}")
                traceback.print_exc()
            
            # Restore original effect after short delay
            # Define restore_effect function outside the if widget block to avoid NameError
            def restore_effect():
                try:
                    if widget and widget.isVisible():
                        # Only restore if the current effect is still our feedback effect
                        current_effect = widget.graphicsEffect()
                        if current_effect == self.language_feedback_effect:
                            # Restore original effect (or None if there was none)
                            widget.setGraphicsEffect(original_effect)
                            self.language_feedback_effect = None
                            # Clear stored original effect after restoration
                            self.language_feedback_original_effect = None
                except Exception:
                    pass  # Ignore restore errors
            
            # Only set up timer if widget exists
            if widget:
                # Create timer if it doesn't exist
                if self.language_feedback_timer is None:
                    self.language_feedback_timer = QTimer()
                    self.language_feedback_timer.setSingleShot(True)
                    self.language_feedback_timer.timeout.connect(restore_effect)
                    self.language_feedback_restore_func = restore_effect
                else:
                    # Disconnect previous connection if it exists
                    if self.language_feedback_restore_func is not None:
                        try:
                            self.language_feedback_timer.timeout.disconnect(self.language_feedback_restore_func)
                        except TypeError:
                            # If disconnect fails, try disconnecting all (fallback)
                            try:
                                self.language_feedback_timer.timeout.disconnect()
                            except TypeError:
                                pass  # No connections to disconnect
                    # Connect new restore function
                    self.language_feedback_timer.timeout.connect(restore_effect)
                    self.language_feedback_restore_func = restore_effect
                
                self.language_feedback_timer.start(150)
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

