# CachyOS Multi-Updater

> **Language / Sprache:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

A simple one-click update tool for CachyOS that automatically updates system packages, AUR packages, Cursor editor, Flatpak applications, and AdGuard Home.

---

## 🚀 Quick Start

### Installation (3 steps)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
   cd sc-cachyos-multi-updater
   ```

2. **Run setup (recommended for first-time installation):**
   ```bash
   ./cachyos-update
   ```
   Select option `1` to run setup, which will guide you through configuration and create a desktop shortcut.

3. **Start updating:**
   ```bash
   ./cachyos-update
   ```
   Select option `2` to start updates.

### Start Commands

**Console version (with menu):**
```bash
./cachyos-update
```

**GUI version:**
```bash
./cachyos-update-gui
```

### Basic Configuration

Create `cachyos-multi-updater/config.conf` from the example:
```bash
cp cachyos-multi-updater/config.conf.example cachyos-multi-updater/config.conf
```

Edit to enable/disable components:
```ini
ENABLE_SYSTEM_UPDATE=true
ENABLE_AUR_UPDATE=true
ENABLE_CURSOR_UPDATE=true
ENABLE_FLATPAK_UPDATE=true
ENABLE_ADGUARD_UPDATE=true
```

---

## 🤔 What is this?

**CachyOS Multi-Updater** is a script that helps you keep your CachyOS Linux system up-to-date. Instead of manually updating different parts of your system one by one, this script does it all automatically in one go.

### What is CachyOS?

CachyOS is a Linux operating system based on Arch Linux. It's designed to be fast and optimized for performance. Like any operating system, it needs regular updates to get security fixes, new features, and bug fixes.

### Why do I need this?

Normally, updating a Linux system involves running multiple commands:
- Updating system packages
- Updating AUR packages (community-made software)
- Updating applications like Cursor editor
- Updating services like AdGuard Home

This script does all of that automatically, saving you time and ensuring everything stays updated.

---

## ✨ Features

- ✅ **System Updates** - Updates CachyOS packages via pacman
- ✅ **AUR Updates** - Updates AUR packages via yay/paru
- ✅ **Cursor Editor** - Automatic download and update (version check before download)
- ✅ **Flatpak Applications** - Updates all Flatpak apps and runtimes
- ✅ **AdGuard Home** - Automatic update with configuration backup
- ✅ **Automatic Cleanup** - Removes old packages, caches, and temporary files
- ✅ **GUI Version** - Modern Qt-based graphical interface with real-time progress, secure password management, log viewer, and comprehensive settings dialog
- ✅ **Interactive Mode** - Choose what to update before running
- ✅ **Dry-Run Mode** - Preview changes without making them
- ✅ **Statistics** - Track update history and success rates
- ✅ **Logging** - Detailed logs for troubleshooting
- ✅ **Notifications** - Desktop notifications when updates complete

---

## 📋 Requirements

### Required:
- **CachyOS or Arch Linux**
- **sudo privileges**
- **Internet connection**

### Optional:
- **AUR Helper** (yay or paru) - for AUR package updates
- **Cursor Editor** - for Cursor updates
- **AdGuard Home** - for AdGuard updates (must be in `~/AdGuardHome`)
- **PyQt6** - for GUI version (`pip3 install PyQt6`)

---

## 🔧 Installation Guide

### Step 1: Download

**Option A: Using Git (recommended)**
```bash
git clone https://github.com/SunnyCueq/cachyos-multi-updater.git
cd cachyos-multi-updater
```

**Option B: Download as ZIP**
1. Go to https://github.com/benjarogit/sc-cachyos-multi-updater
2. Click "Code" → "Download ZIP"
3. Extract and navigate to the folder

### Step 2: Run Setup

The easiest way to get started:

```bash
./cachyos-update
```

Select option `1` to run the setup script, which will:
- Guide you through configuration
- Create a desktop shortcut (optional)
- Start the update script automatically

**Alternative: Manual setup**
```bash
cd cachyos-multi-updater
chmod +x update-all.sh
./update-all.sh --help  # Test that it works
```

### Step 3: Configure (optional)

Create configuration file:
```bash
cp cachyos-multi-updater/config.conf.example cachyos-multi-updater/config.conf
nano cachyos-multi-updater/config.conf
```

See [Configuration](#-configuration) section below for details.

---

## 💻 How to use it

### Console Version

**Start with menu:**
```bash
./cachyos-update
```

This shows a menu with options:
1. Setup durchführen (First-time setup)
2. Updates starten (Start updates)
3. Beenden (Exit)

**Direct script execution:**
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

### GUI Version

**Start GUI:**
```bash
./cachyos-update-gui
```

The GUI provides a modern, user-friendly interface for managing system updates without using the command line.

#### GUI Features

**Main Window:**
- **Component Selection** - Checkboxes to enable/disable each update type (System, AUR, Cursor, AdGuard, Flatpak)
- **Real-time Output** - Colored console output showing update progress:
  - 🟢 Green: Success messages
  - 🔴 Red: Error messages
  - 🟠 Orange: Warning messages
  - ⚫ Black: Normal output
- **Progress Bar** - Visual progress indicator (0-100%)
- **Status Display** - Current status message and update information
- **Version Check** - Automatic check for script updates (shows if newer version available)
- **Theme Support** - Light and dark themes (follows system theme)

**Buttons:**
- **Check for Updates** - Runs update script in dry-run mode (preview only, no changes)
- **Start Updates** - Starts the actual update process
- **Stop** - Stops a running update (if possible)
- **Settings** - Opens comprehensive settings dialog
- **View Logs** - Opens log viewer to browse update logs

**Settings Dialog (6 Tabs):**

1. **Update Components** - Enable/disable each update component
2. **General Settings** - Log files, retries, notifications, colors, dry-run mode
3. **Logs** - View and browse log files directly in the GUI
4. **System** - Script paths, directories, language settings
5. **Advanced Settings** - GitHub repository, paths, directories, GUI language
6. **Info** - Version information, links to GitHub, changelog

**Additional Features:**
- **Secure Password Management** - Encrypted sudo password storage (system keyring or Fernet encryption)
- **Desktop Shortcut Creation** - Create desktop shortcuts directly from GUI
- **Update Statistics** - View update history and success rates
- **Log Viewer** - Browse and view log files with proper formatting
- **Toast Notifications** - Desktop notifications when updates complete
- **Syntax Highlighting** - Colored output in console area for better readability
- **Animations** - Smooth UI animations and transitions
- **Internationalization** - Multi-language support (German/English, auto-detected)

**Requirements:**
- PyQt6 must be installed: `pip3 install PyQt6`
- Or install all dependencies: `pip3 install -r cachyos-multi-updater/requirements-gui.txt`

**GUI Installation:**
```bash
# Install PyQt6
pip3 install PyQt6

