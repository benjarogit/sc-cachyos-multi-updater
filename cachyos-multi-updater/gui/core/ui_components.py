"""
UI Component Builders for MainWindow
Extracted from window.py for better organization
"""

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QTextEdit,
    QProgressBar,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..widgets import ClickableLabel
from ..core.i18n import t


class UIComponents:
    """Helper class for creating UI components"""

    @staticmethod
    def create_header(
        script_version: str, config_manager, parent
    ) -> tuple[QHBoxLayout, dict]:
        """Create header layout with title, version, and icons

        Returns:
            tuple: (header_layout, widget_refs_dict)
        """
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        widget_refs = {}

        # Title
        header_label = QLabel(t("app_name", "CachyOS Multi-Updater"))
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 120, 212, 0.1),
                    stop:1 transparent);
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        header_layout.addWidget(header_label)
        widget_refs["header_label"] = header_label

        # Version label
        version_label = ClickableLabel(f"v{script_version} (Lokal)")
        version_font = QFont()
        version_font.setPointSize(10)
        version_font.setItalic(True)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: #666;")
        version_label.setToolTip(
            t("gui_version_check_tooltip", "Click to check for updates")
        )
        header_layout.addWidget(version_label)
        widget_refs["version_label"] = version_label

        # Update badge
        update_badge = ClickableLabel("NEW")
        update_badge.setVisible(False)
        update_badge.setStyleSheet("""
            QLabel {
                background-color: #dc3545;
                color: white;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
            }
        """)
        update_badge.setToolTip(t("gui_update_available", "Update available"))
        header_layout.addWidget(update_badge)
        widget_refs["update_badge"] = update_badge

        header_layout.addStretch()

        # Language switcher
        language_widget = QWidget()
        language_layout = QHBoxLayout()
        language_layout.setContentsMargins(6, 4, 6, 4)
        language_layout.setSpacing(6)
        language_widget.setLayout(language_layout)

        language_icon_label = QLabel()
        language_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        language_layout.addWidget(language_icon_label)
        widget_refs["language_icon_label"] = language_icon_label

        current_lang = config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            import os

            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"

        language_text_label = QLabel("DE" if current_lang == "de" else "EN")
        language_text_font = QFont("Courier", 9)
        language_text_font.setBold(True)
        language_text_label.setFont(language_text_font)
        language_text_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        language_layout.addWidget(language_text_label)
        widget_refs["language_text_label"] = language_text_label

        language_clickable = ClickableLabel()
        language_clickable.setToolTip(t("gui_switch_language", "Switch Language"))
        language_clickable_layout = QHBoxLayout()
        language_clickable_layout.setContentsMargins(0, 0, 0, 0)
        language_clickable_layout.addWidget(language_widget)
        language_clickable.setLayout(language_clickable_layout)
        header_layout.addWidget(language_clickable)
        widget_refs["language_clickable"] = language_clickable

        # Theme switcher
        theme_label = ClickableLabel()
        theme_label.setToolTip(t("gui_switch_theme", "Switch Theme"))
        header_layout.addWidget(theme_label)
        widget_refs["theme_label"] = theme_label

        # Changelog icon
        changelog_label = ClickableLabel()
        changelog_label.setToolTip(t("gui_open_changelog", "Open Changelog/Releases"))
        header_layout.addWidget(changelog_label)
        widget_refs["changelog_label"] = changelog_label

        # GitHub icon
        github_label = ClickableLabel()
        github_label.setToolTip(t("gui_open_github", "Open GitHub repository"))
        header_layout.addWidget(github_label)
        widget_refs["github_label"] = github_label

        return header_layout, widget_refs

    @staticmethod
    def create_components_info_section(
        get_fa_checkbox_class, parent
    ) -> tuple[QHBoxLayout, dict]:
        """Create components and update info section

        Returns:
            tuple: (layout, widget_refs_dict)
        """
        components_info_layout = QHBoxLayout()
        components_info_layout.setSpacing(12)

        widget_refs = {}

        # Update Components Group
        components_group = QGroupBox(t("gui_update_components", "Update Components"))
        components_layout = QVBoxLayout()
        components_layout.setSpacing(6)

        CheckBoxClass = get_fa_checkbox_class()

        check_system = CheckBoxClass(t("system_updates", "System Updates (pacman)"))
        check_aur = CheckBoxClass(t("aur_updates", "AUR Updates (yay/paru)"))
        check_cursor = CheckBoxClass(t("cursor_editor_update", "Cursor Editor Update"))
        check_adguard = CheckBoxClass(t("adguard_home_update", "AdGuard Home Update"))
        check_flatpak = CheckBoxClass(t("flatpak_updates", "Flatpak Updates"))

        components_layout.addWidget(check_system)
        components_layout.addWidget(check_aur)
        components_layout.addWidget(check_cursor)
        components_layout.addWidget(check_adguard)
        components_layout.addWidget(check_flatpak)

        components_group.setLayout(components_layout)
        components_info_layout.addWidget(components_group)
        widget_refs["components_group"] = components_group
        widget_refs["check_system"] = check_system
        widget_refs["check_aur"] = check_aur
        widget_refs["check_cursor"] = check_cursor
        widget_refs["check_adguard"] = check_adguard
        widget_refs["check_flatpak"] = check_flatpak

        # Update Infos Panel
        update_info_group = QGroupBox(t("gui_update_info", "Update Infos"))
        update_info_layout = QVBoxLayout()
        update_info_layout.setSpacing(6)

        update_info_text = QTextEdit()
        update_info_text.setReadOnly(True)
        update_info_text.setFont(QFont("Monospace", 9))
        # Keine maximale Höhe - Update-Info kann frei wachsen
        update_info_text.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        update_info_text.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        update_info_text.setPlaceholderText(
            t(
                "gui_update_info_placeholder",
                "Update information will appear here during check/update...",
            )
        )
        update_info_layout.addWidget(update_info_text)

        update_info_group.setLayout(update_info_layout)
        components_info_layout.addWidget(update_info_group, 1)
        widget_refs["update_info_group"] = update_info_group
        widget_refs["update_info_text"] = update_info_text

        return components_info_layout, widget_refs

    @staticmethod
    def create_progress_output_section(parent) -> tuple[QVBoxLayout, dict]:
        """Create progress bar, status label, and output text area

        Returns:
            tuple: (layout, widget_refs_dict)
        """
        progress_output_layout = QVBoxLayout()
        progress_output_layout.setSpacing(6)

        widget_refs = {}

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        progress_bar.setFormat("")
        progress_output_layout.addWidget(progress_bar)
        widget_refs["progress_bar"] = progress_bar

        # Status label
        status_label = QLabel(t("gui_ready", "Ready"))
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_output_layout.addWidget(status_label)
        widget_refs["status_label"] = status_label

        # Output area
        output_label = QLabel(t("gui_output", "Output:"))
        progress_output_layout.addWidget(output_label)
        widget_refs["output_label"] = output_label

        output_text = QTextEdit()
        output_text.setReadOnly(True)
        output_text.setFont(QFont("Monospace", 9))
        progress_output_layout.addWidget(output_text)
        widget_refs["output_text"] = output_text

        return progress_output_layout, widget_refs

    @staticmethod
    def create_button_bar(parent) -> tuple[QHBoxLayout, dict]:
        """Create button bar

        Returns:
            tuple: (layout, widget_refs_dict)
        """
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        widget_refs = {}

        # Will be populated by MainWindow
        return button_layout, widget_refs

    @staticmethod
    def create_footer(parent) -> tuple[QHBoxLayout, dict]:
        """Create footer

        Returns:
            tuple: (layout, widget_refs_dict)
        """
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        widget_refs = {}

        # Will be populated by MainWindow
        return footer_layout, widget_refs
