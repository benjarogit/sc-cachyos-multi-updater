#!/usr/bin/env python3
"""
Version Checker for CachyOS Multi-Updater GUI
Checks local version against GitHub releases
"""

import re
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import requests
from requests.exceptions import RequestException, Timeout, HTTPError as RequestsHTTPError

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


class VersionChecker:
    """Checks for updates from GitHub"""

    def __init__(
        self, script_dir: str, github_repo: str = "benjarogit/sc-cachyos-multi-updater"
    ):
        self.script_dir = Path(script_dir)
        self.github_repo = github_repo
        self.logger = get_logger()
        self.logger.debug(f"VersionChecker initialized for {github_repo}")
        self.local_version = self.get_local_version()
        self.latest_version = None

    def get_local_version(self) -> str:
        """Get local script version from VERSION file (root), fallback to update-all.sh"""
        # First try: Read from VERSION file (root directory)
        root_dir = self.script_dir.parent
        version_file = root_dir / "VERSION"

        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version = f.read().strip()
                    if version and re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", version):
                        return version
            except (OSError, IOError, ValueError):
                pass

        # Fallback: Read from update-all.sh
        script_path = self.script_dir / "update-all.sh"
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "readonly SCRIPT_VERSION=" in line:
                        # Extract version from line like: readonly SCRIPT_VERSION="1.0.6"
                        match = re.search(r'["\']([0-9.]+)["\']', line)
                        if match:
                            return match.group(1)
        except (OSError, IOError):
            pass
        except (ValueError, IndexError, AttributeError):
            pass
        except Exception:
            pass
        return "unknown"

    def get_github_repo_url(self) -> str:
        """Get GitHub repository URL from config or use default"""
        config_file = self.script_dir / "config.conf"
        github_repo = self.github_repo

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GITHUB_REPO="):
                            github_repo = line.split("=", 1)[1].strip().strip("\"'")
                            break
            except (OSError, IOError):
                # Failed to read config file - use default
                pass
            except (ValueError, AttributeError):
                # Failed to parse config - use default
                pass
            except Exception:
                # Unexpected error - use default
                pass

        return github_repo

    def check_latest_version(self) -> Tuple[Optional[str], Optional[str]]:
        """Check latest version from GitHub

        Returns:
            Tuple of (latest_version, error_message)
        """
        github_repo = self.get_github_repo_url()

        # Try latest release API first
        api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

        try:
            # Use requests library for secure HTTP requests with SSL verification
            response = requests.get(
                api_url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "CachyOS-Multi-Updater-GUI",
                },
                timeout=10,
                verify=True,
            )
            response.raise_for_status()
            data = response.json()
            tag_name = data.get("tag_name", "")
            # Remove 'v' prefix if present
            version = tag_name.lstrip("v")
            if version:
                self.latest_version = version
                return version, None
        except (RequestException, Timeout, RequestsHTTPError, json.JSONDecodeError, ValueError) as e:
            error_msg = str(e)

        # Fallback: try tags API
        tags_url = f"https://api.github.com/repos/{github_repo}/git/refs/tags"

        try:
            # Use requests library for secure HTTP requests with SSL verification
            response = requests.get(
                tags_url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "CachyOS-Multi-Updater-GUI",
                },
                timeout=10,
                verify=True,
            )
            response.raise_for_status()
            data = response.json()
            versions = []
            for ref in data:
                ref_name = ref.get("ref", "")
                # Extract version from refs/tags/v1.0.6
                match = re.search(r"v?([0-9.]+)$", ref_name)
                if match:
                    versions.append(match.group(1))

            if versions:
                # Sort versions and get latest
                versions.sort(key=lambda v: [int(x) for x in v.split(".")])
                latest = versions[-1]
                self.latest_version = latest
                return latest, None
        except (RequestException, Timeout, RequestsHTTPError, json.JSONDecodeError, ValueError) as e:
            error_msg = str(e)

        return None, error_msg

    def compare_versions(self, local: str, remote: str) -> int:
        """Compare two version strings

        Returns:
            -1 if local < remote (update available)
            0 if local == remote (up to date)
            1 if local > remote (local is newer)
        """

        def version_tuple(v: str) -> Tuple[int, ...]:
            parts = v.split(".")
            return tuple(int(x) for x in parts)

        try:
            local_tuple = version_tuple(local)
            remote_tuple = version_tuple(remote)

            if local_tuple < remote_tuple:
                return -1
            elif local_tuple > remote_tuple:
                return 1
            else:
                return 0
        except (ValueError, AttributeError):
            # If versions can't be compared, assume they're equal
            return 0

    def is_update_available(self) -> Optional[bool]:
        """Check if update is available

        Returns:
            True if update available, False if up to date, None if check failed
        """
        latest, error = self.check_latest_version()
        if latest is None:
            return None

        comparison = self.compare_versions(self.local_version, latest)
        return comparison < 0

    def get_download_url(self) -> str:
        """Get download URL for latest release"""
        github_repo = self.get_github_repo_url()
        if self.latest_version:
            return f"https://github.com/{github_repo}/releases/latest"
        return f"https://github.com/{github_repo}"

    def get_release_zip_url(self, version: str) -> str:
        """Get ZIP download URL for specific version

        Args:
            version: Version string (e.g., "1.0.17")

        Returns:
            URL to download ZIP archive for the version
        """
        github_repo = self.get_github_repo_url()
        # Remove 'v' prefix if present
        version_clean = version.lstrip("v")
        # GitHub archive URL for tag
        return (
            f"https://github.com/{github_repo}/archive/refs/tags/v{version_clean}.zip"
        )

    def get_release_assets(self, version: Optional[str] = None) -> List[Dict]:
        """Get release assets for a specific version or latest release

        Args:
            version: Version string (e.g., "1.0.17"). If None, uses latest release.

        Returns:
            List of asset dictionaries with 'name', 'browser_download_url', 'size', etc.
        """
        github_repo = self.get_github_repo_url()

        # Determine API URL
        if version:
            version_clean = version.lstrip("v")
            api_url = f"https://api.github.com/repos/{github_repo}/releases/tags/v{version_clean}"
        else:
            api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

        try:
            # Use requests library for secure HTTP requests with SSL verification
            import requests
            response = requests.get(
                api_url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "CachyOS-Multi-Updater-GUI",
                },
                timeout=10,
                verify=True,
            )
            response.raise_for_status()
            data = response.json()
            assets = data.get("assets", [])
            return assets
        except (RequestException, Timeout, RequestsHTTPError, json.JSONDecodeError, ValueError):
            return []
