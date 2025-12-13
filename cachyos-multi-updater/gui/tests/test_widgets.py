#!/usr/bin/env python3
"""
Tests for custom widgets
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from gui.widgets.widgets import ClickableLabel, FlatButton


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_clickable_label_init(qapp):
    """Test ClickableLabel initialization"""
    label = ClickableLabel("Test", None)

    assert label.text() == "Test"
    assert label.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_clickable_label_signal(qapp):
    """Test ClickableLabel clicked signal"""
    label = ClickableLabel("Test", None)
    clicked = False

    def on_clicked():
        nonlocal clicked
        clicked = True

    label.clicked.connect(on_clicked)

    # Simulate mouse click
    QTest.mouseClick(label, Qt.MouseButton.LeftButton)

    assert clicked is True


def test_clickable_label_right_click_no_signal(qapp):
    """Test that right click doesn't emit signal"""
    label = ClickableLabel("Test", None)
    clicked = False

    def on_clicked():
        nonlocal clicked
        clicked = True

    label.clicked.connect(on_clicked)

    # Simulate right mouse click
    QTest.mouseClick(label, Qt.MouseButton.RightButton)

    assert clicked is False


def test_flat_button_init(qapp):
    """Test FlatButton initialization"""
    button = FlatButton("Test", None)

    assert button.text() == "Test"
    assert button.isFlat() is True
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_flat_button_click(qapp):
    """Test FlatButton click"""
    button = FlatButton("Test", None)
    clicked = False

    def on_clicked():
        nonlocal clicked
        clicked = True

    button.clicked.connect(on_clicked)

    QTest.mouseClick(button, Qt.MouseButton.LeftButton)

    assert clicked is True
