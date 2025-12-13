#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Toast Notifications
Provides toast-style notifications for the GUI
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont

# Handle imports for both direct execution and module import
try:
    from .debug_logger import get_logger
except ImportError:
    try:
        from debug_logger import get_logger
    except ImportError:

        def get_logger():
            class DummyLogger:
                def debug(self, *args, **kwargs):
                    pass

                def info(self, *args, **kwargs):
                    pass

                def warning(self, *args, **kwargs):
                    pass

                def error(self, *args, **kwargs):
                    pass

                def exception(self, *args, **kwargs):
                    pass

            return DummyLogger()


class ToastNotification(QWidget):
    """Toast notification widget"""

    closed = pyqtSignal()

    def __init__(self, message: str, duration: int = 3000, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.logger.debug(f"ToastNotification created: {message[:50]}...")
        self.message = message
        self.duration = duration
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)

        # Message label
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(43, 43, 43, 240);
                color: #ffffff;
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #555555;
            }
        """)
        layout.addWidget(self.label)

        self.setLayout(layout)

        # Adjust size
        self.adjustSize()

        # Animation
        self.fade_animation = None
        self.slide_animation = None

    def showEvent(self, event):
        """Show toast with animation"""
        super().showEvent(event)

        # Position at top-right of parent
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(parent_rect.right() - self.width() - 20, parent_rect.top() + 20)
        else:
            # Center on screen if no parent
            from PyQt6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            self.move(screen.right() - self.width() - 20, screen.top() + 20)

        # Fade in animation
        self.setWindowOpacity(0.0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()

        # Auto-close timer
        QTimer.singleShot(self.duration, self.fade_out)

    def fade_out(self):
        """Fade out and close"""
        if self.fade_animation:
            self.fade_animation.stop()

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

    def closeEvent(self, event):
        """Handle close event"""
        self.closed.emit()
        super().closeEvent(event)


def show_toast(
    parent: QWidget, message: str, duration: int = 3000
) -> ToastNotification:
    """Show a toast notification"""
    toast = ToastNotification(message, duration, parent)
    toast.show()
    return toast