# Or install all GUI dependencies
pip3 install -r cachyos-multi-updater/requirements-gui.txt

# Optional: Install for secure password storage
pip3 install keyring cryptography
```

**GUI Usage:**
1. Start the GUI: `./cachyos-update-gui`
2. Select which components to update (checkboxes)
3. Click "Check for Updates" to preview changes (dry-run)
4. Click "Start Updates" to begin the update process
5. Monitor progress in real-time
6. View logs if needed
7. Configure settings via the Settings button

**GUI Advantages:**
- ✅ No command-line knowledge required
- ✅ Visual feedback and progress indication
- ✅ Easy configuration through settings dialog
- ✅ Secure password management
- ✅ Real-time update monitoring
- ✅ Log viewing without terminal
- ✅ Desktop notifications
- ✅ Modern, intuitive interface

---

## ⚙️ Configuration

The script can be customized using `cachyos-multi-updater/config.conf`. Copy from `config.conf.example` and edit as needed.

### Configuration Options

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
| `ENABLE_AUTO_UPDATE` | `true`/`false` | `false` | Enable automatic script updates |

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

# Downloads
DOWNLOAD_RETRIES=3
```

### Configuration Priority

1. **Command-line options** (highest priority)
2. **Configuration file** (`config.conf`)
3. **Default values** (lowest priority)

---

## 🐛 Troubleshooting

### Common Problems

#### Script says "Update läuft bereits!" (Update already running)

**Solution:** Delete the lock file:
```bash
rm cachyos-multi-updater/.update-all.lock
```

**Why:** The script might have crashed or been interrupted, leaving the lock file behind.

#### "Permission denied" when running script

**Solution:** Make it executable:
```bash
chmod +x cachyos-update
chmod +x cachyos-update-gui
chmod +x cachyos-multi-updater/update-all.sh
```

#### "Command not found" for yay/paru

**Solution:** Install an AUR helper or disable AUR updates:
```bash
# Install yay
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si

# Or disable in config.conf
ENABLE_AUR_UPDATE=false
```

#### Cursor is not being updated

**Check:**
1. Cursor installed? `which cursor`
2. Internet connection? `ping api2.cursor.sh`
3. Check logs: `grep -i cursor cachyos-multi-updater/logs/update-*.log`
4. Disable if not needed: `ENABLE_CURSOR_UPDATE=false`

#### AdGuard Home is not being updated

