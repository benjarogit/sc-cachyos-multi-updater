#!/usr/bin/env python3
"""
Pytest configuration and fixtures for GUI tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def script_dir(temp_dir: Path) -> Path:
    """Create a script directory structure for tests"""
    script_path = temp_dir / "cachyos-multi-updater"
    script_path.mkdir()

    # Create lang directory
    lang_dir = script_path / "lang"
    lang_dir.mkdir()

    # Create minimal lang files
    (lang_dir / "en.sh").write_text('TRANSLATIONS_EN["test_key"]="Test Value"\n')
    (lang_dir / "de.sh").write_text('TRANSLATIONS_DE["test_key"]="Test Wert"\n')

    # Create config.conf.example
    (script_path / "config.conf.example").write_text(
        "# Example config\nENABLE_SYSTEM_UPDATE=true\n"
    )

    return script_path


@pytest.fixture
def config_file(script_dir: Path) -> Path:
    """Create a test config file"""
    config_path = script_dir / "config.conf"
    config_path.write_text("ENABLE_SYSTEM_UPDATE=true\nENABLE_AUR_UPDATE=false\n")
    return config_path


@pytest.fixture
def version_file(script_dir: Path) -> Path:
    """Create a test VERSION file"""
    root_dir = script_dir.parent
    version_path = root_dir / "VERSION"
    version_path.write_text("1.0.0\n")
    return version_path


@pytest.fixture
def update_script(script_dir: Path) -> Path:
    """Create a test update-all.sh script"""
    script_path = script_dir / "update-all.sh"
    script_path.write_text('#!/bin/bash\nreadonly SCRIPT_VERSION="1.0.0"\n')
    script_path.chmod(0o755)
    return script_path
