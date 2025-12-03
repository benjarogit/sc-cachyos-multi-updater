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

# Handle imports for both direct execution and module import
try:
    from .i18n import t
except ImportError:
    try:
        from i18n import t
    except ImportError:
        # Fallback if i18n not available
        def t(key: str, default: str = "") -> str:
            return default


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
        self.temp_script_path = None
        
    def start_update(self, dry_run: bool = False, interactive: bool = False, sudo_password: str = None):
        """Start the update process"""
        if not self.script_path.exists():
            self.error_occurred.emit(t("gui_script_not_found_runner", "Script not found: {path}").format(path=self.script_path))
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
        temp_script_path = None
        if sudo_password and not dry_run:
            import tempfile
            import stat
            try:
                temp_script = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh')
                # Escape password for bash (complete escaping for all special characters)
                # Order matters: backslash must be escaped first!
                escaped_password = (sudo_password
                    .replace('\\', '\\\\')  # Backslash first!
                    .replace('"', '\\"')
                    .replace('$', '\\$')
                    .replace('`', '\\`')
                    .replace('\n', '\\n')
                    .replace('\r', '\\r')
                    .replace("'", "\\'"))
                temp_script.write(f'''#!/bin/bash
set -euo pipefail
# Validate sudo with password
echo "{escaped_password}" | sudo -S -v || exit 1
# Run the actual script
exec bash "{self.script_path}" {" ".join(cmd[2:]) if len(cmd) > 2 else ""}
''')
                temp_script.close()
                temp_script_path = temp_script.name
                os.chmod(temp_script_path, stat.S_IRWXU)
                # Store temp script path IMMEDIATELY for cleanup
                self.temp_script_path = temp_script_path
                cmd = ["bash", temp_script_path]
            except Exception as e:
                # Cleanup temp script if creation failed
                if temp_script_path and os.path.exists(temp_script_path):
                    try:
                        os.unlink(temp_script_path)
                    except Exception:
                        pass
                self.error_occurred.emit(t("gui_sudo_wrapper_failed", "Failed to create sudo wrapper script: {error}").format(error=str(e)))
                return
        
        # Create process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        
        # Start process
        self.process.setWorkingDirectory(str(self.script_dir))
        
        # Set environment variables
        process_env = self.process.processEnvironment()
        for key, value in env.items():
            process_env.insert(key, value)
        self.process.setProcessEnvironment(process_env)
        
        # Start process and check for errors
        started = self.process.start(cmd[0], cmd[1:] if len(cmd) > 1 else [])
        
        if not started:
            # Process failed to start immediately
            error_msg = self.process.errorString()
            if not error_msg:
                error_msg = t("gui_process_start_failed", "Failed to start process: {cmd}").format(cmd=cmd[0])
            else:
                error_msg = t("gui_process_start_failed_detail", "Failed to start update script: {error}").format(error=error_msg)
            # Cleanup temp script if created (use self.temp_script_path which is set immediately)
            if self.temp_script_path and os.path.exists(self.temp_script_path):
                try:
                    os.unlink(self.temp_script_path)
                except OSError:
                    # Log but don't fail - cleanup is best effort
                    pass  # File might already be deleted
                except Exception:
                    # Unexpected error during cleanup - log but continue
                    pass  # Cleanup failure shouldn't break the flow
                self.temp_script_path = None
            self.error_occurred.emit(error_msg)
            self.process.deleteLater()
            self.process = None
            return
        
        # Wait for process to start (with timeout)
        if not self.process.waitForStarted(5000):  # 5 second timeout
            # Check what went wrong
            error = self.process.error()
            error_msg = self.process.errorString()
            
            if error == QProcess.ProcessError.FailedToStart:
                if not error_msg:
                    error_msg = t("gui_process_failed_to_start", "Process '{cmd}' failed to start. Is bash installed and in PATH?").format(cmd=cmd[0])
                else:
                    error_msg = t("gui_process_failed_to_start_detail", "Failed to start: {error}").format(error=error_msg)
            elif error == QProcess.ProcessError.Crashed:
                error_msg = t("gui_process_crashed", "Process crashed immediately after start: {error}").format(error=error_msg)
            elif error == QProcess.ProcessError.Timedout:
                error_msg = t("gui_process_timeout", "Process start timed out")
            elif error == QProcess.ProcessError.WriteError:
                error_msg = t("gui_process_write_error", "Write error: {error}").format(error=error_msg)
            elif error == QProcess.ProcessError.ReadError:
                error_msg = t("gui_process_read_error", "Read error: {error}").format(error=error_msg)
            else:
                if error_msg:
                    error_msg = t("gui_process_unknown_error", "Unknown error: {error}").format(error=error_msg)
                else:
                    error_msg = t("gui_process_unknown_error_generic", "Unknown error starting process")
            
            # Cleanup temp script if created (use self.temp_script_path which is set immediately)
            if self.temp_script_path and os.path.exists(self.temp_script_path):
                try:
                    os.unlink(self.temp_script_path)
                except OSError:
                    # Log but don't fail - cleanup is best effort
                    pass  # File might already be deleted
                except Exception:
                    # Unexpected error during cleanup - log but continue
                    pass  # Cleanup failure shouldn't break the flow
                self.temp_script_path = None
            
            self.error_occurred.emit(error_msg)
            self.process.deleteLater()
            self.process = None
            return
    
    def stop_update(self):
        """Stop the update process"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(5000)  # 5 second timeout
        
        # Cleanup temp script if it was created
        if self.temp_script_path and os.path.exists(self.temp_script_path):
            try:
                os.unlink(self.temp_script_path)
            except Exception:
                pass
            self.temp_script_path = None
    
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
        
        # Cleanup temp script if it was created
        if self.temp_script_path and os.path.exists(self.temp_script_path):
            try:
                os.unlink(self.temp_script_path)
            except Exception:
                pass
            self.temp_script_path = None
        
        # Cleanup process
        if self.process:
            self.process.deleteLater()
            self.process = None
    
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
            except (ValueError, IndexError, AttributeError):
                # Invalid progress format - ignore silently
                pass
            except Exception:
                # Unexpected error parsing progress - ignore silently
                pass
        elif "%" in line:
            # Try to extract percentage without step info
            try:
                percent_match = re.search(r'(\d+)%', line)
                if percent_match:
                    percent = int(percent_match.group(1))
                    self.progress_update.emit(percent, line)
            except (ValueError, AttributeError):
                # Invalid progress format - ignore silently
                pass
            except Exception:
                # Unexpected error parsing progress - ignore silently
                pass

