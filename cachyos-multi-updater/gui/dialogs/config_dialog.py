#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Config Dialog
Settings dialog for configuring update options
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSpinBox,
    QPushButton,
    QGroupBox,
    QLineEdit,
    QFileDialog,
    QComboBox,
    QTextEdit,
    QWidget,
    QFormLayout,
    QMessageBox,
    QRadioButton,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont
import os
import shlex
import subprocess

# Import from new structure
from ..core.config_manager import ConfigManager
from ..core.i18n import t
from ..widgets import get_fa_icon, apply_fa_font
from ..utils import get_logger


class ConfigDialog(QDialog):
    """Configuration dialog"""

    def __init__(self, script_dir: str, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.logger.info(f"ConfigDialog initialized with script_dir: {script_dir}")
        try:
            self.script_dir = script_dir
            self.config_manager = ConfigManager(script_dir)
            self.config = self.config_manager.load_config()
            self.setWindowTitle(t("gui_settings", "Settings"))
            self.setMinimumWidth(600)
            self.setMinimumHeight(500)
            self.init_ui()
            self.load_config()
            self.logger.info("ConfigDialog initialized successfully")
        except Exception as e:
            self.logger.log_exception_details(e, context="ConfigDialog.__init__")
            raise

    def init_ui(self):
        """Initialize UI with sidebar navigation"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Create sidebar (left) - use QListWidget for navigation
        sidebar = QListWidget()
        sidebar.setMaximumWidth(200)
        sidebar.setSpacing(2)
        sidebar.setCurrentRow(0)
        sidebar.currentRowChanged.connect(self.on_sidebar_changed)

        # Create stacked widget (right) - standard QStackedWidget
        self.stacked_widget = QStackedWidget()

        # Add all tabs to stacked widget and sidebar
        self.tab_pages = []

        # Page 1: Update Components
        components_tab = self.create_components_tab()
        self.stacked_widget.addWidget(components_tab)
        self.tab_pages.append(("gui_tab_components", "Update Components"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_components", "Update Components")))

        # Page 2: General Settings
        general_tab = self.create_general_tab()
        self.stacked_widget.addWidget(general_tab)
        self.tab_pages.append(("gui_tab_general", "General"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_general", "General")))

        # Page 3: Shortcut
        desktop_tab = self.create_desktop_tab()
        self.stacked_widget.addWidget(desktop_tab)
        self.tab_pages.append(("gui_shortcut", "Shortcut"))
        sidebar.addItem(QListWidgetItem(t("gui_shortcut", "Shortcut")))

        # Page 4: Logs
        logs_tab = self.create_logs_tab()
        self.stacked_widget.addWidget(logs_tab)
        self.tab_pages.append(("gui_tab_logs", "Logs"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_logs", "Logs")))

        # Page 5: System
        system_tab = self.create_system_tab()
        self.stacked_widget.addWidget(system_tab)
        self.tab_pages.append(("gui_tab_system", "System"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_system", "System")))

        # Page 6: Advanced Settings
        advanced_tab = self.create_advanced_tab()
        self.stacked_widget.addWidget(advanced_tab)
        self.tab_pages.append(("gui_tab_advanced", "Advanced"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_advanced", "Advanced")))

        # Page 7: Info
        info_tab = self.create_info_tab()
        self.stacked_widget.addWidget(info_tab)
        self.tab_pages.append(("gui_tab_info", "Info"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_info", "Info")))

        # Page 8: Update (NEW - Tool Update Management)
        update_tab = self.create_update_tab()
        self.stacked_widget.addWidget(update_tab)
        self.tab_pages.append(("gui_tab_update", "Update"))
        sidebar.addItem(QListWidgetItem(t("gui_tab_update", "Update")))

        # Store sidebar reference
        self.sidebar = sidebar

        # Add sidebar and stacked widget to main layout (following PyQt best practices)
        # Sidebar takes minimal space (stretch factor 0), content takes remaining (stretch factor 1)
        main_layout.addWidget(sidebar, 0)  # Sidebar takes minimal space
        main_layout.addWidget(self.stacked_widget, 1)  # Content takes remaining space

        # Create container widget for main layout
        container = QWidget()
        container.setLayout(main_layout)

        # Create outer layout for buttons
        layout = QVBoxLayout()
        layout.addWidget(container)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(12, 12, 12, 12)

        icon, text = get_fa_icon(
            "undo", t("gui_reset_to_defaults", "Reset to Defaults")
        )
        reset_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(reset_btn)
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        icon, text = get_fa_icon("times", t("gui_cancel", "Cancel"))
        cancel_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(cancel_btn)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        icon, text = get_fa_icon("save", t("gui_save", "Save"))
        save_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(save_btn)
        save_btn.clicked.connect(self.save_and_close)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_sidebar_changed(self, index: int):
        """Handle sidebar selection change (QListWidget)"""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)

    def create_components_tab(self):
        """Create update components tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox(t("gui_update_components", "Update Components"))
        group_layout = QVBoxLayout()

        # Use Font Awesome checkboxes for consistency
        try:
            from ..widgets import FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
            except ImportError:
                FACheckBox = QCheckBox  # Fallback

        self.enable_system = FACheckBox(t("system_updates", "System Updates (pacman)"))
        self.enable_aur = FACheckBox(t("aur_updates", "AUR Updates (yay/paru)"))
        self.enable_cursor = FACheckBox(t("cursor_editor_update", "Cursor Editor Update"))
        self.enable_adguard = FACheckBox(t("adguard_home_update", "AdGuard Home Update"))
        self.enable_flatpak = FACheckBox(t("flatpak_updates", "Flatpak Updates"))

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

    def create_desktop_tab(self):
        """Create desktop shortcut tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        desktop_info = QLabel(
            t(
                "gui_shortcut_info",
                "Create a shortcut for easy access (Desktop, Application Menu, or Taskbar)",
            )
        )
        desktop_info.setWordWrap(True)
        layout.addWidget(desktop_info)

        # Form layout for name and comment
        name_comment_form = QFormLayout()
        name_comment_form.setSpacing(16)
        name_comment_form.setVerticalSpacing(16)
        name_comment_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )

        # Shortcut name
        self.shortcut_name = QLineEdit()
        self.shortcut_name.setPlaceholderText("Update All")
        self.shortcut_name.setText("Update All")
        self.shortcut_name.setMinimumWidth(500)
        name_comment_form.addRow(t("gui_shortcut_name", "Name:"), self.shortcut_name)

        # Shortcut comment
        self.shortcut_comment = QLineEdit()
        self.shortcut_comment.setPlaceholderText(
            "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak"
        )
        self.shortcut_comment.setText(
            "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak"
        )
        self.shortcut_comment.setMinimumWidth(500)
        name_comment_form.addRow(
            t("gui_shortcut_comment", "Comment:"), self.shortcut_comment
        )

        layout.addLayout(name_comment_form)

        # Icon selection with preview side by side
        icon_form_layout = QFormLayout()
        icon_form_layout.setSpacing(16)
        icon_form_layout.setVerticalSpacing(16)
        icon_form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )

        icon_container = QWidget()
        icon_container_layout = QHBoxLayout()
        icon_container_layout.setSpacing(20)
        icon_container_layout.setContentsMargins(0, 0, 0, 0)

        # Icon selection (left side)
        icon_selection_widget = QWidget()
        icon_selection_layout = QVBoxLayout()
        icon_selection_layout.setSpacing(8)
        icon_selection_layout.setContentsMargins(0, 0, 0, 0)

        self.desktop_icon = QComboBox()
        # Common system icons (ensured unique icons)
        system_icons = [
            ("system-software-update", t("gui_icon_system_update", "System Update")),
            ("package-updater", t("gui_icon_update_manager", "Update Manager")),
            (
                "applications-system",
                t("gui_icon_applications_system", "Applications System"),
            ),
            ("preferences-system", t("gui_icon_distributor", "Distributor Logo")),
            (
                "system-file-manager",
                t("gui_icon_preferences_system", "Preferences System"),
            ),
            ("utilities-terminal", t("gui_icon_terminal", "Terminal")),
        ]
        for icon_name, icon_label_text in system_icons:
            self.desktop_icon.addItem(icon_label_text, icon_name)

        # Custom icon option
        self.desktop_icon.addItem(t("gui_icon_custom", "Custom Icon File..."), "custom")
        icon_selection_layout.addWidget(self.desktop_icon)

        # Custom icon file selector (hidden by default)
        self.custom_icon_path = QLineEdit()
        self.custom_icon_path.setPlaceholderText(
            t("gui_icon_custom_path", "Select icon file (PNG, SVG, etc.)")
        )
        self.custom_icon_path.setVisible(False)
        self.icon_browse_btn = QPushButton("...")
        self.icon_browse_btn.setFixedWidth(40)
        self.icon_browse_btn.clicked.connect(lambda: self.browse_icon_file())
        self.icon_browse_btn.setVisible(False)

        custom_icon_layout = QHBoxLayout()
        custom_icon_layout.setContentsMargins(0, 0, 0, 0)
        custom_icon_layout.setSpacing(8)
        custom_icon_layout.addWidget(self.custom_icon_path)
        custom_icon_layout.addWidget(self.icon_browse_btn)
        icon_selection_layout.addLayout(custom_icon_layout)

        # Show/hide custom icon path based on selection
        self.desktop_icon.currentIndexChanged.connect(self.on_icon_selection_changed)

        icon_selection_widget.setLayout(icon_selection_layout)
        icon_container_layout.addWidget(icon_selection_widget)

        # Icon preview (right side)
        preview_container = QWidget()
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(8)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel(t("gui_icon_preview", "Preview:"))
        preview_layout.addWidget(preview_label)

        self.icon_preview = QLabel()
        self.icon_preview.setMinimumSize(96, 96)
        self.icon_preview.setMaximumSize(96, 96)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview.setScaledContents(True)
        preview_layout.addWidget(self.icon_preview)
        preview_layout.addStretch()

        preview_container.setLayout(preview_layout)
        icon_container_layout.addWidget(preview_container)
        icon_container.setLayout(icon_container_layout)

        # Add icon container to form layout with label
        icon_form_layout.addRow(t("gui_icon", "Icon:"), icon_container)
        layout.addLayout(icon_form_layout)

        # Connect signals (update_icon_preview is called from on_icon_selection_changed, so no duplicate)
        self.custom_icon_path.textChanged.connect(self.update_icon_preview)
        # Initial preview update
        try:
            self.update_icon_preview()
        except (OSError, IOError, ValueError) as e:
            self.logger.debug(
                f"Failed to update icon preview during initialization: {e}"
            )
        except Exception as e:
            self.logger.warning(
                f"Unexpected error updating icon preview during initialization: {e}"
            )

        # Options section (Version and Location) - side by side
        options_container = QWidget()
        options_layout = QHBoxLayout()
        options_layout.setSpacing(24)
        options_layout.setContentsMargins(0, 0, 0, 0)

        # Shortcut version selection removed - always use GUI version
        # (Radio buttons for console/gui selection removed as requested)

        # Shortcut location (right)
        location_group = QGroupBox(t("gui_shortcut_type", "Create Shortcut"))
        location_layout = QVBoxLayout()
        location_layout.setSpacing(8)

        # Use Font Awesome checkboxes for consistency
        try:
            from ..widgets import FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
            except ImportError:
                FACheckBox = QCheckBox  # Fallback

        self.shortcut_app_menu = FACheckBox(
            t("gui_shortcut_app_menu", "Application Menu")
        )
        self.shortcut_desktop = FACheckBox(t("gui_shortcut_desktop", "Desktop"))

        self.shortcut_app_menu.setChecked(True)
        self.shortcut_desktop.setChecked(True)  # Desktop also selected by default

        location_layout.addWidget(self.shortcut_app_menu)
        location_layout.addWidget(self.shortcut_desktop)
        location_layout.addStretch()

        location_group.setLayout(location_layout)
        options_layout.addWidget(location_group)

        options_container.setLayout(options_layout)
        layout.addWidget(options_container)

        # Create shortcut button
        create_shortcut_btn = QPushButton(t("gui_create_shortcut", "Create Shortcut"))
        create_shortcut_btn.clicked.connect(self.create_desktop_shortcut)
        layout.addWidget(create_shortcut_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # GUI Language & Theme section
        appearance_group = QGroupBox(t("gui_appearance", "Appearance"))
        appearance_layout = QVBoxLayout()

        appearance_info = QLabel(
            t("gui_appearance_info", "Configure the appearance and language of the GUI")
        )
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

        options_info = QLabel(
            t("gui_options_info", "General options for update behavior")
        )
        options_info.setWordWrap(True)
        options_layout.addWidget(options_info)

        # Use Font Awesome checkboxes for consistency
        try:
            from ..widgets import FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
            except ImportError:
                FACheckBox = QCheckBox  # Fallback

        self.enable_notifications = FACheckBox(
            t("gui_enable_notifications", "Enable Notifications")
        )
        self.enable_colors = FACheckBox(t("gui_enable_colors", "Enable Colors"))
        self.dry_run = FACheckBox(t("gui_dry_run", "Dry Run Mode (test only)"))
        self.enable_auto_update = FACheckBox(
            t("gui_enable_auto_update", "Enable Auto Update")
        )

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

        logs_info = QLabel(
            t("gui_logs_info", "Configure log file settings and storage locations")
        )
        logs_info.setWordWrap(True)
        layout.addWidget(logs_info)

        form = QFormLayout()

        # Max log files
        self.max_log_files = QSpinBox()
        self.max_log_files.setMinimum(1)
        self.max_log_files.setMaximum(100)
        self.max_log_files.setToolTip(
            t(
                "gui_max_log_files_tooltip",
                "Maximum number of log files to keep. Older files will be automatically deleted.",
            )
        )
        form.addRow(t("gui_max_log_files", "Max Log Files:"), self.max_log_files)

        # Cache max age
        self.cache_max_age = QSpinBox()
        self.cache_max_age.setMinimum(60)
        self.cache_max_age.setMaximum(86400)
        self.cache_max_age.setSuffix(" " + t("gui_seconds", "seconds"))
        self.cache_max_age.setToolTip(
            t(
                "gui_cache_max_age_tooltip",
                "Maximum age of cached data in seconds before it is refreshed.",
            )
        )
        form.addRow(t("gui_cache_max_age", "Cache Max Age:"), self.cache_max_age)

        # Log directory
        log_layout = QHBoxLayout()
        self.log_dir = QLineEdit()
        self.log_dir.setToolTip(
            t("gui_log_dir_tooltip", "Directory where log files are stored")
        )
        icon, text = get_fa_icon("folder-open", t("gui_browse", "Browse..."))
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
        self.stats_dir.setToolTip(
            t("gui_stats_dir_tooltip", "Directory where statistics files are stored")
        )
        icon, text = get_fa_icon("folder-open", t("gui_browse", "Browse..."))
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

        pacman_info = QLabel(
            t(
                "gui_pacman_info",
                "Configure pacman command parameters for system updates",
            )
        )
        pacman_info.setWordWrap(True)
        pacman_layout.addWidget(pacman_info)

        # Use Font Awesome checkboxes for consistency
        try:
            from ..widgets import FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
            except ImportError:
                FACheckBox = QCheckBox  # Fallback

        self.pacman_sync = FACheckBox(t("gui_pacman_sync", "Sync (-S)"))
        self.pacman_refresh = FACheckBox(t("gui_pacman_refresh", "Refresh (-y)"))
        self.pacman_upgrade = FACheckBox(t("gui_pacman_upgrade", "Upgrade (-u)"))
        self.pacman_noconfirm = FACheckBox(
            t("gui_pacman_noconfirm", "No Confirm (--noconfirm)")
        )

        self.pacman_sync.setToolTip(
            t("gui_pacman_sync_tooltip", "Update package database before upgrading")
        )
        self.pacman_refresh.setToolTip(
            t("gui_pacman_refresh_tooltip", "Refresh package lists")
        )
        self.pacman_upgrade.setToolTip(
            t("gui_pacman_upgrade_tooltip", "Upgrade all installed packages")
        )
        self.pacman_noconfirm.setToolTip(
            t(
                "gui_pacman_noconfirm_tooltip",
                "Don't ask for confirmation (non-interactive mode)",
            )
        )

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

        sudo_info = QLabel(
            t(
                "gui_sudo_password_info",
                "Store sudo password for automatic updates (not recommended for security reasons)",
            )
        )
        sudo_info.setWordWrap(True)
        sudo_layout.addWidget(sudo_info)

        sudo_password_layout = QHBoxLayout()
        self.sudo_password = QLineEdit()
        self.sudo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.sudo_password.setPlaceholderText(
            t("gui_sudo_password_placeholder", "Leave empty to keep current password")
        )
        self.sudo_password.setToolTip(
            t(
                "gui_sudo_password_tooltip",
                "Enter sudo password to store for automatic updates",
            )
        )
        sudo_password_layout.addWidget(QLabel(t("gui_password", "Password:")))
        sudo_password_layout.addWidget(self.sudo_password)
        sudo_layout.addLayout(sudo_password_layout)

        # Use Font Awesome checkboxes for consistency
        try:
            from ..widgets import FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
            except ImportError:
                FACheckBox = QCheckBox  # Fallback

        self.save_sudo_password = FACheckBox(
            t("gui_save_password", "Save password (encrypted)")
        )
        self.save_sudo_password.setToolTip(
            t(
                "gui_save_password_tooltip",
                "Save password securely (System Keyring or encryption)",
            )
        )
        sudo_layout.addWidget(self.save_sudo_password)

        sudo_group.setLayout(sudo_layout)
        layout.addWidget(sudo_group)

        # Download Retries section
        retries_group = QGroupBox(t("gui_download_retries", "Download Retries"))
        retries_layout = QVBoxLayout()

        retries_info = QLabel(
            t(
                "gui_download_retries_info",
                "Number of retry attempts for failed downloads",
            )
        )
        retries_info.setWordWrap(True)
        retries_layout.addWidget(retries_info)

        retries_form = QFormLayout()
        self.download_retries = QSpinBox()
        self.download_retries.setMinimum(1)
        self.download_retries.setMaximum(10)
        self.download_retries.setToolTip(
            t(
                "gui_download_retries_tooltip",
                "How many times to retry a failed download before giving up",
            )
        )
        retries_form.addRow(
            t("gui_download_retries", "Download Retries:"), self.download_retries
        )
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

        advanced_info = QLabel(
            t(
                "gui_advanced_info",
                "Advanced settings for power users. Change these only if you know what you're doing.",
            )
        )
        advanced_info.setWordWrap(True)
        layout.addWidget(advanced_info)

        form = QFormLayout()

        # GitHub Repository URL
        self.github_repo = QLineEdit()
        self.github_repo.setToolTip(
            t(
                "gui_github_repo_tooltip",
                "GitHub repository URL for version checks and updates (format: owner/repo)",
            )
        )
        form.addRow(t("gui_github_repo", "GitHub Repository URL:"), self.github_repo)

        # Script path
        script_layout = QHBoxLayout()
        self.script_path = QLineEdit()
        self.script_path.setToolTip(
            t("gui_script_path_tooltip", "Path to the update-all.sh script")
        )
        icon, text = get_fa_icon("folder-open", t("gui_browse", "Browse..."))
        script_browse = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(script_browse)
        script_browse.clicked.connect(lambda: self.browse_file(self.script_path))
        script_layout.addWidget(self.script_path)
        script_layout.addWidget(script_browse)
        form.addRow(t("gui_script_path", "Script Path:"), script_layout)

        layout.addLayout(form)

        # Cleanup Settings Group
        cleanup_group = QGroupBox(t("gui_cleanup_settings", "Cleanup Settings"))
        cleanup_layout = QVBoxLayout()

        cleanup_info = QLabel(
            t("gui_cleanup_info", "Configure system cleanup behavior after updates")
        )
        cleanup_info.setWordWrap(True)
        cleanup_layout.addWidget(cleanup_info)

        cleanup_form = QFormLayout()

        # Cleanup Aggressiveness
        self.cleanup_aggressiveness = QComboBox()
        self.cleanup_aggressiveness.addItems(
            [
                t("gui_cleanup_safe", "Safe"),
                t("gui_cleanup_moderate", "Moderate"),
                t("gui_cleanup_aggressive", "Aggressive"),
            ]
        )
        self.cleanup_aggressiveness.setToolTip(
            t(
                "gui_cleanup_aggressiveness_tooltip",
                "Safe: Only obvious unused files\nModerate: Includes old caches (with confirmation)\nAggressive: All caches, temp files, old backups",
            )
        )
        cleanup_form.addRow(
            t("gui_cleanup_aggressiveness", "Cleanup Aggressiveness:"),
            self.cleanup_aggressiveness,
        )

        # Cleanup Timing
        self.cleanup_timing = QComboBox()
        self.cleanup_timing.addItems(
            [
                t("gui_cleanup_after_updates", "After Updates"),
                t("gui_cleanup_manual", "Manual Only"),
                t("gui_cleanup_never", "Never"),
            ]
        )
        self.cleanup_timing.setToolTip(
            t("gui_cleanup_timing_tooltip", "When to perform cleanup operations")
        )
        cleanup_form.addRow(
            t("gui_cleanup_timing", "Cleanup Timing:"), self.cleanup_timing
        )

        # Cleanup Options - Use FACheckBox for consistency
        try:
            from ..widgets import FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
            except ImportError:
                FACheckBox = (
                    QCheckBox  # Fallback to QCheckBox if FACheckBox not available
                )

        self.cleanup_orphans = FACheckBox(
            t("gui_cleanup_orphans", "Remove Orphan Packages")
        )
        self.cleanup_orphans.setToolTip(
            t(
                "gui_cleanup_orphans_tooltip",
                "Remove packages that are no longer needed",
            )
        )
        cleanup_form.addRow("", self.cleanup_orphans)

        self.cleanup_cache = FACheckBox(t("gui_cleanup_cache", "Clean Package Cache"))
        self.cleanup_cache.setToolTip(
            t("gui_cleanup_cache_tooltip", "Clean package manager cache")
        )
        cleanup_form.addRow("", self.cleanup_cache)

        self.cleanup_temp = FACheckBox(t("gui_cleanup_temp", "Remove Temporary Files"))
        self.cleanup_temp.setToolTip(
            t("gui_cleanup_temp_tooltip", "Remove temporary files from /tmp")
        )
        cleanup_form.addRow("", self.cleanup_temp)

        # Icon Cache Update
        self.icon_cache_update = QComboBox()
        self.icon_cache_update.addItems(
            [
                t("gui_icon_cache_both", "Both (After Shortcuts & Updates)"),
                t("gui_icon_cache_after_shortcut", "After Creating Shortcuts"),
                t("gui_icon_cache_after_updates", "After Updates"),
                t("gui_icon_cache_manual", "Manual Only"),
            ]
        )
        self.icon_cache_update.setToolTip(
            t(
                "gui_icon_cache_update_tooltip",
                "When to update icon caches (GTK, KDE, Desktop Database)",
            )
        )
        cleanup_form.addRow(
            t("gui_icon_cache_update", "Icon Cache Update:"), self.icon_cache_update
        )

        cleanup_layout.addLayout(cleanup_form)
        cleanup_group.setLayout(cleanup_layout)
        layout.addWidget(cleanup_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_info_tab(self):
        """Create info tab with tool and system information"""
        widget = QWidget()
        layout = QVBoxLayout()

        import platform
        import subprocess

        # Tool Information
        tool_group = QGroupBox(t("gui_info_tool", "Tool Information"))
        tool_layout = QVBoxLayout()

        # Read script version from VERSION file (root), fallback to update-all.sh
        import re

        root_dir = Path(self.script_dir).parent
        version_file = root_dir / "VERSION"
        local_version = "unknown"
        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version = f.read().strip()
                    # Validate version format (should be like "1.0.15")
                    if re.match(r"^\d+\.\d+\.\d+$", version):
                        local_version = version
            except Exception as e:
                self.logger.debug(f"Failed to read version from VERSION file: {e}")

        # Fallback: Read from update-all.sh
        if local_version == "unknown":
            script_path = Path(self.script_dir) / "update-all.sh"
            if script_path.exists():
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if "readonly SCRIPT_VERSION=" in line:
                                match = re.search(r'["\']([0-9.]+)["\']', line)
                                if match:
                                    local_version = match.group(1)
                                    break
                except (OSError, IOError) as e:
                    self.logger.debug(
                        f"Failed to read script version from update-all.sh: {e}"
                    )
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Failed to parse script version: {e}")
                except Exception as e:
                    self.logger.warning(f"Unexpected error reading script version: {e}")

        # Get GitHub version
        github_version = "checking..."
        try:
            from ..utils.version_checker import VersionChecker
            github_repo = self.config.get(
                "GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"
            )
            checker = VersionChecker(str(self.script_dir), github_repo)
            latest, error = checker.check_latest_version()
            if latest and not error:
                github_version = latest
            elif error:
                github_version = f"error: {error}"
        except (ImportError, AttributeError) as e:
            self.logger.debug(
                f"Failed to check GitHub version (module import/attribute error): {e}"
            )
            github_version = "unavailable"
        except Exception as e:
            self.logger.warning(f"Unexpected error checking GitHub version: {e}")
            github_version = "unavailable"

        # Version comparison
        version_status = ""
        try:
            local_parts = [int(x) for x in local_version.split(".")]
            github_parts = [int(x) for x in github_version.split(".")]
            if github_parts > local_parts:
                version_status = f" ({t('gui_update_available', 'Update available!')})"
            elif github_parts == local_parts:
                version_status = f" ({t('gui_version_up_to_date', 'Up to date')})"
        except (ValueError, AttributeError) as e:
            self.logger.debug(f"Failed to compare versions: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error comparing versions: {e}")

        tool_info = QTextEdit()
        tool_info.setReadOnly(True)
        tool_info.setMaximumHeight(150)
        tool_info_text = f"""{t("gui_info_tool_name", "Tool Name")}: CachyOS Multi-Updater
{t("gui_info_version_local", "Local Version")}: {local_version}
{t("gui_info_version_github", "GitHub Version")}: {github_version}{version_status}
{t("gui_info_github_repo", "GitHub Repository")}: {self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater")}
{t("gui_info_author", "Author")}: Sunny C.
{t("gui_info_website", "Website")}: https://benjaro.info
{t("gui_info_year", "Year")}: 2025"""
        tool_info.setPlainText(tool_info_text.strip())
        tool_layout.addWidget(tool_info)

        tool_group.setLayout(tool_layout)
        layout.addWidget(tool_group)

        # System Information
        system_group = QGroupBox(t("gui_info_system", "System Information"))
        system_layout = QVBoxLayout()

        system_info = QTextEdit()
        system_info.setReadOnly(True)
        system_info.setFont(QFont("Monospace", 9))

        # Get system info
        system_info_text = ""

        # OS
        try:
            with open("/etc/os-release", "r") as f:
                os_info = {}
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key] = value.strip('"')
                os_name = os_info.get("PRETTY_NAME", os_info.get("NAME", "Unknown"))
                system_info_text += (
                    f"{t('gui_info_os', 'Operating System')}: {os_name}\n"
                )
        except (OSError, IOError) as e:
            self.logger.debug(f"Failed to read /etc/os-release: {e}")
            try:
                system_info_text += (
                    f"{t('gui_info_os', 'Operating System')}: {platform.system()}\n"
                )
            except (AttributeError, OSError) as e2:
                self.logger.debug(f"Failed to get OS info from platform: {e2}")
                system_info_text += f"{t('gui_info_os', 'Operating System')}: Unknown\n"
        except Exception as e:
            self.logger.warning(f"Unexpected error getting OS info: {e}")
            try:
                system_info_text += (
                    f"{t('gui_info_os', 'Operating System')}: {platform.system()}\n"
                )
            except Exception:
                system_info_text += f"{t('gui_info_os', 'Operating System')}: Unknown\n"

        # Kernel
        try:
            kernel = platform.release()
            system_info_text += f"{t('gui_info_kernel', 'Kernel')}: {kernel}\n"
        except Exception:
            pass

        # CPU
        try:
            cpu_info = platform.processor()
            if not cpu_info or cpu_info == "":
                # Try to get CPU info from /proc/cpuinfo
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line.lower():
                            cpu_info = line.split(":", 1)[1].strip()
                            break
            system_info_text += f"{t('gui_info_cpu', 'CPU')}: {cpu_info}\n"
        except (OSError, IOError, ValueError) as e:
            self.logger.debug(f"Failed to get CPU info: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error getting CPU info: {e}")

        # Memory
        try:
            with open("/proc/meminfo", "r") as f:
                mem_total = 0
                mem_available = 0
                for line in f:
                    if "MemTotal:" in line:
                        mem_total = int(line.split()[1]) // 1024  # Convert to MB
                    elif "MemAvailable:" in line:
                        mem_available = int(line.split()[1]) // 1024
                        break
                mem_used = mem_total - mem_available
                mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
                system_info_text += f"{t('gui_info_memory', 'Memory')}: {mem_used} MB / {mem_total} MB ({mem_percent:.1f}%)\n"
        except (OSError, IOError, ValueError, ZeroDivisionError) as e:
            self.logger.debug(f"Failed to get memory info: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error getting memory info: {e}")

        # Packages
        try:
            # Pacman packages
            result = subprocess.run(
                ["pacman", "-Q"], capture_output=True, text=True, timeout=2
            )
            pacman_count = (
                len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
            )

            # Flatpak packages
            flatpak_count = 0
            try:
                result = subprocess.run(
                    ["flatpak", "list"], capture_output=True, text=True, timeout=2
                )
                flatpak_count = (
                    len(result.stdout.strip().split("\n"))
                    if result.stdout.strip()
                    else 0
                )
            except (
                subprocess.TimeoutExpired,
                subprocess.SubprocessError,
                FileNotFoundError,
            ) as e:
                self.logger.debug(f"Failed to get flatpak package count: {e}")
            except Exception as e:
                self.logger.warning(
                    f"Unexpected error getting flatpak package count: {e}"
                )

            system_info_text += f"{t('gui_info_packages', 'Packages')}: {pacman_count} (pacman), {flatpak_count} (flatpak)\n"
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ) as e:
            self.logger.debug(f"Failed to get package counts: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error getting package counts: {e}")

        # Uptime
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                system_info_text += (
                    f"{t('gui_info_uptime', 'Uptime')}: {hours}h {minutes}m\n"
                )
        except (OSError, IOError, ValueError) as e:
            self.logger.debug(f"Failed to get uptime info: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error getting uptime info: {e}")

        system_info.setPlainText(system_info_text.strip())
        system_layout.addWidget(system_info)

        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        # Wine, Proton-GE and Steam detection
        gaming_group = QGroupBox(t("gui_info_gaming", "Gaming Software"))
        gaming_layout = QVBoxLayout()

        gaming_info = QTextEdit()
        gaming_info.setReadOnly(True)
        gaming_info.setMaximumHeight(100)
        gaming_info_text = ""

        # Check for Wine
        try:
            result = subprocess.run(
                ["which", "wine"], capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                wine_version = subprocess.run(
                    ["wine", "--version"], capture_output=True, text=True, timeout=1
                )
                if wine_version.returncode == 0:
                    gaming_info_text += f"Wine: {wine_version.stdout.strip()}\n"
                else:
                    gaming_info_text += "Wine: Installed\n"
            else:
                gaming_info_text += "Wine: Not installed\n"
        except Exception:
            gaming_info_text += "Wine: Unknown\n"

        # Check for Proton-GE
        try:
            proton_paths = [
                Path.home() / ".steam" / "steam" / "compatibilitytools.d",
                Path.home() / ".local" / "share" / "Steam" / "compatibilitytools.d",
            ]
            proton_found = False
            for path in proton_paths:
                if path.exists():
                    proton_dirs = [
                        d for d in path.iterdir() if d.is_dir() and "Proton" in d.name
                    ]
                    if proton_dirs:
                        gaming_info_text += (
                            f"Proton-GE: Installed ({len(proton_dirs)} version(s))\n"
                        )
                        proton_found = True
                        break
            if not proton_found:
                gaming_info_text += "Proton-GE: Not installed\n"
        except Exception:
            gaming_info_text += "Proton-GE: Unknown\n"

        # Check for Steam
        try:
            result = subprocess.run(
                ["which", "steam"], capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                gaming_info_text += "Steam: Installed\n"
            else:
                gaming_info_text += "Steam: Not installed\n"
        except Exception:
            gaming_info_text += "Steam: Unknown\n"

        gaming_info.setPlainText(gaming_info_text.strip())
        gaming_layout.addWidget(gaming_info)
        gaming_group.setLayout(gaming_layout)
        layout.addWidget(gaming_group)

        # Update Statistics
        stats_group = QGroupBox(t("gui_info_statistics", "Update Statistics"))
        stats_layout = QVBoxLayout()

        stats_info = QTextEdit()
        stats_info.setReadOnly(True)
        stats_info.setMaximumHeight(150)
        stats_info_text = ""

        # Load statistics from JSON file
        # Use configured STATS_DIR or default to .stats
        stats_dir_path = self.config.get(
            "STATS_DIR", str(Path(self.script_dir) / ".stats")
        )
        stats_dir = Path(stats_dir_path)
        stats_file = stats_dir / "stats.json"

        try:
            if stats_file.exists():
                import json

                with open(stats_file, "r", encoding="utf-8") as f:
                    stats_data = json.load(f)

                total_updates = stats_data.get("total_updates", 0)
                successful = stats_data.get("successful_updates", 0)
                failed = stats_data.get("failed_updates", 0)
                avg_duration = stats_data.get("avg_duration", 0)
                last_update = stats_data.get("last_update", "")
                last_duration = stats_data.get("last_duration", 0)

                # Calculate success rate
                success_rate = 0
                if total_updates > 0:
                    success_rate = (successful * 100) // total_updates

                # Format average duration
                avg_minutes = avg_duration // 60
                avg_seconds = avg_duration % 60

                # Format last update date
                last_update_formatted = "Never"
                if last_update:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                        last_update_formatted = dt.strftime("%d.%m.%Y %H:%M")
                    except Exception:
                        last_update_formatted = last_update

                # Format last duration
                last_minutes = last_duration // 60
                last_seconds = last_duration % 60

                stats_info_text = f"{t('gui_stats_total_updates', 'Total Updates')}: {total_updates}\n"
                stats_info_text += (
                    f"{t('gui_stats_successful', 'Successful')}: {successful}\n"
                )
                stats_info_text += f"{t('gui_stats_failed', 'Failed')}: {failed}\n"
                stats_info_text += (
                    f"{t('gui_stats_success_rate', 'Success Rate')}: {success_rate}%\n"
                )
                stats_info_text += f"{t('gui_stats_avg_duration', 'Average Duration')}: {avg_minutes}m {avg_seconds}s\n"
                stats_info_text += f"{t('gui_stats_last_update', 'Last Update')}: {last_update_formatted}\n"
                if last_duration > 0:
                    stats_info_text += f"{t('gui_stats_last_duration', 'Last Duration')}: {last_minutes}m {last_seconds}s"
            else:
                stats_info_text = t(
                    "gui_stats_no_data",
                    "No statistics available yet.\nRun an update to generate statistics.",
                )
        except Exception as e:
            self.logger.debug(f"Failed to load statistics: {e}")
            stats_info_text = t("gui_stats_error", "Error loading statistics")

        stats_info.setPlainText(stats_info_text.strip())
        stats_layout.addWidget(stats_info)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def browse_directory(self, line_edit: QLineEdit):
        """Browse for directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", line_edit.text()
        )
        if directory:
            line_edit.setText(directory)

    def browse_file(self, line_edit: QLineEdit):
        """Browse for file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", line_edit.text()
        )
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
        self.enable_system.setChecked(
            self.config.get("ENABLE_SYSTEM_UPDATE", "true") == "true"
        )
        self.enable_aur.setChecked(
            self.config.get("ENABLE_AUR_UPDATE", "true") == "true"
        )
        self.enable_cursor.setChecked(
            self.config.get("ENABLE_CURSOR_UPDATE", "true") == "true"
        )
        self.enable_adguard.setChecked(
            self.config.get("ENABLE_ADGUARD_UPDATE", "true") == "true"
        )
        self.enable_flatpak.setChecked(
            self.config.get("ENABLE_FLATPAK_UPDATE", "true") == "true"
        )

        # General
        self.max_log_files.setValue(int(self.config.get("MAX_LOG_FILES", "3")))
        self.download_retries.setValue(int(self.config.get("DOWNLOAD_RETRIES", "3")))
        self.cache_max_age.setValue(int(self.config.get("CACHE_MAX_AGE", "3600")))
        self.enable_notifications.setChecked(
            self.config.get("ENABLE_NOTIFICATIONS", "true") == "true"
        )
        self.enable_colors.setChecked(
            self.config.get("ENABLE_COLORS", "true") == "true"
        )
        self.dry_run.setChecked(self.config.get("DRY_RUN", "false") == "true")
        self.enable_auto_update.setChecked(
            self.config.get("ENABLE_AUTO_UPDATE", "false") == "true"
        )

        # Sudo password (don't show actual password, just indicate if stored)
        # Check if password is stored securely
        try:
            from .password_manager import PasswordManager
        except ImportError:
            try:
                from password_manager import PasswordManager
            except ImportError:
                PasswordManager = None

        has_stored_password = False
        if PasswordManager:
            password_manager = PasswordManager(str(self.script_dir))
            stored_password = password_manager.get_password()
            has_stored_password = bool(stored_password)
            # Also check config marker for backward compatibility
            if not has_stored_password:
                has_stored_password = bool(
                    self.config.get("SUDO_PASSWORD_STORED") == "true"
                )

        self.save_sudo_password.setChecked(has_stored_password)
        if has_stored_password:
            storage_method = self.config.get("SUDO_PASSWORD_METHOD", "secure storage")
            self.sudo_password.setPlaceholderText(
                t(
                    "gui_password_stored",
                    f"Password is stored ({storage_method}) - enter new to change",
                )
            )

        # System - Pacman (set defaults if not in config)
        self.pacman_sync.setChecked(self.config.get("PACMAN_SYNC", "true") == "true")
        self.pacman_refresh.setChecked(
            self.config.get("PACMAN_REFRESH", "true") == "true"
        )
        self.pacman_upgrade.setChecked(
            self.config.get("PACMAN_UPGRADE", "true") == "true"
        )
        self.pacman_noconfirm.setChecked(
            self.config.get("PACMAN_NOCONFIRM", "true") == "true"
        )

        # Desktop shortcut name/comment
        if hasattr(self, "shortcut_name"):
            self.shortcut_name.setText(self.config.get("SHORTCUT_NAME", "Update All"))
        if hasattr(self, "shortcut_comment"):
            self.shortcut_comment.setText(
                self.config.get(
                    "SHORTCUT_COMMENT",
                    "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak",
                )
            )

        # Advanced
        self.github_repo.setText(
            self.config.get("GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater")
        )
        self.log_dir.setText(
            self.config.get("LOG_DIR", str(Path(self.script_dir) / "logs"))
        )
        self.stats_dir.setText(
            self.config.get("STATS_DIR", str(Path(self.script_dir) / ".stats"))
        )
        self.script_path.setText(
            self.config.get("SCRIPT_PATH", str(Path(self.script_dir) / "update-all.sh"))
        )

        # Cleanup Settings
        if hasattr(self, "cleanup_aggressiveness"):
            aggressiveness = self.config.get("CLEANUP_AGGRESSIVENESS", "moderate")
            index_map = {"safe": 0, "moderate": 1, "aggressive": 2}
            self.cleanup_aggressiveness.setCurrentIndex(
                index_map.get(aggressiveness, 1)
            )

        if hasattr(self, "cleanup_timing"):
            timing = self.config.get("CLEANUP_TIMING", "after_updates")
            index_map = {"after_updates": 0, "manual": 1, "never": 2}
            self.cleanup_timing.setCurrentIndex(index_map.get(timing, 0))

        if hasattr(self, "cleanup_orphans"):
            self.cleanup_orphans.setChecked(
                self.config.get("CLEANUP_ORPHANS", "true") == "true"
            )

        if hasattr(self, "cleanup_cache"):
            self.cleanup_cache.setChecked(
                self.config.get("CLEANUP_CACHE", "true") == "true"
            )

        if hasattr(self, "cleanup_temp"):
            self.cleanup_temp.setChecked(
                self.config.get("CLEANUP_TEMP_FILES", "true") == "true"
            )

        if hasattr(self, "icon_cache_update"):
            icon_cache = self.config.get("ICON_CACHE_UPDATE", "both")
            index_map = {
                "both": 0,
                "after_shortcut": 1,
                "after_updates": 2,
                "manual": 3,
            }
            self.icon_cache_update.setCurrentIndex(index_map.get(icon_cache, 0))

        self.update_command_preview()

    def save_config(self):
        """Save config from UI"""
        # Components
        self.config["ENABLE_SYSTEM_UPDATE"] = str(
            self.enable_system.isChecked()
        ).lower()
        self.config["ENABLE_AUR_UPDATE"] = str(self.enable_aur.isChecked()).lower()
        self.config["ENABLE_CURSOR_UPDATE"] = str(
            self.enable_cursor.isChecked()
        ).lower()
        self.config["ENABLE_ADGUARD_UPDATE"] = str(
            self.enable_adguard.isChecked()
        ).lower()
        self.config["ENABLE_FLATPAK_UPDATE"] = str(
            self.enable_flatpak.isChecked()
        ).lower()

        # General
        self.config["MAX_LOG_FILES"] = str(self.max_log_files.value())
        self.config["DOWNLOAD_RETRIES"] = str(self.download_retries.value())
        self.config["CACHE_MAX_AGE"] = str(self.cache_max_age.value())
        self.config["ENABLE_NOTIFICATIONS"] = str(
            self.enable_notifications.isChecked()
        ).lower()
        self.config["ENABLE_COLORS"] = str(self.enable_colors.isChecked()).lower()
        self.config["DRY_RUN"] = str(self.dry_run.isChecked()).lower()
        self.config["ENABLE_AUTO_UPDATE"] = str(
            self.enable_auto_update.isChecked()
        ).lower()

        # Sudo password (save securely using PasswordManager)
        try:
            from .password_manager import PasswordManager
        except ImportError:
            try:
                from password_manager import PasswordManager
            except ImportError:
                PasswordManager = None

        # Handle sudo password saving
        if PasswordManager and hasattr(self, "sudo_password"):
            password_text = self.sudo_password.text()
            password_manager = PasswordManager(str(self.script_dir))
            had_stored_password = self.config.get("SUDO_PASSWORD_STORED") == "true"

            if (
                hasattr(self, "save_sudo_password")
                and self.save_sudo_password.isChecked()
            ):
                # Checkbox is checked - save password if provided
                if password_text:
                    # Save new password securely
                    if password_manager.is_available():
                        if password_manager.save_password(password_text):
                            # Store marker in config (not the password itself)
                            self.config["SUDO_PASSWORD_STORED"] = "true"
                            self.config["SUDO_PASSWORD_METHOD"] = (
                                password_manager.get_storage_method()
                            )
                        else:
                            # Fallback: warn user
                            from PyQt6.QtWidgets import QMessageBox

                            QMessageBox.warning(
                                self,
                                t("gui_error", "Error"),
                                t(
                                    "gui_password_save_failed",
                                    "Failed to save password securely. Please install python-keyring or cryptography.",
                                ),
                            )
                    else:
                        # No secure storage available
                        from PyQt6.QtWidgets import QMessageBox

                        QMessageBox.warning(
                            self,
                            t("gui_error", "Error"),
                            t(
                                "gui_password_storage_unavailable",
                                "Secure password storage not available. Please install python-keyring or cryptography.",
                            ),
                        )
                # If password field is empty but checkbox is checked, keep existing password
            else:
                # Checkbox is unchecked
                # IMPORTANT: Only delete password if:
                # 1. User had a stored password before (had_stored_password == True)
                # 2. AND password field is empty (user didn't enter a new password)
                # This means: User explicitly unchecked checkbox AND wants to remove stored password
                #
                # If password field has text but checkbox is unchecked:
                # - Don't save the new password (checkbox unchecked)
                # - But DON'T delete the old password (user might just be testing/entering)
                # - Only delete if field is empty (explicit removal intent)
                if had_stored_password and not password_text:
                    # User had stored password, checkbox is unchecked, and field is empty
                    # This indicates explicit intent to remove stored password
                    password_manager.delete_password()
                    self.config.pop("SUDO_PASSWORD_STORED", None)
                    self.config.pop("SUDO_PASSWORD_METHOD", None)
                # Otherwise: checkbox unchecked but password field has text -> don't save new, but keep old
                # Or: checkbox unchecked, no stored password -> nothing to do

        # Advanced
        if self.github_repo.text():
            self.config["GITHUB_REPO"] = self.github_repo.text()
        if self.log_dir.text():
            self.config["LOG_DIR"] = self.log_dir.text()
        if self.stats_dir.text():
            self.config["STATS_DIR"] = self.stats_dir.text()
        if self.script_path.text():
            self.config["SCRIPT_PATH"] = self.script_path.text()

        # Desktop shortcut name/comment
        if hasattr(self, "shortcut_name"):
            self.config["SHORTCUT_NAME"] = self.shortcut_name.text() or "Update All"
        if hasattr(self, "shortcut_comment"):
            self.config["SHORTCUT_COMMENT"] = (
                self.shortcut_comment.text()
                or "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak"
            )

        # GUI Language
        self.config["GUI_LANGUAGE"] = self.gui_language.itemData(
            self.gui_language.currentIndex()
        )

        # GUI Theme
        self.config["GUI_THEME"] = self.gui_theme.itemData(
            self.gui_theme.currentIndex()
        )

        # Pacman
        self.config["PACMAN_SYNC"] = str(self.pacman_sync.isChecked()).lower()
        self.config["PACMAN_REFRESH"] = str(self.pacman_refresh.isChecked()).lower()
        self.config["PACMAN_UPGRADE"] = str(self.pacman_upgrade.isChecked()).lower()
        self.config["PACMAN_NOCONFIRM"] = str(self.pacman_noconfirm.isChecked()).lower()

        # Cleanup Settings
        if hasattr(self, "cleanup_aggressiveness"):
            aggressiveness_map = {0: "safe", 1: "moderate", 2: "aggressive"}
            self.config["CLEANUP_AGGRESSIVENESS"] = aggressiveness_map.get(
                self.cleanup_aggressiveness.currentIndex(), "moderate"
            )

        if hasattr(self, "cleanup_timing"):
            timing_map = {0: "after_updates", 1: "manual", 2: "never"}
            self.config["CLEANUP_TIMING"] = timing_map.get(
                self.cleanup_timing.currentIndex(), "after_updates"
            )

        if hasattr(self, "cleanup_orphans"):
            self.config["CLEANUP_ORPHANS"] = str(
                self.cleanup_orphans.isChecked()
            ).lower()

        if hasattr(self, "cleanup_cache"):
            self.config["CLEANUP_CACHE"] = str(self.cleanup_cache.isChecked()).lower()

        if hasattr(self, "cleanup_temp"):
            self.config["CLEANUP_TEMP_FILES"] = str(
                self.cleanup_temp.isChecked()
            ).lower()

        if hasattr(self, "icon_cache_update"):
            icon_cache_map = {
                0: "both",
                1: "after_shortcut",
                2: "after_updates",
                3: "manual",
            }
            self.config["ICON_CACHE_UPDATE"] = icon_cache_map.get(
                self.icon_cache_update.currentIndex(), "both"
            )

        return self.config_manager.save_config(self.config)

    def reset_to_defaults(self):
        """Reset to default values"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config = self.config_manager.load_config()
            self.load_config()

    def on_icon_selection_changed(self, index):
        """Handle icon selection change"""
        try:
            icon_data = self.desktop_icon.itemData(index)
            if icon_data == "custom":
                self.custom_icon_path.setVisible(True)
                self.icon_browse_btn.setVisible(True)
            else:
                self.custom_icon_path.setVisible(False)
                self.icon_browse_btn.setVisible(False)
            # Update preview
            self.update_icon_preview()
        except (OSError, IOError, ValueError) as e:
            self.logger.debug(f"Failed to update icon preview: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error updating icon preview: {e}")

    def browse_icon_file(self):
        """Browse for custom icon file"""
        icon_file, _ = QFileDialog.getOpenFileName(
            self,
            t("gui_select_icon", "Select Icon File"),
            "",
            "Image Files (*.png *.svg *.xpm *.ico);;All Files (*)",
        )
        if icon_file:
            self.custom_icon_path.setText(icon_file)

    def update_icon_preview(self):
        """Update icon preview"""
        # Update preview border color based on theme
        try:
            from ..ui.theme_manager import ThemeManager
        except ImportError:
            from gui.ui.theme_manager import ThemeManager

        theme_mode = self.config_manager.get("GUI_THEME", "auto")
        if theme_mode == "auto":
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = theme_mode

        border_color = "#555555" if actual_theme == "dark" else "#cccccc"
        bg_color = "#2b2b2b" if actual_theme == "dark" else "#f0f0f0"
        self.icon_preview.setStyleSheet(
            f"border: 1px solid {border_color}; border-radius: 4px; background-color: {bg_color};"
        )

        icon_data = self.desktop_icon.itemData(self.desktop_icon.currentIndex())

        if icon_data == "custom":
            icon_path = self.custom_icon_path.text()
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        96,
                        96,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
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
                pixmap = icon.pixmap(96, 96)
                if not pixmap.isNull():
                    self.icon_preview.clear()  # Clear any text first
                    self.icon_preview.setPixmap(pixmap)
                    return

            # Try to find icon in standard paths
            from PyQt6.QtCore import QStandardPaths

            icon_paths = QStandardPaths.standardLocations(
                QStandardPaths.StandardLocation.IconThemePath
            )
            for icon_path in icon_paths:
                # Try different sizes and formats
                for size in ["64x64", "48x48", "32x32", "scalable"]:
                    for ext in ["png", "svg", "xpm"]:
                        test_path = f"{icon_path}/{icon_name}/{size}/icon.{ext}"
                        if os.path.exists(test_path):
                            pixmap = QPixmap(test_path)
                            if not pixmap.isNull():
                                pixmap = pixmap.scaled(
                                    96,
                                    96,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation,
                                )
                                self.icon_preview.clear()
                                self.icon_preview.setPixmap(pixmap)
                                return

        # Fallback: show text (only if no icon could be loaded)
        self.icon_preview.clear()  # Clear pixmap first
        self.icon_preview.setText(t("gui_icon_preview", "Preview"))

    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        self.logger.info("create_desktop_shortcut() called")
        try:
            script_dir = Path(self.script_dir)
            script_path = script_dir / "update-all.sh"
            self.logger.debug(f"Script path: {script_path}")

            if not script_path.exists():
                self.logger.error(f"Script not found: {script_path}")
                QMessageBox.critical(
                    self,
                    t("gui_error", "Error"),
                    t("gui_script_not_found", "update-all.sh not found!"),
                )
                return

            # Get icon
            try:
                current_index = self.desktop_icon.currentIndex()
                self.logger.debug(f"Getting icon data for index: {current_index}")
                icon_data = self.desktop_icon.itemData(current_index)
                self.logger.debug(f"Icon data: {icon_data}")
            except Exception as e:
                self.logger.log_exception_details(e, context="Getting icon data")
                icon_data = "system-software-update"  # Fallback
                self.logger.warning(f"Using fallback icon: {icon_data}")

            if icon_data == "custom":
                icon_value = self.custom_icon_path.text()
                self.logger.debug(f"Custom icon path: {icon_value}")
                if not icon_value or not os.path.exists(icon_value):
                    self.logger.error(f"Custom icon file not found: {icon_value}")
                    QMessageBox.warning(
                        self,
                        t("gui_error", "Error"),
                        t("gui_icon_not_found", "Please select a valid icon file!"),
                    )
                    return
            else:
                icon_value = icon_data if icon_data else "system-software-update"
                self.logger.debug(f"Using system icon: {icon_value}")

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
            if self.shortcut_app_menu.isChecked():
                app_dir.mkdir(parents=True, exist_ok=True)

            # Create desktop entry content
            script_abs_path = script_path.absolute()

            # Helper function to escape desktop entry values
            def escape_desktop_entry_value(value: str) -> str:
                """Escape value for desktop entry file according to Desktop Entry Specification"""
                if not value:
                    return ""
                # Escape according to Desktop Entry Specification
                # Order matters: backslash must be escaped first!
                return (
                    value.replace("\\", "\\\\")  # Backslash first!
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                    .replace("=", "\\=")
                    .replace("[", "\\[")
                    .replace("]", "\\]")
                    .replace(";", "\\;")
                )

            # Determine which version to use (Console or GUI)
            # Always use GUI version (console/gui selection removed)
            use_gui = True

            if use_gui:
                # GUI version
                gui_script = script_dir / "gui" / "main.py"
                if gui_script.exists():
                    # Use shlex.quote() for shell injection protection
                    exec_cmd = f"python3 {shlex.quote(str(gui_script.absolute()))}"
                    terminal = "false"
                else:
                    QMessageBox.warning(
                        self,
                        t("gui_error", "Error"),
                        t(
                            "gui_gui_not_found",
                            "GUI script not found! Using console version instead.",
                        ),
                    )
                    use_gui = False

            if not use_gui:
                # Console version
                wrapper_script = script_dir / "run-update.sh"
                if wrapper_script.exists():
                    # Use shlex.quote() for shell injection protection
                    exec_cmd = f"konsole --hold -e {shlex.quote(str(wrapper_script.absolute()))}"
                else:
                    # Use shlex.quote() for shell injection protection
                    exec_cmd = (
                        f"konsole --hold -e bash {shlex.quote(str(script_abs_path))}"
                    )
                terminal = "true"

            # Escape desktop entry values
            name_value = escape_desktop_entry_value(
                self.shortcut_name.text() or "Update All"
            )
            comment_value = escape_desktop_entry_value(
                self.shortcut_comment.text()
                or "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak"
            )

            desktop_entry = f"""[Desktop Entry]
Name={name_value}
Comment={comment_value}
Exec={exec_cmd}
Icon={icon_value}
Terminal={terminal}
Type=Application
Categories=System;
"""

            # Create desktop files based on selected locations
            locations = []

            # Application Menu (always create if checked)
            if self.shortcut_app_menu.isChecked():
                app_desktop_file = app_dir / "update-all.desktop"
                with open(app_desktop_file, "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
                os.chmod(app_desktop_file, 0o755)
                locations.append(str(app_desktop_file))
                # Update desktop database to refresh application menu
                try:
                    subprocess.run(
                        ["update-desktop-database", str(app_dir)],
                        check=False,
                        capture_output=True,
                        timeout=5,
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                    pass  # Non-critical - menu will refresh on next login

            # Desktop (create if checked)
            if self.shortcut_desktop.isChecked() and desktop_dir:
                desktop_file_copy = desktop_dir / "update-all.desktop"
                with open(desktop_file_copy, "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
                os.chmod(desktop_file_copy, 0o755)
                locations.append(str(desktop_file_copy))

            if locations:
                QMessageBox.information(
                    self,
                    t("gui_success", "Success"),
                    t("gui_shortcut_created", "Shortcut created successfully!")
                    + "\n\n"
                    + "\n".join(locations),
                )
            else:
                QMessageBox.warning(
                    self,
                    t("gui_warning", "Warning"),
                    t(
                        "gui_shortcut_no_location",
                        "Please select at least one location (Application Menu or Desktop)!",
                    ),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_shortcut_failed", "Failed to create desktop shortcut:")
                + f"\n{str(e)}",
            )

    def create_update_tab(self):
        """Create update tab for tool update management"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Version Check Section
        version_group = QGroupBox(t("gui_version_check_section", "Version Check"))
        version_layout = QVBoxLayout()

        # Version display
        self.update_local_version_label = QLabel()
        self.update_github_version_label = QLabel()
        self.update_status_label = QLabel()

        version_layout.addWidget(QLabel(t("gui_local_version", "Local Version") + ":"))
        version_layout.addWidget(self.update_local_version_label)
        version_layout.addWidget(
            QLabel(t("gui_github_version", "GitHub Version") + ":")
        )
        version_layout.addWidget(self.update_github_version_label)
        version_layout.addWidget(self.update_status_label)

        # Check for updates button
        check_update_btn = QPushButton(t("gui_check_for_updates", "Check for Updates"))
        check_update_btn.clicked.connect(self.check_tool_version)
        version_layout.addWidget(check_update_btn)

        version_group.setLayout(version_layout)
        layout.addWidget(version_group)

        # Update Section
        update_group = QGroupBox(t("gui_perform_update", "Perform Update"))
        update_layout = QVBoxLayout()

        update_info = QLabel(
            t("gui_update_info", "Update the tool to the latest version from GitHub.")
        )
        update_info.setWordWrap(True)
        update_layout.addWidget(update_info)

        self.start_update_btn = QPushButton(t("gui_start_update", "Start Update"))
        self.start_update_btn.clicked.connect(self.start_tool_update)
        self.start_update_btn.setEnabled(False)  # Disabled until update available
        update_layout.addWidget(self.start_update_btn)

        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        # Version Downgrade Section
        downgrade_group = QGroupBox(t("gui_downgrade_version", "Downgrade Version"))
        downgrade_layout = QVBoxLayout()

        downgrade_warning = QLabel(
            t(
                "gui_version_downgrade_warning",
                "Warning: This only changes the VERSION file. For a full reinstallation, use 'Perform Update'.",
            )
        )
        downgrade_warning.setWordWrap(True)
        downgrade_warning.setStyleSheet("color: #dc3545;")
        downgrade_layout.addWidget(downgrade_warning)

        version_input_layout = QHBoxLayout()
        version_input_layout.addWidget(
            QLabel(t("gui_set_version", "Set Version") + ":")
        )

        # ComboBox with last 3 versions as presets
        self.version_combo = QComboBox()
        self.version_combo.setEditable(True)
        self.version_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Get last 3 versions from git tags
        try:
            import subprocess

            result = subprocess.run(
                ["git", "tag", "-l", "v*"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=str(Path(self.script_dir).parent),
            )
            if result.returncode == 0:
                tags = sorted(
                    result.stdout.strip().split("\n"),
                    key=lambda x: [int(i) for i in x.replace("v", "").split(".")],
                )[-3:]
                for tag in tags:
                    version = tag.replace("v", "")
                    self.version_combo.addItem(version)
        except Exception:
            pass

        # Set default to one version before current (if we can determine current version)
        try:
            root_dir = Path(self.script_dir).parent
            version_file = root_dir / "VERSION"
            if version_file.exists():
                with open(version_file, "r", encoding="utf-8") as f:
                    current_version = f.read().strip()
                    # Try to calculate previous version
                    parts = [int(x) for x in current_version.split(".")]
                    if parts[2] > 0:
                        parts[2] -= 1
                        prev_version = ".".join(map(str, parts))
                        self.version_combo.setCurrentText(prev_version)
        except Exception:
            pass

        version_input_layout.addWidget(self.version_combo)

        set_version_btn = QPushButton(t("gui_set_version", "Set Version"))
        set_version_btn.clicked.connect(self.set_version)
        version_input_layout.addWidget(set_version_btn)

        downgrade_layout.addLayout(version_input_layout)
        downgrade_group.setLayout(downgrade_layout)
        layout.addWidget(downgrade_group)

        layout.addStretch()
        widget.setLayout(layout)

        # Initialize version display
        self.update_version_display()

        return widget

    def update_version_display(self):
        """Update version display in update tab"""
        import re

        root_dir = Path(self.script_dir).parent
        version_file = root_dir / "VERSION"
        local_version = "unknown"

        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version = f.read().strip()
                    if re.match(r"^\d+\.\d+\.\d+$", version):
                        local_version = version
            except Exception:
                pass

        # Fallback to update-all.sh
        if local_version == "unknown":
            script_path = Path(self.script_dir) / "update-all.sh"
            if script_path.exists():
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if "readonly SCRIPT_VERSION=" in line:
                                match = re.search(r'["\']([0-9.]+)["\']', line)
                                if match:
                                    local_version = match.group(1)
                                    break
                except Exception:
                    pass

        self.update_local_version_label.setText(f"v{local_version}")

        # Check GitHub version
        try:
            from ..utils.version_checker import VersionChecker
        except ImportError:
            VersionChecker = None

        if VersionChecker:
            github_repo = self.config.get(
                "GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"
            )
            checker = VersionChecker(str(self.script_dir), github_repo)
            latest, error = checker.check_latest_version()

            if latest and not error:
                self.update_github_version_label.setText(f"v{latest}")
                comparison = checker.compare_versions(local_version, latest)

                if comparison < 0:
                    # Update available
                    self.update_status_label.setText(
                        t("gui_update_available", "Update available!")
                    )
                    self.update_status_label.setStyleSheet(
                        "color: #dc3545; font-weight: bold;"
                    )
                    self.start_update_btn.setEnabled(True)
                elif comparison == 0:
                    # Up to date
                    self.update_status_label.setText(
                        t("gui_version_up_to_date", "Up to date")
                    )
                    self.update_status_label.setStyleSheet("color: #28a745;")
                    self.start_update_btn.setEnabled(False)
                else:
                    # Local is newer
                    self.update_status_label.setText(
                        t("gui_version_dev", "Development version (local is newer)")
                    )
                    self.update_status_label.setStyleSheet("color: #28a745;")
                    self.start_update_btn.setEnabled(False)
            else:
                self.update_github_version_label.setText(
                    t("gui_version_check_failed", "Version check failed")
                )
                self.update_status_label.setText("")
                self.start_update_btn.setEnabled(False)
        else:
            self.update_github_version_label.setText("unavailable")
            self.update_status_label.setText("")
            self.start_update_btn.setEnabled(False)

    def check_tool_version(self):
        """Check for tool version updates"""
        self.update_version_display()
        QMessageBox.information(
            self,
            t("gui_version_check_complete", "Version Check Complete"),
            t(
                "gui_version_check_complete_msg",
                "Version check completed. See status above.",
            ),
        )

    def start_tool_update(self):
        """Start tool update (opens update dialog)"""
        try:
            from .update_dialog import UpdateDialog
        except ImportError:
            try:
                from update_dialog import UpdateDialog
            except ImportError:
                QMessageBox.warning(
                    self,
                    t("gui_update_failed", "Update Failed"),
                    t(
                        "gui_update_dialog_not_found",
                        "Update dialog not found. Please update manually.",
                    ),
                )
                return

        # Get versions
        import re

        root_dir = Path(self.script_dir).parent
        version_file = root_dir / "VERSION"
        local_version = "unknown"

        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version = f.read().strip()
                    if re.match(r"^\d+\.\d+\.\d+$", version):
                        local_version = version
            except Exception:
                pass

        # Get GitHub version
        from ..utils.version_checker import VersionChecker

        github_repo = self.config.get(
            "GITHUB_REPO", "benjarogit/sc-cachyos-multi-updater"
        )
        checker = VersionChecker(str(self.script_dir), github_repo)
        latest, error = checker.check_latest_version()

        if not latest or error:
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_version_check_failed", "Version check failed"),
            )
            return

        # Open update dialog
        dialog = UpdateDialog(
            str(self.script_dir), local_version, latest, checker, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update was performed, refresh display
            self.update_version_display()

    def set_version(self):
        """Set version in VERSION file"""
        # Get version from combo box (which is editable)
        version_text = self.version_combo.currentText().strip()

        if not version_text:
            QMessageBox.warning(
                self,
                t("gui_error", "Error"),
                t("gui_version_empty", "Version cannot be empty"),
            )
            return

        # Validate version format
        import re

        if not re.match(r"^\d+\.\d+\.\d+$", version_text):
            QMessageBox.warning(
                self,
                t("gui_error", "Error"),
                t(
                    "gui_version_invalid",
                    "Invalid version format. Use format: X.Y.Z (e.g., 1.0.15)",
                ),
            )
            return

        # Confirm
        reply = QMessageBox.question(
            self,
            t("gui_confirm", "Confirm"),
            t(
                "gui_set_version_confirm",
                "Set version to {version}?\n\nThis only changes the VERSION file.",
            ).format(version=version_text),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Write VERSION file
        root_dir = Path(self.script_dir).parent
        version_file = root_dir / "VERSION"

        try:
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(version_text)

            QMessageBox.information(
                self,
                t("gui_success", "Success"),
                t("gui_version_set_success", "Version set to {version}").format(
                    version=version_text
                ),
            )

            # Refresh display
            self.update_version_display()
            self.version_combo.setCurrentText("")
        except Exception as e:
            QMessageBox.critical(
                self,
                t("gui_error", "Error"),
                t("gui_version_set_failed", "Failed to set version:\n\n{error}").format(
                    error=str(e)
                ),
            )


    def save_and_close(self):
        """Save config and close dialog"""
        if self.save_config():
            self.accept()
        else:
            QMessageBox.warning(
                self,
                t("gui_error", "Error"),
                t("gui_config_save_failed", "Failed to save configuration"),
            )
