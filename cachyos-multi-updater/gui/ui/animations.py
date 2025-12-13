#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Animation Utilities
Provides animation helpers for modern GUI interactions
"""

from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QAbstractAnimation,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
)
from PyQt6.QtWidgets import QWidget
from typing import Optional, Callable


class AnimationHelper:
    """Helper class for creating common animations"""

    # Animation durations (in milliseconds)
    DURATION_FAST = 150
    DURATION_MEDIUM = 300
    DURATION_SLOW = 500

    @staticmethod
    def create_fade_animation(
        widget: QWidget,
        start_opacity: float = 0.0,
        end_opacity: float = 1.0,
        duration: int = DURATION_FAST,
        easing: QEasingCurve.Type = QEasingCurve.Type.InOutCubic,
    ) -> QPropertyAnimation:
        """Create a fade in/out animation"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(easing)
        return animation

    @staticmethod
    def create_scale_animation(
        widget: QWidget,
        start_scale: float = 1.0,
        end_scale: float = 1.1,
        duration: int = DURATION_FAST,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """Create a scale animation (requires custom property)"""
        # Note: Qt doesn't have built-in scale property, this would need a custom widget
        # For now, we'll use geometry animation as a workaround
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(easing)
        return animation

    @staticmethod
    def create_color_animation(
        widget: QWidget,
        start_color: str,
        end_color: str,
        duration: int = DURATION_FAST,
        easing: QEasingCurve.Type = QEasingCurve.Type.InOutCubic,
    ) -> QPropertyAnimation:
        """Create a color animation (requires custom property)"""
        # Note: Qt doesn't have built-in color property, this would need custom styling
        # For now, this is a placeholder
        animation = QPropertyAnimation(widget, b"styleSheet")
        animation.setDuration(duration)
        animation.setEasingCurve(easing)
        return animation

    @staticmethod
    def create_combined_animation(
        widget: QWidget, animations: list, duration: int = DURATION_MEDIUM
    ) -> QParallelAnimationGroup:
        """Create a parallel animation group combining multiple animations"""
        group = QParallelAnimationGroup()
        for anim in animations:
            anim.setDuration(duration)
            group.addAnimation(anim)
        return group

    @staticmethod
    def create_sequential_animation(animations: list) -> QSequentialAnimationGroup:
        """Create a sequential animation group"""
        group = QSequentialAnimationGroup()
        for anim in animations:
            group.addAnimation(anim)
        return group


def animate_button_hover(
    widget: QWidget, hover: bool = True, duration: int = AnimationHelper.DURATION_FAST
):
    """Animate button hover effect"""
    if hover:
        # Scale up slightly
        # Note: Actual implementation would require custom widget with scale property
        # For now, we'll use opacity and style changes
        widget.setStyleSheet(widget.styleSheet() + " transform: scale(1.05);")
    else:
        widget.setStyleSheet(
            widget.styleSheet().replace(" transform: scale(1.05);", "")
        )


def animate_dialog_show(
    dialog: QWidget, duration: int = AnimationHelper.DURATION_MEDIUM
):
    """Animate dialog appearance (fade + scale)"""
    # Set initial state
    dialog.setWindowOpacity(0.0)

    # Create fade animation
    fade_anim = AnimationHelper.create_fade_animation(dialog, 0.0, 1.0, duration)

    # Start animation
    fade_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    return fade_anim


def animate_dialog_hide(
    dialog: QWidget,
    callback: Optional[Callable] = None,
    duration: int = AnimationHelper.DURATION_FAST,
):
    """Animate dialog disappearance (fade out)"""
    fade_anim = AnimationHelper.create_fade_animation(dialog, 1.0, 0.0, duration)

    if callback:
        fade_anim.finished.connect(callback)

    fade_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    return fade_anim
