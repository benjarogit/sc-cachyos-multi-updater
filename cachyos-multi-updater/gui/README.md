# CachyOS Multi-Updater - GUI Version

Qt-based graphical user interface for the CachyOS Multi-Updater script.

## Features

- **Graphical Interface**: Easy-to-use GUI for managing system updates
- **Real-time Output**: See update progress in real-time with colored output
- **Component Selection**: Enable/disable update components (System, AUR, Cursor, AdGuard, Flatpak)
- **Settings Management**: Configure all options through a settings dialog
- **Log Viewer**: View and browse log files directly in the GUI
- **Progress Tracking**: Visual progress bar and status updates

## Requirements

- Python 3.8 or higher
- PyQt6 (or PySide6)
- Bash (for running update-all.sh)

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements-gui.txt
   ```

   Or install PyQt6 directly:
   ```bash
   pip install PyQt6
   ```

2. Make sure `update-all.sh` is in the same directory or parent directory

## Usage

### Running the GUI

From the script directory:
```bash
python gui/main.py
```

Or make it executable and run directly:
```bash
chmod +x gui/main.py
./gui/main.py
```

### Setting Script Directory

If the GUI can't find `update-all.sh`, set the `SCRIPT_DIR` environment variable:
```bash
export SCRIPT_DIR=/path/to/cachyos-multi-updater
python gui/main.py
```

## GUI Components

### Main Window

- **Update Components**: Checkboxes to enable/disable each update type
- **Progress Bar**: Shows update progress (0-100%)
- **Status Label**: Current status message
- **Output Area**: Real-time output from the update script with color coding:
  - Green: Success messages
  - Red: Error messages
  - Orange: Warning messages
  - Black: Normal output

### Buttons

- **Check for Updates**: Runs update script in dry-run mode (test only)
- **Start Updates**: Starts the actual update process
- **Stop**: Stops a running update (if possible)
- **Settings**: Opens the settings dialog
- **View Logs**: Opens the log viewer

### Settings Dialog

The settings dialog has four tabs:

#### 1. Update Components
Enable or disable each update component:
- System Updates (pacman)
- AUR Updates (yay/paru)
- Cursor Editor
- AdGuard Home
- Flatpak Updates

#### 2. General Settings
- Max Log Files: Number of log files to keep (default: 3)
- Download Retries: Number of retry attempts for downloads (default: 3)
- Cache Max Age: Cache duration in seconds (default: 3600)
- Enable Notifications: Desktop notifications
- Enable Colors: Colored terminal output
- Dry Run Mode: Test mode (no actual changes)
- Enable Auto Update: Automatic script updates

#### 3. Advanced Settings
- GitHub Repository URL: Repository for version checks
- Log Directory: Directory for log files
- Stats Directory: Directory for statistics
- Script Path: Path to update-all.sh script
- GUI Language: Language for GUI (auto, de, en)

#### 4. Pacman Parameters
Configure pacman command parameters:
- Sync (-S): Update package database
- Refresh (-y): Refresh package lists
- Upgrade (-u): Upgrade all packages
- No Confirm (--noconfirm): Don't ask for confirmation

Command preview shows the final pacman command that will be executed.

## Configuration

The GUI reads and writes to the same `config.conf` file as the command-line script. Changes made in the GUI are immediately saved to the config file.

## Log Viewer

The log viewer allows you to:
- Browse through log files
- View the latest log file automatically
- Read log contents with proper formatting

## Troubleshooting

### GUI won't start

1. Check if PyQt6 is installed:
   ```bash
   python -c "import PyQt6; print('OK')"
   ```

2. Check if update-all.sh exists in the script directory

3. Check Python version (must be 3.8+):
   ```bash
   python --version
   ```

### Script not found

Set the `SCRIPT_DIR` environment variable:
```bash
export SCRIPT_DIR=/path/to/cachyos-multi-updater
python gui/main.py
```

### Updates not working

- Make sure you have the necessary permissions (sudo)
- Check the output area for error messages
- View logs for detailed error information

## Development

### Project Structure

```
gui/
├── __init__.py          # Package initialization
├── main.py              # Main entry point
├── window.py            # Main window class
├── config_dialog.py     # Settings dialog
├── config_manager.py    # Config file management
└── update_runner.py     # Script execution handler
```

### Adding Features

The GUI is modular and easy to extend:
- Add new settings in `config_dialog.py`
- Modify UI layout in `window.py`
- Extend script execution in `update_runner.py`

## License

Same as the main project - MIT License

## Support

For issues and questions, please visit the GitHub repository:
https://github.com/benjarogit/sc-cachyos-multi-updater

