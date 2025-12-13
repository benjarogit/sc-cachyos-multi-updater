#!/usr/bin/env python3
"""
Tests for BashWrapper
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from gui.utils.bash_wrapper import BashWrapper, UpdateCheckResult


def test_bash_wrapper_init(script_dir: Path, update_script: Path):
    """Test BashWrapper initialization"""
    wrapper = BashWrapper(str(script_dir))

    assert wrapper.script_dir == script_dir
    assert wrapper.update_script == update_script


def test_bash_wrapper_init_missing_script(script_dir: Path):
    """Test BashWrapper initialization with missing script"""
    update_script = script_dir / "update-all.sh"
    if update_script.exists():
        update_script.unlink()

    with pytest.raises(FileNotFoundError):
        BashWrapper(str(script_dir))


def test_run_bash_function_valid(script_dir: Path, update_script: Path):
    """Test running a valid bash function"""
    # Create a test function in the script
    update_script.write_text(
        '#!/bin/bash\nfunction test_func() { echo "test output"; }\n'
    )

    wrapper = BashWrapper(str(script_dir))
    stdout, returncode = wrapper._run_bash_function("test_func")

    assert returncode == 0
    assert "test output" in stdout


def test_run_bash_function_invalid_name(script_dir: Path, update_script: Path):
    """Test running a function with invalid name"""
    wrapper = BashWrapper(str(script_dir))
    stdout, returncode = wrapper._run_bash_function("invalid-function-name!")

    assert returncode == 1
    assert stdout == ""


def test_run_bash_function_with_args(script_dir: Path, update_script: Path):
    """Test running a bash function with arguments"""
    # Create a test function that takes arguments
    update_script.write_text('#!/bin/bash\nfunction test_func() { echo "$1 $2"; }\n')

    wrapper = BashWrapper(str(script_dir))
    stdout, returncode = wrapper._run_bash_function("test_func", "arg1", "arg2")

    assert returncode == 0
    assert "arg1 arg2" in stdout


@patch("subprocess.run")
def test_check_system_updates(mock_subprocess, script_dir: Path, update_script: Path):
    """Test checking system updates"""
    # Mock pacman output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "package1 1.0.0 -> 1.0.1\npackage2 2.0.0 -> 2.0.1\n"
    mock_subprocess.return_value = mock_result

    wrapper = BashWrapper(str(script_dir))
    result = wrapper.check_system_updates()

    assert isinstance(result, UpdateCheckResult)
    assert result.component == "system"
    assert result.has_update is True
    assert result.package_count == 2


@patch("subprocess.run")
def test_check_system_updates_no_updates(
    mock_subprocess, script_dir: Path, update_script: Path
):
    """Test checking system updates when none available"""
    # Mock pacman output (no updates)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_subprocess.return_value = mock_result

    wrapper = BashWrapper(str(script_dir))
    result = wrapper.check_system_updates()

    assert result.has_update is False
    assert result.package_count == 0


@patch("subprocess.run")
def test_check_aur_updates(mock_subprocess, script_dir: Path, update_script: Path):
    """Test checking AUR updates"""
    # Mock yay/paru output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "package1 1.0.0 -> 1.0.1\n"
    mock_subprocess.return_value = mock_result

    wrapper = BashWrapper(str(script_dir))
    result = wrapper.check_aur_updates()

    assert isinstance(result, UpdateCheckResult)
    assert result.component == "aur"
    assert result.has_update is True


def test_update_check_result_dataclass():
    """Test UpdateCheckResult dataclass"""
    result = UpdateCheckResult(
        component="test",
        has_update=True,
        current_version="1.0.0",
        available_version="1.0.1",
        package_count=5,
    )

    assert result.component == "test"
    assert result.has_update is True
    assert result.current_version == "1.0.0"
    assert result.available_version == "1.0.1"
    assert result.package_count == 5
    assert result.error is None
