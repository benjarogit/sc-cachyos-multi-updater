#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Password Manager
Handles secure storage and retrieval of sudo password using system keyring
"""

import base64
import os
from pathlib import Path
from typing import Optional

# Try to use keyring (system keyring - most secure)
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

# Fallback: Use Fernet encryption (cryptography library)
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class PasswordManager:
    """Manages secure password storage"""
    
    SERVICE_NAME = "cachyos-multi-updater"
    USERNAME = "sudo-password"
    
    def __init__(self, script_dir: str):
        """
        Initialize password manager
        
        Args:
            script_dir: Script directory for key storage (fallback only)
        """
        self.script_dir = Path(script_dir)
        self.key_file = self.script_dir / ".password-key"
        
        # Initialize logger
        try:
            from .debug_logger import get_logger
            self.logger = get_logger()
        except ImportError:
            try:
                from debug_logger import get_logger
                self.logger = get_logger()
            except ImportError:
                # Fallback: Use standard logging
                import logging
                self.logger = logging.getLogger(__name__)
                if not self.logger.handlers:
                    handler = logging.NullHandler()
                    self.logger.addHandler(handler)
        
    def _get_encryption_key(self) -> Optional[bytes]:
        """
        Get or generate encryption key for Fernet
        
        Returns:
            Encryption key bytes or None if cryptography not available
        """
        if not HAS_CRYPTOGRAPHY:
            return None
            
        # Try to load existing key
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except (OSError, IOError) as e:
                self.logger.debug(f"Failed to read key file: {e}")
            except Exception as e:
                self.logger.warning(f"Unexpected error reading key file: {e}")
        
        # Generate new key
        try:
            key = Fernet.generate_key()
            # Store key securely (only readable by owner)
            with open(self.key_file, 'wb') as f:
                os.chmod(self.key_file, 0o600)  # rw-------
                f.write(key)
            return key
        except (OSError, IOError, PermissionError) as e:
            self.logger.error(f"Failed to write key file: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Unexpected error generating/writing key: {e}")
            return None
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password (for Fernet)
        
        Args:
            password: User password
            salt: Salt bytes
            
        Returns:
            Derived key bytes
        """
        if not HAS_CRYPTOGRAPHY:
            return None
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def save_password(self, password: str) -> bool:
        """
        Save password securely
        
        Args:
            password: Password to save
            
        Returns:
            True if successful, False otherwise
        """
        if not password:
            return False
            
        # Method 1: Use system keyring (most secure)
        if HAS_KEYRING:
            try:
                keyring.set_password(self.SERVICE_NAME, self.USERNAME, password)
                return True
            except Exception:
                # Fallback to encryption if keyring fails
                pass
        
        # Method 2: Use Fernet encryption (fallback)
        if HAS_CRYPTOGRAPHY:
            try:
                key = self._get_encryption_key()
                if not key:
                    return False
                    
                fernet = Fernet(key)
                encrypted = fernet.encrypt(password.encode())
                
                # Store encrypted password in config file (base64 encoded)
                # We need to store it in the config file since we can't use keyring
                encrypted_b64 = base64.b64encode(encrypted).decode()
                
                # Store encrypted password in config file via ConfigManager
                # Import ConfigManager here to avoid circular imports
                try:
                    from .config_manager import ConfigManager
                except ImportError:
                    try:
                        from config_manager import ConfigManager
                    except ImportError:
                        self.logger.error("ConfigManager not available for storing encrypted password")
                        return False
                
                config_manager = ConfigManager(self.script_dir)
                config = config_manager.load_config()
                config["SUDO_PASSWORD_ENCRYPTED"] = encrypted_b64
                config_manager.save_config(config)
                
                return True
            except (ValueError, TypeError, AttributeError) as e:
                self.logger.error(f"Failed to encrypt password: {e}")
                return False
            except Exception as e:
                self.logger.warning(f"Unexpected error encrypting password: {e}")
                return False
        
        # Method 3: No encryption available (should not happen)
        return False
    
    def get_password(self) -> Optional[str]:
        """
        Retrieve password securely
        
        Returns:
            Decrypted password or None if not found/error
        """
        # Method 1: Try system keyring first
        if HAS_KEYRING:
            try:
                password = keyring.get_password(self.SERVICE_NAME, self.USERNAME)
                if password:
                    return password
            except Exception:
                pass
        
        # Method 2: Try encrypted config (for Fernet fallback)
        if HAS_CRYPTOGRAPHY:
            try:
                # Import ConfigManager here to avoid circular imports
                try:
                    from .config_manager import ConfigManager
                except ImportError:
                    try:
                        from config_manager import ConfigManager
                    except ImportError:
                        return None
                
                config_manager = ConfigManager(self.script_dir)
                config = config_manager.load_config()
                encrypted_b64 = config.get("SUDO_PASSWORD_ENCRYPTED")
                
                if encrypted_b64:
                    # Decrypt password
                    key = self._get_encryption_key()
                    if not key:
                        return None
                    
                    fernet = Fernet(key)
                    encrypted = base64.b64decode(encrypted_b64.encode())
                    password = fernet.decrypt(encrypted).decode()
                    return password
            except Exception as e:
                self.logger.debug(f"Failed to retrieve encrypted password: {e}")
                return None
        
        return None
    
    def delete_password(self) -> bool:
        """
        Delete stored password
        
        Returns:
            True if successful, False otherwise
        """
        # Method 1: Delete from keyring
        if HAS_KEYRING:
            try:
                keyring.delete_password(self.SERVICE_NAME, self.USERNAME)
            except keyring.errors.PasswordDeleteError:
                # Password doesn't exist, that's OK
                pass
            except (keyring.errors.KeyringError, RuntimeError) as e:
                self.logger.debug(f"Failed to delete password from keyring: {e}")
            except Exception as e:
                self.logger.warning(f"Unexpected error deleting password from keyring: {e}")
        
        # Method 2: Delete encrypted password from config (for Fernet)
        try:
            try:
                from .config_manager import ConfigManager
            except ImportError:
                try:
                    from config_manager import ConfigManager
                except ImportError:
                    ConfigManager = None
            
            if ConfigManager:
                config_manager = ConfigManager(self.script_dir)
                config = config_manager.load_config()
                config.pop("SUDO_PASSWORD_ENCRYPTED", None)
                config_manager.save_config(config)
        except Exception as e:
            self.logger.debug(f"Failed to delete encrypted password from config: {e}")
        
        # Method 3: Delete key file (optional - only if we want to remove encryption key)
        # Note: We don't delete the key file by default, as it might be used for other purposes
        # Uncomment if you want to delete the key file as well:
        # if self.key_file.exists():
        #     try:
        #         self.key_file.unlink()
        #     except (OSError, PermissionError) as e:
        #         self.logger.error(f"Failed to delete key file: {e}")
        
        return True
    
    def is_available(self) -> bool:
        """
        Check if password storage is available
        
        Returns:
            True if keyring or cryptography is available
        """
        return HAS_KEYRING or HAS_CRYPTOGRAPHY
    
    def get_storage_method(self) -> str:
        """
        Get description of storage method
        
        Returns:
            Description string
        """
        if HAS_KEYRING:
            return "System Keyring (most secure)"
        elif HAS_CRYPTOGRAPHY:
            return "Fernet Encryption (secure)"
        else:
            return "Not available (install python-keyring or cryptography)"

