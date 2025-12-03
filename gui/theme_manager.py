#!/usr/bin/env python3
"""
Theme Manager for CachyOS Multi-Updater GUI
Handles dark/light mode themes with system detection
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import Qt


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
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
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
            transform: scale(1.02);
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
            transform: scale(0.98);
        }
        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #666666;
            border: 1px solid #3c3c3c;
        }
        QCheckBox {
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
            background-color: #0078d4;
            border: 1px solid #0078d4;
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
                stop:0 #0078d4,
                stop:0.5 #0099ff,
                stop:1 #0078d4);
            border-radius: 3px;
        }
        QLabel {
            color: #ffffff;
        }
        QLineEdit {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #ffffff;
        }
        QLineEdit:focus {
            border: 2px solid #0078d4;
            background-color: #fafafa;
            box-shadow: 0 0 5px rgba(0, 120, 212, 0.3);
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
            selection-background-color: #0078d4;
            color: #ffffff;
        }
        QSpinBox {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #ffffff;
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
            border-bottom: 3px solid #0078d4;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background-color: #4a4a4a;
            border-bottom: 2px solid #0078d4;
        }
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMessageBox {
            background-color: #2b2b2b;
            color: #ffffff;
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
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
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
            transform: scale(1.02);
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
            transform: scale(0.98);
        }
        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #999999;
            border: 1px solid #e0e0e0;
        }
        QCheckBox {
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
            background-color: #0078d4;
            border: 1px solid #0078d4;
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
                stop:0 #0078d4,
                stop:0.5 #0099ff,
                stop:1 #0078d4);
            border-radius: 3px;
        }
        QLabel {
            color: #000000;
        }
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
        }
        QLineEdit:focus {
            border: 2px solid #0078d4;
            background-color: #fafafa;
            box-shadow: 0 0 5px rgba(0, 120, 212, 0.3);
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
            selection-background-color: #0078d4;
            color: #000000;
        }
        QSpinBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
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
            border-bottom: 3px solid #0078d4;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background-color: #e0e0e0;
            border-bottom: 2px solid #0078d4;
        }
        QDialog {
            background-color: #ffffff;
            color: #000000;
        }
        QMessageBox {
            background-color: #ffffff;
            color: #000000;
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
        app = QApplication.instance()
        if app is None:
            return
        
        if theme_mode == "auto":
            # Detect system theme
            system_theme = ThemeManager.detect_system_theme()
            stylesheet = ThemeManager.DARK_STYLESHEET if system_theme == "dark" else ThemeManager.LIGHT_STYLESHEET
        elif theme_mode == "dark":
            stylesheet = ThemeManager.DARK_STYLESHEET
        else:  # light
            stylesheet = ThemeManager.LIGHT_STYLESHEET
        
        app.setStyleSheet(stylesheet)

