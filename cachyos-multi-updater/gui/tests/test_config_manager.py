#!/usr/bin/env python3
"""
Tests for ConfigManager
"""

from pathlib import Path
from gui.core.config_manager import ConfigManager


def test_config_manager_init(script_dir: Path):
    """Test ConfigManager initialization"""
    manager = ConfigManager(str(script_dir))
    assert manager.script_dir == script_dir
    assert manager.config_file == script_dir / "config.conf"
    assert manager.config_example == script_dir / "config.conf.example"


def test_load_config_defaults(script_dir: Path):
    """Test loading config with defaults when no config file exists"""
    manager = ConfigManager(str(script_dir))
    config = manager.load_config()

    assert "ENABLE_SYSTEM_UPDATE" in config
    assert config["ENABLE_SYSTEM_UPDATE"] == "true"
    assert "ENABLE_AUR_UPDATE" in config
    assert config["ENABLE_AUR_UPDATE"] == "true"
    assert "GUI_LANGUAGE" in config
    assert config["GUI_LANGUAGE"] == "auto"


def test_load_config_from_file(config_file: Path, script_dir: Path):
    """Test loading config from existing file"""
    manager = ConfigManager(str(script_dir))
    config = manager.load_config()

    assert config["ENABLE_SYSTEM_UPDATE"] == "true"
    assert config["ENABLE_AUR_UPDATE"] == "false"


def test_load_config_caching(script_dir: Path):
    """Test config caching"""
    manager = ConfigManager(str(script_dir))

    # First load
    config1 = manager.load_config()

    # Second load should use cache
    config2 = manager.load_config()

    assert config1 == config2
    assert config1 is not config2  # Should be a copy


def test_load_config_force_reload(config_file: Path, script_dir: Path):
    """Test force reload bypasses cache"""
    manager = ConfigManager(str(script_dir))

    # Modify file
    config_file.write_text("ENABLE_SYSTEM_UPDATE=false\n")

    # Force reload
    config2 = manager.load_config(force_reload=True)

    assert config2["ENABLE_SYSTEM_UPDATE"] == "false"


def test_save_config(script_dir: Path):
    """Test saving config"""
    manager = ConfigManager(str(script_dir))

    config = manager.load_config()
    config["TEST_KEY"] = "test_value"

    result = manager.save_config(config)
    assert result is True

    # Verify file was written
    assert (script_dir / "config.conf").exists()

    # Verify cache was invalidated
    new_config = manager.load_config()
    assert new_config["TEST_KEY"] == "test_value"


def test_get_method(script_dir: Path):
    """Test get method"""
    manager = ConfigManager(str(script_dir))

    value = manager.get("ENABLE_SYSTEM_UPDATE")
    assert value == "true"

    value = manager.get("NON_EXISTENT_KEY", "default")
    assert value == "default"


def test_set_method(script_dir: Path):
    """Test set method"""
    manager = ConfigManager(str(script_dir))

    result = manager.set("TEST_KEY", "test_value")
    assert result is True

    value = manager.get("TEST_KEY")
    assert value == "test_value"


def test_config_validation_boolean(script_dir: Path):
    """Test boolean value validation"""
    manager = ConfigManager(str(script_dir))

    config = manager.load_config()
    config["ENABLE_SYSTEM_UPDATE"] = "invalid"

    # Save and reload
    manager.save_config(config)
    reloaded = manager.load_config()

    # Invalid boolean values are rejected on load and fall back to default
    # The validation only accepts 'true' or 'false', so invalid values are ignored
    # and the default value is used instead
    assert reloaded["ENABLE_SYSTEM_UPDATE"] == "true"  # Default value


def test_config_validation_numeric(script_dir: Path):
    """Test numeric value validation"""
    manager = ConfigManager(str(script_dir))

    config = manager.load_config()
    config["MAX_LOG_FILES"] = "5"

    manager.save_config(config)
    reloaded = manager.load_config()

    assert reloaded["MAX_LOG_FILES"] == "5"


def test_config_preserves_comments(script_dir: Path):
    """Test that comments are preserved when saving"""
    config_file = script_dir / "config.conf"
    config_file.write_text(
        "# This is a comment\nENABLE_SYSTEM_UPDATE=true\n# Another comment\n"
    )

    manager = ConfigManager(str(script_dir))
    config = manager.load_config()
    config["ENABLE_AUR_UPDATE"] = "false"

    manager.save_config(config)

    content = config_file.read_text()
    assert "# This is a comment" in content
    assert "# Another comment" in content
