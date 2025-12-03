#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Config Manager
Handles reading and writing config.conf file
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """Manages config.conf file reading and writing"""
    
    def __init__(self, script_dir: str):
        self.script_dir = Path(script_dir)
        self.config_file = self.script_dir / "config.conf"
        self.config_example = self.script_dir / "config.conf.example"
        
    def load_config(self) -> Dict[str, str]:
        """Load config from config.conf file"""
        config = {}
        
        # Set defaults
        defaults = {
            "ENABLE_SYSTEM_UPDATE": "true",
            "ENABLE_AUR_UPDATE": "true",
            "ENABLE_CURSOR_UPDATE": "true",
            "ENABLE_ADGUARD_UPDATE": "true",
            "ENABLE_FLATPAK_UPDATE": "true",
            "MAX_LOG_FILES": "3",
            "ENABLE_NOTIFICATIONS": "true",
            "DRY_RUN": "false",
            "ENABLE_COLORS": "true",
            "DOWNLOAD_RETRIES": "3",
            "ENABLE_AUTO_UPDATE": "false",
            "CACHE_MAX_AGE": "3600",
            "GUI_LANGUAGE": "auto",  # auto, de, en
            "GUI_THEME": "auto",  # auto, light, dark
            "PACMAN_SYNC": "true",
            "PACMAN_REFRESH": "true",
            "PACMAN_UPGRADE": "true",
            "PACMAN_NOCONFIRM": "true",
            "SHORTCUT_NAME": "Update All",
            "SHORTCUT_COMMENT": "Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard + Flatpak",
        }
        config.update(defaults)
        
        if not self.config_file.exists():
            return config
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Validate boolean values
                        if key in ["DRY_RUN", "ENABLE_NOTIFICATIONS", "ENABLE_COLORS", 
                                  "ENABLE_AUTO_UPDATE", "ENABLE_SYSTEM_UPDATE", 
                                  "ENABLE_AUR_UPDATE", "ENABLE_CURSOR_UPDATE",
                                  "ENABLE_ADGUARD_UPDATE", "ENABLE_FLATPAK_UPDATE",
                                  "PACMAN_SYNC", "PACMAN_REFRESH", "PACMAN_UPGRADE",
                                  "PACMAN_NOCONFIRM"]:
                            if value.lower() in ('true', 'false'):
                                config[key] = value.lower()
                        # Validate numeric values
                        elif key in ["MAX_LOG_FILES", "DOWNLOAD_RETRIES", "CACHE_MAX_AGE"]:
                            if value.isdigit():
                                config[key] = value
                        else:
                            config[key] = value
        except Exception as e:
            print(f"Error loading config: {e}")
            
        return config
    
    def save_config(self, config: Dict[str, str]) -> bool:
        """Save config to config.conf file"""
        try:
            # Read existing file to preserve comments
            lines = []
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Create new content
            new_lines = []
            written_keys = set()
            
            # Process existing lines
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    new_lines.append(line)
                    continue
                    
                if '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in config:
                        new_lines.append(f"{key}={config[key]}\n")
                        written_keys.add(key)
                        continue
                
                new_lines.append(line)
            
            # Add any new keys
            for key, value in sorted(config.items()):
                if key not in written_keys:
                    new_lines.append(f"{key}={value}\n")
            
            # Write file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get config value"""
        config = self.load_config()
        return config.get(key, default)
    
    def set(self, key: str, value: str) -> bool:
        """Set config value"""
        config = self.load_config()
        config[key] = value
        return self.save_config(config)
    
    def get_password(self) -> Optional[str]:
        """
        Get stored sudo password (from secure storage, not config)
        
        Returns:
            Password string or None
        """
        # Password should be stored in keyring, not config
        # This method is for backward compatibility
        # Real password retrieval should use PasswordManager
        return None
    
    def set_password(self, password: str) -> bool:
        """
        Store sudo password securely (not in config file)
        
        Args:
            password: Password to store
            
        Returns:
            True if successful
        """
        # Password should be stored in keyring, not config
        # This method is for backward compatibility
        # Real password storage should use PasswordManager
        # For now, we'll use a marker in config to indicate password is stored
        if password:
            config = self.load_config()
            config["SUDO_PASSWORD_STORED"] = "true"  # Marker only
            return self.save_config(config)
        else:
            config = self.load_config()
            config.pop("SUDO_PASSWORD_STORED", None)
            return self.save_config(config)

