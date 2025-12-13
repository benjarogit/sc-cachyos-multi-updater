#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Migration Dialog
Dialog for showing migration hints from manual/portable to AUR installations
"""

import subprocess
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt

# Import from new structure
from ..core.i18n import t
from ..widgets import get_fa_icon, apply_fa_font
from ..utils import get_logger


class MigrationDialog(QDialog):
    """Dialog for showing migration instructions"""

    def __init__(
        self,
        parent=None,
        component: str = "cursor",
        installation_type: str = "manual",
        migration_hint: Optional[str] = None,
    ):
        super().__init__(parent)
        self.logger = get_logger()
        self.component = component
        self.installation_type = installation_type
        self.migration_hint = migration_hint
        self.setWindowTitle(
            t("gui_migration_dialog_title", "Migration to AUR Package")
        )
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Title
        title_label = QLabel(
            t(
                "gui_migration_dialog_title",
                f"Migrate {self.component.capitalize()} to AUR Package",
            )
        )
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Info label
        info_text = t(
            "gui_migration_dialog_info",
            f"Your {self.component} is installed as {self.installation_type}. "
            "Migrating to an AUR package provides automatic updates.",
        )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Migration steps
        steps_label = QLabel(t("gui_migration_steps", "Migration Steps:"))
        steps_font = steps_label.font()
        steps_font.setBold(True)
        steps_label.setFont(steps_font)
        layout.addWidget(steps_label)

        # Scrollable commands area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(8)

        # Generate migration commands
        commands = self._generate_migration_commands()
        for i, (step_title, command) in enumerate(commands, 1):
            step_label = QLabel(f"{i}. {step_title}")
            step_label.setWordWrap(True)
            scroll_layout.addWidget(step_label)

            command_text = QTextEdit()
            command_text.setPlainText(command)
            command_text.setReadOnly(True)
            command_text.setMaximumHeight(80)
            command_text.setFont(step_label.font())
            scroll_layout.addWidget(command_text)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Warning
        warning_label = QLabel(
            t(
                "gui_migration_warning",
                "⚠️ Warning: Make sure to backup your data before migration!",
            )
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(warning_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        icon, text = get_fa_icon("times", t("gui_close", "Close"))
        close_btn = QPushButton(icon, text) if icon else QPushButton(text)
        if not icon:
            apply_fa_font(close_btn)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _generate_migration_commands(self) -> list[tuple[str, str]]:
        """Generate migration commands based on component and installation type"""
        commands: list[tuple[str, str]] = []

        if self.component == "cursor":
            # Detect AUR helper
            aur_helper = self._detect_aur_helper()
            if not aur_helper:
                commands.append(
                    (
                        t("gui_migration_step_aur_helper", "Install AUR Helper"),
                        "# Install yay (recommended)\n"
                        "git clone https://aur.archlinux.org/yay.git\n"
                        "cd yay\n"
                        "makepkg -si",
                    )
                )
                aur_helper = "yay"

            # Step 1: Stop Cursor
            commands.append(
                (
                    t("gui_migration_step_stop", "Stop Cursor"),
                    "killall cursor electron 2>/dev/null || pkill -f cursor",
                )
            )

            # Step 2: Backup
            commands.append(
                (
                    t("gui_migration_step_backup", "Backup Data"),
                    "mkdir -p ~/Backup-Cursor-Alt\n"
                    "cp -r ~/.config/Cursor ~/Backup-Cursor-Alt/\n"
                    "cp -r ~/.cursor ~/Backup-Cursor-Alt/ 2>/dev/null || true",
                )
            )

            # Step 3: Remove old installation
            if self.installation_type == "manual":
                commands.append(
                    (
                        t("gui_migration_step_remove", "Remove Old Installation"),
                        "sudo rm -rf /usr/share/cursor /opt/cursor /opt/Cursor\n"
                        "sudo rm -f /usr/bin/cursor /usr/local/bin/cursor\n"
                        "sudo rm -f /usr/share/applications/cursor*.desktop",
                    )
                )
            elif self.installation_type == "portable":
                commands.append(
                    (
                        t("gui_migration_step_remove", "Remove Old Installation"),
                        "# Remove portable installation\n"
                        "rm -f ~/.local/bin/cursor ~/.local/bin/cursor.AppImage\n"
                        "rm -f ~/Applications/cursor.AppImage ~/Apps/cursor.AppImage\n"
                        "rm -f ~/Applications/Cursor.AppImage ~/Apps/Cursor.AppImage",
                    )
                )

            # Step 4: Install AUR package
            commands.append(
                (
                    t("gui_migration_step_install", "Install AUR Package"),
                    f"{aur_helper} -S cursor-bin",
                )
            )

            # Step 5: Start Cursor
            commands.append(
                (
                    t("gui_migration_step_start", "Start Cursor"),
                    "cursor",
                )
            )

        elif self.component == "adguard":
            # Detect AUR helper
            aur_helper = self._detect_aur_helper()
            if not aur_helper:
                commands.append(
                    (
                        t("gui_migration_step_aur_helper", "Install AUR Helper"),
                        "# Install paru (recommended)\n"
                        "git clone https://aur.archlinux.org/paru.git\n"
                        "cd paru\n"
                        "makepkg -si",
                    )
                )
                aur_helper = "paru"

            # Step 1: Stop service
            commands.append(
                (
                    t("gui_migration_step_stop", "Stop AdGuard Home"),
                    "sudo systemctl stop AdGuardHome || systemctl --user stop AdGuardHome",
                )
            )

            # Step 2: Backup
            commands.append(
                (
                    t("gui_migration_step_backup", "Backup Data"),
                    "sudo cp -a ~/AdGuardHome ~/AdGuardHome.old-backup 2>/dev/null || true",
                )
            )

            # Step 3: Install AUR package
            commands.append(
                (
                    t("gui_migration_step_install", "Install AUR Package"),
                    f"{aur_helper} -S adguardhome",
                )
            )

            # Step 4: Migrate config
            commands.append(
                (
                    t("gui_migration_step_migrate", "Migrate Configuration"),
                    "sudo mkdir -p /etc/AdGuardHome /var/lib/AdGuardHome\n"
                    "sudo cp -a ~/AdGuardHome/AdGuardHome.yaml /etc/AdGuardHome/ 2>/dev/null || true\n"
                    "sudo cp -a ~/AdGuardHome/data /var/lib/AdGuardHome/ 2>/dev/null || true\n"
                    "# Set permissions (user may vary: adguard or adguardhome)\n"
                    "sudo chown -R adguard:adguard /etc/AdGuardHome /var/lib/AdGuardHome 2>/dev/null || \\\n"
                    "sudo chown -R adguardhome:adguardhome /etc/AdGuardHome /var/lib/AdGuardHome 2>/dev/null || true",
                )
            )

            # Step 5: Start service
            commands.append(
                (
                    t("gui_migration_step_start", "Start AdGuard Home"),
                    "sudo systemctl daemon-reload\n"
                    "sudo systemctl enable --now AdGuardHome",
                )
            )

        return commands

    def _detect_aur_helper(self) -> Optional[str]:
        """Detect available AUR helper"""
        helpers = ["yay", "paru", "pikaur", "aurman"]
        for helper in helpers:
            try:
                result = subprocess.run(
                    ["which", helper],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return helper
            except Exception:
                continue
        return None