**Check:**
1. Installed in `~/AdGuardHome`? `ls -l ~/AdGuardHome/AdGuardHome`
2. Check logs: `grep -i adguard cachyos-multi-updater/logs/update-*.log`
3. Disable if not needed: `ENABLE_ADGUARD_UPDATE=false`

#### Script runs but nothing happens

**Possible causes:**
1. Everything is already up-to-date (normal!)
2. Dry-run mode enabled (`DRY_RUN=true` in config)
3. All updates disabled in config
4. Check logs: `cat cachyos-multi-updater/logs/$(ls -t cachyos-multi-updater/logs/ | head -1)`

#### GUI won't start

**Check:**
1. PyQt6 installed? `python3 -c "from PyQt6.QtWidgets import QApplication"`
2. Python version 3.8+? `python3 --version`
3. Dependencies installed? `pip3 install -r cachyos-multi-updater/requirements-gui.txt`
4. Script directory correct? Check that `cachyos-multi-updater/update-all.sh` exists

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

#### GUI password dialog not working

**Check:**
1. Keyring installed? `pip3 install keyring cryptography`
2. System keyring available? (usually automatic)
3. Try entering password manually each time (disable password saving)

**Solution:**
```bash
# Install password storage dependencies
pip3 install keyring cryptography
```

### Getting Help

1. **Check logs first** - Most problems are logged in `cachyos-multi-updater/logs/`
2. **Try dry-run mode** - See what would happen: `./cachyos-multi-updater/update-all.sh --dry-run`
3. **Check troubleshooting section** - Your problem might be listed above
4. **Create GitHub issue** - Include log excerpts and describe what you tried

---

## 📚 Further Information

### Logs

Logs are stored in `cachyos-multi-updater/logs/` with names like `update-20241215-143022.log`.

**View logs:**
```bash
# List all logs
ls -lh cachyos-multi-updater/logs/

# View most recent log
cat cachyos-multi-updater/logs/$(ls -t cachyos-multi-updater/logs/ | head -1)

# Search for errors
grep -i error cachyos-multi-updater/logs/update-*.log
```

### Statistics

View update statistics:
```bash
./cachyos-multi-updater/update-all.sh --stats
```

Shows:
- Total number of updates
- Success vs. failed updates
- Success rate percentage
- Average update duration
- Last update timestamp

### Desktop Shortcut

The setup script can create a desktop shortcut. Or create manually:

```bash
cd cachyos-multi-updater
./create-desktop-shortcut.sh
```

### Update the Script

If you cloned with Git:
```bash
cd cachyos-multi-updater
git pull
```

---

## ❓ FAQ

### Q: How often should I run this script?

**A:** It depends on your preference:
- Daily (for security updates)
- Weekly (balanced approach)
- Before important work sessions
- When notified about updates

### Q: Is it safe to run automatically (via cron)?

**A:** Yes, but with caution:
- The script has error handling
- Requires sudo access (configure properly)
- Test manually first
- Consider using `--dry-run` in cron

### Q: Can I use this on regular Arch Linux?

**A:** Yes! While designed for CachyOS, it works on Arch Linux too.

### Q: Does the script automatically close and restart Cursor?

**A:** No, the script does NOT automatically close or restart Cursor. It only downloads and installs the update. You can manually restart Cursor if needed.

### Q: Will this script break my system?

**A:** The script is designed to be safe:
- Uses standard package managers
- Has error handling
- Backs up AdGuard Home configuration
- Logs everything

However, any system update carries some risk. Use `--dry-run` first if you're unsure!

### Q: Can I customize what gets updated?

**A:** Yes! Multiple ways:
1. **Configuration file** (`config.conf`) - Enable/disable components
2. **Command-line flags** - `--only-system`, `--only-aur`, etc.
3. **Combine both** - Use config for defaults, flags for one-time changes

---

## 📅 Version History

For the complete version history and changelog, please see the [GitHub Releases](https://github.com/SunnyCueq/cachyos-multi-updater/releases).

---

## 📄 License

This project is open source. You can freely use, modify, and distribute it under the terms of the MIT License.

## 🤝 Contributing

Improvements and bug reports are welcome! Please create an issue or pull request on [GitHub](https://github.com/benjarogit/sc-cachyos-multi-updater).

## 📧 Support

For questions or problems:
1. Check the log files in `cachyos-multi-updater/logs/`
2. Check the [Troubleshooting](#-troubleshooting) section above
3. Create an issue on [GitHub](https://github.com/benjarogit/sc-cachyos-multi-updater)

## 🔗 Links

- **GitHub Repository:** https://github.com/SunnyCueq/cachyos-multi-updater
- **Issues:** https://github.com/SunnyCueq/cachyos-multi-updater/issues

---

**Good luck with your updates! 🎉**
