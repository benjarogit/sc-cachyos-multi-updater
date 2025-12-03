#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Syntax Highlighter
Provides syntax highlighting for console output
"""

from PyQt6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt6.QtCore import QRegularExpression


class ConsoleSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for console output"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Success messages (green)
        success_format = QTextCharFormat()
        success_format.setForeground(QColor("#28a745"))
        success_pattern = QRegularExpression(r"✓|✅|success|erfolgreich|completed|done|finished")
        self.highlighting_rules.append((success_pattern, success_format))
        
        # Error messages (red)
        error_format = QTextCharFormat()
        error_format.setForeground(QColor("#dc3545"))
        error_pattern = QRegularExpression(r"✗|❌|error|fehler|failed|failure|warnung|warning")
        self.highlighting_rules.append((error_pattern, error_format))
        
        # Warning messages (orange/yellow)
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor("#ffc107"))
        warning_pattern = QRegularExpression(r"⚠|⚠️|warning|warnung|caution|achtung")
        self.highlighting_rules.append((warning_pattern, warning_format))
        
        # Info messages (blue)
        info_format = QTextCharFormat()
        info_format.setForeground(QColor("#17a2b8"))
        info_pattern = QRegularExpression(r"ℹ|ℹ️|info|information|hinweis")
        self.highlighting_rules.append((info_pattern, info_format))
        
        # Progress indicators (cyan)
        progress_format = QTextCharFormat()
        progress_format.setForeground(QColor("#00bcd4"))
        progress_pattern = QRegularExpression(r"\d+%|\[.*\]\s+\d+%")
        self.highlighting_rules.append((progress_pattern, progress_format))
        
        # Package names (bold)
        package_format = QTextCharFormat()
        package_format.setFontWeight(700)
        package_format.setForeground(QColor("#6f42c1"))
        package_pattern = QRegularExpression(r"\b(pacman|yay|paru|flatpak|cursor|adguard)\b")
        self.highlighting_rules.append((package_pattern, package_format))
        
        # Version numbers (magenta)
        version_format = QTextCharFormat()
        version_format.setForeground(QColor("#e83e8c"))
        version_pattern = QRegularExpression(r"\b\d+\.\d+\.\d+\b")
        self.highlighting_rules.append((version_pattern, version_format))
    
    def highlightBlock(self, text: str):
        """Apply highlighting rules to a block of text"""
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

