#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Config Dialog
Settings dialog for configuring update options
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox,
    QPushButton, QGroupBox, QLineEdit, QFileDialog, QComboBox, QTextEdit,
    QTabWidget, QWidget, QFormLayout, QMessageBox, QRadioButton
)
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui import QIcon, QPixmap, QFont
import os
from pathlib import Path

# Handle imports for both direct execution and module import
try:
    from .config_manager import ConfigManager
    from .fa_icons import get_fa_icon, apply_fa_font
    from .i18n import t
except ImportError:
    from config_manager import ConfigManager
    from fa_icons import get_fa_icon, apply_fa_font
    from i18n import t


class ConfigDialog(QDialog):
    """Configuration dialog"""
    
    def __init__(self, script_dir: str, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.config_manager = ConfigManager(script_dir)
        self.config = self.config_manager.load_config()
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        
        # Tab 1: Update Components
        components_tab = self.create_components_tab()
        tabs.addTab(components_tab, t("gui_tab_components", "Update Components"))
        
        # Tab 2: General Settings
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, t("gui_tab_general", "General"))
        
        # Tab 3: Logs
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, t("gui_tab_logs", "Logs"))
        
        # Tab 4: System
        system_tab = self.create_system_tab()
        tabs.addTab(system_tab, t("gui_tab_system", "System"))
        
        # Tab 5: Advanced Settings
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, t("gui_tab_advanced", "Advanced"))
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        icon, text = get_fa_icon('undo', "Reset to Defaults")
        reset_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(reset_btn)
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        icon, text = get_fa_icon('times', "Cancel")
        cancel_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(cancel_btn)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        icon, text = get_fa_icon('save', "Save")
        save_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(save_btn)
        save_btn.clicked.connect(self.save_and_close)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_components_tab(self):
        """Create update components tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        group = QGroupBox("Enable/Disable Update Components")
        group_layout = QVBoxLayout()
        
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
            self.enable_system = FACheckBox("System Updates (pacman)")
            self.enable_aur = FACheckBox("AUR Updates (yay/paru)")
            self.enable_cursor = FACheckBox("Cursor Editor")
            self.enable_adguard = FACheckBox("AdGuard Home")
            self.enable_flatpak = FACheckBox("Flatpak Updates")
        else:
            self.enable_system = QCheckBox("System Updates (pacman)")
            self.enable_aur = QCheckBox("AUR Updates (yay/paru)")
            self.enable_cursor = QCheckBox("Cursor Editor")
            self.enable_adguard = QCheckBox("AdGuard Home")
            self.enable_flatpak = QCheckBox("Flatpak Updates")
        
        group_layout.addWidget(self.enable_system)
        group_layout.addWidget(self.enable_aur)
        group_layout.addWidget(self.enable_cursor)
        group_layout.addWidget(self.enable_adguard)
        group_layout.addWidget(self.enable_flatpak)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Desktop Shortcut section
        desktop_group = QGroupBox(t("gui_desktop_shortcut", "Desktop Shortcut"))
        desktop_layout = QVBoxLayout()
        
        desktop_info = QLabel(t("gui_desktop_shortcut_info", "Create a desktop shortcut for easy access"))
        desktop_info.setWordWrap(True)
        desktop_layout.addWidget(desktop_info)
        
        # Icon selection
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel(t("gui_icon", "Icon:")))
        
        self.desktop_icon = QComboBox()
        # Common system icons
        system_icons = [
            ("system-software-update", t("gui_icon_system_update", "System Update")),
            ("system-update", t("gui_icon_system", "System")),
            ("software-update-available", t("gui_icon_software_update", "Software Update")),
            ("update-manager", t("gui_icon_update_manager", "Update Manager")),
            ("package-updater", t("gui_icon_package_updater", "Package Updater")),
            ("applications-system", t("gui_icon_applications_system", "Applications System")),
        ]
        for icon_name, icon_label in system_icons:
            self.desktop_icon.addItem(icon_label, icon_name)
        
        # Custom icon option
        self.desktop_icon.addItem(t("gui_icon_custom", "Custom Icon File..."), "custom")
        icon_layout.addWidget(self.desktop_icon)
        
        # Custom icon file selector (hidden by default)
        self.custom_icon_path = QLineEdit()
        self.custom_icon_path.setPlaceholderText(t("gui_icon_custom_path", "Select icon file (PNG, SVG, etc.)"))
        self.custom_icon_path.setVisible(False)
        self.icon_browse_btn = QPushButton("...")
        self.icon_browse_btn.setMaximumWidth(40)
        self.icon_browse_btn.clicked.connect(lambda: self.browse_icon_file())
        self.icon_browse_btn.setVisible(False)
        
        icon_path_layout = QHBoxLayout()
        icon_path_layout.addWidget(self.custom_icon_path)
        icon_path_layout.addWidget(self.icon_browse_btn)
        
        # Show/hide custom icon path based on selection
        self.desktop_icon.currentIndexChanged.connect(self.on_icon_selection_changed)
        
        desktop_layout.addLayout(icon_layout)
        desktop_layout.addLayout(icon_path_layout)
        
        # Icon preview
        preview_label = QLabel(t("gui_icon_preview", "Preview:"))
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(64, 64)
        self.icon_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Don't set text - it will be set by update_icon_preview() or show pixmap
        self.update_icon_preview()
        self.desktop_icon.currentIndexChanged.connect(self.update_icon_preview)
        self.custom_icon_path.textChanged.connect(self.update_icon_preview)
        
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.icon_preview)
        preview_layout.addStretch()
        desktop_layout.addLayout(preview_layout)
        
        # Shortcut version selection (Console or GUI)
        shortcut_version_layout = QVBoxLayout()
        shortcut_version_label = QLabel(t("gui_shortcut_version", "Shortcut Type:"))
        shortcut_version_layout.addWidget(shortcut_version_label)
        
        shortcut_version_radio_layout = QHBoxLayout()
        
        # Radio buttons for version selection
        self.shortcut_version_console = QRadioButton(t("gui_shortcut_version_console", "Console Version"))
        self.shortcut_version_gui = QRadioButton(t("gui_shortcut_version_gui", "GUI Version"))
        self.shortcut_version_gui.setChecked(True)  # Default to GUI
        
        shortcut_version_radio_layout.addWidget(self.shortcut_version_console)
        shortcut_version_radio_layout.addWidget(self.shortcut_version_gui)
        shortcut_version_radio_layout.addStretch()
        shortcut_version_layout.addLayout(shortcut_version_radio_layout)
        desktop_layout.addLayout(shortcut_version_layout)
        
        # Shortcut type (where to create)
        shortcut_type_layout = QVBoxLayout()
        shortcut_type_label = QLabel(t("gui_shortcut_type", "Create shortcut:"))
        shortcut_type_layout.addWidget(shortcut_type_label)
        
        shortcut_checkbox_layout = QHBoxLayout()
        
        # Try to use Font Awesome checkboxes
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
            self.shortcut_app_menu = FACheckBox(t("gui_shortcut_app_menu", "Application Menu"))
            self.shortcut_desktop = FACheckBox(t("gui_shortcut_desktop", "Desktop"))
        else:
            self.shortcut_app_menu = QCheckBox(t("gui_shortcut_app_menu", "Application Menu"))
            self.shortcut_desktop = QCheckBox(t("gui_shortcut_desktop", "Desktop"))
        
        self.shortcut_app_menu.setChecked(True)
        self.shortcut_desktop.setChecked(False)
        
        shortcut_checkbox_layout.addWidget(self.shortcut_app_menu)
        shortcut_checkbox_layout.addWidget(self.shortcut_desktop)
        shortcut_checkbox_layout.addStretch()
        shortcut_type_layout.addLayout(shortcut_checkbox_layout)
        desktop_layout.addLayout(shortcut_type_layout)
        
        # Create shortcut button
        create_shortcut_btn = QPushButton(t("gui_create_shortcut", "Create Desktop Shortcut"))
        create_shortcut_btn.clicked.connect(self.create_desktop_shortcut)
        desktop_layout.addWidget(create_shortcut_btn)
        
        desktop_group.setLayout(desktop_layout)
        layout.addWidget(desktop_group)
        
        # GUI Language & Theme section
        appearance_group = QGroupBox(t("gui_appearance", "Appearance"))
        appearance_layout = QVBoxLayout()
        
        appearance_info = QLabel(t("gui_appearance_info", "Configure the appearance and language of the GUI"))
        appearance_info.setWordWrap(True)
        appearance_layout.addWidget(appearance_info)
        
        appearance_form = QFormLayout()
        
        # GUI Language
        self.gui_language = QComboBox()
        self.gui_language.addItem(t("gui_theme_auto", "Automatic (System)"), "auto")
        self.gui_language.addItem("Deutsch", "de")
        self.gui_language.addItem("English", "en")
        appearance_form.addRow(t("gui_language", "GUI Language:"), self.gui_language)
        
        # GUI Theme
        self.gui_theme = QComboBox()
        self.gui_theme.addItem(t("gui_theme_auto", "Automatic (System)"), "auto")
        self.gui_theme.addItem(t("gui_theme_light", "Light"), "light")
        self.gui_theme.addItem(t("gui_theme_dark", "Dark"), "dark")
        appearance_form.addRow(t("gui_theme", "GUI Theme:"), self.gui_theme)
        
        appearance_layout.addLayout(appearance_form)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Options section
        options_group = QGroupBox(t("gui_options", "Options"))
        options_layout = QVBoxLayout()
        
        options_info = QLabel(t("gui_options_info", "General options for update behavior"))
        options_info.setWordWrap(True)
        options_layout.addWidget(options_info)
        
        # Try to use Font Awesome checkboxes
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
            self.enable_notifications = FACheckBox(t("gui_enable_notifications", "Enable Notifications"))
            self.enable_colors = FACheckBox(t("gui_enable_colors", "Enable Colors"))
            self.dry_run = FACheckBox(t("gui_dry_run", "Dry Run Mode (test only)"))
            self.enable_auto_update = FACheckBox(t("gui_enable_auto_update", "Enable Auto Update"))
        else:
            self.enable_notifications = QCheckBox(t("gui_enable_notifications", "Enable Notifications"))
            self.enable_colors = QCheckBox(t("gui_enable_colors", "Enable Colors"))
            self.dry_run = QCheckBox(t("gui_dry_run", "Dry Run Mode (test only)"))
            self.enable_auto_update = QCheckBox(t("gui_enable_auto_update", "Enable Auto Update"))
        
        options_layout.addWidget(self.enable_notifications)
        options_layout.addWidget(self.enable_colors)
        options_layout.addWidget(self.dry_run)
        options_layout.addWidget(self.enable_auto_update)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_logs_tab(self):
        """Create logs settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        logs_info = QLabel(t("gui_logs_info", "Configure log file settings and storage locations"))
        logs_info.setWordWrap(True)
        layout.addWidget(logs_info)
        
        form = QFormLayout()
        
        # Max log files
        self.max_log_files = QSpinBox()
        self.max_log_files.setMinimum(1)
        self.max_log_files.setMaximum(100)
        self.max_log_files.setToolTip(t("gui_max_log_files_tooltip", "Maximum number of log files to keep. Older files will be automatically deleted."))
        form.addRow(t("gui_max_log_files", "Max Log Files:"), self.max_log_files)
        
        # Cache max age
        self.cache_max_age = QSpinBox()
        self.cache_max_age.setMinimum(60)
        self.cache_max_age.setMaximum(86400)
        self.cache_max_age.setSuffix(" seconds")
        self.cache_max_age.setToolTip(t("gui_cache_max_age_tooltip", "Maximum age of cached data in seconds before it is refreshed."))
        form.addRow(t("gui_cache_max_age", "Cache Max Age:"), self.cache_max_age)
        
        # Log directory
        log_layout = QHBoxLayout()
        self.log_dir = QLineEdit()
        self.log_dir.setToolTip(t("gui_log_dir_tooltip", "Directory where log files are stored"))
        icon, text = get_fa_icon('folder-open', "Browse...")
        log_browse = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(log_browse)
        log_browse.clicked.connect(lambda: self.browse_directory(self.log_dir))
        log_layout.addWidget(self.log_dir)
        log_layout.addWidget(log_browse)
        form.addRow(t("gui_log_directory", "Log Directory:"), log_layout)
        
        # Stats directory
        stats_layout = QHBoxLayout()
        self.stats_dir = QLineEdit()
        self.stats_dir.setToolTip(t("gui_stats_dir_tooltip", "Directory where statistics files are stored"))
        icon, text = get_fa_icon('folder-open', "Browse...")
        stats_browse = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(stats_browse)
        stats_browse.clicked.connect(lambda: self.browse_directory(self.stats_dir))
        stats_layout.addWidget(self.stats_dir)
        stats_layout.addWidget(stats_browse)
        form.addRow(t("gui_stats_directory", "Stats Directory:"), stats_layout)
        
        layout.addLayout(form)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_system_tab(self):
        """Create system settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Pacman Parameters section
        pacman_group = QGroupBox(t("gui_pacman_parameters", "Pacman Parameters"))
        pacman_layout = QVBoxLayout()
        
        pacman_info = QLabel(t("gui_pacman_info", "Configure pacman command parameters for system updates"))
        pacman_info.setWordWrap(True)
        pacman_layout.addWidget(pacman_info)
        
        # Try to use Font Awesome checkboxes
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
            self.pacman_sync = FACheckBox(t("gui_pacman_sync", "Sync (-S)"))
            self.pacman_refresh = FACheckBox(t("gui_pacman_refresh", "Refresh (-y)"))
            self.pacman_upgrade = FACheckBox(t("gui_pacman_upgrade", "Upgrade (-u)"))
            self.pacman_noconfirm = FACheckBox(t("gui_pacman_noconfirm", "No Confirm (--noconfirm)"))
        else:
            self.pacman_sync = QCheckBox(t("gui_pacman_sync", "Sync (-S)"))
            self.pacman_refresh = QCheckBox(t("gui_pacman_refresh", "Refresh (-y)"))
            self.pacman_upgrade = QCheckBox(t("gui_pacman_upgrade", "Upgrade (-u)"))
            self.pacman_noconfirm = QCheckBox(t("gui_pacman_noconfirm", "No Confirm (--noconfirm)"))
        
        self.pacman_sync.setToolTip(t("gui_pacman_sync_tooltip", "Update package database before upgrading"))
        self.pacman_refresh.setToolTip(t("gui_pacman_refresh_tooltip", "Refresh package lists"))
        self.pacman_upgrade.setToolTip(t("gui_pacman_upgrade_tooltip", "Upgrade all installed packages"))
        self.pacman_noconfirm.setToolTip(t("gui_pacman_noconfirm_tooltip", "Don't ask for confirmation (non-interactive mode)"))
        
        pacman_layout.addWidget(self.pacman_sync)
        pacman_layout.addWidget(self.pacman_refresh)
        pacman_layout.addWidget(self.pacman_upgrade)
        pacman_layout.addWidget(self.pacman_noconfirm)
        
        # Command preview
        preview_label = QLabel(t("gui_command_preview", "Command Preview:"))
        pacman_layout.addWidget(preview_label)
        
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setMaximumHeight(60)
        self.command_preview.setFont(QFont("Monospace", 9))
        pacman_layout.addWidget(self.command_preview)
        
        # Set default values (all checked by default)
        self.pacman_sync.setChecked(True)
        self.pacman_refresh.setChecked(True)
        self.pacman_upgrade.setChecked(True)
        self.pacman_noconfirm.setChecked(True)
        
        # Connect checkboxes to update preview
        self.pacman_sync.toggled.connect(self.update_command_preview)
        self.pacman_refresh.toggled.connect(self.update_command_preview)
        self.pacman_upgrade.toggled.connect(self.update_command_preview)
        self.pacman_noconfirm.toggled.connect(self.update_command_preview)
        
        pacman_group.setLayout(pacman_layout)
        layout.addWidget(pacman_group)
        
        # Sudo Password section
        sudo_group = QGroupBox(t("gui_sudo_password", "Sudo Password"))
        sudo_layout = QVBoxLayout()
        
        sudo_info = QLabel(t("gui_sudo_password_info", "Store sudo password for automatic updates (not recommended for security reasons)"))
        sudo_info.setWordWrap(True)
        sudo_layout.addWidget(sudo_info)
        
        sudo_password_layout = QHBoxLayout()
        self.sudo_password = QLineEdit()
        self.sudo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.sudo_password.setPlaceholderText(t("gui_sudo_password_placeholder", "Leave empty to keep current password"))
        self.sudo_password.setToolTip(t("gui_sudo_password_tooltip", "Enter sudo password to store for automatic updates"))
        sudo_password_layout.addWidget(QLabel(t("gui_password", "Password:")))
        sudo_password_layout.addWidget(self.sudo_password)
        sudo_layout.addLayout(sudo_password_layout)
        
        # Try to use Font Awesome checkboxes
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
            self.save_sudo_password = FACheckBox(t("gui_save_password", "Save password (encrypted)"))
        else:
            self.save_sudo_password = QCheckBox(t("gui_save_password", "Save password (encrypted)"))
        self.save_sudo_password.setToolTip(t("gui_save_password_tooltip", "Save the password in config file (currently stored in plain text - encryption coming soon)"))
        sudo_layout.addWidget(self.save_sudo_password)
        
        sudo_group.setLayout(sudo_layout)
        layout.addWidget(sudo_group)
        
        # Download Retries section
        retries_group = QGroupBox(t("gui_download_retries", "Download Retries"))
        retries_layout = QVBoxLayout()
        
        retries_info = QLabel(t("gui_download_retries_info", "Number of retry attempts for failed downloads"))
        retries_info.setWordWrap(True)
        retries_layout.addWidget(retries_info)
        
        retries_form = QFormLayout()
        self.download_retries = QSpinBox()
        self.download_retries.setMinimum(1)
        self.download_retries.setMaximum(10)
        self.download_retries.setToolTip(t("gui_download_retries_tooltip", "How many times to retry a failed download before giving up"))
        retries_form.addRow(t("gui_download_retries", "Download Retries:"), self.download_retries)
        retries_layout.addLayout(retries_form)
        
        retries_group.setLayout(retries_layout)
        layout.addWidget(retries_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        advanced_info = QLabel(t("gui_advanced_info", "Advanced settings for power users. Change these only if you know what you're doing."))
        advanced_info.setWordWrap(True)
        layout.addWidget(advanced_info)
        
        form = QFormLayout()
        
        # GitHub Repository URL
        self.github_repo = QLineEdit()
        self.github_repo.setToolTip(t("gui_github_repo_tooltip", "GitHub repository URL for version checks and updates (format: owner/repo)"))
        form.addRow(t("gui_github_repo", "GitHub Repository URL:"), self.github_repo)
        
        # Script path
        script_layout = QHBoxLayout()
        self.script_path = QLineEdit()
        self.script_path.setToolTip(t("gui_script_path_tooltip", "Path to the update-all.sh script"))
        icon, text = get_fa_icon('folder-open', "Browse...")
        script_browse = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(script_browse)
        script_browse.clicked.connect(lambda: self.browse_file(self.script_path))
        script_layout.addWidget(self.script_path)
        script_layout.addWidget(script_browse)
        form.addRow(t("gui_script_path", "Script Path:"), script_layout)
        
        layout.addLayout(form)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def browse_directory(self, line_edit: QLineEdit):
        """Browse for directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if directory:
            line_edit.setText(directory)
    
    def browse_file(self, line_edit: QLineEdit):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text())
        if file_path:
            line_edit.setText(file_path)
    
    def update_command_preview(self):
        """Update command preview"""
        parts = []
        if self.pacman_sync.isChecked():
            parts.append("-S")
        if self.pacman_refresh.isChecked():
            parts.append("-y")
        if self.pacman_upgrade.isChecked():
            parts.append("-u")
        if self.pacman_noconfirm.isChecked():
            parts.append("--noconfirm")
        
        if parts:
            cmd = f"pacman {' '.join(parts)}"
        else:
            cmd = "pacman (no parameters)"
        
        self.command_preview.setText(cmd)
    
    def load_config(self):
        """Load config into UI"""
        # Components
        self.enable_system.setChecked(self.config.get("ENABLE_SYSTEM_UPDATE", "true") == "true")
        self.enable_aur.setChecked(self.config.get("ENABLE_AUR_UPDATE", "true") == "true")
        self.enable_cursor.setChecked(self.config.get("ENABLE_CURSOR_UPDATE", "true") == "true")
        self.enable_adguard.setChecked(self.config.get("ENABLE_ADGUARD_UPDATE", "true") == "true")
        self.enable_flatpak.setChecked(self.config.get("ENABLE_FLATPAK_UPDATE", "true") == "true")
        
        # General
        self.max_log_files.setValue(int(self.config.get("MAX_LOG_FILES", "3")))
        self.download_retries.setValue(int(self.config.get("DOWNLOAD_RETRIES", "3")))
        self.cache_max_age.setValue(int(self.config.get("CACHE_MAX_AGE", "3600")))
        self.enable_notifications.setChecked(self.config.get("ENABLE_NOTIFICATIONS", "true") == "true")
        self.enable_colors.setChecked(self.config.get("ENABLE_COLORS", "true") == "true")
        self.dry_run.setChecked(self.config.get("DRY_RUN", "false") == "true")
        self.enable_auto_update.setChecked(self.config.get("ENABLE_AUTO_UPDATE", "false") == "true")
        
        # Sudo password (don't show actual password, just indicate if stored)
        has_stored_password = bool(self.config.get("SUDO_PASSWORD"))
        self.save_sudo_password.setChecked(has_stored_password)
        if has_stored_password:
            self.sudo_password.setPlaceholderText("Password is stored (enter new to change)")
        
        # System - Pacman (set defaults if not in config)
        self.pacman_sync.setChecked(self.config.get("PACMAN_SYNC", "true") == "true")
        self.pacman_refresh.setChecked(self.config.get("PACMAN_REFRESH", "true") == "true")
        self.pacman_upgrade.setChecked(self.config.get("PACMAN_UPGRADE", "true") == "true")
        self.pacman_noconfirm.setChecked(self.config.get("PACMAN_NOCONFIRM", "true") == "true")
        
        # Advanced
        self.github_repo.setText(self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"))
        self.log_dir.setText(self.config.get("LOG_DIR", str(Path(self.script_dir) / "logs")))
        self.stats_dir.setText(self.config.get("STATS_DIR", str(Path(self.script_dir) / ".stats")))
        self.script_path.setText(self.config.get("SCRIPT_PATH", str(Path(self.script_dir) / "update-all.sh")))
        
        self.update_command_preview()
    
    def save_config(self):
        """Save config from UI"""
        # Components
        self.config["ENABLE_SYSTEM_UPDATE"] = str(self.enable_system.isChecked()).lower()
        self.config["ENABLE_AUR_UPDATE"] = str(self.enable_aur.isChecked()).lower()
        self.config["ENABLE_CURSOR_UPDATE"] = str(self.enable_cursor.isChecked()).lower()
        self.config["ENABLE_ADGUARD_UPDATE"] = str(self.enable_adguard.isChecked()).lower()
        self.config["ENABLE_FLATPAK_UPDATE"] = str(self.enable_flatpak.isChecked()).lower()
        
        # General
        self.config["MAX_LOG_FILES"] = str(self.max_log_files.value())
        self.config["DOWNLOAD_RETRIES"] = str(self.download_retries.value())
        self.config["CACHE_MAX_AGE"] = str(self.cache_max_age.value())
        self.config["ENABLE_NOTIFICATIONS"] = str(self.enable_notifications.isChecked()).lower()
        self.config["ENABLE_COLORS"] = str(self.enable_colors.isChecked()).lower()
        self.config["DRY_RUN"] = str(self.dry_run.isChecked()).lower()
        self.config["ENABLE_AUTO_UPDATE"] = str(self.enable_auto_update.isChecked()).lower()
        
        # Sudo password (only save if provided and checkbox is checked)
        if hasattr(self, 'sudo_password') and self.sudo_password.text():
            if hasattr(self, 'save_sudo_password') and self.save_sudo_password.isChecked():
                self.config["SUDO_PASSWORD"] = self.sudo_password.text()
            else:
                # Remove password if checkbox unchecked
                if "SUDO_PASSWORD" in self.config:
                    del self.config["SUDO_PASSWORD"]
        elif hasattr(self, 'save_sudo_password') and not self.save_sudo_password.isChecked():
            # Remove password if checkbox unchecked
            if "SUDO_PASSWORD" in self.config:
                del self.config["SUDO_PASSWORD"]
        
        # Advanced
        if self.github_repo.text():
            self.config["GITHUB_REPO"] = self.github_repo.text()
        if self.log_dir.text():
            self.config["LOG_DIR"] = self.log_dir.text()
        if self.stats_dir.text():
            self.config["STATS_DIR"] = self.stats_dir.text()
        if self.script_path.text():
            self.config["SCRIPT_PATH"] = self.script_path.text()
        
        # GUI Language
        self.config["GUI_LANGUAGE"] = self.gui_language.itemData(self.gui_language.currentIndex())
        
        # GUI Theme
        self.config["GUI_THEME"] = self.gui_theme.itemData(self.gui_theme.currentIndex())
        
        # Pacman
        self.config["PACMAN_SYNC"] = str(self.pacman_sync.isChecked()).lower()
        self.config["PACMAN_REFRESH"] = str(self.pacman_refresh.isChecked()).lower()
        self.config["PACMAN_UPGRADE"] = str(self.pacman_upgrade.isChecked()).lower()
        self.config["PACMAN_NOCONFIRM"] = str(self.pacman_noconfirm.isChecked()).lower()
        
        return self.config_manager.save_config(self.config)
    
    def reset_to_defaults(self):
        """Reset to default values"""
        reply = QMessageBox.question(
            self, "Reset to Defaults",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config = self.config_manager.load_config()
            self.load_config()
    
    def on_icon_selection_changed(self, index):
        """Handle icon selection change"""
        icon_data = self.desktop_icon.itemData(index)
        if icon_data == "custom":
            self.custom_icon_path.setVisible(True)
            self.icon_browse_btn.setVisible(True)
        else:
            self.custom_icon_path.setVisible(False)
            self.icon_browse_btn.setVisible(False)
    
    def browse_icon_file(self):
        """Browse for custom icon file"""
        icon_file, _ = QFileDialog.getOpenFileName(
            self,
            t("gui_select_icon", "Select Icon File"),
            "",
            "Image Files (*.png *.svg *.xpm *.ico);;All Files (*)"
        )
        if icon_file:
            self.custom_icon_path.setText(icon_file)
    
    def update_icon_preview(self):
        """Update icon preview"""
        icon_data = self.desktop_icon.itemData(self.desktop_icon.currentIndex())
        
        if icon_data == "custom":
            icon_path = self.custom_icon_path.text()
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_preview.clear()  # Clear any text first
                    self.icon_preview.setPixmap(pixmap)
                    return
        else:
            # Try to load system icon
            icon_name = icon_data if icon_data else "system-software-update"
            
            # Try multiple methods to load the icon
            icon = QIcon.fromTheme(icon_name)
            if icon.isNull():
                # Try with different icon name variations
                icon_variations = [
                    icon_name,
                    icon_name.replace("-", "_"),
                    icon_name.replace("_", "-"),
                    f"applications-{icon_name}",
                    f"system-{icon_name}",
                ]
                for var_name in icon_variations:
                    icon = QIcon.fromTheme(var_name)
                    if not icon.isNull():
                        break
            
            if not icon.isNull():
                pixmap = icon.pixmap(64, 64)
                if not pixmap.isNull():
                    self.icon_preview.clear()  # Clear any text first
                    self.icon_preview.setPixmap(pixmap)
                    return
            
            # Try to find icon in standard paths
            from PyQt6.QtCore import QStandardPaths
            icon_paths = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.IconThemePath)
            for icon_path in icon_paths:
                # Try different sizes and formats
                for size in ["64x64", "48x48", "32x32", "scalable"]:
                    for ext in ["png", "svg", "xpm"]:
                        test_path = f"{icon_path}/{icon_name}/{size}/icon.{ext}"
                        if os.path.exists(test_path):
                            pixmap = QPixmap(test_path)
                            if not pixmap.isNull():
                                pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                self.icon_preview.clear()
                                self.icon_preview.setPixmap(pixmap)
                                return
        
        # Fallback: show text (only if no icon could be loaded)
        self.icon_preview.clear()  # Clear pixmap first
        self.icon_preview.setText(t("gui_icon_preview", "Preview"))
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        script_dir = Path(self.script_dir)
        script_path = script_dir / "update-all.sh"
        
        if not script_path.exists():
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_script_not_found", "update-all.sh not found!")
            )
            return
        
        # Get icon
        icon_data = self.desktop_icon.itemData(self.desktop_icon.currentIndex())
        if icon_data == "custom":
            icon_value = self.custom_icon_path.text()
            if not icon_value or not os.path.exists(icon_value):
                QMessageBox.warning(
                    self,
                    t("gui_error", "Error"),
                    t("gui_icon_not_found", "Please select a valid icon file!")
                )
                return
        else:
            icon_value = icon_data if icon_data else "system-software-update"
        
        # Determine target directories
        app_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir = None
        
        # Try to find desktop directory
        desktop_paths = [
            Path.home() / "Desktop",
            Path.home() / "Schreibtisch",
            Path.home() / "desktop",
        ]
        for path in desktop_paths:
            if path.exists() and path.is_dir():
                desktop_dir = path
                break
        
        # Create directories if needed
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Create desktop entry content
        script_abs_path = script_path.absolute()
        
        # Determine which version to use (Console or GUI)
        use_gui = self.shortcut_version_gui.isChecked()
        
        if use_gui:
            # GUI version
            gui_script = script_dir / "gui" / "main.py"
            if gui_script.exists():
                exec_cmd = f'python3 "{gui_script.absolute()}"'
                terminal = "false"
            else:
                QMessageBox.warning(
                    self,
                    t("gui_error", "Error"),
                    t("gui_gui_not_found", "GUI script not found! Using console version instead.")
                )
                use_gui = False
        
        if not use_gui:
            # Console version
            wrapper_script = script_dir / "run-update.sh"
            if wrapper_script.exists():
                exec_cmd = f'konsole --hold -e "{wrapper_script.absolute()}"'
            else:
                exec_cmd = f'konsole --hold -e "bash \\"{script_abs_path}\\""'
            terminal = "true"
        
        desktop_entry = f"""[Desktop Entry]
Name={self.shortcut_name.text() or "Update All"}
Comment={self.shortcut_comment.text() or "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak"}
Exec={exec_cmd}
Icon={icon_value}
Terminal={terminal}
Type=Application
Categories=System;
"""
        
        desktop_file = app_dir / "update-all.desktop"
        
        try:
            # Write desktop file
            with open(desktop_file, 'w', encoding='utf-8') as f:
                f.write(desktop_entry)
            
            # Make executable
            os.chmod(desktop_file, 0o755)
            
            # Copy to desktop if requested
            if self.shortcut_desktop.isChecked() and desktop_dir:
                desktop_file_copy = desktop_dir / "update-all.desktop"
                with open(desktop_file_copy, 'w', encoding='utf-8') as f:
                    f.write(desktop_entry)
                os.chmod(desktop_file_copy, 0o755)
            
            # Success message
            locations = []
            if self.shortcut_app_menu.isChecked():
                locations.append(str(app_dir / "update-all.desktop"))
            if self.shortcut_desktop.isChecked() and desktop_dir:
                locations.append(str(desktop_dir / "update-all.desktop"))
            
            QMessageBox.information(
                self,
                t("gui_success", "Success"),
                t("gui_shortcut_created", "Desktop shortcut created successfully!") + "\n\n" +
                "\n".join(locations)
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_shortcut_failed", "Failed to create desktop shortcut:") + f"\n{str(e)}"
            )
    
    def save_and_close(self):
        """Save config and close dialog"""
        if self.save_config():
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save configuration")

