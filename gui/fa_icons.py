#!/usr/bin/env python3
"""
Font Awesome Icons Helper
Provides helper function to create Font Awesome icons for buttons
"""

from PyQt6.QtGui import QFont

# Try to import qtawesome for icons, fallback to Unicode if not available
try:
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False

# Font Awesome icon Unicode codes (if qtawesome not available)
FA_ICONS = {
    'github': '\uf09b',      # fa-github
    'search': '\uf002',      # fa-search
    'play': '\uf04b',        # fa-play
    'stop': '\uf04d',        # fa-stop
    'cog': '\uf013',         # fa-cog
    'file-text': '\uf15c',   # fa-file-text
    'times': '\uf00d',       # fa-times
    'check': '\uf00c',       # fa-check
    'save': '\uf0c7',        # fa-save
    'undo': '\uf0e2',        # fa-undo
    'folder-open': '\uf07c', # fa-folder-open
    'window-close': '\uf2d3', # fa-window-close
    'sun': '\uf185',         # fa-sun (light mode)
    'moon': '\uf186',        # fa-moon (dark mode)
    'adjust': '\uf042',      # fa-adjust (auto/theme toggle)
    'language': '\uf1ab',    # fa-language
    'list-alt': '\uf022',    # fa-list-alt (changelog/release)
    'terminal': '\uf120',    # fa-terminal
}

def get_fa_icon(icon_name: str, text: str = "", size: int = 12, color: str = None):
    """Get Font Awesome icon for button
    
    Returns:
        tuple: (icon, text) where icon is QIcon if qtawesome available, None otherwise
               text contains Unicode icon if qtawesome not available
    """
    if HAS_QTAWESOME:
        try:
            icon_map = {
                'github': 'fa.github',
                'search': 'fa.search',
                'play': 'fa.play',
                'stop': 'fa.stop',
                'cog': 'fa.cog',
                'file-text': 'fa.file-text',
                'times': 'fa.times',
                'check': 'fa.check',
                'save': 'fa.save',
                'undo': 'fa.undo',
                'folder-open': 'fa.folder-open',
                'window-close': 'fa.window-close',
                'sun': 'fa.sun',
                'moon': 'fa.moon',
                'adjust': 'fa.adjust',
                'language': 'fa.language',
                'list-alt': 'fa.list-alt',
                'terminal': 'fa.terminal',
            }
            if icon_name in icon_map:
                icon_color = color or '#000000'
                icon = qta.icon(icon_map[icon_name], color=icon_color)
                return icon, text
        except (ImportError, AttributeError, KeyError) as e:
            # qtawesome not available or icon not found - fallback to Unicode
            pass
        except Exception as e:
            # Unexpected error - fallback to Unicode
            pass
    
    # Fallback to Unicode
    if icon_name in FA_ICONS:
        return None, f"{FA_ICONS[icon_name]} {text}".strip()
    return None, text

def apply_fa_font(button, size: int = 12):
    """Apply Font Awesome font to button if using Unicode icons"""
    fa_font = QFont("FontAwesome", size)
    button.setFont(fa_font)

