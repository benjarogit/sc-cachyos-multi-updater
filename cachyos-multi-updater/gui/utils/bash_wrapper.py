#!/usr/bin/env python3
"""
Bash Function Wrapper for CachyOS Multi-Updater GUI
Python wrapper for simple bash functions (version checks, update checks)
"""

import subprocess
import json
import re
import shlex
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass
import logging

# Import from new structure
from .debug_logger import get_logger


@dataclass
class UpdateCheckResult:
    """Result of an update check"""

    component: str
    has_update: bool
    current_version: Optional[str] = None
    available_version: Optional[str] = None
    package_count: int = 0
    packages: Optional[List[str]] = None
    error: Optional[str] = None
    installation_type: Optional[str] = None  # "aur", "manual", "portable", "unknown"
    migration_hint: Optional[str] = None  # Hint for migration if manual/portable


class BashWrapper:
    """Wrapper for calling bash functions directly"""

    def __init__(self, script_dir: str) -> None:
        self.script_dir: Path = Path(script_dir)
        self.update_script: Path = self.script_dir / "update-all.sh"
        self.logger: logging.Logger = get_logger()

        if not self.update_script.exists():
            raise FileNotFoundError(f"update-all.sh not found in {script_dir}")

    def _run_bash_function(
        self, function_name: str, *args: Any, env: Optional[Dict[str, str]] = None
    ) -> Tuple[str, int]:
        """
        Run a bash function from update-all.sh

        Args:
            function_name: Name of the function to call
            *args: Arguments to pass to the function
            env: Optional environment variables

        Returns:
            Tuple of (stdout, return_code)
        """
        # Security: Validate function_name to prevent command injection
        if not function_name or not re.match(
            r"^[a-zA-Z_][a-zA-Z0-9_]*$", function_name
        ):
            self.logger.error(f"Invalid function name: {function_name}")
            return "", 1

        # Security: Use shlex.quote() to prevent shell injection
        quoted_script = shlex.quote(str(self.update_script))
        quoted_function = shlex.quote(function_name)
        quoted_args = " ".join(shlex.quote(str(arg)) for arg in args)

        # Create a bash command that sources the script and calls the function
        bash_cmd = f"""
        set -euo pipefail
        source {quoted_script}
        {quoted_function} {quoted_args}
        """

        try:
            result = subprocess.run(
                ["bash", "-c", bash_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=str(self.script_dir),
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
                ["pacman", "-Qu"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                packages = [
                    line for line in result.stdout.strip().split("\n") if line.strip()
                ]
                return UpdateCheckResult(
                    component="system",
                    has_update=len(packages) > 0,
                    package_count=len(packages),
                    packages=packages if packages else [],
                )
            else:
                # No updates available
                return UpdateCheckResult(
                    component="system", has_update=False, package_count=0
                )
        except subprocess.TimeoutExpired:
            return UpdateCheckResult(
                component="system",
                has_update=False,
                error="Timeout checking system updates",
            )
        except FileNotFoundError:
            return UpdateCheckResult(
                component="system", has_update=False, error="pacman not found"
            )
        except Exception as e:
            return UpdateCheckResult(component="system", has_update=False, error=str(e))

    def check_aur_updates(self) -> UpdateCheckResult:
        """Check for AUR updates"""
        try:
            # Try yay first, then paru
            aur_helper: Optional[str] = None
            for helper in ["yay", "paru"]:
                try:
                    subprocess.run(
                        [helper, "--version"], capture_output=True, timeout=2
                    )
                    aur_helper = helper
                    break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            if not aur_helper:
                return UpdateCheckResult(
                    component="aur",
                    has_update=False,
                    error="No AUR helper found (yay/paru)",
                )

            # Check for updates (non-interactive)
            result = subprocess.run(
                [aur_helper, "-Qua"], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                packages = [
                    line for line in result.stdout.strip().split("\n") if line.strip()
                ]
                return UpdateCheckResult(
                    component="aur",
                    has_update=len(packages) > 0,
                    package_count=len(packages),
                    packages=packages if packages else [],
                )
            else:
                return UpdateCheckResult(
                    component="aur", has_update=False, package_count=0
                )
        except subprocess.TimeoutExpired:
            return UpdateCheckResult(
                component="aur", has_update=False, error="Timeout checking AUR updates"
            )
        except Exception as e:
            return UpdateCheckResult(component="aur", has_update=False, error=str(e))

    def _detect_cursor_installation_type(self) -> Tuple[Optional[str], Optional[str]]:
        """Detect Cursor installation type and return (type, hint)
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (installation_type, migration_hint)
            installation_type: "aur", "manual", "portable", "unknown"
        """
        installation_type: Optional[str] = None
        migration_hint: Optional[str] = None
        
        # 1. Check AUR installation
        try:
            # Check if cursor-bin is installed via AUR
            result = subprocess.run(
                ["pacman", "-Q", "cursor-bin"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return ("aur", None)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check via pacman -Qo (which package owns the cursor binary)
        try:
            cursor_path = subprocess.run(
                ["which", "cursor"], capture_output=True, text=True, timeout=2
            ).stdout.strip()
            
            if cursor_path:
                result = subprocess.run(
                    ["pacman", "-Qo", cursor_path],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and "cursor" in result.stdout.lower():
                    return ("aur", None)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 2. Check portable installation
        portable_paths = [
            str(Path.home() / ".local/bin/cursor"),
            str(Path.home() / ".local/bin/cursor.AppImage"),
            str(Path.home() / "Applications/cursor.AppImage"),
            str(Path.home() / "Apps/cursor.AppImage"),
            str(Path.home() / "Applications/Cursor.AppImage"),
            str(Path.home() / "Apps/Cursor.AppImage"),
        ]
        
        for portable in portable_paths:
            if Path(portable).exists():
                migration_hint = (
                    "Portable installation detected. Consider migrating to AUR package "
                    "(cursor-bin) for automatic updates."
                )
                return ("portable", migration_hint)
        
        # Check if running process is AppImage
        try:
            result = subprocess.run(
                ["pgrep", "-f", "cursor"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                pid = result.stdout.strip().split()[0]
                exe_path = Path(f"/proc/{pid}/exe")
                if exe_path.exists():
                    real_path = exe_path.resolve()
                    if ".AppImage" in str(real_path) or ".local/bin" in str(real_path):
                        migration_hint = (
                            "Portable installation detected. Consider migrating to AUR package "
                            "(cursor-bin) for automatic updates."
                        )
                        return ("portable", migration_hint)
        except Exception:
            pass
        
        # 3. Check manual installation
        manual_paths = [
            "/usr/share/cursor",
            "/opt/cursor",
            "/opt/Cursor",
            "/usr/local/bin/cursor",
        ]
        
        for manual_path in manual_paths:
            if Path(manual_path).exists():
                migration_hint = (
                    "Manual installation detected. Consider migrating to AUR package "
                    "(cursor-bin) for automatic updates."
                )
                return ("manual", migration_hint)
        
        # 4. Unknown
        return ("unknown", None)

    def check_cursor_version(self) -> UpdateCheckResult:
        """Check Cursor version and available updates"""
        try:
            # Detect installation type first
            installation_type, migration_hint = self._detect_cursor_installation_type()
            
            # Try to get installed version
            installed_version: Optional[str] = None

            # Check package.json paths (including portable installations)
            package_json_paths = [
                "/usr/share/cursor/resources/app/package.json",
                "/opt/Cursor/resources/app/package.json",
                "/opt/cursor/resources/app/package.json",
                str(Path.home() / ".local/share/cursor/resources/app/package.json"),
            ]

            # Check portable installation paths
            portable_paths = [
                str(Path.home() / ".local/bin/cursor"),
                str(Path.home() / ".local/bin/cursor.AppImage"),
                str(Path.home() / "Applications/cursor.AppImage"),
                str(Path.home() / "Apps/cursor.AppImage"),
                str(Path.home() / "Applications/Cursor.AppImage"),
                str(Path.home() / "Apps/Cursor.AppImage"),
            ]
            
            is_portable = installation_type == "portable"
            portable_path = None

            for path in package_json_paths:
                if Path(path).exists():
                    try:
                        with open(path, "r") as f:
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
                        ["which", "cursor"], capture_output=True, text=True, timeout=2
                    ).stdout.strip()

                    if cursor_path:
                        # Check if it's a portable installation (AppImage or in ~/.local/bin)
                        cursor_path_obj = Path(cursor_path)
                        if cursor_path_obj.suffix == ".AppImage" or ".local/bin" in str(cursor_path_obj):
                            is_portable = True
                            portable_path = cursor_path
                        
                        cursor_dir = cursor_path_obj.resolve().parent
                        package_json = cursor_dir / "resources" / "app" / "package.json"
                        if package_json.exists():
                            with open(package_json, "r") as f:
                                content = f.read()
                                match = re.search(r'"version":\s*"([0-9.]+)"', content)
                                if match:
                                    installed_version = match.group(1)
                except Exception:
                    pass
            
            # Check portable paths directly
            if not installed_version:
                for portable in portable_paths:
                    portable_obj = Path(portable)
                    if portable_obj.exists():
                        is_portable = True
                        portable_path = str(portable_obj)
                        # Try to extract version from AppImage or portable installation
                        if portable_obj.suffix == ".AppImage":
                            # For AppImage, try to run it with --version or check metadata
                            try:
                                result = subprocess.run(
                                    [str(portable_obj), "--version"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5,
                                )
                                if result.returncode == 0:
                                    match = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", result.stdout)
                                    if match:
                                        installed_version = match.group(1)
                                        break
                            except Exception:
                                pass
                        # Check if there's a package.json nearby
                        if portable_obj.is_file():
                            cursor_dir = portable_obj.parent
                            package_json = cursor_dir / "resources" / "app" / "package.json"
                            if not package_json.exists() and portable_obj.name.endswith(".AppImage"):
                                # AppImage might be in a directory
                                app_dir = portable_obj.parent / portable_obj.stem
                                package_json = app_dir / "resources" / "app" / "package.json"
                            if package_json.exists():
                                try:
                                    with open(package_json, "r") as f:
                                        content = f.read()
                                        match = re.search(r'"version":\s*"([0-9.]+)"', content)
                                        if match:
                                            installed_version = match.group(1)
                                            break
                                except Exception:
                                    pass

            if not installed_version:
                error_msg = "Cursor not installed or version not detectable"
                if migration_hint:
                    error_msg += f" ({migration_hint})"
                return UpdateCheckResult(
                    component="cursor",
                    has_update=False,
                    error=error_msg,
                    installation_type=installation_type,
                    migration_hint=migration_hint,
                )

            # Check for updates via AUR (if available)
            try:
                for helper in ["yay", "paru"]:
                    try:
                        result = subprocess.run(
                            [helper, "-Qi", "cursor-bin"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        if result.returncode == 0:
                            # Extract version from output
                            match = re.search(r"Version\s*:\s*([0-9.]+)", result.stdout)
                            if match:
                                aur_version = match.group(1)
                                has_update = (
                                    self._compare_versions(
                                        installed_version, aur_version
                                    )
                                    < 0
                                )
                                return UpdateCheckResult(
                                    component="cursor",
                                    has_update=has_update,
                                    current_version=installed_version,
                                    available_version=aur_version
                                    if has_update
                                    else None,
                                    installation_type=installation_type,
                                    migration_hint=migration_hint,
                                )
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
            except Exception:
                pass

            # Fallback: Assume no update if we can't check
            return UpdateCheckResult(
                component="cursor",
                has_update=False,
                current_version=installed_version,
                installation_type=installation_type,
                migration_hint=migration_hint,
            )

        except Exception as e:
            installation_type, migration_hint = self._detect_cursor_installation_type()
            return UpdateCheckResult(
                component="cursor",
                has_update=False,
                error=str(e),
                installation_type=installation_type,
                migration_hint=migration_hint,
            )

    def _detect_adguard_installation_type(self) -> Tuple[Optional[str], Optional[str]]:
        """Detect AdGuard Home installation type and return (type, hint)
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (installation_type, migration_hint)
            installation_type: "aur", "manual", "portable", "unknown"
        """
        installation_type: Optional[str] = None
        migration_hint: Optional[str] = None
        
        # 1. Check AUR installation
        try:
            # Check if adguardhome is installed via AUR
            for pkg_name in ["adguardhome", "adguard-home-bin"]:
                result = subprocess.run(
                    ["pacman", "-Q", pkg_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return ("aur", None)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check via pacman -Qo (which package owns the AdGuardHome binary)
        try:
            adguard_path = subprocess.run(
                ["which", "AdGuardHome"], capture_output=True, text=True, timeout=2
            ).stdout.strip()
            
            if adguard_path:
                result = subprocess.run(
                    ["pacman", "-Qo", adguard_path],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and "adguard" in result.stdout.lower():
                    return ("aur", None)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check systemd service
        try:
            result = subprocess.run(
                ["systemctl", "status", "AdGuardHome"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Service exists - check if it's from package or manual
                service_file = subprocess.run(
                    ["systemctl", "cat", "AdGuardHome"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if service_file.returncode == 0:
                    # If service file is in /usr/lib/systemd, it's from package
                    if "/usr/lib/systemd" in service_file.stdout:
                        return ("aur", None)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 2. Check portable installation
        portable_paths = [
            Path.home() / ".local/bin/AdGuardHome",
            Path.home() / "AdGuardHome" / "AdGuardHome",
        ]
        
        for portable in portable_paths:
            if portable.exists():
                migration_hint = (
                    "Portable installation detected. Consider migrating to AUR package "
                    "(adguardhome) for automatic updates and systemd service."
                )
                return ("portable", migration_hint)
        
        # 3. Check manual installation
        manual_paths = [
            Path("/opt/AdGuardHome/AdGuardHome"),
            Path("/usr/local/bin/AdGuardHome"),
        ]
        
        for manual_path in manual_paths:
            if manual_path.exists():
                migration_hint = (
                    "Manual installation detected. Consider migrating to AUR package "
                    "(adguardhome) for automatic updates and systemd service."
                )
                return ("manual", migration_hint)
        
        # 4. Unknown
        return ("unknown", None)

    def check_adguard_version(self) -> UpdateCheckResult:
        """Check AdGuard Home version and available updates"""
        try:
            # Detect installation type first
            installation_type, migration_hint = self._detect_adguard_installation_type()
            
            # Try to get current version
            current_version: Optional[str] = None

            # Check common installation paths (including portable installations)
            adguard_paths = [
                Path.home() / "AdGuardHome" / "AdGuardHome",
                Path("/opt/AdGuardHome/AdGuardHome"),
                Path("/usr/local/bin/AdGuardHome"),
                Path.home() / ".local/bin/AdGuardHome",
            ]

            for path in adguard_paths:
                if path.exists() and path.is_file():
                    try:
                        result = subprocess.run(
                            [str(path), "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if result.returncode == 0:
                            match = re.search(r"v([0-9.]+)", result.stdout)
                            if match:
                                current_version = match.group(1)
                                break
                    except Exception:
                        continue

            if not current_version:
                error_msg = "AdGuard Home not found or version not detectable"
                if migration_hint:
                    error_msg += f" ({migration_hint})"
                return UpdateCheckResult(
                    component="adguard",
                    has_update=False,
                    error=error_msg,
                    installation_type=installation_type,
                    migration_hint=migration_hint,
                )

            # Check GitHub for latest version
            try:
                url = "https://api.github.com/repos/AdguardTeam/AdGuardHome/releases/latest"
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                    latest_version = data.get("tag_name", "").lstrip("v")

                    if latest_version:
                        has_update = (
                            self._compare_versions(current_version, latest_version) < 0
                        )
                        return UpdateCheckResult(
                            component="adguard",
                            has_update=has_update,
                            current_version=current_version,
                            available_version=latest_version if has_update else None,
                            installation_type=installation_type,
                            migration_hint=migration_hint,
                        )
            except Exception as e:
                self.logger.debug(f"Failed to check AdGuard version from GitHub: {e}")

            return UpdateCheckResult(
                component="adguard",
                has_update=False,
                current_version=current_version,
                installation_type=installation_type,
                migration_hint=migration_hint,
            )

        except Exception as e:
            installation_type, migration_hint = self._detect_adguard_installation_type()
            return UpdateCheckResult(
                component="adguard",
                has_update=False,
                error=str(e),
                installation_type=installation_type,
                migration_hint=migration_hint,
            )

    def check_proton_ge_version(self) -> UpdateCheckResult:
        """Check Proton-GE version and available updates"""
        try:
            # Check installed versions in Steam compatibilitytools directories
            proton_paths = [
                Path.home() / ".steam" / "steam" / "compatibilitytools.d",
                Path.home() / ".local" / "share" / "Steam" / "compatibilitytools.d",
            ]
            
            installed_versions: List[str] = []
            
            for proton_path in proton_paths:
                if proton_path.exists() and proton_path.is_dir():
                    for item in proton_path.iterdir():
                        if item.is_dir() and "Proton" in item.name and "GE" in item.name:
                            # Extract version from directory name (e.g., "GE-Proton8-25" -> "8-25")
                            match = re.search(r"GE-Proton(\d+-\d+)", item.name)
                            if match:
                                installed_versions.append(match.group(1))
            
            if not installed_versions:
                return UpdateCheckResult(
                    component="proton_ge",
                    has_update=False,
                    error="Proton-GE not found in Steam compatibilitytools directories",
                )
            
            # Get latest version from GitHub
            try:
                url = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                    latest_tag = data.get("tag_name", "")
                    
                    # Extract version from tag (e.g., "GE-Proton8-25" -> "8-25")
                    match = re.search(r"GE-Proton(\d+-\d+)", latest_tag)
                    if match:
                        latest_version = match.group(1)
                        
                        # Compare versions (format: "8-25" -> compare major.minor)
                        latest_major, latest_minor = map(int, latest_version.split("-"))
                        
                        # Check if any installed version is older
                        has_update = False
                        current_version_str = ", ".join(installed_versions)
                        
                        for installed in installed_versions:
                            try:
                                installed_major, installed_minor = map(int, installed.split("-"))
                                if (installed_major < latest_major) or (
                                    installed_major == latest_major
                                    and installed_minor < latest_minor
                                ):
                                    has_update = True
                                    break
                            except ValueError:
                                continue
                        
                        return UpdateCheckResult(
                            component="proton_ge",
                            has_update=has_update,
                            current_version=current_version_str,
                            available_version=latest_version if has_update else None,
                        )
            except Exception as e:
                self.logger.debug(f"Failed to check Proton-GE version from GitHub: {e}")
            
            # Fallback: return installed versions
            return UpdateCheckResult(
                component="proton_ge",
                has_update=False,
                current_version=", ".join(installed_versions),
            )
            
        except Exception as e:
            return UpdateCheckResult(
                component="proton_ge", has_update=False, error=str(e)
            )

    def check_flatpak_updates(self) -> UpdateCheckResult:
        """Check for Flatpak updates"""
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--updates"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                packages = [
                    line for line in result.stdout.strip().split("\n") if line.strip()
                ]
                return UpdateCheckResult(
                    component="flatpak",
                    has_update=len(packages) > 0,
                    package_count=len(packages),
                    packages=packages if packages else [],
                )
            else:
                return UpdateCheckResult(
                    component="flatpak", has_update=False, package_count=0
                )
        except subprocess.TimeoutExpired:
            return UpdateCheckResult(
                component="flatpak",
                has_update=False,
                error="Timeout checking Flatpak updates",
            )
        except FileNotFoundError:
            return UpdateCheckResult(
                component="flatpak", has_update=False, error="flatpak not found"
            )
        except Exception as e:
            return UpdateCheckResult(
                component="flatpak", has_update=False, error=str(e)
            )

    def check_all_updates(self) -> Dict[str, UpdateCheckResult]:
        """Check all components for updates"""
        return {
            "system": self.check_system_updates(),
            "aur": self.check_aur_updates(),
            "cursor": self.check_cursor_version(),
            "adguard": self.check_adguard_version(),
            "flatpak": self.check_flatpak_updates(),
            "proton_ge": self.check_proton_ge_version(),
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
            parts = v.split(".")
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
