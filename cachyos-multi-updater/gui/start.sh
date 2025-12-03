#!/bin/bash
#
# Start script for CachyOS Multi-Updater GUI
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Check if PyQt6 is installed
if ! python3 -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null; then
    echo "❌ PyQt6 is not installed!"
    echo ""
    echo "Please install it with:"
    echo "  pip3 install PyQt6"
    echo ""
    echo "Or install from requirements:"
    echo "  pip3 install -r requirements-gui.txt"
    echo ""
    exit 1
fi

# Check if update-all.sh exists
if [ ! -f "$SCRIPT_DIR/update-all.sh" ]; then
    echo "❌ update-all.sh not found in: $SCRIPT_DIR"
    exit 1
fi

# Start GUI
echo "🚀 Starting CachyOS Multi-Updater GUI..."
python3 gui/main.py

