#!/usr/bin/env python3
"""
Bash Function Wrapper for CachyOS Multi-Updater GUI
Python wrapper for simple bash functions (version checks, update checks)
"""

import subprocess
import json
import re
import os
import shlex
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

# Handle imports
try:
    from .debug_logger import get_logger
except ImportError:
    try:
        from debug_logger import get_logger
    except ImportError:
        def get_logger():
            class DummyLogger:
                def debug(self, *args, **kwargs): pass
                def info(self, *args, **kwargs): pass
                def warning(self, *args, **kwargs): pass
                def error(self, *args, **kwargs): pass
            return DummyLogger()


@dataclass
class UpdateCheckResult:
    """Result of an update check"""
    component: str
    has_update: bool
    current_version: Optional[str] = None
    available_version: Optional[str] = None
    package_count: int = 0
    error: Optional[str] = None


class BashWrapper:
    """Wrapper for calling bash functions directly"""
    
    def __init__(self, script_dir: str):
        self.script_dir = Path(script_dir)
        self.update_script = self.script_dir / "update-all.sh"
        self.logger = get_logger()
        
        if not self.update_script.exists():
            raise FileNotFoundError(f"update-all.sh not found in {script_dir}")
    
    def _run_bash_function(self, function_name: str, *args, env: Optional[Dict] = None) -> Tuple[str, int]:
        """
        Run a bash function from update-all.sh
        
        Args:
            function_name: Name of the function to call
            *args: Arguments to pass to the function
            env: Optional environment variables
            
        Returns:
            Tuple of (stdout, return_code)
        """
        # Create a bash command that sources the script and calls the function
        bash_cmd = f"""
        set -euo pipefail
        source "{self.update_script}"
        {function_name} {' '.join(str(arg) for arg in args)}
        """
        
        try:
            result = subprocess.run(
                ["bash", "-c", bash_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=str(self.script_dir)
            )
            return result.stdout.strip(), result.returncode
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout calling bash function {function_name}")
            return "", 1
        except Exception as e:
            self.logger.error(f"Error calling bash function {function_name}: {e}")
            return "", 1
    
    def check_system_updates(self) -> UpdateCheckResult:
        """Check for system (pacman) updates"""
        try:
            # Use pacman directly for quick check
            result = subprocess.run(
                ["pacman", "-Qu"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                packages = [line for line in result.stdout.strip().split('\n') if line.strip()]
                return UpdateCheckResult(
                    component="system",
                    has_update=len(packages) > 0,
                    package_count=len(packages)
                )
            else:
                # No updates available
                return UpdateCheckResult(
                    component="system",
                    has_update=False,
                    package_count=0
                )
        except subprocess.TimeoutExpired:
            return UpdateCheckResult(
                component="system",
                has_update=False,
                error="Timeout checking system updates"
            )
        except FileNotFoundError:
            return UpdateCheckResult(
                component="system",
                has_update=False,
                error="pacman not found"
            )
        except Exception as e:
            return UpdateCheckResult(
                component="system",
                has_update=False,
                error=str(e)
            )
    
    def check_aur_updates(self) -> UpdateCheckResult:
        """Check for AUR updates"""
        try:
            # Try yay first, then paru
            aur_helper = None
            for helper in ["yay", "paru"]:
                try:
                    subprocess.run([helper, "--version"], capture_output=True, timeout=2)
                    aur_helper = helper
                    break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            if not aur_helper:
                return UpdateCheckResult(
                    component="aur",
                    has_update=False,
                    error="No AUR helper found (yay/paru)"
                )
            
            # Check for updates (non-interactive)
            result = subprocess.run(
                [aur_helper, "-Qua"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = [line for line in result.stdout.strip().split('\n') if line.strip()]
                return UpdateCheckResult(
                    component="aur",
                    has_update=len(packages) > 0,
                    package_count=len(packages)
                )
            else:
                return UpdateCheckResult(
                    component="aur",
                    has_update=False,
                    package_count=0
                )
        except subprocess.TimeoutExpired:
            return UpdateCheckResult(
                component="aur",
                has_update=False,
                error="Timeout checking AUR updates"
            )
        except Exception as e:
            return UpdateCheckResult(
                component="aur",
                has_update=False,
                error=str(e)
            )
    
    def check_cursor_version(self) -> UpdateCheckResult:
        """Check Cursor version and available updates"""
        try:
            # Try to get installed version
            installed_version = None
            
            # Check package.json paths
            package_json_paths = [
                "/usr/share/cursor/resources/app/package.json",
                "/opt/Cursor/resources/app/package.json",
                "/opt/cursor/resources/app/package.json",
                str(Path.home() / ".local/share/cursor/resources/app/package.json")
            ]
            
            for path in package_json_paths:
                if Path(path).exists():
                    try:
                        with open(path, 'r') as f:
                            content = f.read()
                            match = re.search(r'"version":\s*"([0-9.]+)"', content)
                            if match:
                                installed_version = match.group(1)
                                break
                    except Exception:
                        continue
            
            # Check via which cursor
            if not installed_version:
                try:
                    cursor_path = subprocess.run(
                        ["which", "cursor"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    ).stdout.strip()
                    
                    if cursor_path:
                        cursor_dir = Path(cursor_path).resolve().parent
                        package_json = cursor_dir / "resources" / "app" / "package.json"
                        if package_json.exists():
                            with open(package_json, 'r') as f:
                                content = f.read()
                                match = re.search(r'"version":\s*"([0-9.]+)"', content)
                                if match:
                                    installed_version = match.group(1)
                except Exception:
                    pass
            
            if not installed_version:
                return UpdateCheckResult(
                    component="cursor",
                    has_update=False,
                    error="Cursor not installed or version not detectable"
                )
            
            # Check for updates via AUR (if available)
            try:
                for helper in ["yay", "paru"]:
                    try:
                        result = subprocess.run(
                            [helper, "-Qi", "cursor-bin"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            # Extract version from output
                            match = re.search(r'Version\s*:\s*([0-9.]+)', result.stdout)
                            if match:
                                aur_version = match.group(1)
                                has_update = self._compare_versions(installed_version, aur_version) < 0
                                return UpdateCheckResult(
                                    component="cursor",
                                    has_update=has_update,
                                    current_version=installed_version,
                                    available_version=aur_version if has_update else None
                                )
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
            except Exception:
                pass
            
            # Fallback: Assume no update if we can't check
            return UpdateCheckResult(
                component="cursor",
                has_update=False,
                current_version=installed_version
            )
            
        except Exception as e:
            return UpdateCheckResult(
                component="cursor",
                has_update=False,
                error=str(e)
            )
    
    def check_adguard_version(self) -> UpdateCheckResult:
        """Check AdGuard Home version and available updates"""
        try:
            # Try to get current version
            current_version = None
            
            # Check common installation paths
            adguard_paths = [
                Path.home() / "AdGuardHome" / "AdGuardHome",
                Path("/opt/AdGuardHome/AdGuardHome"),
                Path("/usr/local/bin/AdGuardHome")
            ]
            
            for path in adguard_paths:
                if path.exists() and path.is_file():
                    try:
                        result = subprocess.run(
                            [str(path), "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            match = re.search(r'v([0-9.]+)', result.stdout)
                            if match:
                                current_version = match.group(1)
                                break
                    except Exception:
                        continue
            
            if not current_version:
                return UpdateCheckResult(
                    component="adguard",
                    has_update=False,
                    error="AdGuard Home not found or version not detectable"
                )
            
            # Check GitHub for latest version
            try:
                import urllib.request
                import json
                
                url = "https://api.github.com/repos/AdguardTeam/AdGuardHome/releases/latest"
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                    latest_version = data.get("tag_name", "").lstrip("v")
                    
                    if latest_version:
                        has_update = self._compare_versions(current_version, latest_version) < 0
                        return UpdateCheckResult(
                            component="adguard",
                            has_update=has_update,
                            current_version=current_version,
                            available_version=latest_version if has_update else None
                        )
            except Exception as e:
                self.logger.debug(f"Failed to check AdGuard version from GitHub: {e}")
            
            return UpdateCheckResult(
                component="adguard",
                has_update=False,
                current_version=current_version
            )
            
        except Exception as e:
            return UpdateCheckResult(
                component="adguard",
                has_update=False,
                error=str(e)
            )
    
    def check_flatpak_updates(self) -> UpdateCheckResult:
        """Check for Flatpak updates"""
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--updates"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = [line for line in result.stdout.strip().split('\n') if line.strip()]
                return UpdateCheckResult(
                    component="flatpak",
                    has_update=len(packages) > 0,
                    package_count=len(packages)
                )
            else:
                return UpdateCheckResult(
                    component="flatpak",
                    has_update=False,
                    package_count=0
                )
        except subprocess.TimeoutExpired:
            return UpdateCheckResult(
                component="flatpak",
                has_update=False,
                error="Timeout checking Flatpak updates"
            )
        except FileNotFoundError:
            return UpdateCheckResult(
                component="flatpak",
                has_update=False,
                error="flatpak not found"
            )
        except Exception as e:
            return UpdateCheckResult(
                component="flatpak",
                has_update=False,
                error=str(e)
            )
    
    def check_all_updates(self) -> Dict[str, UpdateCheckResult]:
        """Check all components for updates"""
        return {
            "system": self.check_system_updates(),
            "aur": self.check_aur_updates(),
            "cursor": self.check_cursor_version(),
            "adguard": self.check_adguard_version(),
            "flatpak": self.check_flatpak_updates()
        }
    
    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """
        Compare two version strings
        
        Returns:
            -1 if v1 < v2
            0 if v1 == v2
            1 if v1 > v2
        """
        def version_tuple(v: str) -> Tuple[int, ...]:
            parts = v.split('.')
            return tuple(int(part) for part in parts if part.isdigit())
        
        try:
            t1 = version_tuple(v1)
            t2 = version_tuple(v2)
            
            if t1 < t2:
                return -1
            elif t1 > t2:
                return 1
            else:
                return 0
        except Exception:
            # Fallback: string comparison
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0

