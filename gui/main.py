#!/usr/bin/env python3
"""
CachyOS Multi-Updater - GUI Main Entry Point
Qt-based GUI wrapper for update-all.sh
"""

import sys
import os
from pathlib import Path

# Suppress Qt QDBus warnings (harmless but annoying)
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")

# Add gui directory to path for imports
gui_dir = Path(__file__).parent
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QtMsgType, qInstallMessageHandler

# Initialize i18n before importing window
from i18n import init_i18n, t
from window import MainWindow
from theme_manager import ThemeManager
from config_manager import ConfigManager


def get_script_dir():
    """Get script directory"""
    # Try to get from environment or use current directory
    script_dir = os.environ.get("SCRIPT_DIR")
    if script_dir and Path(script_dir).exists():
        return script_dir
    
    # Try to find update-all.sh in parent directory
    current_dir = Path(__file__).parent.parent.absolute()
    if (current_dir / "update-all.sh").exists():
        return str(current_dir)
    
    # Fallback to current directory
    return str(Path.cwd())


def main():
    """Main entry point"""
    # Suppress Qt QDBus warnings and other Qt messages
    def qt_message_handler(msg_type, context, message):
        # Filter out QDBus warnings and portal errors
        if ("QDBusError" in message or 
            "qt.qpa.services" in message or 
            "Failed to register with host portal" in message or
            "org.freedesktop.portal" in message or
            "org.kde.kioclient" in message):
            return
        # Print other messages normally (optional, can be removed)
        # print(message)
    
    qInstallMessageHandler(qt_message_handler)
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("CachyOS Multi-Updater")
    app.setOrganizationName("CachyOS")
    
    # Get script directory
    script_dir = get_script_dir()
    
    # Initialize i18n early (needed for error messages)
    init_i18n(script_dir)
    
    # Check if update-all.sh exists
    script_path = Path(script_dir) / "update-all.sh"
    if not script_path.exists():
        QMessageBox.critical(
            None,
            t("gui_error", "Error"),
            t("gui_script_not_found_main", "update-all.sh not found in:\n{script_dir}\n\nPlease run this GUI from the script directory or set SCRIPT_DIR environment variable.").format(script_dir=script_dir)
        )
        sys.exit(1)
    
    # Apply theme
    config_manager = ConfigManager(script_dir)
    theme_mode = config_manager.get("GUI_THEME", "auto")
    ThemeManager.apply_theme(theme_mode)
    
    # Create and show main window
    window = MainWindow(script_dir)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

