#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Main Window UI Components
UI creation and setup methods extracted from window.py
"""

from typing import TYPE_CHECKING, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..widgets import get_fa_icon, apply_fa_font, ClickableLabel
from .i18n import t

if TYPE_CHECKING:
    from .window import MainWindow


class WindowUIMixin:
    """Mixin class for UI creation methods"""

    def init_ui(self: "MainWindow") -> None:
        """Initialize UI - Best Practice: Modular structure"""
        central_widget = QWidget(self)  # Set parent for proper memory management
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        # KRITISCH: Keine Constraints für vollständiges Resizing
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)
        central_widget.setLayout(layout)
        
        # KRITISCH: Central Widget muss auch Expanding sein für horizontales Resizing
        central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Modular UI creation
        layout.addLayout(self._create_header())
        layout.addLayout(self._create_components_info_section())
        layout.addLayout(self._create_progress_output_section())
        layout.addLayout(self._create_button_bar())
        layout.addLayout(self._create_footer())

        # Initialize update info data structure
        self.update_info_data = {
            "planned": {
                "system": False,
                "aur": False,
                "cursor": False,
                "adguard": False,
                "flatpak": False,
                "proton_ge": False,
            },
            "status": {
                "system": {"found": 0, "current": False, "packages": []},
                "aur": {"found": 0, "current": False, "packages": []},
                "cursor": {
                    "current_version": "",
                    "available_version": "",
                    "version": "",
                    "update_available": False,
                },
                "adguard": {
                    "current_version": "",
                    "available_version": "",
                    "version": "",
                    "update_available": False,
                },
                "flatpak": {"found": 0, "current": False, "packages": []},
                "proton_ge": {
                    "current_version": "",
                    "available_version": "",
                    "version": "",
                    "update_available": False,
                },
            },
            "summary": {"total_packages": 0, "components_updated": []},
        }

    def _create_header(self: "MainWindow") -> QHBoxLayout:
        """Create header layout with title, version, and icons

        Returns:
            QHBoxLayout: Header layout
        """
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        # KRITISCH: Horizontales Resizing ermöglichen
        header_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetNoConstraint)

        # Title with modern styling
        self.header_label = QLabel(t("app_name", "CachyOS Multi-Updater"))
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_label.setFont(header_font)
        self.header_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
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

        # Version label (will be updated after version check) - Best Practice: Use ClickableLabel
        self.version_label = ClickableLabel(f"v{self.script_version} (Lokal)")
        version_font = QFont()
        version_font.setPointSize(10)
        version_font.setItalic(True)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet("color: #666;")
        self.version_label.setToolTip(
            t("gui_version_check_tooltip", "Click to check for updates")
        )
        self.version_label.clicked.connect(self._on_version_label_clicked)
        header_layout.addWidget(self.version_label)

        # Update badge (shown when update is available) - Best Practice: Use ClickableLabel
        self.update_badge = ClickableLabel("NEW")
        self.update_badge.setVisible(False)
        self.update_badge.setStyleSheet("""
            QLabel {
                background-color: #dc3545;
                color: white;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
            }
        """)
        self.update_badge.setToolTip(t("gui_update_available", "Update available"))
        self.update_badge.clicked.connect(self._on_version_label_clicked_update)
        header_layout.addWidget(self.update_badge)

        header_layout.addStretch()

        # Language switcher with icon and text - QWidget mit Layout (Icon + Text)
        current_lang = self.config_manager.get("GUI_LANGUAGE", "auto")
        if current_lang == "auto":
            import os
            lang = os.environ.get("LANG", "en_US.UTF-8")
            lang = lang.split("_")[0].split(".")[0].lower()
            current_lang = "de" if lang == "de" else "en"

        # Get theme for icon color
        theme_mode = self.config_manager.get("GUI_THEME", "auto")
        if theme_mode == "auto":
            from ..ui.theme_manager import ThemeManager
            actual_theme = ThemeManager.detect_system_theme()
        else:
            actual_theme = theme_mode
        icon_color = "#ffffff" if actual_theme == "dark" else "#000000"
        text_color = "#ffffff" if actual_theme == "dark" else "#000000"
        
        # QWidget mit horizontalem Layout für Icon + Text
        language_widget = QWidget()
        language_layout = QHBoxLayout()
        language_layout.setContentsMargins(4, 2, 4, 2)
        language_layout.setSpacing(4)
        language_widget.setLayout(language_layout)
        
        # Icon Label
        self.language_icon_label = QLabel()
        self.language_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.language_icon_label.setFixedSize(20, 20)
        language_layout.addWidget(self.language_icon_label)
        
        # Text Label (DE/EN) - kleiner, mittig
        self.language_text_label = QLabel("DE" if current_lang == "de" else "EN")
        text_font = QFont("Courier", 9)
        text_font.setBold(True)
        self.language_text_label.setFont(text_font)
        self.language_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.language_text_label.setStyleSheet(f"color: {text_color};")
        language_layout.addWidget(self.language_text_label)
        
        # ClickableLabel kann kein Layout haben - wir machen language_widget selbst klickbar
        # Lösung: QWidget mit mousePressEvent
        def language_click_handler(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._on_language_label_clicked()
        
        language_widget.mousePressEvent = language_click_handler
        language_widget.setToolTip(t("gui_switch_language", "Switch Language"))
        language_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Verwende language_widget direkt als language_label
        self.language_label = language_widget
        
        # Icon setzen
        from ..widgets import get_fa_icon, FA_ICONS
        icon, _ = get_fa_icon("language", "", size=18, color=icon_color)
        if icon:
            pixmap = icon.pixmap(20, 20)
            self.language_icon_label.setPixmap(pixmap)
            self.language_icon_label.setScaledContents(True)
        else:
            self.language_icon_label.setText(FA_ICONS.get("language", "🌐"))
            fa_font = QFont("FontAwesome", 16)
            self.language_icon_label.setFont(fa_font)
            self.language_icon_label.setStyleSheet(f"color: {icon_color};")
        
        header_layout.addWidget(self.language_label)

        # Theme switcher icon - Best Practice: Use ClickableLabel
        self.theme_label = ClickableLabel()
        self.update_theme_icon()
        self.theme_label.setToolTip(t("gui_switch_theme", "Switch Theme"))
        self.theme_label.clicked.connect(self._on_theme_label_clicked)
        header_layout.addWidget(self.theme_label)

        # Changelog/Release icon - Best Practice: Use ClickableLabel
        self.changelog_label = ClickableLabel()
        self.update_changelog_icon()
        self.changelog_label.setToolTip(
            t("gui_open_changelog", "Open Changelog/Releases")
        )
        self.changelog_label.clicked.connect(self._on_changelog_label_clicked)
        header_layout.addWidget(self.changelog_label)

        # GitHub icon - Best Practice: Use ClickableLabel
        self.github_label = ClickableLabel()
        self.update_github_icon()
        self.github_label.setToolTip(t("gui_open_github", "Open GitHub repository"))
        self.github_label.clicked.connect(self._on_github_label_clicked)
        header_layout.addWidget(self.github_label)

        return header_layout

    def _create_components_info_section(self: "MainWindow") -> QHBoxLayout:
        """Create components and update info section

        Returns:
            QHBoxLayout: Components and info layout
        """
        components_info_layout = QHBoxLayout()
        components_info_layout.setSpacing(12)
        # KRITISCH: Horizontales Resizing ermöglichen - keine Constraints
        components_info_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetNoConstraint)

        # Update Components Group
        self.components_group = QGroupBox(
            t("gui_update_components", "Update Components")
        )
        components_layout = QVBoxLayout()
        components_layout.setSpacing(6)

        # Try to use Font Awesome checkboxes, fallback to regular checkboxes
        # Best Practice: Use helper method
        CheckBoxClass = self._get_fa_checkbox_class()

        self.check_system = CheckBoxClass(
            t("system_updates", "System Updates (pacman)")
        )
        self.check_aur = CheckBoxClass(t("aur_updates", "AUR Updates (yay/paru)"))
        self.check_cursor = CheckBoxClass(
            t("cursor_editor_update", "Cursor Editor Update")
        )
        self.check_adguard = CheckBoxClass(
            t("adguard_home_update", "AdGuard Home Update")
        )
        self.check_flatpak = CheckBoxClass(t("flatpak_updates", "Flatpak Updates"))
        self.check_proton_ge = CheckBoxClass(
            t("proton_ge_update", "Proton-GE Update")
        )

        components_layout.addWidget(self.check_system)
        components_layout.addWidget(self.check_aur)
        components_layout.addWidget(self.check_cursor)
        components_layout.addWidget(self.check_adguard)
        components_layout.addWidget(self.check_flatpak)
        components_layout.addWidget(self.check_proton_ge)

        self.components_group.setLayout(components_layout)
        # KRITISCH: Horizontales Resizing ermöglichen
        self.components_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Keine feste Breite - kann frei skaliert werden
        components_info_layout.addWidget(self.components_group, 1)  # Stretch factor 1

        # Update Infos Panel
        self.update_info_group = QGroupBox(t("gui_update_info", "Update Infos"))
        update_info_layout = QVBoxLayout()
        update_info_layout.setSpacing(6)
        # KRITISCH: Horizontales Resizing ermöglichen
        update_info_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)

        self.update_info_text = QTextEdit()
        self.update_info_text.setReadOnly(True)
        self.update_info_text.setFont(QFont("Monospace", 9))
        # Keine maximale Höhe - Update-Info kann frei wachsen
        # Best Practice: Enable scrolling so users can read update info during updates
        self.update_info_text.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.update_info_text.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.update_info_text.setPlaceholderText(
            t(
                "gui_update_info_placeholder",
                "Update information will appear here during check/update...",
            )
        )
        update_info_layout.addWidget(self.update_info_text)

        self.update_info_group.setLayout(update_info_layout)
        # KRITISCH: Horizontales Resizing ermöglichen
        self.update_info_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Keine feste Breite - kann frei skaliert werden
        components_info_layout.addWidget(self.update_info_group, 1)  # Stretch factor 1

        return components_info_layout

    def _create_progress_output_section(self: "MainWindow") -> QVBoxLayout:
        """Create progress bar, status label, and output text area

        Returns:
            QVBoxLayout: Progress and output layout
        """
        progress_output_layout = QVBoxLayout()
        progress_output_layout.setSpacing(6)
        # KRITISCH: Horizontales Resizing ermöglichen
        progress_output_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)

        # Progress bar (without text format to avoid duplication)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")  # No text format - status_label shows the info
        progress_output_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel(t("gui_ready", "Ready"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_output_layout.addWidget(self.status_label)

        # Output area with copy button
        output_header_layout = QHBoxLayout()
        self.output_label = QLabel(t("gui_output", "Output:"))
        output_header_layout.addWidget(self.output_label)
        output_header_layout.addStretch()
        
        # Copy button for console output
        from PyQt6.QtWidgets import QApplication
        
        self.btn_copy_output = QPushButton("📋 " + t("gui_copy", "Copy"))
        self.btn_copy_output.setToolTip(t("gui_copy_output_tooltip", "Copy complete console output to clipboard"))
        self.btn_copy_output.clicked.connect(lambda: QApplication.clipboard().setText(self.output_text.toPlainText()))
        output_header_layout.addWidget(self.btn_copy_output)
        
        progress_output_layout.addLayout(output_header_layout)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        # Terminal-like styling: Monospace font, larger size
        monospace_font = QFont("JetBrains Mono", 10)
        if not monospace_font.exactMatch():
            # Fallback to DejaVu Sans Mono or system monospace
            monospace_font = QFont("DejaVu Sans Mono", 10)
            if not monospace_font.exactMatch():
                monospace_font = QFont("Monospace", 10)
        self.output_text.setFont(monospace_font)
        
        # Terminal-like dark background and white text
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
            }
        """)
        
        # KEINE Syntax-Highlighting - rohe Terminal-Ausgabe, unverändert
        self.highlighter = None
        
        # Ensure horizontal and vertical resizing works
        self.output_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        
        progress_output_layout.addWidget(
            self.output_text, 1
        )  # Stretch factor 1: expand to fill available space

        return progress_output_layout

    def _create_button_bar(self: "MainWindow") -> QHBoxLayout:
        """Create button bar with action buttons

        Returns:
            QHBoxLayout: Button bar layout
        """
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        # KRITISCH: Horizontales Resizing ermöglichen
        button_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetNoConstraint)

        # Check for Updates button - Best Practice: Use helper method
        self.btn_check = self._create_fa_button(
            "search",
            t("gui_check_for_updates", "Check for Updates"),
            self.check_updates,
        )
        button_layout.addWidget(self.btn_check)

        # Start Updates button - Best Practice: Use helper method
        self.btn_start = self._create_fa_button(
            "play", t("gui_start_updates", "Start Updates"), self.start_updates
        )
        button_layout.addWidget(self.btn_start)

        # Stop button - Best Practice: Use helper method
        self.btn_stop = self._create_fa_button(
            "stop", t("gui_stop", "Stop"), self.stop_updates
        )
        self.btn_stop.setEnabled(False)
        self.btn_stop.setVisible(False)  # Hidden by default
        button_layout.addWidget(self.btn_stop)

        # Wait label with spinner (shown during updates)
        self.wait_label = QLabel()
        # Keine maximale Höhe - Label kann frei wachsen
        self.wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wait_font = QFont()
        wait_font.setPointSize(10)
        self.wait_label.setFont(wait_font)
        self.wait_label.setStyleSheet("color: #666; font-style: italic;")
        self.wait_label.setVisible(False)
        button_layout.addWidget(self.wait_label)

        button_layout.addStretch()

        # Settings button - Best Practice: Use helper method
        self.btn_settings = self._create_fa_button(
            "cog", t("gui_settings", "Settings"), self.show_settings
        )
        button_layout.addWidget(self.btn_settings)

        # View Logs button - Best Practice: Use helper method
        self.btn_logs = self._create_fa_button(
            "file-text", t("gui_view_logs", "View Logs"), self.view_logs
        )
        button_layout.addWidget(self.btn_logs)

        return button_layout

    def _create_footer(self: "MainWindow") -> QHBoxLayout:
        """Create footer with copyright information

        Returns:
            QHBoxLayout: Footer layout
        """
        copyright_layout = QHBoxLayout()
        # KRITISCH: Horizontales Resizing ermöglichen
        copyright_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetNoConstraint)
        copyright_layout.addStretch()

        # Use HTML entity for heart and style only the heart red
        copyright_text = "© 2025 Sunny C. - <a href='https://benjaro.info'>benjaro.info</a> | I <span style='color: #d32f2f;'>❤️</span> <a href='https://www.woltlab.com/en/'>WoltLab Suite</a> | <a href='https://github.com/benjarogit/photoshopCClinux'>photoshopCClinux</a>"
        copyright_label = QLabel(copyright_text)
        copyright_label.setOpenExternalLinks(True)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_font = QFont()
        copyright_font.setPointSize(8)
        copyright_label.setFont(copyright_font)
        # Don't set link color to red - only the heart should be red
        copyright_layout.addWidget(copyright_label)
        copyright_layout.addStretch()

        return copyright_layout

    def _create_fa_button(
        self: "MainWindow", icon_name: str, text: str, slot: Optional[Callable] = None
    ) -> QPushButton:
        """Create a QPushButton with Font Awesome icon

        Best Practice: Helper method to reduce code duplication

        Args:
            icon_name: Font Awesome icon name (e.g., 'search', 'play', 'cog')
            text: Button text
            slot: Optional slot function to connect to clicked signal

        Returns:
            QPushButton: Configured button with icon
        """
        icon, button_text = get_fa_icon(icon_name, text)
        btn = QPushButton(icon, button_text) if icon else QPushButton(button_text)
        if not icon:
            apply_fa_font(btn)
        if slot:
            btn.clicked.connect(slot)
        
        # KRITISCH: Konsistente Button-Styles - weniger "fett", Theme Engine nutzen
        # SizePolicy für responsives Verhalten
        btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        # Theme Engine Styles werden automatisch angewendet (padding bereits reduziert)
        
        return btn

    def _get_fa_checkbox_class(self: "MainWindow") -> type:
        """Get FACheckBox class if available, otherwise QCheckBox

        Best Practice: Helper method to reduce code duplication

        Returns:
            Class: FACheckBox if available, QCheckBox otherwise
        """
        try:
            from ..widgets import FACheckBox
            return FACheckBox
        except ImportError:
            try:
                from gui.widgets import FACheckBox
                return FACheckBox
            except ImportError:
                return QCheckBox

