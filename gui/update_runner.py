#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Update Runner
Handles running update-all.sh script and capturing output
"""

import os
import re
import subprocess
from pathlib import Path
from PyQt6.QtCore import QProcess, QObject, pyqtSignal


class UpdateRunner(QObject):
    """Runs update-all.sh script and emits signals for output"""
    
    # Signals
    output_received = pyqtSignal(str)  # New output line
    progress_update = pyqtSignal(int, str)  # Progress percentage, status message
    finished = pyqtSignal(int)  # Exit code
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, script_dir: str, config: dict):
        super().__init__()
        self.script_dir = Path(script_dir)
        self.script_path = self.script_dir / "update-all.sh"
        self.config = config
        self.process = None
        
    def start_update(self, dry_run: bool = False, interactive: bool = False, sudo_password: str = None):
        """Start the update process"""
        if not self.script_path.exists():
            self.error_occurred.emit(f"Script not found: {self.script_path}")
            return
        
        # Build command
        cmd = ["bash", str(self.script_path)]
        
        if dry_run:
            cmd.append("--dry-run")
        elif interactive:
            cmd.append("--interactive")
        
        # Set environment variables from config
        env = os.environ.copy()
        env["ENABLE_SYSTEM_UPDATE"] = str(self.config.get("ENABLE_SYSTEM_UPDATE", "true")).lower()
        env["ENABLE_AUR_UPDATE"] = str(self.config.get("ENABLE_AUR_UPDATE", "true")).lower()
        env["ENABLE_CURSOR_UPDATE"] = str(self.config.get("ENABLE_CURSOR_UPDATE", "true")).lower()
        env["ENABLE_ADGUARD_UPDATE"] = str(self.config.get("ENABLE_ADGUARD_UPDATE", "true")).lower()
        env["ENABLE_FLATPAK_UPDATE"] = str(self.config.get("ENABLE_FLATPAK_UPDATE", "true")).lower()
        
        # Store sudo password for later use
        self.sudo_password = sudo_password
        
        # If sudo password provided, create wrapper script
        if sudo_password and not dry_run:
            import tempfile
            import stat
            temp_script = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh')
            # Escape password for bash
            escaped_password = sudo_password.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
            temp_script.write(f'''#!/bin/bash
# Validate sudo with password
echo "{escaped_password}" | sudo -S -v || exit 1
# Run the actual script
exec bash "{self.script_path}" {" ".join(cmd[2:]) if len(cmd) > 2 else ""}
''')
            temp_script.close()
            os.chmod(temp_script.name, stat.S_IRWXU)
            cmd = ["bash", temp_script.name]
        
        # Create process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        
        # Start process
        self.process.setWorkingDirectory(str(self.script_dir))
        self.process.start(cmd[0], cmd[1:] if len(cmd) > 1 else [])
        
        if not self.process.waitForStarted():
            self.error_occurred.emit("Failed to start update script")
    
    def stop_update(self):
        """Stop the update process"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished()
    
    def _on_stdout(self):
        """Handle stdout output"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            # Process line by line, but also handle partial lines
            lines = data.splitlines(keepends=True)
            for line in lines:
                line = line.rstrip('\n\r')
                if line.strip():
                    self.output_received.emit(line)
                    # Try to extract progress info
                    self._parse_progress(line)
            # Handle any remaining partial line
            if data and not data.endswith('\n'):
                remaining = data.splitlines()[-1] if '\n' in data else data
                if remaining.strip():
                    self.output_received.emit(remaining)
    
    def _on_stderr(self):
        """Handle stderr output"""
        if self.process:
            data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            for line in data.splitlines():
                if line.strip():
                    self.output_received.emit(line)
    
    def _on_finished(self, exit_code: int, exit_status: int):
        """Handle process finished"""
        self.finished.emit(exit_code)
    
    def _parse_progress(self, line: str):
        """Try to parse progress information from output"""
        # Look for progress indicators
        # Format: "[████████████████████████████████████████] 100% [5/5]"
        progress_match = re.search(r'\[.*\]\s+(\d+)%\s+\[(\d+)/(\d+)\]', line)
        if progress_match:
            try:
                percent = int(progress_match.group(1))
                current_step = progress_match.group(2)
                total_steps = progress_match.group(3)
                self.progress_update.emit(percent, line)
            except:
                pass
        elif "%" in line:
            # Try to extract percentage without step info
            try:
                percent_match = re.search(r'(\d+)%', line)
                if percent_match:
                    percent = int(percent_match.group(1))
                    self.progress_update.emit(percent, line)
            except:
                pass

