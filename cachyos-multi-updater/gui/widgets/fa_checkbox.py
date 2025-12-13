#!/usr/bin/env python3
"""
Font Awesome Checkbox Widget
Custom checkbox that uses Font Awesome check icon
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent

try:
    from .fa_icons import get_fa_icon, apply_fa_font, FA_ICONS
except ImportError:
    from fa_icons import get_fa_icon, apply_fa_font, FA_ICONS


class FACheckBox(QWidget):
    """Checkbox with Font Awesome check icon"""

    toggled = pyqtSignal(bool)
    clicked = pyqtSignal()

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._checked = False
        self._text = text

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Check icon label
        self.check_label = QLabel()
        self.check_label.setObjectName("fa_checkbox_indicator")
        self.check_label.setFixedSize(18, 18)
        self.check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Don't set hardcoded stylesheet here - let Theme Manager handle it
        # Stylesheet will be set by update_check_icon() based on checked state
        self.update_check_icon()
        layout.addWidget(self.check_label)

        # Text label
        self.text_label = QLabel(text)
        self.text_label.setObjectName("fa_checkbox_text")
        layout.addWidget(self.text_label)

        layout.addStretch()
        self.setLayout(layout)

        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def update_check_icon(self) -> None:
        """Update check icon based on checked state"""
        if self._checked:
            # Show Font Awesome check icon
            icon, text = get_fa_icon("check", "", size=12, color="#ffffff")
            if icon:
                pixmap = icon.pixmap(14, 14)
                self.check_label.setPixmap(pixmap)
            else:
                self.check_label.setText(FA_ICONS.get("check", "✓"))
                apply_fa_font(self.check_label, size=12)
            # Use theme colors - checked state uses accent color
            self.check_label.setStyleSheet("""
                QLabel#fa_checkbox_indicator {
                    border: 2px solid #00D9FF;
                    border-radius: 3px;
                    background-color: #00D9FF;
                    color: #ffffff;
                }
            """)
        else:
            # Empty checkbox - clear icon but set stylesheet for visibility
            self.check_label.clear()
            # Set stylesheet for unchecked state - use theme colors
            # Get theme from parent widget if available
            try:
                from ..ui.theme_manager import ThemeManager
                # Try to detect theme from parent
                parent = self.parent()
                theme = "dark"  # Default
                if parent:
                    # Check if parent has theme info
                    try:
                        stylesheet = parent.styleSheet()
                        if "background-color: #ffffff" in stylesheet or "background-color: #f" in stylesheet:
                            theme = "light"
                    except Exception:
                        pass
                else:
                    theme = ThemeManager.detect_system_theme()
            except Exception:
                theme = "dark"
            
            # Set border color based on theme
            border_color = "#555555" if theme == "dark" else "#cccccc"
            bg_color = "#3c3c3c" if theme == "dark" else "#ffffff"
            
            self.check_label.setStyleSheet(f"""
                QLabel#fa_checkbox_indicator {{
                    border: 2px solid {border_color};
                    border-radius: 3px;
                    background-color: {bg_color};
                }}
            """)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.clicked.emit()
        super().mousePressEvent(event)

    def setChecked(self, checked: bool) -> None:
        """Set checked state"""
        if self._checked != checked:
            self._checked = checked
            self.update_check_icon()
            self.toggled.emit(checked)

    def isChecked(self) -> bool:
        """Get checked state"""
        return self._checked

    def setText(self, text: str) -> None:
        """Set text"""
        self._text = text
        self.text_label.setText(text)

    def text(self) -> str:
        """Get text"""
        return self._text
