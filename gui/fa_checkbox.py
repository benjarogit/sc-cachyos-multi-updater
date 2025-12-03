#!/usr/bin/env python3
"""
Font Awesome Checkbox Widget
Custom checkbox that uses Font Awesome check icon
"""

from PyQt6.QtWidgets import QCheckBox, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

try:
    from .fa_icons import get_fa_icon, apply_fa_font, FA_ICONS
except ImportError:
    from fa_icons import get_fa_icon, apply_fa_font, FA_ICONS


class FACheckBox(QWidget):
    """Checkbox with Font Awesome check icon"""
    
    toggled = pyqtSignal(bool)
    clicked = pyqtSignal()
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._checked = False
        self._text = text
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Check icon label
        self.check_label = QLabel()
        self.check_label.setFixedSize(18, 18)
        self.check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_label.setStyleSheet("""
            border: 2px solid #ccc;
            border-radius: 3px;
            background-color: transparent;
        """)
        self.update_check_icon()
        layout.addWidget(self.check_label)
        
        # Text label
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("color: inherit;")
        layout.addWidget(self.text_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def update_check_icon(self):
        """Update check icon based on checked state"""
        if self._checked:
            # Show Font Awesome check icon
            icon, text = get_fa_icon('check', "", size=12, color='#ffffff')
            if icon:
                pixmap = icon.pixmap(14, 14)
                self.check_label.setPixmap(pixmap)
            else:
                self.check_label.setText(FA_ICONS.get('check', '✓'))
                apply_fa_font(self.check_label, size=12)
            self.check_label.setStyleSheet("""
                border: 2px solid #0078d4;
                border-radius: 3px;
                background-color: #0078d4;
                color: #ffffff;
            """)
        else:
            # Empty checkbox
            self.check_label.clear()
            self.check_label.setStyleSheet("""
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: transparent;
            """)
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def setChecked(self, checked: bool):
        """Set checked state"""
        if self._checked != checked:
            self._checked = checked
            self.update_check_icon()
            self.toggled.emit(checked)
    
    def isChecked(self) -> bool:
        """Get checked state"""
        return self._checked
    
    def setText(self, text: str):
        """Set text"""
        self._text = text
        self.text_label.setText(text)
    
    def text(self) -> str:
        """Get text"""
        return self._text

