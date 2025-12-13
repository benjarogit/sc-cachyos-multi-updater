#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Constants
Centralized constants for the GUI application
"""

# Update-related constants
MAX_DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_DELAY_SECONDS = 2
MAX_BACKUP_DIRS = 3
BACKUP_RETENTION_DAYS = 7
BACKUP_RETENTION_SECONDS = 7 * 24 * 60 * 60

# File permissions
EXECUTABLE_PERMISSIONS = 0o755
READABLE_PERMISSIONS = 0o644

# Executable files that need special permissions
EXECUTABLE_FILES = [
    "update-all.sh",
    "setup.sh",
    "cachyos-update",
    "cachyos-update-gui",
    "run-update.sh",
]

# Critical files for installation verification
CRITICAL_INSTALLATION_FILES = [
    "update-all.sh",
    "gui/main.py",
    "gui/window.py",
    "lib/i18n.sh",
]

# Script directories that contain executable files
SCRIPT_DIRECTORIES = ["lib", "gui"]

# Network check
NETWORK_CHECK_HOST = "8.8.8.8"
NETWORK_CHECK_PORT = 53
NETWORK_CHECK_TIMEOUT = 3

# UI constants
SPINNER_UPDATE_INTERVAL_MS = 100
SPINNER_FRAME_COUNT = 10

# Log cleanup
MAX_LOG_FILES_DEFAULT = 10
