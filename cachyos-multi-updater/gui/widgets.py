#!/usr/bin/env python3
"""
Custom Widgets for CachyOS Multi-Updater
Reusable widgets following PyQt6 best practices
"""

from PyQt6.QtWidgets import QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent


class ClickableLabel(QLabel):
    """Clickable QLabel that emits a clicked signal
    
    Best Practice: Use signals instead of direct method assignment
    Based on: https://www.pythonguis.com/tutorials/pyqt6-signals-slots-events/
    """
    clicked = pyqtSignal()
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press event and emit clicked signal"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class FlatButton(QPushButton):
    """QPushButton with flat style for label-like appearance
    
    Alternative to ClickableLabel - uses native QPushButton signals
    Based on: https://www.pythonguis.com/tutorials/pyqt6-widgets/
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Transparent background, no border
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                text-align: left;
            }
            QPushButton:hover {
                background: transparent;
            }
        """)

