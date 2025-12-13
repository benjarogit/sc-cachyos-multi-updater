#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Update Confirmation Dialog
Dialog shown after check-updates to confirm starting real updates
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

# Import from new structure
from ..core.i18n import t
from ..widgets import get_fa_icon, apply_fa_font
from ..utils import get_logger


class UpdateConfirmationDialog(QDialog):
    """Dialog to confirm starting updates after check"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.logger.debug("UpdateConfirmationDialog initialized")
        self.setWindowTitle(t("gui_updates_available", "Updates Available"))
        self.setMinimumWidth(450)
        self.setModal(True)  # Modal dialog - only closes itself, not parent
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )  # Remove help button
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Info label
        info_label = QLabel(
            t(
                "gui_start_updates_now",
                "Updates are available. Do you want to start the update process now?",
            )
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Spacer
        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()

        # Close button (left) - closes entire GUI
        icon, text = get_fa_icon("window-close", t("gui_exit", "Exit GUI"))
        close_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(close_btn)
        close_btn.clicked.connect(self.close_gui)
        button_layout.addWidget(close_btn)

        button_layout.addStretch()

        # No button (middle)
        icon, text = get_fa_icon("times", t("gui_no", "No"))
        no_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(no_btn)
        no_btn.clicked.connect(self.accept_no)
        button_layout.addWidget(no_btn)

        # Yes button (right)
        icon, text = get_fa_icon("check", t("gui_yes", "Yes"))
        yes_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(yes_btn)
        yes_btn.clicked.connect(self.accept)
        yes_btn.setDefault(True)
        button_layout.addWidget(yes_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def accept_no(self):
        """User clicked No - close dialog without starting updates"""
        # Just close the dialog without starting updates
        self.reject()

    def close_gui(self):
        """Close entire GUI application"""
        # Close parent window (main GUI)
        if self.parent():
            self.parent().close()
        self.reject()

    def accept(self):
        """User clicked Yes - accept dialog and start updates"""
        # Call parent accept() to set result to Accepted
        super().accept()
