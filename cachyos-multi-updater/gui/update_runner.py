#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Update Runner
Handles running update-all.sh script and capturing output
"""

import os
import re
import subprocess
import stat
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

# Import debug logger
try:
    from .debug_logger import get_logger
except ImportError:
    try:
        from debug_logger import get_logger
    except ImportError:
        # Fallback if debug_logger not available
        def get_logger():
            class DummyLogger:
                def debug(self, *args, **kwargs): pass
                def info(self, *args, **kwargs): pass
                def warning(self, *args, **kwargs): pass
                def error(self, *args, **kwargs): pass
                def exception(self, *args, **kwargs): pass
            return DummyLogger()


class UpdateRunner(QObject):
    """Runs update-all.sh script and emits signals for output"""
    
    # Signals
    output_received = pyqtSignal(str)  # New output line
    progress_update = pyqtSignal(int, str)  # Progress percentage, status message
    finished = pyqtSignal(int)  # Exit code
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, script_dir: str, config: dict, parent=None):
        super().__init__(parent)
        self.script_dir = Path(script_dir)
        self.script_path = self.script_dir / "update-all.sh"
        self.config = config
        # Don't create QProcess in __init__ - create it lazily when needed
        self.process = None
        self.temp_script_path = None
        # Initialize logger
        self.logger = get_logger()
        
    def start_update(self, dry_run: bool = False, interactive: bool = False, sudo_password: str = None):
        """Start the update process"""
        self.logger.info(f"Starting update process (dry_run={dry_run}, interactive={interactive})")
        self.logger.debug(f"Script path: {self.script_path}, exists: {self.script_path.exists()}")
        
        if not self.script_path.exists():
            error_msg = t("gui_script_not_found_runner", "Script not found: {path}").format(path=self.script_path)
            self.logger.error(f"Script not found: {self.script_path}")
            self.error_occurred.emit(error_msg)
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
        
        # Bug 1 FIX: Do NOT store password as instance variable (security risk)
        # Password is only used locally in this method and should not persist in memory
        # Use the local parameter directly instead of self.sudo_password
        
        # CRIT-2 FIX: Create minimal wrapper script that receives password via stdin
        # Password is NOT stored in the script file - it's passed via stdin to the wrapper
        # This eliminates the security risk of storing password in a file
        temp_script_path = None
        if sudo_password and not dry_run:
            import tempfile
            import stat
            try:
                # Create minimal wrapper script that reads password from stdin
                # Password is NOT written to the script file - only passed via stdin
                temp_script = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh')
                temp_script.write(f'''#!/bin/bash
set -euo pipefail
# Read password from stdin (passed by QProcess)
read -r SUDO_PASSWORD
# Validate sudo with password from stdin
echo "$SUDO_PASSWORD" | sudo -S -v || exit 1
# Run the actual script (password already validated, sudo session active)
exec bash "{self.script_path}" {" ".join(cmd[2:]) if len(cmd) > 2 else ""}
''')
                temp_script.close()
                temp_script_path = temp_script.name
                os.chmod(temp_script_path, stat.S_IRWXU)  # 0o700 - only user can read/execute
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
        else:
            self.temp_script_path = None
        
        # Create QProcess if it doesn't exist
        if self.process is None:
            self.process = QProcess(self)
            # Connect signals
            self.process.readyReadStandardOutput.connect(self._on_stdout)
            self.process.readyReadStandardError.connect(self._on_stderr)
            self.process.finished.connect(self._on_finished)
        else:
            # Check if process is already running
            if self.process.state() != QProcess.ProcessState.NotRunning:
                # Process is still running, kill it first
                self.process.kill()
                self.process.waitForFinished(1000)
            
            # Disconnect all signals first to avoid duplicate connections
            try:
                self.process.readyReadStandardOutput.disconnect()
            except TypeError:
                pass  # No connections to disconnect
            try:
                self.process.readyReadStandardError.disconnect()
            except TypeError:
                pass  # No connections to disconnect
            try:
                self.process.finished.disconnect()
            except TypeError:
                pass  # No connections to disconnect
            
            # Reconnect signals (only if process already existed)
            self.process.readyReadStandardOutput.connect(self._on_stdout)
            self.process.readyReadStandardError.connect(self._on_stderr)
            self.process.finished.connect(self._on_finished)
        
        # Verify script exists before starting
        if not self.script_path.exists():
            error_msg = t("gui_script_not_found_runner", "Script not found: {path}").format(path=self.script_path)
            self.error_occurred.emit(error_msg)
            return
        
        # Verify bash exists
        import shutil
        bash_path = shutil.which("bash")
        if not bash_path:
            error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: bash nicht gefunden. Ist bash installiert?")
            self.logger.error("bash not found in PATH")
            self.error_occurred.emit(error_msg)
            return
        
        self.logger.debug(f"Using bash: {bash_path}")
        
        # Start process
        self.process.setWorkingDirectory(str(self.script_dir))
        
        # Set environment variables
        process_env = self.process.processEnvironment()
        for key, value in env.items():
            process_env.insert(key, value)
        self.process.setProcessEnvironment(process_env)
        
        # Check script permissions
        import stat
        script_stat = self.script_path.stat()
        script_perms = stat.filemode(script_stat.st_mode)
        self.logger.debug(f"Script permissions: {script_perms} (octal: {oct(script_stat.st_mode)})")
        self.logger.debug(f"Script is executable: {os.access(self.script_path, os.X_OK)}")
        
        # Check if we can read the script
        try:
            with open(self.script_path, 'r') as f:
                first_line = f.readline()
                self.logger.debug(f"Script first line: {first_line.strip()}")
        except Exception as e:
            self.logger.error(f"Cannot read script: {e}")
        
        # Log environment variables
        env_dict = dict(env)
        self.logger.debug(f"Environment variables: {list(env_dict.keys())}")
        self.logger.debug(f"PATH: {env_dict.get('PATH', 'NOT SET')}")
        self.logger.debug(f"SCRIPT_DIR: {env_dict.get('SCRIPT_DIR', 'NOT SET')}")
        
        # Start process and check for errors
        # Use absolute path for bash to avoid PATH issues
        # cmd is: ["bash", str(self.script_path), "--dry-run"] or similar
        # process_args should be: [str(self.script_path), "--dry-run"] (everything after "bash")
        process_args = cmd[1:] if len(cmd) > 1 else []
        self.logger.debug(f"Starting process: {bash_path} {' '.join(process_args)}")
        self.logger.debug(f"Working directory: {self.script_dir}")
        self.logger.debug(f"Process state before start: {self.process.state()}")
        
        # Try to start the process
        # QProcess.start(program, arguments) where:
        # - program = bash_path (e.g., "/usr/bin/bash")
        # - arguments = [script_path, ...flags] (e.g., ["/path/to/update-all.sh", "--dry-run"])
        try:
            # process_args already contains script_path + flags, so use it directly
            started = self.process.start(bash_path, process_args)
            self.logger.debug(f"Process.start() returned: {started}")
            
            if started:
                # start() returned True - wait a bit to confirm process actually starts
                # Note: QProcess.start() can return True even if process fails to start immediately
                # So we need to wait and check the actual state
                if self.process.waitForStarted(2000):  # Wait up to 2 seconds
                    try:
                        process_state = self.process.state()
                        self.logger.debug(f"Process state after waitForStarted: {process_state}")
                        if process_state == QProcess.ProcessState.Running or process_state == QProcess.ProcessState.Starting:
                            try:
                                self.logger.debug(f"Process PID: {self.process.processId()}")
                            except Exception:
                                self.logger.debug("Process PID: Not available yet")
                            self.logger.info("Process started successfully")
                            # Process started successfully - write password if needed BEFORE returning
                            if sudo_password and not dry_run:
                                password_bytes = (sudo_password + '\n').encode('utf-8')
                                bytes_written = self.process.write(password_bytes)
                                
                                if bytes_written != len(password_bytes):
                                    error_detail = f"Expected {len(password_bytes)} bytes, but only {bytes_written} bytes were written"
                                    error_msg = t("gui_process_write_error", "Write error: {error}").format(error=error_detail)
                                    if self.temp_script_path and os.path.exists(self.temp_script_path):
                                        try:
                                            os.unlink(self.temp_script_path)
                                        except Exception:
                                            pass
                                        self.temp_script_path = None
                                    self.error_occurred.emit(error_msg)
                                    self.process.kill()
                                    self.process.waitForFinished(1000)
                                    self.process.deleteLater()
                                    self.process = None
                                    return
                                
                                self.process.closeWriteChannel()
                                del password_bytes
                            # Process started successfully, return early
                            return
                        else:
                            # Process state is not Running/Starting - something went wrong
                            self.logger.warning(f"Process.start() returned True but state is {process_state}")
                            started = False
                    except Exception as e:
                        self.logger.warning(f"Error checking process state: {e}")
                        started = False
                else:
                    # start() returned True but waitForStarted() timed out
                    # Check if process is actually running despite timeout
                    try:
                        process_state = self.process.state()
                        self.logger.warning(f"Process.start() returned True but waitForStarted() timed out. State: {process_state}")
                        if process_state == QProcess.ProcessState.Running or process_state == QProcess.ProcessState.Starting:
                            self.logger.info("Process is running/starting despite timeout - continuing")
                            # Process is running - write password if needed BEFORE returning
                            if sudo_password and not dry_run:
                                password_bytes = (sudo_password + '\n').encode('utf-8')
                                bytes_written = self.process.write(password_bytes)
                                
                                if bytes_written != len(password_bytes):
                                    error_detail = f"Expected {len(password_bytes)} bytes, but only {bytes_written} bytes were written"
                                    error_msg = t("gui_process_write_error", "Write error: {error}").format(error=error_detail)
                                    if self.temp_script_path and os.path.exists(self.temp_script_path):
                                        try:
                                            os.unlink(self.temp_script_path)
                                        except Exception:
                                            pass
                                        self.temp_script_path = None
                                    self.error_occurred.emit(error_msg)
                                    self.process.kill()
                                    self.process.waitForFinished(1000)
                                    self.process.deleteLater()
                                    self.process = None
                                    return
                                
                                self.process.closeWriteChannel()
                                del password_bytes
                            return
                    except Exception:
                        pass
                    started = False
            else:
                # start() returned False immediately - check state anyway
                # Sometimes QProcess.start() returns False even when process is starting
                try:
                    process_state = self.process.state()
                    self.logger.debug(f"Process state after failed start: {process_state}")
                    # If state is Starting or Running, process might have started anyway
                    if process_state == QProcess.ProcessState.Running or process_state == QProcess.ProcessState.Starting:
                        self.logger.info("Process state indicates it's running/starting despite start() returning False - continuing")
                        # Wait a bit more to confirm
                        if self.process.waitForStarted(1000):
                            # Process is running - write password if needed BEFORE returning
                            if sudo_password and not dry_run:
                                password_bytes = (sudo_password + '\n').encode('utf-8')
                                bytes_written = self.process.write(password_bytes)
                                
                                if bytes_written != len(password_bytes):
                                    error_detail = f"Expected {len(password_bytes)} bytes, but only {bytes_written} bytes were written"
                                    error_msg = t("gui_process_write_error", "Write error: {error}").format(error=error_detail)
                                    if self.temp_script_path and os.path.exists(self.temp_script_path):
                                        try:
                                            os.unlink(self.temp_script_path)
                                        except Exception:
                                            pass
                                        self.temp_script_path = None
                                    self.error_occurred.emit(error_msg)
                                    self.process.kill()
                                    self.process.waitForFinished(1000)
                                    self.process.deleteLater()
                                    self.process = None
                                    return
                                
                                self.process.closeWriteChannel()
                                del password_bytes
                            return
                except Exception:
                    pass
        except Exception as e:
            self.logger.exception(f"Exception during process.start(): {e}")
            started = False
        
        if not started:
            # Process failed to start immediately
            error = self.process.error()
            error_msg = self.process.errorString()
            
            self.logger.error(f"Process failed to start immediately. Error: {error}, ErrorString: {error_msg}")
            self.logger.error(f"Command: {bash_path} {' '.join(process_args)}")
            self.logger.error(f"Full command would be: {bash_path} {' '.join(process_args)}")
            self.logger.error(f"Script path: {self.script_path}, exists: {self.script_path.exists()}")
            self.logger.error(f"Script permissions: {script_perms}")
            self.logger.error(f"Script is executable: {os.access(self.script_path, os.X_OK)}")
            self.logger.error(f"Working directory: {self.script_dir}, exists: {self.script_dir.exists()}")
            self.logger.error(f"Bash path: {bash_path}, exists: {Path(bash_path).exists() if bash_path else False}")
            self.logger.error(f"Process state: {self.process.state()}")
            
            # Try to test if we can execute the script manually (with longer timeout)
            try:
                import subprocess
                test_result = subprocess.run(
                    [bash_path, str(self.script_path), "--dry-run"],
                    cwd=str(self.script_dir),
                    env=env,
                    capture_output=True,
                    timeout=10  # Increased timeout to 10 seconds
                )
                self.logger.debug(f"Manual test execution: exit_code={test_result.returncode}")
                if test_result.stdout:
                    self.logger.debug(f"Manual test stdout (first 200 chars): {test_result.stdout[:200]}")
                if test_result.stderr:
                    self.logger.debug(f"Manual test stderr (first 200 chars): {test_result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                self.logger.warning("Manual test execution timed out (script is running but takes longer than 10 seconds)")
            except Exception as test_e:
                self.logger.error(f"Manual test execution failed: {test_e}")
            
            # Provide more detailed error message
            if not error_msg:
                # Check if command exists
                import shutil
                if not shutil.which(cmd[0]):
                    error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: '{cmd}' nicht gefunden. Ist bash installiert?").format(cmd=cmd[0])
                else:
                    error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: Unbekannter Fehler (Prozess konnte nicht gestartet werden)")
            else:
                error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: {error}").format(error=error_msg)
            # Log the log file location for user
            try:
                log_file = self.logger.get_log_file()
                self.logger.info(f"GUI Debug Log file: {log_file}")
                error_msg += f"\n\nDebug-Log: {log_file}"
            except Exception:
                pass
            
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
            
            # Cleanup process safely
            process_to_cleanup = self.process  # Store reference before setting to None
            self.process = None  # Set to None first to prevent race conditions
            
            if process_to_cleanup is not None:
                try:
                    # Check if process is still running before cleanup
                    try:
                        process_state = process_to_cleanup.state()
                        if process_state != QProcess.ProcessState.NotRunning:
                            try:
                                process_to_cleanup.kill()
                                process_to_cleanup.waitForFinished(1000)
                            except Exception:
                                pass  # Process might already be finished
                    except Exception:
                        pass  # Process might already be deleted
                    
                    # Only call deleteLater() if process still exists
                    try:
                        process_to_cleanup.deleteLater()
                    except Exception:
                        pass  # Process might already be deleted
                except Exception as cleanup_e:
                    self.logger.error(f"Error during process cleanup: {cleanup_e}")
            
            self.error_occurred.emit(error_msg)
            return
        
        # Wait for process to start (with timeout)
        if not self.process.waitForStarted(5000):  # 5 second timeout
            # Check what went wrong
            error = self.process.error()
            error_msg = self.process.errorString()
            
            # Debug: Log error details
            process_args = cmd[1:] if len(cmd) > 1 else []
            self.logger.error(f"Process failed to start (timeout). Error: {error}, ErrorString: {error_msg}")
            self.logger.error(f"Command: {bash_path} {' '.join(process_args)}")
            self.logger.error(f"Script path: {self.script_path}, exists: {self.script_path.exists()}")
            self.logger.error(f"Script permissions: {stat.filemode(self.script_path.stat().st_mode)}")
            self.logger.error(f"Script is executable: {os.access(self.script_path, os.X_OK)}")
            self.logger.error(f"Working directory: {self.script_dir}, exists: {self.script_dir.exists()}")
            self.logger.error(f"Bash path: {bash_path}, exists: {Path(bash_path).exists() if bash_path else False}")
            self.logger.error(f"Process state: {self.process.state()}")
            
            # Log the log file location for user
            try:
                log_file = self.logger.get_log_file()
                self.logger.info(f"GUI Debug Log file: {log_file}")
            except Exception:
                pass
            
            if error == QProcess.ProcessError.FailedToStart:
                if not error_msg:
                    # Check if command exists
                    import shutil
                    if not shutil.which(cmd[0]):
                        error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: '{cmd}' nicht gefunden. Ist bash installiert?").format(cmd=cmd[0])
                    elif not self.script_path.exists():
                        error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: Script nicht gefunden: {path}").format(path=self.script_path)
                    else:
                        error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: Prozess konnte nicht gestartet werden (Fehlercode: FailedToStart)")
                else:
                    # Use the more specific error message
                    error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: {error}").format(error=error_msg)
            elif error == QProcess.ProcessError.Crashed:
                error_msg = t("gui_process_crashed", "Process crashed immediately after start: {error}").format(error=error_msg)
            elif error == QProcess.ProcessError.Timedout:
                error_msg = t("gui_process_timeout", "Process start timed out")
            elif error == QProcess.ProcessError.WriteError:
                error_msg = t("gui_process_write_error", "Write error: {error}").format(error=error_msg)
            elif error == QProcess.ProcessError.ReadError:
                error_msg = t("gui_process_read_error", "Read error: {error}").format(error=error_msg)
            else:
                # Unknown error - provide more details
                if error_msg:
                    error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: {error}").format(error=error_msg)
                else:
                    # Try to get more information about why it failed
                    import shutil
                    if not shutil.which(cmd[0]):
                        error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: '{cmd}' nicht gefunden. Ist bash installiert?").format(cmd=cmd[0])
                    elif not self.script_path.exists():
                        error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: Script nicht gefunden: {path}").format(path=self.script_path)
                    else:
                        error_msg = t("gui_process_start_failed_detail", "Update-Script konnte nicht gestartet werden: Unbekannter Fehler (Fehlercode: {error_code})").format(error_code=error)
            
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
            
            # Cleanup process safely
            process_to_cleanup = self.process  # Store reference before setting to None
            self.process = None  # Set to None first to prevent race conditions
            
            if process_to_cleanup is not None:
                try:
                    # Check if process is still running before cleanup
                    try:
                        process_state = process_to_cleanup.state()
                        if process_state != QProcess.ProcessState.NotRunning:
                            try:
                                process_to_cleanup.kill()
                                process_to_cleanup.waitForFinished(1000)
                            except Exception:
                                pass  # Process might already be finished
                    except Exception:
                        pass  # Process might already be deleted
                    
                    # Only call deleteLater() if process still exists
                    try:
                        process_to_cleanup.deleteLater()
                    except Exception:
                        pass  # Process might already be deleted
                except Exception as cleanup_e:
                    self.logger.error(f"Error during process cleanup: {cleanup_e}")
            
            self.error_occurred.emit(error_msg)
            return
        else:
            # Bug 1 FIX: Process started successfully - write password to stdin if needed
            # This must happen AFTER waitForStarted succeeds, regardless of which check passed
            # If we don't write the password, the subprocess will hang on 'read -r SUDO_PASSWORD'
            if sudo_password and not dry_run:
                # Write password to stdin (followed by newline for 'read' command)
                password_bytes = (sudo_password + '\n').encode('utf-8')
                bytes_written = self.process.write(password_bytes)
                
                # Bug 1 FIX: Verify write succeeded before closing channel
                # QProcess.write() returns number of bytes written, or -1 on error
                if bytes_written != len(password_bytes):
                    # Write failed - subprocess will hang waiting for input
                    # Bug 1 FIX: Format error message with actual error details
                    error_detail = f"Expected {len(password_bytes)} bytes, but only {bytes_written} bytes were written"
                    error_msg = t("gui_process_write_error", "Write error: {error}").format(error=error_detail)
                    # Cleanup temp script
                    if self.temp_script_path and os.path.exists(self.temp_script_path):
                        try:
                            os.unlink(self.temp_script_path)
                        except Exception:
                            pass
                        self.temp_script_path = None
                    self.error_occurred.emit(error_msg)
                    self.process.kill()
                    self.process.waitForFinished(1000)
                    self.process.deleteLater()
                    self.process = None
                    return
                
                # Close write channel to signal EOF to subprocess
                # The wrapper script uses 'read -r SUDO_PASSWORD' which blocks until EOF
                self.process.closeWriteChannel()
                # Clear password from memory immediately after writing
                # Note: Python strings are immutable, but we can't guarantee memory clearing
                # This is the best we can do without using secure memory libraries
                del password_bytes
            # Process started successfully, continue with normal execution
    
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
        self.logger.debug("Received stdout data")
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
    
    def _parse_progress(self, line: str):
        """Parse progress information from script output"""
        import re
        
        # Format from lib/progress.sh: "[████████████████████████████████████████] 100% [5/5]"
        # Also handle: "100% [5/5]" or just percentage
        # Remove ANSI color codes first
        line_clean = re.sub(r'\033\[[0-9;]*m', '', line)
        
        # Try to match: [bar] percentage% [step/total]
        progress_match = re.search(r'\[.*?\]\s+(\d+)%\s+\[(\d+)/(\d+)\]', line_clean)
        if progress_match:
            percent = int(progress_match.group(1))
            current_step = int(progress_match.group(2))
            total_steps = int(progress_match.group(3))
            message = f"[{current_step}/{total_steps}]"
            self.progress_update.emit(percent, message)
            return
        
        # Try to match: percentage% [step/total]
        progress_match = re.search(r'(\d+)%\s+\[(\d+)/(\d+)\]', line_clean)
        if progress_match:
            percent = int(progress_match.group(1))
            current_step = int(progress_match.group(2))
            total_steps = int(progress_match.group(3))
            message = f"[{current_step}/{total_steps}]"
            self.progress_update.emit(percent, message)
            return
        
        # Try to match: just percentage%
        progress_match = re.search(r'(\d+)%', line_clean)
        if progress_match:
            percent = int(progress_match.group(1))
            self.progress_update.emit(percent, "")
            return
    
    def _on_stderr(self):
        """Handle stderr output
        
        Best Practice: Only log stderr if it contains actual errors, not just warnings
        """
        if self.process:
            data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            for line in data.splitlines():
                if line.strip():
                    # Best Practice: Only log stderr as warning if it looks like an error
                    # Many scripts write normal output to stderr (e.g., progress bars)
                    line_lower = line.lower()
                    is_error = any(keyword in line_lower for keyword in [
                        'error', 'failed', 'fatal', 'cannot', 'unable', 'missing',
                        'not found', 'permission denied', 'access denied'
                    ])
                    
                    if is_error:
                        self.logger.warning(f"Stderr (error): {line}")
                    else:
                        # Normal stderr output - just debug log it
                        self.logger.debug(f"Stderr: {line}")
                    
                    # Always emit to output (user should see it)
                    self.output_received.emit(line)
                    # Also try to parse progress from stderr
                    self._parse_progress(line)
    
    def _on_finished(self, exit_code: int, exit_status: int):
        """Handle process finished"""
        self.logger.info(f"Process finished with exit_code={exit_code}, exit_status={exit_status}")
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

