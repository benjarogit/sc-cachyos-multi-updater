#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Sudo Password Dialog
Dialog for entering sudo password
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
)


# Import from new structure
from ..core.i18n import t
from ..widgets import get_fa_icon, apply_fa_font
from ..utils import get_logger

# Try to import FACheckBox
try:
    from ..widgets import FACheckBox

    HAS_FA_CHECKBOX = True
except ImportError:
    HAS_FA_CHECKBOX = False
    FACheckBox = None


class SudoDialog(QDialog):
    """Dialog for sudo password input"""

    def __init__(self, parent=None, save_to_config=True):
        super().__init__(parent)
        self.logger = get_logger()
        self.logger.debug("SudoDialog initialized")
        self.password = None
        self.save_to_config = save_to_config
        self.save_password = False
        self.setWindowTitle(t("gui_sudo_password_required", "Sudo Password Required"))
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Info label
        info_label = QLabel(
            t(
                "gui_sudo_password_info",
                "Sudo password is required to perform system updates.",
            )
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Password input
        password_label = QLabel(t("gui_password", "Password:"))
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.accept_dialog)
        layout.addWidget(self.password_input)

        # Save to config checkbox (always show if save_to_config is True)
        if self.save_to_config:
            if HAS_FA_CHECKBOX and FACheckBox:
                self.save_checkbox = FACheckBox(
                    t("gui_save_password", "Save password in settings (encrypted)")
                )
                # Ensure checkbox is visible and properly initialized
                self.save_checkbox.setChecked(False)  # Default: don't save
            else:
                self.save_checkbox = QCheckBox(
                    t("gui_save_password", "Save password in settings (encrypted)")
                )
                self.save_checkbox.setChecked(False)  # Default: don't save
            layout.addWidget(self.save_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        icon, text = get_fa_icon("times", t("gui_cancel", "Cancel"))
        cancel_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(cancel_btn)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        icon, text = get_fa_icon("check", t("gui_ok", "OK"))
        ok_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(ok_btn)
        ok_btn.clicked.connect(self.accept_dialog)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Focus password input
        self.password_input.setFocus()

    def accept_dialog(self):
        """Accept dialog and return password"""
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(
                self,
                t("gui_error", "Error"),
                t("gui_password_empty", "Password cannot be empty!"),
            )
            return

        self.password = password
        # Check if user wants to save password (only if checkbox exists and is checked)
        if self.save_to_config and hasattr(self, "save_checkbox"):
            self.save_password = self.save_checkbox.isChecked()
        else:
            self.save_password = False
        self.accept()

    def get_password(self):
        """Get entered password"""
        return self.password

    def should_save_password(self):
        """Check if password should be saved"""
        return self.save_password if hasattr(self, "save_password") else False
