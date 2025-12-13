#!/usr/bin/env python3
"""
Tests for VersionChecker
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
from gui.utils.version_checker import VersionChecker


def test_version_checker_init(script_dir: Path, version_file: Path):
    """Test VersionChecker initialization"""
    checker = VersionChecker(str(script_dir))

    assert checker.script_dir == script_dir
    assert checker.github_repo == "benjarogit/sc-cachyos-multi-updater"
    assert checker.local_version == "1.0.0"


def test_get_local_version_from_file(script_dir: Path, version_file: Path):
    """Test getting local version from VERSION file"""
    checker = VersionChecker(str(script_dir))
    version = checker.get_local_version()

    assert version == "1.0.0"


def test_get_local_version_from_script(script_dir: Path, update_script: Path):
    """Test getting local version from update-all.sh"""
    # Remove VERSION file
    root_dir = script_dir.parent
    version_file = root_dir / "VERSION"
    if version_file.exists():
        version_file.unlink()

    checker = VersionChecker(str(script_dir))
    version = checker.get_local_version()

    assert version == "1.0.0"


def test_get_local_version_unknown(script_dir: Path):
    """Test getting local version when no version found"""
    # Remove VERSION file and update script
    root_dir = script_dir.parent
    version_file = root_dir / "VERSION"
    if version_file.exists():
        version_file.unlink()

    update_script = script_dir / "update-all.sh"
    if update_script.exists():
        update_script.unlink()

    checker = VersionChecker(str(script_dir))
    version = checker.get_local_version()

    assert version == "unknown"


def test_get_github_repo_url_from_config(script_dir: Path):
    """Test getting GitHub repo URL from config"""
    config_file = script_dir / "config.conf"
    config_file.write_text("GITHUB_REPO=test/repo\n")

    checker = VersionChecker(str(script_dir))
    repo = checker.get_github_repo_url()

    assert repo == "test/repo"


def test_get_github_repo_url_default(script_dir: Path):
    """Test getting default GitHub repo URL"""
    checker = VersionChecker(str(script_dir))
    repo = checker.get_github_repo_url()

    assert repo == "benjarogit/sc-cachyos-multi-updater"


@patch("gui.utils.version_checker.urlopen")
def test_check_latest_version_success(mock_urlopen, script_dir: Path):
    """Test checking latest version successfully"""
    # Mock GitHub API response - urlopen returns a context manager
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"tag_name": "v1.0.1"}'
    # urlopen is called directly and returns a context manager
    mock_urlopen.return_value.__enter__.return_value = mock_response
    mock_urlopen.return_value.__exit__.return_value = False

    checker = VersionChecker(str(script_dir))
    latest, error = checker.check_latest_version()

    assert latest == "1.0.1"
    assert error is None


@patch("gui.utils.version_checker.urlopen")
def test_check_latest_version_error(mock_urlopen, script_dir: Path):
    """Test checking latest version with error"""
    # Mock network error - exception raised when urlopen is called
    from urllib.error import URLError

    mock_urlopen.side_effect = URLError("Network error")

    checker = VersionChecker(str(script_dir))
    latest, error = checker.check_latest_version()

    # On error, latest should be None and error should contain the error message
    assert latest is None
    assert error is not None
    assert len(error) > 0  # Error message should be present


def test_compare_versions(script_dir: Path):
    """Test version comparison"""
    checker = VersionChecker(str(script_dir))

    # Test newer version
    result = checker.compare_versions("1.0.0", "1.0.1")
    assert result < 0

    # Test older version
    result = checker.compare_versions("1.0.1", "1.0.0")
    assert result > 0

    # Test same version
    result = checker.compare_versions("1.0.0", "1.0.0")
    assert result == 0


def test_compare_versions_invalid(script_dir: Path):
    """Test version comparison with invalid versions"""
    checker = VersionChecker(str(script_dir))

    # Invalid version should return 0 (equal)
    result = checker.compare_versions("invalid", "1.0.0")
    assert result == 0
