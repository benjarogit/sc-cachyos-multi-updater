[![Version](https://img.shields.io/badge/version-2.3.0-blue)](https://github.com/benjarogit/sc-cachyos-multi-updater/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org)
[![PyQt6](https://img.shields.io/pypi/pyversions/PyQt6)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/benjarogit/sc-cachyos-multi-updater/total)](https://github.com/benjarogit/sc-cachyos-multi-updater/releases)

# CachyOS Multi-Updater

A modern PyQt6 tool that lets you update **all package sources simultaneously** on CachyOS / Arch Linux – pacman, flatpak, snap, aura, yay, pikaur, paru and more – with just one click.

> **Language / Sprache:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

## Features

- ✅ **Simultaneous Updates** - Update all supported package managers at once
- ✅ **Live Log View** - Real-time colored output with syntax highlighting
- ✅ **Dark / Light / Auto Theme** - Automatically adapts to your system theme
- ✅ **Full Localization** - Complete German/English translation support
- ✅ **Configuration Dialog** - Comprehensive settings with validation
- ✅ **Automatic Version Check** - Checks for updates on startup
- ✅ **Secure Bash Wrapper** - Uses shlex.quote, no unsafe shell=True calls
- ✅ **Type Hints** - 100% type-annotated codebase for better maintainability
- ✅ **Comprehensive Tests** - 44+ unit tests with 13% coverage
- ✅ **Modern Architecture** - Clean code, best practices, performance optimizations

## Screenshots

![Hero](screenshots/hero.png)

<details>
<summary>More Screenshots (click to expand)</summary>

![Thumb 1](screenshots/thumb-1.png) ![Thumb 2](screenshots/thumb-2.png) ![Thumb 3](screenshots/thumb-3.png)  
![Thumb 4](screenshots/thumb-4.png) ![Thumb 5](screenshots/thumb-5.png) ![Thumb 6](screenshots/thumb-6.png)

</details>

## System Requirements

- CachyOS or any Arch Linux distribution
- Python 3.11 or newer
- PyQt6 ≥ 6.7
- sudo privileges for package managers

## Installation

```bash
git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
cd sc-cachyos-multi-updater
python -m venv venv
source venv/bin/activate
pip install -r cachyos-multi-updater/requirements-gui.txt
```

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
   cd sc-cachyos-multi-updater
   ```

2. **Run setup (recommended for first-time installation):**
   ```bash
   cd cachyos-multi-updater
   ./setup.sh
   ```
   This will guide you through configuration and create a desktop shortcut.

3. **Start updating:**
   ```bash
   ./cachyos-update-gui
   ```
   Or use the desktop shortcut created during setup.

## Configuration

The tool can be customized using `cachyos-multi-updater/config.conf`. Copy from `config.conf.example` and edit as needed.

### Environment Variables

- `SCRIPT_DIR` - Path to script directory (if GUI can't find update-all.sh)
- `GUI_LANGUAGE` - Override language detection (`de`, `en`, or `auto`)
- `GUI_THEME` - Override theme detection (`light`, `dark`, or `auto`)

### Configuration File Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `ENABLE_SYSTEM_UPDATE` | `true`/`false` | `true` | Enable system package updates |
| `ENABLE_AUR_UPDATE` | `true`/`false` | `true` | Enable AUR package updates |
| `ENABLE_CURSOR_UPDATE` | `true`/`false` | `true` | Enable Cursor editor updates |
| `ENABLE_FLATPAK_UPDATE` | `true`/`false` | `true` | Enable Flatpak application updates |
| `ENABLE_ADGUARD_UPDATE` | `true`/`false` | `true` | Enable AdGuard Home updates |
| `ENABLE_NOTIFICATIONS` | `true`/`false` | `true` | Show desktop notifications |
| `ENABLE_COLORS` | `true`/`false` | `true` | Colored terminal output |
| `DRY_RUN` | `true`/`false` | `false` | Always run in preview mode |
| `MAX_LOG_FILES` | Number | `10` | Number of log files to keep |
| `DOWNLOAD_RETRIES` | Number | `3` | Retry failed downloads N times |
| `GUI_LANGUAGE` | `auto`/`de`/`en` | `auto` | GUI language |
| `GUI_THEME` | `auto`/`light`/`dark` | `auto` | GUI theme |

### Example Configuration

```ini
# Enable/disable update components
ENABLE_SYSTEM_UPDATE=true
ENABLE_AUR_UPDATE=true
ENABLE_CURSOR_UPDATE=true
ENABLE_FLATPAK_UPDATE=true
ENABLE_ADGUARD_UPDATE=false

# Logging
MAX_LOG_FILES=10

# Notifications
ENABLE_NOTIFICATIONS=true

# Safety
DRY_RUN=false

# Appearance
ENABLE_COLORS=true
GUI_THEME=auto
GUI_LANGUAGE=auto

# Downloads
DOWNLOAD_RETRIES=3
```

## Usage

### GUI Version (Recommended)

**Start GUI:**
```bash
./cachyos-update-gui
```

Or use the desktop shortcut created during setup.

**GUI Features:**
- Component selection checkboxes
- Real-time colored output
- Progress bar (0-100%)
- Settings dialog with 6 tabs
- Log viewer
- Secure password management
- Toast notifications

### Command Line Version

**Run update script directly:**
```bash
cd cachyos-multi-updater
./update-all.sh
```

**Command-line options:**

| Option | Description |
|--------|-------------|
| `./update-all.sh` | Standard update (all components) |
| `--only-system` | Only system packages |
| `--only-aur` | Only AUR packages |
| `--only-cursor` | Only Cursor editor |
| `--only-flatpak` | Only Flatpak applications |
| `--only-adguard` | Only AdGuard Home |
| `--dry-run` | Preview without changes |
| `--interactive` or `-i` | Choose what to update |
| `--stats` | Show update statistics |
| `--version` or `-v` | Show version |
| `--help` or `-h` | Show help |

**Examples:**

```bash
# Preview what would be updated
./update-all.sh --dry-run

# Only update system packages
./update-all.sh --only-system

# Interactive mode
./update-all.sh --interactive

# Show statistics
./update-all.sh --stats
```

## Troubleshooting

### Common Problems

#### Script says "Update already running"

**Solution:** Delete the lock file:
```bash
rm cachyos-multi-updater/.update-all.lock
```

#### "Permission denied" when running script

**Solution:** Make it executable:
```bash
chmod +x cachyos-update-gui
chmod +x cachyos-multi-updater/update-all.sh
chmod +x cachyos-multi-updater/setup.sh
```

#### GUI won't start

**Check:**
1. PyQt6 installed? `python3 -c "from PyQt6.QtWidgets import QApplication"`
2. Python version 3.11+? `python3 --version`
3. Dependencies installed? `pip3 install -r cachyos-multi-updater/requirements-gui.txt`

**Solution:**
```bash
# Install PyQt6
pip3 install PyQt6

# Or install all dependencies
pip3 install -r cachyos-multi-updater/requirements-gui.txt
```

#### GUI shows "Script not found"

**Solution:** The GUI needs to find `update-all.sh`. Make sure:
1. You're running from the project root: `./cachyos-update-gui`
2. Or set environment variable: `export SCRIPT_DIR=/path/to/cachyos-multi-updater`
3. Check that `cachyos-multi-updater/update-all.sh` exists

### Getting Help

1. **Check logs first** - Most problems are logged in `cachyos-multi-updater/logs/`
2. **Try dry-run mode** - See what would happen: `./cachyos-multi-updater/update-all.sh --dry-run`
3. **Check troubleshooting section** - Your problem might be listed above
4. **Create GitHub issue** - Include log excerpts and describe what you tried

## Contributing

Improvements and bug reports are welcome! Please create an issue or pull request on [GitHub](https://github.com/benjarogit/sc-cachyos-multi-updater).

### Development Setup

```bash
git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
cd sc-cachyos-multi-updater
python -m venv venv
source venv/bin/activate
pip install -r cachyos-multi-updater/requirements-gui.txt
pip install pytest pytest-cov pytest-qt
```

### Running Tests

```bash
cd cachyos-multi-updater
pytest gui/tests/ -v --cov=gui/core --cov=gui/utils --cov=gui/dialogs --cov=gui/widgets
```

## License

This project is open source. You can freely use, modify, and distribute it under the terms of the MIT License.

## Links

- **GitHub Repository:** https://github.com/benjarogit/sc-cachyos-multi-updater
- **Issues:** https://github.com/benjarogit/sc-cachyos-multi-updater/issues
- **Releases:** https://github.com/benjarogit/sc-cachyos-multi-updater/releases

---

**Good luck with your updates! 🎉**
