#!/usr/bin/env python3
"""
CachyOS Multi-Updater - GUI Main Entry Point (Wrapper)
This file exists for backward compatibility with launcher scripts.
It redirects to gui/core/main.py by executing it as a module.
"""

import sys
import os
from pathlib import Path

# Suppress Qt QDBus warnings (harmless but annoying)
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.debug=false")

# Get the project root directory (parent of gui/)
project_root = Path(__file__).parent.parent.absolute()

# Change to project root so imports work correctly
os.chdir(project_root)

# Add project root to Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Execute core/main.py as a module
if __name__ == "__main__":
    # Import and run main from core/main.py
    # We need to import it as a module from the gui package
    from gui.core.main import main
    main()

