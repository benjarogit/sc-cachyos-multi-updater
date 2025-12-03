#!/usr/bin/env python3
"""
CachyOS Multi-Updater - GUI Internationalization
Handles translations for the GUI
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional


class GUIi18n:
    """Internationalization for GUI"""
    
    def __init__(self, script_dir: str):
        self.script_dir = Path(script_dir)
        self.lang_dir = self.script_dir / "lang"
        self.translations: Dict[str, str] = {}
        self.current_lang = self.detect_language()
        self.load_translations()
    
    def detect_language(self) -> str:
        """Detect system language"""
        # Check config first
        config_file = self.script_dir / "config.conf"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("GUI_LANGUAGE="):
                            lang = line.split("=", 1)[1].strip()
                            if lang and lang != "auto":
                                return lang
            except (OSError, IOError) as e:
                # Failed to read config file - will detect from system
                pass
            except (ValueError, AttributeError) as e:
                # Failed to parse config - will detect from system
                pass
            except Exception as e:
                # Unexpected error - will detect from system
                pass
        
        # Detect from system
        lang = os.environ.get("LANG", os.environ.get("LC_ALL", "en_US.UTF-8"))
        lang = lang.split("_")[0].split(".")[0].lower()
        
        if lang == "de":
            return "de"
        return "en"
    
    def load_translations(self):
        """Load translations from language file"""
        lang_file = self.lang_dir / f"{self.current_lang}.sh"
        
        if not lang_file.exists():
            # Fallback to English
            lang_file = self.lang_dir / "en.sh"
            self.current_lang = "en"
        
        if not lang_file.exists():
            return
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Parse TRANSLATIONS_DE or TRANSLATIONS_EN array
                array_name = f"TRANSLATIONS_{self.current_lang.upper()}"
                pattern = rf'{array_name}\["([^"]+)"\]="([^"]*)"'
                
                for match in re.finditer(pattern, content):
                    key = match.group(1)
                    value = match.group(2)
                    # Unescape quotes
                    value = value.replace('\\"', '"').replace('\\n', '\n')
                    self.translations[key] = value
        except Exception as e:
            print(f"Error loading translations: {e}")
    
    def t(self, key: str, default: Optional[str] = None) -> str:
        """Get translation"""
        return self.translations.get(key, default or key)
    
    def set_language(self, lang: str):
        """Set language"""
        if lang in ("de", "en"):
            self.current_lang = lang
            self.translations.clear()
            self.load_translations()


# Global instance
_i18n_instance: Optional[GUIi18n] = None


def init_i18n(script_dir: str):
    """Initialize i18n"""
    global _i18n_instance
    _i18n_instance = GUIi18n(script_dir)


def t(key: str, default: Optional[str] = None) -> str:
    """Get translation"""
    if _i18n_instance:
        return _i18n_instance.t(key, default)
    return default or key

