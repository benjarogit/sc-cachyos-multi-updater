# CachyOS Multi-Updater

> **Language / Sprache:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

A simple one-click update tool for CachyOS that automatically updates system packages, AUR packages, Cursor editor, Flatpak applications, and AdGuard Home.

---

## 📖 Table of Contents

1. [What is this?](#-what-is-this)
2. [What does this script do?](#-what-does-this-script-do)
3. [What you need to know first](#-what-you-need-to-know-first)
4. [Requirements](#-requirements)
5. [Installation Guide](#-installation-guide)
6. [How to use it](#-how-to-use-it)
7. [Configuration explained in detail](#-configuration-explained-in-detail)
8. [Understanding logs](#-understanding-logs)
9. [Troubleshooting](#-troubleshooting)
10. [Version History](#-version-history)

---

## 🤔 What is this?

**CachyOS Multi-Updater** is a script (a small program) that helps you keep your CachyOS Linux system up-to-date. Instead of manually updating different parts of your system one by one, this script does it all automatically in one go.

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

## 🚀 What does this script do?

This script automatically updates five different things on your system, then cleans up:

### 1. ✅ CachyOS System Updates (via pacman)

**What is pacman?** Pacman is the package manager for Arch Linux and CachyOS. It's like an app store that manages all the software on your system.

**What gets updated?** All official CachyOS packages including:
- System libraries
- Applications from the official repositories
- Security patches
- Bug fixes

**How it works:** The script runs `sudo pacman -Syu` which:
- `-S` = Sync (update packages)
- `-y` = Refresh package database
- `-u` = Upgrade all packages
- `--noconfirm` = Don't ask for confirmation (automatic)

### 2. ✅ AUR Packages (via yay or paru)

**What is AUR?** AUR stands for "Arch User Repository". It's a community-driven repository where users share packages that aren't in the official repositories. Think of it as a community app store.

**What is yay/paru?** These are "AUR helpers" - tools that make it easier to install and update AUR packages. You need one of them installed for this feature to work.

**What gets updated?** All packages you've installed from AUR, such as:
- Community-made applications
- Custom builds of software
- Packages not available in official repos

**How it works:** The script automatically detects if you have `yay` or `paru` installed and uses it to update all AUR packages.

### 3. ✅ Cursor Editor (automatic download and update)

**What is Cursor?** Cursor is a code editor (like VS Code) with AI features. If you have it installed, this script will keep it updated.

**What happens during update?**
1. The script checks your current Cursor version (from package.json)
2. Checks the latest available version via HTTP HEAD request (no download needed!)
3. Extracts the version from the Location header (`cursor_2.0.69_amd64.deb` → `2.0.69`)
4. Compares versions - if already up-to-date, skips download and installation completely
5. If update needed, downloads and installs the new version
6. The .deb file is automatically deleted after installation
7. You can manually restart Cursor if it was running

**Note:** The version check uses an HTTP HEAD request (only a few KB) instead of downloading the entire .deb file (132MB). This makes the check much faster and saves bandwidth. If the HTTP HEAD request fails, the script falls back to the old method (download + extraction).

**Note:** The script does NOT automatically close or restart Cursor. If Cursor is running, you may want to close it manually before running the update for a clean installation.

### 4. ✅ AdGuard Home (automatic download and update)

**What is AdGuard Home?** AdGuard Home is a network-wide ad blocker and DNS server. It blocks ads and trackers for all devices on your network.

**What happens during update?**
1. Checks current version
2. Checks latest version via GitHub Releases API
3. If already up-to-date, skips download
4. If update needed:
   - Stops the AdGuard Home service
   - Downloads the latest version from official AdGuard servers
   - Backs up your configuration
   - Installs the new version
   - Restarts the service

**Important:** AdGuard Home must be installed in `~/AdGuardHome` (in your home directory).

### 6. ✅ Automatic Cleanup (after updates)

**What is cleanup?** After all updates are complete, the script automatically cleans up temporary files, old packages, and unused dependencies to keep your system clean and save disk space.

**What gets cleaned up?**
- **Pacman cache:** Removes old and uninstalled packages (keeps last 3 versions)
- **Orphan packages:** Removes packages that are no longer needed
- **Flatpak cache:** Removes unused Flatpak runtimes and applications
- **Cursor downloads:** Removes leftover `.deb` files from script directory
- **AdGuard temporary files:** Cleans up temporary directories in `/tmp`
- **Cursor temporary files:** Cleans up extraction directories in `/tmp`

**How it works:** The cleanup runs automatically after all updates complete. No user interaction required.

---

## 📚 What you need to know first

### Basic Linux concepts

**Terminal/Command Line:** This is a text-based interface where you type commands. On CachyOS, you can open it by pressing `Ctrl+Alt+T` or searching for "Terminal" in your application menu.

**sudo:** This stands for "Super User DO". It allows you to run commands with administrator privileges. You'll need to enter your password when the script asks for it.

**Script:** A script is a file containing commands that the computer can execute. This project is a Bash script (written in the Bash programming language).

**Repository:** A collection of software packages. Think of it as a library of programs you can install.

### File paths explained

When you see paths like `/home/username/`, here's what they mean:
- `/` = The root of your file system (like C:\ on Windows)
- `/home/username/` = Your home directory (like Documents folder)
- `~` = Shortcut for your home directory
- `./` = Current directory (where you are now)

---

## 📋 Requirements

Before you can use this script, you need:

### Required (must have):

1. **CachyOS or Arch Linux** - This script is designed for these systems
   - How to check: Open terminal and type `cat /etc/os-release`
   - You should see "CachyOS" or "Arch Linux"

2. **sudo privileges** - You need to be able to run commands as administrator
   - How to check: Type `sudo -v` in terminal
   - If it asks for your password, you have sudo access

3. **Internet connection** - The script needs internet to download updates

### Optional (nice to have):

4. **AUR Helper (yay or paru)** - Only needed if you want to update AUR packages
   - How to check: Type `which yay` or `which paru` in terminal
   - If it shows a path, you have it installed
   - If not, you can install it (see troubleshooting section)

5. **Cursor Editor** - Only needed if you want to update Cursor
   - How to check: Type `which cursor` in terminal
   - If it shows a path, Cursor is installed

6. **AdGuard Home** - Only needed if you want to update AdGuard Home
   - How to check: Look for `~/AdGuardHome/AdGuardHome` file
   - Type `ls ~/AdGuardHome/AdGuardHome` in terminal

---

## 🔧 Installation Guide

This is a step-by-step guide for complete beginners. Follow each step carefully.

### Step 1: Download the script

You have two options:

#### Option A: Using Git (recommended)

**What is Git?** Git is a version control system. It's like a way to download and keep software updated.

1. Open a terminal (press `Ctrl+Alt+T` or search for "Terminal")
2. Navigate to where you want to install the script (for example, your home directory):
   ```bash
   cd ~
   ```
3. Clone the repository (download the files):
   ```bash
   git clone https://github.com/SunnyCueq/cachyos-multi-updater.git
   ```
   This creates a folder called `cachyos-multi-updater` with all the files.

4. Enter the folder:
   ```bash
   cd cachyos-multi-updater
   ```

#### Option B: Download as ZIP

1. Go to https://github.com/SunnyCueq/cachyos-multi-updater
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to a location (like `~/Downloads/`)
5. Open terminal and navigate to the extracted folder:
   ```bash
   cd ~/Downloads/cachyos-multi-updater-main
   ```

### Step 2: Run the setup script (recommended for first-time installation)

**The easiest way to get started!** The setup script will guide you through the configuration.

1. Make the setup script executable:
   ```bash
   chmod +x setup.sh
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

3. The setup script will:
   - Ask you to choose an update mode (--dry-run, --interactive, or automatic)
   - Ask if you want to create a desktop shortcut
   - Create the desktop shortcut with your chosen options
   - Start the update script automatically

**Alternative: Manual setup**

If you prefer to set up manually:

1. Make the script executable:
   ```bash
   chmod +x update-all.sh
   ```

2. Verify it worked:
   ```bash
   ls -l update-all.sh
   ```
   You should see something like `-rwxr-xr-x` - the `x` means it's executable.

**What if I get "Permission denied"?**
- Make sure you're in the correct directory
- Try: `chmod 755 update-all.sh`
- If still not working, you might need to use `sudo` (but this is unusual)

### Step 3: Test the script (optional but recommended)

Before using it for real, test that it works:

1. Run the help command:
   ```bash
   ./update-all.sh --help
   ```

2. You should see a help message. If you see an error, check the troubleshooting section.

3. Try dry-run mode (safe, doesn't make changes):
   ```bash
   ./update-all.sh --dry-run
   ```

### Step 4: Install desktop shortcut (optional)

**What is a desktop shortcut?** It's an icon in your application menu (and optionally on your desktop) that you can click to run the script without opening terminal.

#### Option A: Application Menu Icon (Recommended)

This creates an icon in your application menu:

1. Copy the desktop file to your applications folder:
   ```bash
   cp update-all.desktop ~/.local/share/applications/
   ```

2. Edit the desktop file to set the correct path:
   ```bash
   nano ~/.local/share/applications/update-all.desktop
   ```

3. Find the line that says:
   ```ini
   Exec=bash -c "cd '%k' && ./update-all.sh"
   ```

4. Replace it with the actual path to your script. For example, if you installed it in your home directory:
   ```ini
   Exec=bash -c "cd '/home/yourusername/cachyos-multi-updater' && ./update-all.sh"
   ```
   **Important:** Replace `yourusername` with your actual username!

5. Save and exit:
   - Press `Ctrl+O` to save
   - Press `Enter` to confirm
   - Press `Ctrl+X` to exit

6. Make the desktop file executable:
   ```bash
   chmod +x ~/.local/share/applications/update-all.desktop
   ```

7. Test it:
   - Open your application menu (usually by pressing the Super/Windows key)
   - Search for "Update All"
   - Click on it
   - A terminal should open and the script should start

#### Option B: Desktop Icon (Visible on Desktop)

To show the icon directly on your desktop:

1. Follow steps 1-6 from Option A above

2. Copy the desktop file to your desktop:
   ```bash
   cp ~/.local/share/applications/update-all.desktop ~/Desktop/
   ```
   Or if your desktop is in a different location:
   ```bash
   cp ~/.local/share/applications/update-all.desktop ~/Schreibtisch/  # German
   cp ~/.local/share/applications/update-all.desktop ~/Desktop/        # English
   ```

3. Make it executable:
   ```bash
   chmod +x ~/Desktop/update-all.desktop
   ```

4. The icon should now appear on your desktop. You can double-click it to run the script.

**Note:** Some desktop environments may require you to enable "Allow launching applications" in desktop settings for icons to work.

#### Changing the Icon

The desktop file uses a system icon by default (`system-software-update`). To change it:

1. Open the desktop file:
   ```bash
   nano ~/.local/share/applications/update-all.desktop
   ```

2. Find the line:
   ```ini
   Icon=system-software-update
   ```

3. Replace it with one of these options:

   **Option 1: Use a system icon name**
   ```ini
   Icon=system-software-update
   Icon=system-update
   Icon=software-update-available
   Icon=update-manager
   ```
   (Common icon names on Linux systems)

   **Option 2: Use a custom icon file**
   ```ini
   Icon=/path/to/your/icon.png
   ```
   For example:
   ```ini
   Icon=/home/yourusername/Pictures/my-update-icon.png
   ```

   **Option 3: Use an icon from the script directory**
   ```ini
   Icon=/home/yourusername/cachyos-multi-updater/icon.png
   ```

4. Save and exit (Ctrl+O, Enter, Ctrl+X)

5. Refresh the desktop (or log out and back in) to see the new icon

**How to find your username?**
- Type `whoami` in terminal
- Or type `echo $USER`

**How to find the full path to the script?**
- Navigate to the script folder in terminal
- Type `pwd` (print working directory)
- This shows the full path

### Step 5: Configure (optional but recommended)

**What is configuration?** Configuration lets you customize how the script behaves. You can enable/disable certain updates, change settings, etc.

See the [Configuration explained in detail](#-configuration-explained-in-detail) section below for complete instructions.

---

## 💻 How to use it

### Method 1: Using the desktop shortcut

This is the easiest method if you set up the desktop shortcut:

1. Open your application menu (usually by pressing the Super/Windows key)
2. Type "Update All" in the search box
3. Click on "Update All"
4. A terminal window will open
5. The script will start automatically
6. When it asks for your password, type it and press Enter
   - **Note:** When typing your password, you won't see any characters (not even dots). This is normal for security.
7. Wait for the updates to complete
8. The terminal will show you what's being updated

### Method 2: Using the command line

This method requires you to open terminal manually:

1. Open terminal (press `Ctrl+Alt+T` or search for "Terminal")
2. Navigate to the script folder:
   ```bash
   cd ~/cachyos-multi-updater
   ```
   (Adjust the path if you installed it elsewhere)

3. Run the script:
   ```bash
   ./update-all.sh
   ```

4. Enter your password when prompted

5. Wait for updates to complete

### Command line options explained

The script supports several options that change its behavior:

#### Standard update (all components)

```bash
./update-all.sh
```

This updates everything: system packages, AUR packages, Cursor, Flatpak applications, and AdGuard Home.

#### Selective updates

Sometimes you only want to update specific things:

**Only system updates:**
```bash
./update-all.sh --only-system
```
This only updates CachyOS system packages. Useful if you only want official packages updated.

**Only AUR packages:**
```bash
./update-all.sh --only-aur
```
This only updates packages from AUR. Useful if you only want community packages updated.

**Only Cursor:**
```bash
./update-all.sh --only-cursor
```
This only updates Cursor editor. Useful if you just want to update Cursor without touching anything else.

**Only AdGuard Home:**
```bash
./update-all.sh --only-adguard
```
This only updates AdGuard Home. Useful if you just want to update AdGuard without other updates.

**Only Flatpak:**
```bash
./update-all.sh --only-flatpak
```
This only updates Flatpak applications. Useful if you just want to update Flatpak apps without other updates.

**Why use selective updates?**
- Faster (only updates what you need)
- Safer (less chance of something breaking)
- More control (you decide what gets updated)

#### Dry-run mode (preview without changes)

```bash
./update-all.sh --dry-run
```

**What is dry-run?** Dry-run shows you what WOULD be updated without actually making any changes. It's like a preview.

**When to use it:**
- First time using the script (to see what it does)
- Before a big update (to see what will change)
- Testing (to make sure everything works)

**What you'll see:**
- A list of what would be updated
- Current versions
- What commands would be run
- But NO actual changes are made

#### Interactive mode (choose what to update)

```bash
./update-all.sh --interactive
```
or
```bash
./update-all.sh -i
```

**What is interactive mode?** Interactive mode lets you choose which components to update before the process starts.

**How it works:**
1. The script asks you for each component (System, AUR, Cursor, AdGuard)
2. You answer with 'j' (yes) or 'n' (no)
3. The script shows a summary of your selections
4. You confirm and the selected updates run

**Example:**
```
🎮 INTERAKTIVER MODUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welche Komponenten möchtest du aktualisieren?

  [1] System (pacman)?        (J/n): j
      ✅ System-Updates aktiviert
  [2] AUR (yay/paru)?         (J/n): n
      ⏭️  AUR-Updates übersprungen
  [3] Cursor Editor?          (J/n): j
      ✅ Cursor-Update aktiviert
  [4] AdGuard Home?           (J/n): n
      ⏭️  AdGuard Home-Update übersprungen
```

**When to use it:**
- You want more control without using command-line flags
- You're not sure what needs updating
- You want to skip certain updates this time

#### Show statistics

```bash
./update-all.sh --stats
```

**What are statistics?** The script tracks all your updates and shows useful statistics.

**What you'll see:**
- Total number of updates performed
- Success vs. failed updates
- Success rate percentage
- Average update duration
- Last update timestamp

**Example:**
```
📊 UPDATE-STATISTIKEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Gesamt-Updates:     47
   Erfolgreich:        45
   Fehlgeschlagen:     2
   Erfolgsrate:        95%
   Durchschn. Dauer:   6m 32s
   Letztes Update:     08.11.2025 14:30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**When to use it:**
- Check how often you update
- See if updates are getting slower
- Track your update success rate

#### Show version

```bash
./update-all.sh --version
```
or
```bash
./update-all.sh -v
```

This shows the current version of the script. Useful to know which version you're running.

#### Show help

```bash
./update-all.sh --help
```
or
```bash
./update-all.sh -h
```

This shows all available options and how to use them.

### Combining options

You can combine some options:

```bash
./update-all.sh --only-system --dry-run
```

This would show what system updates would be done, without actually doing them.

---

## ⚙️ Configuration explained in detail

The script can be customized using a configuration file. This is optional - the script works fine with default settings. But configuration gives you more control.

### What is a configuration file?

A configuration file (config file) is a text file that contains settings. The script reads this file and adjusts its behavior based on the settings.

### Creating the configuration file

1. Navigate to the script folder:
   ```bash
   cd ~/cachyos-multi-updater
   ```

2. Copy the example configuration file:
   ```bash
   cp config.conf.example config.conf
   ```

3. Open it in a text editor:
   ```bash
   nano config.conf
   ```
   (You can use any text editor: `nano`, `vim`, `gedit`, `kate`, etc.)

4. Edit the values as needed (see explanations below)

5. Save and exit:
   - In nano: `Ctrl+O` to save, `Enter` to confirm, `Ctrl+X` to exit
   - In other editors: Use their save function

### Configuration file format

The configuration file uses a simple format:
- Each setting is on its own line
- Format: `KEY=value`
- Lines starting with `#` are comments (ignored)
- Empty lines are ignored
- Case doesn't matter for `true`/`false` values

**Example:**
```ini
# This is a comment
ENABLE_SYSTEM_UPDATE=true
ENABLE_AUR_UPDATE=false
```

### All configuration options explained

#### 1. ENABLE_SYSTEM_UPDATE

```ini
ENABLE_SYSTEM_UPDATE=true
```

**What it does:** Controls whether CachyOS system updates are performed.

**Values:**
- `true` = System updates are enabled (default)
- `false` = System updates are disabled

**When to disable:**
- You only want to update AUR packages
- You're testing and don't want system changes
- You prefer to update system packages manually

**Example:**
```ini
ENABLE_SYSTEM_UPDATE=false
```
This disables system updates. Only AUR, Cursor, and AdGuard would be updated.

#### 2. ENABLE_AUR_UPDATE

```ini
ENABLE_AUR_UPDATE=true
```

**What it does:** Controls whether AUR package updates are performed.

**Values:**
- `true` = AUR updates are enabled (default)
- `false` = AUR updates are disabled

**When to disable:**
- You don't have yay/paru installed
- You prefer to update AUR packages manually
- You only want system updates

**Example:**
```ini
ENABLE_AUR_UPDATE=false
```
This disables AUR updates. Only system packages, Cursor, and AdGuard would be updated.

#### 3. ENABLE_CURSOR_UPDATE

```ini
ENABLE_CURSOR_UPDATE=true
```

**What it does:** Controls whether Cursor editor is updated.

**Values:**
- `true` = Cursor updates are enabled (default)
- `false` = Cursor updates are disabled

**When to disable:**
- You don't have Cursor installed
- You prefer to update Cursor manually
- You don't want Cursor to be closed during updates

**Example:**
```ini
ENABLE_CURSOR_UPDATE=false
```
This disables Cursor updates. Cursor won't be touched by the script.

#### 4. ENABLE_FLATPAK_UPDATE

```ini
ENABLE_FLATPAK_UPDATE=true
```

**What it does:** Controls whether Flatpak applications are updated.

**Values:**
- `true` = Flatpak updates are enabled (default)
- `false` = Flatpak updates are disabled

**When to disable:**
- You don't have Flatpak installed
- You don't use Flatpak applications
- You prefer to update Flatpak applications manually

**Example:**
```ini
ENABLE_FLATPAK_UPDATE=false
```
This disables Flatpak updates. Flatpak applications won't be updated by the script.

#### 5. ENABLE_ADGUARD_UPDATE

```ini
ENABLE_ADGUARD_UPDATE=true
```

**What it does:** Controls whether AdGuard Home is updated.

**Values:**
- `true` = AdGuard Home updates are enabled (default)
- `false` = AdGuard Home updates are disabled

**When to disable:**
- You don't have AdGuard Home installed
- You prefer to update AdGuard Home manually
- You don't want the service to be stopped during updates

**Example:**
```ini
ENABLE_ADGUARD_UPDATE=false
```
This disables AdGuard Home updates. AdGuard won't be touched by the script.

#### 6. ENABLE_NOTIFICATIONS

```ini
ENABLE_NOTIFICATIONS=true
```

**What it does:** Controls whether desktop notifications are shown when updates complete.

**Values:**
- `true` = Notifications are enabled (default)
- `false` = Notifications are disabled

**What are desktop notifications?** They're pop-up messages that appear in the corner of your screen. They show when updates are finished.

**When to disable:**
- You don't want pop-up notifications
- You're running the script automatically and don't need notifications
- Notifications don't work on your system

**Example:**
```ini
ENABLE_NOTIFICATIONS=false
```
This disables notifications. You'll still see output in the terminal, but no pop-up messages.

#### 6. DRY_RUN

```ini
DRY_RUN=false
```

**What it does:** If set to `true`, the script runs in preview mode by default (without making changes).

**Values:**
- `true` = Always run in dry-run mode (preview only)
- `false` = Normal operation, make actual changes (default)

**When to enable:**
- You want to always preview before updating
- You're testing the script
- You want an extra safety layer

**Note:** You can still override this with command-line options. For example:
- If `DRY_RUN=true` in config, but you run `./update-all.sh`, it will still be dry-run
- If `DRY_RUN=false` in config, but you run `./update-all.sh --dry-run`, it will be dry-run

**Example:**
```ini
DRY_RUN=true
```
This makes the script always run in preview mode. No changes will be made unless you explicitly override it.

#### 7. MAX_LOG_FILES

```ini
MAX_LOG_FILES=10
```

**What it does:** Controls how many log files are kept. Older log files are automatically deleted.

**Values:**
- Any number (default: 10)
- The script keeps the most recent N log files
- Older files are automatically deleted

**What are log files?** Every time you run the script, it creates a log file that records everything that happened. These files are stored in the `logs/` folder.

**Why limit them?** Log files can take up disk space. By limiting how many are kept, you prevent your disk from filling up.

**Example:**
```ini
MAX_LOG_FILES=5
```
This keeps only the 5 most recent log files. Older ones are deleted automatically.

```ini
MAX_LOG_FILES=20
```
This keeps the 20 most recent log files.

```ini
MAX_LOG_FILES=1
```
This keeps only the most recent log file (not recommended - you lose history).

#### 8. ENABLE_COLORS

```ini
ENABLE_COLORS=true
```

**What it does:** Controls whether colored output is used in the terminal.

**Values:**
- `true` = Colored output enabled (default)
- `false` = No colors (useful for logs/redirects)

**What are colors?** The script uses colors to make output more readable:
- Cyan for info messages
- Green for success messages
- Red for error messages
- Yellow for warnings

**When to disable:**
- You're redirecting output to a file
- Your terminal doesn't support colors
- You prefer plain text output

**Example:**
```ini
ENABLE_COLORS=false
```
This disables colored output. All messages will be plain text.

#### 9. DOWNLOAD_RETRIES

```ini
DOWNLOAD_RETRIES=3
```

**What it does:** Controls how many times the script retries a failed download.

**Values:**
- Any number (default: 3)
- The script will retry up to N times if a download fails
- Waits 2 seconds between retries

**Why retry?** Network issues can cause temporary download failures. Retrying gives the download another chance to succeed.

**Example:**
```ini
DOWNLOAD_RETRIES=5
```
This retries up to 5 times if a download fails.

```ini
DOWNLOAD_RETRIES=1
```
This only tries once (no retries).

#### 10. ENABLE_AUTO_UPDATE

```ini
ENABLE_AUTO_UPDATE=false
```

**What it does:** Enables automatic update of the script itself (with confirmation).

**Values:**
- `true` = Automatic update enabled (asks for confirmation)
- `false` = Only shows update notification (default)

**What happens when enabled?** If a new script version is available, the script will:
1. Show that a new version is available
2. Ask if you want to update now
3. If yes, automatically run `git pull` to update
4. If no, just show update instructions

**When to enable:**
- You want convenient script updates
- You trust the repository
- You want to stay up-to-date easily

**Example:**
```ini
ENABLE_AUTO_UPDATE=true
```
This enables automatic script updates with confirmation.

### Complete configuration example

Here's a complete example configuration file with comments:

```ini
# CachyOS Multi-Updater Configuration File
# Copy this file to config.conf and customize it

# Enable/disable update components
ENABLE_SYSTEM_UPDATE=true      # Update CachyOS system packages
ENABLE_AUR_UPDATE=true         # Update AUR packages
ENABLE_CURSOR_UPDATE=true      # Update Cursor editor
ENABLE_ADGUARD_UPDATE=false    # Don't update AdGuard Home

# Logging settings
MAX_LOG_FILES=10               # Keep 10 most recent log files

# Notifications
ENABLE_NOTIFICATIONS=true      # Show desktop notifications

# Safety settings
DRY_RUN=false                  # Make actual changes (not preview mode)

# Appearance
ENABLE_COLORS=true              # Colored terminal output

# Download settings
DOWNLOAD_RETRIES=3             # Retry failed downloads up to 3 times

# Script update
ENABLE_AUTO_UPDATE=false       # Enable automatic script updates (with confirmation)
```

### How configuration works

1. The script looks for `config.conf` in the same folder as the script
2. If found, it reads the settings
3. Settings override the default values
4. Command-line options override configuration file settings

**Priority order (highest to lowest):**
1. Command-line options (e.g., `--only-system`)
2. Configuration file settings
3. Default values

**Example:**
- Config file says: `ENABLE_SYSTEM_UPDATE=false`
- You run: `./update-all.sh --only-system`
- Result: System updates run anyway (command-line overrides config)

---

## 📝 Understanding logs

### What are logs?

Logs are text files that record everything the script does. They're like a diary of what happened during each update.

### Where are logs stored?

Logs are stored in the `logs/` folder, inside the script directory.

**Full path example:**
```
/home/yourusername/cachyos-multi-updater/logs/
```

### Log file naming

Each log file has a name like:
```
update-20241215-143022.log
```

**Breaking it down:**
- `update-` = Prefix
- `20241215` = Date (December 15, 2024)
- `143022` = Time (14:30:22 = 2:30:22 PM)
- `.log` = File extension

### What's in a log file?

A log file contains:
- Timestamp of each action
- What was updated
- Success/failure messages
- Error messages (if any)
- Version information
- System information

**Example log entry:**
```
[2024-12-15 14:30:22] [INFO] CachyOS Multi-Updater Version 2.1.0
[2024-12-15 14:30:22] [INFO] Update gestartet...
[2024-12-15 14:30:23] [INFO] Starte CachyOS-Update...
[2024-12-15 14:30:45] [SUCCESS] CachyOS-Update erfolgreich
```

### Viewing logs

#### List all log files

```bash
ls -lh logs/
```

This shows all log files with their sizes and dates.

#### View a specific log file

```bash
cat logs/update-20241215-143022.log
```

This shows the entire log file.

#### View the most recent log

```bash
cat logs/$(ls -t logs/ | head -1)
```

Or simply:
```bash
cat logs/update-*.log | tail -50
```

#### Watch log in real-time

If the script is running, you can watch the log being written:

```bash
tail -f logs/update-*.log
```

Press `Ctrl+C` to stop watching.

#### Search logs for errors

```bash
grep -i error logs/update-*.log
```

This finds all lines containing "error" (case-insensitive).

#### Search logs for specific text

```bash
grep "Cursor" logs/update-*.log
```

This finds all lines mentioning "Cursor".

### Automatic log cleanup

The script automatically deletes old log files to save disk space. By default, it keeps the 10 most recent logs.

**How it works:**
1. After each run, the script checks how many log files exist
2. If there are more than `MAX_LOG_FILES`, it deletes the oldest ones
3. Only the most recent N files are kept

**Configure cleanup:**
Set `MAX_LOG_FILES` in `config.conf` (see configuration section).

---

## 🐛 Troubleshooting

### General troubleshooting steps

1. **Check the logs first!** Most problems are logged. See the "Understanding logs" section above.

2. **Try dry-run mode** to see what would happen without making changes:
   ```bash
   ./update-all.sh --dry-run
   ```

3. **Check your internet connection** - Updates require internet.

4. **Make sure you have sudo access:**
   ```bash
   sudo -v
   ```
   If this fails, you don't have sudo access.

### Specific problems and solutions

#### Problem: Script says "Update läuft bereits!" (Update already running)

**What this means:** The script found a lock file, which means it thinks another update is already running.

**Solutions:**

1. **Check if update is actually running:**
   ```bash
   ps aux | grep update-all.sh
   ```
   If you see a process, wait for it to finish.

2. **If no process is running, delete the lock file:**
   ```bash
   rm ~/cachyos-multi-updater/.update-all.lock
   ```
   (Adjust path if your script is elsewhere)

3. **Why did this happen?** The script might have crashed or been interrupted, leaving the lock file behind.

#### Problem: "Permission denied" when running script

**What this means:** The script file doesn't have execute permissions.

**Solutions:**

1. **Make it executable:**
   ```bash
   chmod +x update-all.sh
   ```

2. **Verify it worked:**
   ```bash
   ls -l update-all.sh
   ```
   You should see `x` in the permissions (like `-rwxr-xr-x`).

#### Problem: "Command not found" for yay/paru

**What this means:** You don't have an AUR helper installed, or it's not in your PATH.

**Solutions:**

1. **Check if installed:**
   ```bash
   which yay
   which paru
   ```

2. **If not installed, install one:**

   **Install yay:**
   ```bash
   git clone https://aur.archlinux.org/yay.git
   cd yay
   makepkg -si
   ```

   **Install paru:**
   ```bash
   git clone https://aur.archlinux.org/paru.git
   cd paru
   makepkg -si
   ```

3. **Or disable AUR updates** in `config.conf`:
   ```ini
   ENABLE_AUR_UPDATE=false
   ```

#### Problem: Cursor is not being updated

**Possible causes and solutions:**

1. **Cursor not installed:**
   ```bash
   which cursor
   ```
   If this shows nothing, Cursor isn't installed or not in PATH.

2. **Check internet connection:**
   ```bash
   ping api2.cursor.sh
   ```

3. **Check log files** for specific error messages:
   ```bash
   grep -i cursor logs/update-*.log
   ```

4. **Permission issues:**
   - Make sure you can write to Cursor's installation directory
   - Check log files for permission errors

5. **Disable Cursor updates** if you don't use it:
   ```ini
   ENABLE_CURSOR_UPDATE=false
   ```

#### Problem: AdGuard Home is not being updated

**Possible causes and solutions:**

1. **AdGuard Home not in expected location:**
   ```bash
   ls -l ~/AdGuardHome/AdGuardHome
   ```
   If this fails, AdGuard Home isn't in the expected location.

2. **Check if service exists:**
   ```bash
   systemctl --user status AdGuardHome
   ```

3. **Check log files** for specific errors:
   ```bash
   grep -i adguard logs/update-*.log
   ```

4. **Disable AdGuard updates** if you don't use it:
   ```ini
   ENABLE_ADGUARD_UPDATE=false
   ```

#### Problem: Sudo password prompt keeps appearing

**What this means:** The script needs sudo access for system and AUR updates.

**Solutions:**

1. **Enter your password when prompted** - This is normal and required.

2. **Configure sudo to not require password** (advanced, not recommended for security):
   ```bash
   sudo visudo
   ```
   Add line:
   ```
   yourusername ALL=(ALL) NOPASSWD: /usr/bin/pacman
   ```
   (Replace `yourusername` with your actual username)

3. **Or disable updates that require sudo:**
   ```ini
   ENABLE_SYSTEM_UPDATE=false
   ENABLE_AUR_UPDATE=false
   ```

#### Problem: Script runs but nothing seems to happen

**Possible causes:**

1. **Everything is already up-to-date** - This is normal! The script only updates if there are updates available.

2. **Dry-run mode is enabled** - Check your `config.conf`:
   ```ini
   DRY_RUN=true
   ```
   Change to `false` to make actual changes.

3. **All updates are disabled** - Check your `config.conf` - all `ENABLE_*` options might be `false`.

4. **Check the logs** - They'll tell you what happened:
   ```bash
   cat logs/$(ls -t logs/ | head -1)
   ```

#### Problem: "No space left on device"

**What this means:** Your disk is full.

**Solutions:**

1. **Free up disk space:**
   ```bash
   df -h
   ```
   This shows disk usage.

2. **Clean package cache:**
   ```bash
   sudo pacman -Sc
   ```

3. **Delete old log files:**
   ```bash
   rm logs/update-*.log
   ```
   (Keep recent ones if you need them)

4. **Reduce MAX_LOG_FILES** in `config.conf`:
   ```ini
   MAX_LOG_FILES=5
   ```

### Getting help

If you can't solve a problem:

1. **Check the logs** - They contain detailed error messages
2. **Try dry-run mode** - See what would happen
3. **Check this troubleshooting section** - Your problem might be listed
4. **Create an issue on GitHub:**
   - Go to https://github.com/SunnyCueq/cachyos-multi-updater/issues
   - Click "New Issue"
   - Describe your problem
   - Include relevant log excerpts
   - Describe what you tried

---

## ❓ FAQ (Frequently Asked Questions)

### Q: How often should I run this script?

**A:** It depends on your preference. Many users run it:
- Daily (for security updates)
- Weekly (balanced approach)
- Before important work sessions
- When notified about updates

There's no "right" frequency - choose what works for you!

### Q: Is it safe to run automatically (via cron)?

**A:** Yes, but with caution:
- The script has error handling and won't break your system if one update fails
- However, it requires sudo access, so configure sudo properly
- Recommended: Test it manually first, then set up automation
- Consider using `--dry-run` in cron to preview changes

### Q: What happens if the script crashes or is interrupted?

**A:** The script is designed to handle interruptions:
- Lock file prevents multiple simultaneous runs
- If interrupted, you may need to manually delete `.update-all.lock`
- Logs will show what was completed before interruption
- System updates that started will complete (pacman handles this)
- AUR updates that started might need manual attention

### Q: Can I use this on regular Arch Linux?

**A:** Yes! While designed for CachyOS, it works on Arch Linux too. Just ensure:
- You have pacman installed (standard on Arch)
- AUR helpers work the same way
- Cursor and AdGuard Home updates work identically

### Q: Does the script automatically close and restart Cursor?

**A:** No, the script does NOT automatically close or restart Cursor. It only:
- Checks if Cursor is running (shows a warning if it is)
- Downloads and installs the update
- You can manually close/restart Cursor if needed

**Why?** Automatic closing/restarting can be disruptive. You have full control over when Cursor runs.

### Q: Will this script break my system?

**A:** The script is designed to be safe:
- It uses standard package managers (pacman, yay/paru)
- It has error handling to prevent cascading failures
- It backs up AdGuard Home configuration
- It logs everything for troubleshooting

However, any system update carries some risk. Use `--dry-run` first if you're unsure!

### Q: Can I customize what gets updated?

**A:** Yes! Multiple ways:
1. **Configuration file** (`config.conf`) - Enable/disable components
2. **Command-line flags** - `--only-system`, `--only-aur`, etc.
3. **Combine both** - Use config for defaults, flags for one-time changes

### Q: What if I don't have yay or paru installed?

**A:** No problem! The script will:
- Skip AUR updates if no helper is found
- Log a warning message
- Continue with other updates
- You can disable AUR updates in `config.conf` to suppress the warning

### Q: How do I update the script itself?

**A:** If you cloned with Git:
```bash
cd ~/cachyos-multi-updater
git pull
```

If you downloaded as ZIP, download the latest version from GitHub.

**Note:** Future versions may include automatic update checking.

### Q: The script asks for my password multiple times. Why?

**A:** This depends on your sudo configuration:
- By default, sudo asks for password each time
- The script needs sudo for system and AUR updates
- You can configure sudo to remember your password (see troubleshooting)
- Or disable system/AUR updates if you don't need them

### Q: Can I see what will be updated before running?

**A:** Yes! Use dry-run mode:
```bash
./update-all.sh --dry-run
```

This shows what WOULD be updated without making changes.

### Q: What is update-all.1? What can it do? Why do I need it?

**A:** `update-all.1` is a **Man-Page** (manual page) - a standard Unix/Linux documentation format.

**What is a Man-Page?**
- It's the traditional way to document command-line tools on Linux/Unix systems
- It provides concise, technical documentation that follows Unix conventions
- It's what you see when you type `man ls` or `man pacman` on Linux

**What can it do?**
- View documentation directly in the terminal: `man ./update-all.1`
- If installed system-wide: `man update-all` (works from anywhere)
- Provides quick reference for command options and usage
- Follows standard Unix documentation format

**Why do I need it?**
- **You probably don't need it** - the README files are more detailed and beginner-friendly
- It's useful if you're familiar with Unix documentation standards
- Some Linux users prefer Man-Pages for quick reference
- It's optional - you can ignore it if you prefer the README

**How to use it:**
```bash
# View the Man-Page directly
man ./update-all.1

# Or if installed system-wide (after installation)
man update-all
```

**Installation (optional):**
If you want to make it available system-wide:
```bash
sudo cp update-all.1 /usr/local/share/man/man1/
sudo mandb
```
Then you can use `man update-all` from anywhere.

### Q: What if I have a problem not covered in the FAQ?

**A:** Check these resources in order:
1. **Logs** - Check `logs/` folder for detailed information
2. **Troubleshooting section** - See the troubleshooting guide above
3. **GitHub Issues** - Search existing issues
4. **Create an issue** - Describe your problem with log excerpts

---

## 📅 Version History

For the complete version history and changelog, please see the [GitHub Releases](https://github.com/SunnyCueq/cachyos-multi-updater/releases).

---

## 📄 License

This project is open source. You can freely use, modify, and distribute it.

## 🤝 Contributing

Improvements and bug reports are welcome! Please create an issue or pull request on [GitHub](https://github.com/SunnyCueq/cachyos-multi-updater).

## 📧 Support

For questions or problems:
1. First check the log files in `logs/`
2. Check the [Troubleshooting](#-troubleshooting) section above
3. Create an issue on [GitHub](https://github.com/SunnyCueq/cachyos-multi-updater)
4. Describe the problem as detailed as possible (include log excerpts)

## 🔗 Links

- **GitHub Repository:** https://github.com/SunnyCueq/cachyos-multi-updater
- **Issues:** https://github.com/SunnyCueq/cachyos-multi-updater/issues

---

**Good luck with your updates! 🎉**
