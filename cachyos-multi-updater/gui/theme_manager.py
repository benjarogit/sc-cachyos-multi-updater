#!/usr/bin/env python3
"""
Theme Manager for CachyOS Multi-Updater GUI
Handles dark/light mode themes with system detection
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import Qt

# Handle imports for both direct execution and module import
try:
    from .debug_logger import get_logger
except ImportError:
    try:
        from debug_logger import get_logger
    except ImportError:
        def get_logger():
            class DummyLogger:
                def debug(self, *args, **kwargs): pass
                def info(self, *args, **kwargs): pass
                def warning(self, *args, **kwargs): pass
                def error(self, *args, **kwargs): pass
                def exception(self, *args, **kwargs): pass
            return DummyLogger()


class ThemeManager:
    """Manages application themes"""
    
    DARK_STYLESHEET = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 16px;
            padding: 16px;
            font-weight: bold;
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px;
            color: #ffffff;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
            border: 1px solid #666666;
            /* Note: Qt stylesheets don't support transform: scale(), using border-width instead for visual feedback */
            border-width: 2px;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
            border-width: 1px;
        }
        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #666666;
            border: 1px solid #3c3c3c;
        }
        QCheckBox {
            color: #ffffff;
        }
        QRadioButton {
            color: #ffffff;
        }
        QLabel#fa_checkbox_indicator {
            border-color: #555555;
        }
        QLabel#fa_checkbox_text {
            color: #ffffff;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            background-color: #00D9FF;
            border: 1px solid #00D9FF;
            border-radius: 3px;
        }
        QTextEdit {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            color: #ffffff;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00D9FF,
                stop:0.5 #00A8CC,
                stop:1 #00D9FF);
            border-radius: 3px;
        }
        QLabel {
            color: #ffffff;
        }
        QLineEdit {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 12px;
            color: #ffffff;
            min-height: 20px;
        }
        QLineEdit:focus {
            border: 2px solid #00D9FF;
            background-color: #2b2b2b;
        }
        QLineEdit::placeholder {
            color: #71757a;
        }
        QComboBox {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #ffffff;
        }
        QComboBox:hover {
            border: 1px solid #666666;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #2b2b2b;
            border: 1px solid #555555;
            selection-background-color: #00D9FF;
            color: #ffffff;
        }
        QSpinBox {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 12px;
            color: #ffffff;
            min-height: 20px;
        }
        QSpinBox:focus {
            border: 2px solid #00D9FF;
            background-color: #2b2b2b;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom: 3px solid #00D9FF;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background-color: #4a4a4a;
            border-bottom: 2px solid #00D9FF;
        }
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMessageBox {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QToolTip {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 12px;
        }
    """
    
    LIGHT_STYLESHEET = """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 4px;
            font-weight: bold;
        }
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 16px;
            padding: 16px;
            font-weight: bold;
            background-color: #ffffff;
            color: #000000;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px;
            color: #000000;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 6px 12px;
            color: #000000;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
            border: 1px solid #999999;
            /* Note: Qt stylesheets don't support transform: scale(), using border-width instead for visual feedback */
            border-width: 2px;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
            border-width: 1px;
        }
        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #999999;
            border: 1px solid #e0e0e0;
        }
        QCheckBox {
            color: #000000;
        }
        QRadioButton {
            color: #000000;
        }
        QLabel#fa_checkbox_indicator {
            border-color: #cccccc;
        }
        QLabel#fa_checkbox_text {
            color: #000000;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            background-color: #00D9FF;
            border: 1px solid #00D9FF;
            border-radius: 3px;
        }
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            color: #000000;
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            background-color: #f0f0f0;
            color: #000000;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00D9FF,
                stop:0.5 #00A8CC,
                stop:1 #00D9FF);
            border-radius: 3px;
        }
        QLabel {
            color: #000000;
        }
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px 12px;
            color: #000000;
            min-height: 20px;
        }
        QLineEdit:focus {
            border: 2px solid #00D9FF;
            background-color: #fafafa;
        }
        QLineEdit::placeholder {
            color: #71757a;
        }
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
        }
        QComboBox:hover {
            border: 1px solid #999999;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            selection-background-color: #00D9FF;
            color: #000000;
        }
        QSpinBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px 12px;
            color: #000000;
            min-height: 20px;
        }
        QSpinBox:focus {
            border: 2px solid #00D9FF;
            background-color: #fafafa;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 3px solid #00D9FF;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background-color: #e0e0e0;
            border-bottom: 2px solid #00D9FF;
        }
        QDialog {
            background-color: #ffffff;
            color: #000000;
        }
        QMessageBox {
            background-color: #ffffff;
            color: #000000;
        }
        QToolTip {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 12px;
        }
    """
    
    @staticmethod
    def detect_system_theme():
        """Detect system theme (dark or light)"""
        app = QApplication.instance()
        if app is None:
            return "light"  # Default to light if no app instance
        
        palette = app.palette()
        bg_color = palette.color(QPalette.ColorRole.Window)
        # Calculate brightness
        brightness = (bg_color.red() + bg_color.green() + bg_color.blue()) / 3
        
        # If brightness is less than 128, it's likely dark mode
        return "dark" if brightness < 128 else "light"
    
    @staticmethod
    def apply_theme(theme_mode: str):
        """Apply theme to application
        
        Args:
            theme_mode: "auto", "dark", or "light"
        """
        logger = get_logger()
        logger.debug(f"ThemeManager.apply_theme called with mode: {theme_mode}")
        app = QApplication.instance()
        if app is None:
            logger.warning("QApplication instance not found, cannot apply theme")
            return
        
        if theme_mode == "auto":
            # Detect system theme
            system_theme = ThemeManager.detect_system_theme()
            logger.debug(f"Auto theme detected: {system_theme}")
            stylesheet = ThemeManager.DARK_STYLESHEET if system_theme == "dark" else ThemeManager.LIGHT_STYLESHEET
        elif theme_mode == "dark":
            stylesheet = ThemeManager.DARK_STYLESHEET
        else:  # light
            stylesheet = ThemeManager.LIGHT_STYLESHEET
        
        app.setStyleSheet(stylesheet)
        logger.info(f"Theme applied: {theme_mode}")

