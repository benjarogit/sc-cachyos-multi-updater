"""
Update Handler for MainWindow
Handles all update-related operations (check, start, stop, parse output)
Extracted from window.py for better organization
"""

from typing import Dict
import re
from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import QProcess, QThread, pyqtSignal

from ..utils import UpdateRunner, UpdateCheckResult, get_logger
from ..dialogs import UpdateConfirmationDialog, SudoDialog
from .i18n import t


class UpdateHandler:
    """Handles update operations for MainWindow"""

    def __init__(self, window):
        """Initialize update handler

        Args:
            window: MainWindow instance (for accessing UI elements and methods)
        """
        self.window = window
        self.logger = get_logger()

    def check_updates(self) -> None:
        """Check for available updates
        
        Zwei getrennte Systeme:
        1. GUI-Konsole: stdout/stderr unverändert anzeigen (subprocess)
        2. Update-Info: Nur über explizite Events befüllen (BashWrapper parallel)
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("Starting update check (subprocess + parallel BashWrapper)")
            self.logger.info(f"Script directory: {self.window.script_dir}")
            self.logger.info(f"Log file: {self.logger.get_log_file()}")
            self.logger.info("=" * 80)
        except Exception:
            pass  # Logger not critical

        if self.window.is_updating:
            QMessageBox.warning(
                self.window,
                t("gui_update_failed", "Update Failed"),
                t(
                    "gui_update_already_running",
                    "Another update is already in progress.\n\nPlease wait for it to complete.",
                ),
            )
            return

        # Reset Update-Info to "Prüfe..." state
        self._reset_update_info()
        
        # Start subprocess for console output (unmodified stdout/stderr)
        self._check_updates_with_subprocess()
        
        # Start parallel BashWrapper check for Update-Info (explicit events)
        self._check_updates_parallel()

    def _reset_update_info(self) -> None:
        """Reset Update-Info to 'Prüfe...' state"""
        self.window.update_info_data["planned"] = {
            "system": self.window.check_system.isChecked(),
            "aur": self.window.check_aur.isChecked(),
            "cursor": self.window.check_cursor.isChecked(),
            "adguard": self.window.check_adguard.isChecked(),
            "flatpak": self.window.check_flatpak.isChecked(),
            "proton_ge": self.window.check_proton_ge.isChecked() if hasattr(self.window, "check_proton_ge") else False,
        }
        # Reset all status to "Prüfe..." (current = None means "checking")
        for component in ["system", "aur", "cursor", "adguard", "flatpak", "proton_ge"]:
            if component in self.window.update_info_data["status"]:
                self.window.update_info_data["status"][component]["current"] = None
                self.window.update_info_data["status"][component]["found"] = 0
                if "packages" in self.window.update_info_data["status"][component]:
                    self.window.update_info_data["status"][component]["packages"] = []
        self.window.update_info_display()
    
    def _check_updates_parallel(self) -> None:
        """Check updates in parallel using BashWrapper (for Update-Info only)"""
        try:
            from ..utils import BashWrapper
        except ImportError:
            self.logger.warning("BashWrapper not available, Update-Info will not be updated")
            return
        
        # Get enabled components
        enabled_components = []
        if self.window.check_system.isChecked():
            enabled_components.append("system")
        if self.window.check_aur.isChecked():
            enabled_components.append("aur")
        if self.window.check_cursor.isChecked():
            enabled_components.append("cursor")
        if self.window.check_adguard.isChecked():
            enabled_components.append("adguard")
        if self.window.check_flatpak.isChecked():
            enabled_components.append("flatpak")
        if hasattr(self.window, "check_proton_ge") and self.window.check_proton_ge.isChecked():
            enabled_components.append("proton_ge")
        
        if not enabled_components:
            return
        
        # Use QThread to run BashWrapper checks in parallel
        # Best Practice: Use QObject worker with moveToThread instead of inheriting from QThread
        from PyQt6.QtCore import QThread, QObject
        
        class UpdateCheckWorker(QObject):
            update_found = pyqtSignal(str, object)  # component, UpdateCheckResult
            finished = pyqtSignal()
            
            def __init__(self, script_dir, components):
                super().__init__()
                self.script_dir = script_dir
                self.components = components
                self.wrapper = None
            
            def run(self):
                try:
                    self.wrapper = BashWrapper(str(self.script_dir))
                    results = self.wrapper.check_all_updates()
                    for component, result in results.items():
                        if component in self.components:
                            self.update_found.emit(component, result)
                except Exception as e:
                    # Use print instead of logger in thread context
                    print(f"Error in parallel update check: {e}")
                finally:
                    self.finished.emit()
        
        # Create thread and worker
        self.check_thread = QThread(self.window)
        self.check_worker = UpdateCheckWorker(str(self.window.script_dir), enabled_components)
        self.check_worker.moveToThread(self.check_thread)
        
        # Connect signals
        self.check_thread.started.connect(self.check_worker.run)
        self.check_worker.update_found.connect(self._on_update_found_event)
        self.check_worker.finished.connect(self.check_thread.quit)
        self.check_thread.finished.connect(self.check_thread.deleteLater)
        self.check_worker.finished.connect(self.check_worker.deleteLater)
        
        # Start thread
        self.check_thread.start()
    
    def _on_update_found_event(self, component: str, result: UpdateCheckResult) -> None:
        """Handle explicit update event - update Update-Info immediately"""
        if component == "system":
            if result.has_update:
                self.window.update_info_data["status"]["system"]["found"] = result.package_count
                self.window.update_info_data["status"]["system"]["current"] = False
                if result.packages:
                    self.window.update_info_data["status"]["system"]["packages"] = result.packages
            else:
                self.window.update_info_data["status"]["system"]["current"] = True
                self.window.update_info_data["status"]["system"]["found"] = 0
        elif component == "aur":
            if result.has_update:
                self.window.update_info_data["status"]["aur"]["found"] = result.package_count
                self.window.update_info_data["status"]["aur"]["current"] = False
                if result.packages:
                    self.window.update_info_data["status"]["aur"]["packages"] = result.packages
            else:
                self.window.update_info_data["status"]["aur"]["current"] = True
                self.window.update_info_data["status"]["aur"]["found"] = 0
        elif component == "cursor":
            self.window.update_info_data["status"]["cursor"]["current_version"] = result.current_version or ""
            self.window.update_info_data["status"]["cursor"]["available_version"] = result.available_version or ""
            self.window.update_info_data["status"]["cursor"]["update_available"] = result.has_update
            if result.available_version and result.current_version:
                self.window.update_info_data["status"]["cursor"]["version"] = f"{result.current_version} → {result.available_version}"
            else:
                self.window.update_info_data["status"]["cursor"]["version"] = result.current_version or ""
        elif component == "adguard":
            self.window.update_info_data["status"]["adguard"]["current_version"] = result.current_version or ""
            self.window.update_info_data["status"]["adguard"]["available_version"] = result.available_version or ""
            self.window.update_info_data["status"]["adguard"]["update_available"] = result.has_update
            if result.available_version and result.current_version:
                self.window.update_info_data["status"]["adguard"]["version"] = f"{result.current_version} → {result.available_version}"
            else:
                self.window.update_info_data["status"]["adguard"]["version"] = result.current_version or ""
        elif component == "flatpak":
            if result.has_update:
                self.window.update_info_data["status"]["flatpak"]["found"] = result.package_count
                self.window.update_info_data["status"]["flatpak"]["current"] = False
                if result.packages:
                    self.window.update_info_data["status"]["flatpak"]["packages"] = result.packages
            else:
                self.window.update_info_data["status"]["flatpak"]["current"] = True
                self.window.update_info_data["status"]["flatpak"]["found"] = 0
        elif component == "proton_ge":
            self.window.update_info_data["status"]["proton_ge"]["current_version"] = result.current_version or ""
            self.window.update_info_data["status"]["proton_ge"]["available_version"] = result.available_version or ""
            self.window.update_info_data["status"]["proton_ge"]["update_available"] = result.has_update
            if result.available_version and result.current_version:
                self.window.update_info_data["status"]["proton_ge"]["version"] = f"{result.current_version} → {result.available_version}"
            else:
                self.window.update_info_data["status"]["proton_ge"]["version"] = result.current_version or ""
        
        # Update display immediately
        self.window.update_info_display()

    def _check_updates_with_wrapper(self) -> None:
        """Check updates using BashWrapper (fast, direct function calls)"""
        try:
            from ..utils import BashWrapper
        except ImportError:
            self.logger.warning("BashWrapper not available, falling back to subprocess")
            self._check_updates_with_subprocess()
            return

        try:
            # Clear output - NUR stdout/stderr von externen Prozessen wird angezeigt
            self.window.output_text.clear()
            self.window.progress_bar.setValue(0)
            self.window.progress_bar.setVisible(True)
            if hasattr(self.window, "status_label"):
                self.window.status_label.setText(t("gui_checking", "Checking..."))
                self.window.status_label.setVisible(True)

            # Create wrapper with error handling
            try:
                wrapper = BashWrapper(str(self.window.script_dir))
            except Exception as e:
                self.logger.error(f"Failed to create BashWrapper: {e}")
                # Fallback to subprocess
                self._check_updates_with_subprocess()
                return

            # Check all components with error handling
            try:
                results = wrapper.check_all_updates()
            except Exception as e:
                self.logger.error(f"Failed to check updates with BashWrapper: {e}")
                # Fallback to subprocess
                self._check_updates_with_subprocess()
                return

            # Update UI with results
            try:
                self._update_info_from_wrapper_results(results)
            except Exception as e:
                self.logger.error(f"Failed to update UI from wrapper results: {e}")
                # Continue anyway - show what we have

            # Output text is filled by on_output_received() during live execution
            # NUR stdout/stderr von externen Prozessen wird angezeigt
            # KEINE eigenen Meldungen in die Konsolen-Ausgabe

            # Reset UI
            self.window.progress_bar.setValue(100)
            if hasattr(self.window, "status_label"):
                self.window.status_label.setText(t("gui_ready", "Ready"))
        except Exception as e:
            # Any other error - fallback to subprocess
            self.logger.error(f"Unexpected error in _check_updates_with_wrapper: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            self._check_updates_with_subprocess()

    def _check_updates_with_subprocess(self) -> None:
        """Check updates using subprocess (original method, full script execution)"""
        # Check if update-all.sh exists
        script_path = self.window.script_dir / "update-all.sh"
        if not script_path.exists():
            QMessageBox.critical(
                self.window,
                t("gui_error", "Error"),
                t(
                    "gui_script_not_found", "update-all.sh not found in:\n{script_dir}"
                ).format(script_dir=self.window.script_dir),
            )
            return

        # Start update runner in dry-run mode
        try:
            # Create or reuse UpdateRunner
            if self.window.update_runner is None:
                # Create UpdateRunner as child of MainWindow to ensure proper Qt lifecycle
                self.window.update_runner = UpdateRunner(
                    str(self.window.script_dir), self.window.config, parent=self.window
                )
                self.window.update_runner.output_received.connect(
                    self.window.on_output_received
                )
                self.window.update_runner.progress_update.connect(
                    self.window.on_progress_update
                )
                self.window.update_runner.error_occurred.connect(
                    self.window.on_error_occurred
                )
                self.window.update_runner.finished.connect(
                    self.window.on_update_finished
                )
            else:
                # Reuse existing runner - stop process if running
                if (
                    hasattr(self.window.update_runner, "process")
                    and self.window.update_runner.process
                ):
                    if (
                        self.window.update_runner.process.state()
                        != QProcess.ProcessState.NotRunning
                    ):
                        self.window.update_runner.process.kill()
                        self.window.update_runner.process.waitForFinished(1000)

            # Clear output - NUR stdout/stderr von externen Prozessen wird angezeigt
            # Output will be filled by on_output_received() during live execution
            self.window.output_text.clear()
            self.window.progress_bar.setValue(0)
            self.window.progress_bar.setVisible(True)
            if hasattr(self.window, "status_label"):
                self.window.status_label.setText("0%")
                self.window.status_label.setVisible(True)

            # Start in dry-run mode (no sudo password needed for dry-run)
            self.window._last_was_dry_run = True  # Mark as dry-run
            self.window.update_runner.start_update(
                dry_run=True, interactive=False, sudo_password=None
            )

            # Update UI
            self.window.is_updating = True
            self.window.btn_check.setEnabled(False)
            self.window.btn_start.setEnabled(False)
            if hasattr(self.window, "btn_stop"):
                self.window.btn_stop.setEnabled(True)
                self.window.btn_stop.setVisible(True)

        except Exception as e:
            QMessageBox.critical(
                self.window,
                t("gui_error", "Error"),
                t(
                    "gui_update_error",
                    "Error during update:\n\n{error}\n\nPlease update manually via git pull.",
                ).format(error=str(e)),
            )

    def _update_info_from_wrapper_results(
        self, results: Dict[str, UpdateCheckResult]
    ) -> None:
        """Update update_info_data from BashWrapper results"""
        # Reset update info data
        self.window.update_info_data = {
            "planned": {
                "system": self.window.check_system.isChecked(),
                "aur": self.window.check_aur.isChecked(),
                "cursor": self.window.check_cursor.isChecked(),
                "adguard": self.window.check_adguard.isChecked(),
                "flatpak": self.window.check_flatpak.isChecked(),
                "proton_ge": self.window.check_proton_ge.isChecked() if hasattr(self.window, "check_proton_ge") else False,
            },
            "status": {
                "system": {"found": 0, "current": False, "packages": []},
                "aur": {"found": 0, "current": False, "packages": []},
                "cursor": {
                    "current_version": "",
                    "available_version": "",
                    "version": "",
                    "update_available": False,
                },
                "adguard": {
                    "current_version": "",
                    "available_version": "",
                    "version": "",
                    "update_available": False,
                },
                "flatpak": {"found": 0, "current": False, "packages": []},
                "proton_ge": {
                    "current_version": "",
                    "available_version": "",
                    "version": "",
                    "update_available": False,
                },
            },
            "summary": {"total_packages": 0, "components_updated": []},
        }

        # Update from results
        for component, result in results.items():
            if component == "system":
                if result.has_update:
                    self.window.update_info_data["status"]["system"]["found"] = (
                        result.package_count
                    )
                    self.window.update_info_data["status"]["system"]["current"] = False
                    # Store package names if available
                    if result.packages:
                        self.window.update_info_data["status"]["system"]["packages"] = result.packages
                    else:
                        self.window.update_info_data["status"]["system"]["packages"] = []
                else:
                    self.window.update_info_data["status"]["system"]["current"] = True
                    self.window.update_info_data["status"]["system"]["found"] = 0
                    self.window.update_info_data["status"]["system"]["packages"] = []
            elif component == "aur":
                if result.has_update:
                    self.window.update_info_data["status"]["aur"]["found"] = (
                        result.package_count
                    )
                    self.window.update_info_data["status"]["aur"]["current"] = False
                    # Store package names if available
                    if result.packages:
                        self.window.update_info_data["status"]["aur"]["packages"] = result.packages
                    else:
                        self.window.update_info_data["status"]["aur"]["packages"] = []
                else:
                    self.window.update_info_data["status"]["aur"]["current"] = True
                    self.window.update_info_data["status"]["aur"]["found"] = 0
                    self.window.update_info_data["status"]["aur"]["packages"] = []
            elif component == "cursor":
                self.window.update_info_data["status"]["cursor"]["current_version"] = (
                    result.current_version or ""
                )
                self.window.update_info_data["status"]["cursor"]["available_version"] = (
                    result.available_version or ""
                )
                self.window.update_info_data["status"]["cursor"]["update_available"] = (
                    result.has_update
                )
                # Keep version string for backward compatibility
                if result.available_version and result.current_version:
                    self.window.update_info_data["status"]["cursor"]["version"] = (
                        f"{result.current_version} → {result.available_version}"
                    )
                else:
                    self.window.update_info_data["status"]["cursor"]["version"] = (
                        result.current_version or ""
                    )
            elif component == "adguard":
                self.window.update_info_data["status"]["adguard"]["current_version"] = (
                    result.current_version or ""
                )
                self.window.update_info_data["status"]["adguard"]["available_version"] = (
                    result.available_version or ""
                )
                self.window.update_info_data["status"]["adguard"][
                    "update_available"
                ] = result.has_update
                # Keep version string for backward compatibility
                if result.available_version and result.current_version:
                    self.window.update_info_data["status"]["adguard"]["version"] = (
                        f"{result.current_version} → {result.available_version}"
                    )
                else:
                    self.window.update_info_data["status"]["adguard"]["version"] = (
                        result.current_version or ""
                    )
            elif component == "flatpak":
                if result.has_update:
                    self.window.update_info_data["status"]["flatpak"]["found"] = (
                        result.package_count
                    )
                    self.window.update_info_data["status"]["flatpak"]["current"] = False
                    # Store package names if available
                    if result.packages:
                        self.window.update_info_data["status"]["flatpak"]["packages"] = result.packages
                    else:
                        self.window.update_info_data["status"]["flatpak"]["packages"] = []
                else:
                    self.window.update_info_data["status"]["flatpak"]["current"] = True
                    self.window.update_info_data["status"]["flatpak"]["found"] = 0
                    self.window.update_info_data["status"]["flatpak"]["packages"] = []
            elif component == "proton_ge":
                self.window.update_info_data["status"]["proton_ge"]["current_version"] = (
                    result.current_version or ""
                )
                self.window.update_info_data["status"]["proton_ge"]["available_version"] = (
                    result.available_version or ""
                )
                self.window.update_info_data["status"]["proton_ge"]["update_available"] = (
                    result.has_update
                )
                # Keep version string for backward compatibility
                if result.available_version and result.current_version:
                    self.window.update_info_data["status"]["proton_ge"]["version"] = (
                        f"{result.current_version} → {result.available_version}"
                    )
                else:
                    self.window.update_info_data["status"]["proton_ge"]["version"] = (
                        result.current_version or ""
                    )

        # Calculate total packages
        total = 0
        total += self.window.update_info_data["status"]["system"]["found"]
        total += self.window.update_info_data["status"]["aur"]["found"]
        total += self.window.update_info_data["status"]["flatpak"]["found"]
        if self.window.update_info_data["status"]["cursor"]["update_available"]:
            total += 1
        if self.window.update_info_data["status"]["adguard"]["update_available"]:
            total += 1
        if self.window.update_info_data["status"]["proton_ge"]["update_available"]:
            total += 1
        self.window.update_info_data["summary"]["total_packages"] = total

        # Update display
        self.window.update_info_display()
        
        # Show update confirmation dialog if updates are available
        total_updates = self.window.update_info_data["summary"]["total_packages"]
        if total_updates > 0:
            try:
                from ..dialogs import UpdateConfirmationDialog
                dialog = UpdateConfirmationDialog(self.window)
                result = dialog.exec()
                if result == QDialog.DialogCode.Accepted:
                    # User wants to update - start updates
                    self.start_updates(skip_confirmation=True)
            except Exception as e:
                self.logger.error(f"Failed to show update confirmation dialog: {e}")

    def start_updates(self, skip_confirmation: bool = False) -> None:
        """Start the update process

        Args:
            skip_confirmation: If True, skip the confirmation dialog (used when called after dry-run)
        """
        self.logger.info("=" * 80)
        self.logger.info(
            f"start_updates CALLED: skip_confirmation={skip_confirmation}, is_updating={self.window.is_updating}"
        )
        if self.window.is_updating:
            QMessageBox.warning(
                self.window,
                t("gui_update_failed", "Update Failed"),
                t(
                    "gui_update_already_running",
                    "Another update is already in progress.\n\nPlease wait for it to complete.",
                ),
            )
            return

        # Check if update-all.sh exists
        script_path = self.window.script_dir / "update-all.sh"
        if not script_path.exists():
            QMessageBox.critical(
                self.window,
                t("gui_error", "Error"),
                t(
                    "gui_script_not_found", "update-all.sh not found in:\n{script_dir}"
                ).format(script_dir=self.window.script_dir),
            )
            return

        # Show confirmation dialog if not called after dry-run (skip_confirmation=False)
        if not skip_confirmation:
            try:
                self.logger.debug(
                    "start_updates: Showing UpdateConfirmationDialog (skip_confirmation=False)"
                )
            except Exception:
                pass
            try:
                dialog = UpdateConfirmationDialog(self.window)
                result = dialog.exec()
                try:
                    self.logger.debug(
                        f"start_updates: Dialog result={result}, Accepted={QDialog.DialogCode.Accepted}"
                    )
                except Exception:
                    pass
                if result != QDialog.DialogCode.Accepted:
                    try:
                        self.logger.debug(
                            "start_updates: User rejected or closed dialog, returning"
                        )
                    except Exception:
                        pass
                    return
            except Exception as e:
                try:
                    self.logger.error(f"start_updates: Error showing dialog: {e}")
                except Exception:
                    pass
                raise
        else:
            try:
                self.logger.debug(
                    "start_updates: Skipping confirmation dialog (skip_confirmation=True)"
                )
            except Exception:
                pass

        # Ask for sudo password if needed
        sudo_dialog = SudoDialog(self.window)
        if sudo_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        sudo_password = sudo_dialog.get_password()
        if not sudo_password:
            return

        # Start update runner
        try:
            from PyQt6.QtCore import QProcess

            # Create or reuse UpdateRunner
            if self.window.update_runner is None:
                # Create UpdateRunner as child of MainWindow to ensure proper Qt lifecycle
                self.window.update_runner = UpdateRunner(
                    str(self.window.script_dir), self.window.config, parent=self.window
                )
                self.window.update_runner.output_received.connect(
                    self.window.on_output_received
                )
                self.window.update_runner.progress_update.connect(
                    self.window.on_progress_update
                )
                self.window.update_runner.error_occurred.connect(
                    self.window.on_error_occurred
                )
                self.window.update_runner.finished.connect(
                    self.window.on_update_finished
                )
            else:
                # Reuse existing runner - stop process if running
                if (
                    hasattr(self.window.update_runner, "process")
                    and self.window.update_runner.process
                ):
                    if (
                        self.window.update_runner.process.state()
                        != QProcess.ProcessState.NotRunning
                    ):
                        self.window.update_runner.process.kill()
                        self.window.update_runner.process.waitForFinished(1000)

            # Clear output - NUR stdout/stderr von externen Prozessen wird angezeigt
            self.window.output_text.clear()
            self.window.progress_bar.setValue(0)
            self.window.progress_bar.setVisible(True)
            if hasattr(self.window, "status_label"):
                self.window.status_label.setText("0%")
                self.window.status_label.setVisible(True)

            # Start update
            self.window._last_was_dry_run = False  # Mark as real update
            self.window.update_runner.start_update(
                dry_run=False, interactive=False, sudo_password=sudo_password
            )

            # Update UI
            self.window.is_updating = True
            self.window.btn_check.setEnabled(False)
            self.window.btn_start.setEnabled(False)
            if hasattr(self.window, "btn_stop"):
                self.window.btn_stop.setEnabled(True)
                self.window.btn_stop.setVisible(True)

        except Exception as e:
            QMessageBox.critical(
                self.window,
                t("gui_error", "Error"),
                t(
                    "gui_update_error",
                    "Error during update:\n\n{error}\n\nPlease update manually via git pull.",
                ).format(error=str(e)),
            )

    def stop_updates(self) -> None:
        """Stop the running update process"""
        if self.window.update_runner and self.window.update_runner.process:
            self.window.update_runner.process.kill()
            self.window.update_runner.process.waitForFinished(1000)
            # KEINE eigenen Meldungen in die Konsolen-Ausgabe - NUR stdout/stderr

        # Reset UI
        self.window.is_updating = False
        self.window.btn_check.setEnabled(True)
        self.window.btn_start.setEnabled(True)
        if hasattr(self.window, "btn_stop"):
            self.window.btn_stop.setEnabled(False)
            self.window.btn_stop.setVisible(False)

    def parse_update_output(self, text: str) -> None:
        """Parse update output - DEPRECATED: Update-Info wird nur über explizite Events befüllt
        
        Diese Methode wird nicht mehr verwendet. Update-Info wird nur über explizite Events
        befüllt (BashWrapper), nicht aus der Konsolen-Ausgabe.
        """
        # Keine Parsing-Logik mehr - Update-Info wird nur über explizite Events befüllt
        pass
        # Reset planned components at start
        if (
            "VERFÜGBARE UPDATES WERDEN GEPRÜFT" in text
            or "CHECKING FOR AVAILABLE UPDATES" in text
            or "Prüfe auf Updates" in text
            or "checking_updates" in text
        ):
            self.window.update_info_data["planned"] = {
                "system": self.window.check_system.isChecked(),
                "aur": self.window.check_aur.isChecked(),
                "cursor": self.window.check_cursor.isChecked(),
                "adguard": self.window.check_adguard.isChecked(),
                "flatpak": self.window.check_flatpak.isChecked(),
                "proton_ge": self.window.check_proton_ge.isChecked() if hasattr(self.window, "check_proton_ge") else False,
            }
            # Reset status to "Prüfe..." for all components
            for component in ["system", "aur", "cursor", "adguard", "flatpak", "proton_ge"]:
                if component in self.window.update_info_data["status"]:
                    self.window.update_info_data["status"][component]["current"] = None
                    self.window.update_info_data["status"][component]["found"] = 0
                    if "packages" in self.window.update_info_data["status"][component]:
                        self.window.update_info_data["status"][component]["packages"] = []
            self.window.update_info_display()

        # System updates - parse from formatted output AND extract package names from console output
        if re.search(r"📦.*System.*pacman", text, re.IGNORECASE):
            match = re.search(r"✓\s+(\d+)\s+Pakete?\s+verfügbar", text, re.IGNORECASE)
            if match:
                self.window.update_info_data["status"]["system"]["found"] = int(
                    match.group(1)
                )
                self.window.update_info_data["status"]["system"]["current"] = False
                # Update display immediately
                self.window.update_info_display()
            elif re.search(r"○.*aktuell", text, re.IGNORECASE):
                self.window.update_info_data["status"]["system"]["current"] = True
                self.window.update_info_data["status"]["system"]["found"] = 0
                # Update display immediately
                self.window.update_info_display()
        
        # Extract package names from pacman output (format: "package-name old-version -> new-version")
        # This is the REAL console output from pacman -Qu or checkupdates
        # Format: "package-name old-version -> new-version" (can have leading whitespace)
        # Must NOT be a formatted line with emojis
        if not re.search(r"[📦🔧🖱️🛡️📱🎮✅⏱️🔍🔄▸✓○🚀]", text):
            # Match: package-name version -> version (with optional leading whitespace)
            pacman_package_match = re.search(r"^\s*([a-zA-Z0-9@._+-]+)\s+([0-9.]+[a-zA-Z0-9._-]*)\s*->\s*([0-9.]+[a-zA-Z0-9._-]*)", text)
            if pacman_package_match:
                package_name = pacman_package_match.group(1)
                if "packages" not in self.window.update_info_data["status"]["system"]:
                    self.window.update_info_data["status"]["system"]["packages"] = []
                if package_name not in self.window.update_info_data["status"]["system"]["packages"]:
                    self.window.update_info_data["status"]["system"]["packages"].append(package_name)
                    self.window.update_info_data["status"]["system"]["found"] = len(self.window.update_info_data["status"]["system"]["packages"])
                    self.window.update_info_data["status"]["system"]["current"] = False
                    # Update display immediately when we find a package
                    self.window.update_info_display()

        # AUR updates - parse from formatted output AND extract package names from console output
        if re.search(r"🔧.*AUR", text, re.IGNORECASE):
            match = re.search(r"✓\s+(\d+)\s+Pakete?\s+verfügbar", text, re.IGNORECASE)
            if match:
                self.window.update_info_data["status"]["aur"]["found"] = int(
                    match.group(1)
                )
                self.window.update_info_data["status"]["aur"]["current"] = False
                # Update display immediately
                self.window.update_info_display()
            elif re.search(r"○.*aktuell", text, re.IGNORECASE):
                self.window.update_info_data["status"]["aur"]["current"] = True
                self.window.update_info_data["status"]["aur"]["found"] = 0
                # Update display immediately
                self.window.update_info_display()
        
        # Extract package names from AUR output (format: "aur/package-name old-version -> new-version")
        # This is the REAL console output from yay -Qua or paru -Qua
        # Format: "aur/package-name old-version -> new-version" or "community/package-name old-version -> new-version"
        # Must NOT be a formatted line with emojis
        if not re.search(r"[📦🔧🖱️🛡️📱🎮✅⏱️🔍🔄▸✓○🚀]", text):
            # Match: aur/package-name or community/package-name, then version -> version
            aur_package_match = re.search(r"^\s*(aur/|community/)?([a-zA-Z0-9@._+-]+)\s+([0-9.]+[a-zA-Z0-9._-]*)\s*->\s*([0-9.]+[a-zA-Z0-9._-]*)", text)
            if aur_package_match:
                # Extract package name (group 2 is the package name after aur/ or community/)
                package_name = aur_package_match.group(2)
                if not package_name:
                    # Fallback: extract from full match
                    full_match = aur_package_match.group(0)
                    package_name = full_match.split()[0].replace("aur/", "").replace("community/", "")
                if "packages" not in self.window.update_info_data["status"]["aur"]:
                    self.window.update_info_data["status"]["aur"]["packages"] = []
                if package_name and package_name not in self.window.update_info_data["status"]["aur"]["packages"]:
                    self.window.update_info_data["status"]["aur"]["packages"].append(package_name)
                    self.window.update_info_data["status"]["aur"]["found"] = len(self.window.update_info_data["status"]["aur"]["packages"])
                    self.window.update_info_data["status"]["aur"]["current"] = False
                    # Update display immediately when we find a package
                    self.window.update_info_display()

        # Cursor updates - parse from formatted output
        if re.search(r"🖱️.*Cursor", text, re.IGNORECASE):
            match = re.search(
                r"✓.*Update verfügbar:\s+v?([0-9.]+)\s+→\s+v?([0-9.]+)",
                text,
                re.IGNORECASE,
            )
            if match:
                current = match.group(1)
                available = match.group(2)
                self.window.update_info_data["status"]["cursor"]["current_version"] = current
                self.window.update_info_data["status"]["cursor"]["available_version"] = available
                self.window.update_info_data["status"]["cursor"]["version"] = (
                    f"{current} → {available}"
                )
                self.window.update_info_data["status"]["cursor"]["update_available"] = True
                # Update display immediately
                self.window.update_info_display()
            elif re.search(r"○.*aktuell.*v?([0-9.]+)", text, re.IGNORECASE):
                version_match = re.search(r"v?([0-9.]+)", text)
                if version_match:
                    current = version_match.group(1)
                    self.window.update_info_data["status"]["cursor"]["current_version"] = current
                    self.window.update_info_data["status"]["cursor"]["available_version"] = ""
                    self.window.update_info_data["status"]["cursor"]["version"] = current
                self.window.update_info_data["status"]["cursor"]["update_available"] = False
                # Update display immediately
                self.window.update_info_display()

        # AdGuard updates - parse from formatted output
        if re.search(r"🛡️.*AdGuard", text, re.IGNORECASE):
            match = re.search(
                r"✓.*Update verfügbar:\s+v?([0-9.]+)\s+→\s+v?([0-9.]+)",
                text,
                re.IGNORECASE,
            )
            if match:
                current = match.group(1)
                available = match.group(2)
                self.window.update_info_data["status"]["adguard"]["current_version"] = current
                self.window.update_info_data["status"]["adguard"]["available_version"] = available
                self.window.update_info_data["status"]["adguard"]["version"] = (
                    f"{current} → {available}"
                )
                self.window.update_info_data["status"]["adguard"]["update_available"] = True
                # Update display immediately
                self.window.update_info_display()
            elif re.search(r"○.*aktuell.*v?([0-9.]+)", text, re.IGNORECASE):
                version_match = re.search(r"v?([0-9.]+)", text)
                if version_match:
                    current = version_match.group(1)
                    self.window.update_info_data["status"]["adguard"]["current_version"] = current
                    self.window.update_info_data["status"]["adguard"]["available_version"] = ""
                    self.window.update_info_data["status"]["adguard"]["version"] = current
                self.window.update_info_data["status"]["adguard"]["update_available"] = False
                # Update display immediately
                self.window.update_info_display()

        # Flatpak updates - parse from formatted output AND extract package names from console output
        if re.search(r"📱.*Flatpak", text, re.IGNORECASE):
            match = re.search(r"✓\s+(\d+)\s+Pakete?\s+verfügbar", text, re.IGNORECASE)
            if match:
                self.window.update_info_data["status"]["flatpak"]["found"] = int(
                    match.group(1)
                )
                self.window.update_info_data["status"]["flatpak"]["current"] = False
                # Update display immediately
                self.window.update_info_display()
            elif re.search(r"○.*aktuell", text, re.IGNORECASE):
                self.window.update_info_data["status"]["flatpak"]["current"] = True
                self.window.update_info_data["status"]["flatpak"]["found"] = 0
                # Update display immediately
                self.window.update_info_display()
        
        # Extract package names from Flatpak output (format: "app-id old-version new-version branch arch")
        # This is the REAL console output from flatpak remote-ls --updates
        # Format: "app-id    old-version    new-version    branch    arch" (can have leading whitespace)
        # Must NOT be a formatted line with emojis
        if not re.search(r"[📦🔧🖱️🛡️📱🎮✅⏱️🔍🔄▸✓○🚀]", text):
            # Flatpak format: "app-id    old-version    new-version    branch    arch"
            flatpak_package_match = re.search(r"^\s*([a-zA-Z0-9.@_-]+)\s+([0-9.]+[a-zA-Z0-9._-]*)\s+([0-9.]+[a-zA-Z0-9._-]*)\s+(\w+)\s+(\w+)", text)
            if flatpak_package_match:
                app_id = flatpak_package_match.group(1)
                if "packages" not in self.window.update_info_data["status"]["flatpak"]:
                    self.window.update_info_data["status"]["flatpak"]["packages"] = []
                if app_id and app_id not in self.window.update_info_data["status"]["flatpak"]["packages"]:
                    self.window.update_info_data["status"]["flatpak"]["packages"].append(app_id)
                    self.window.update_info_data["status"]["flatpak"]["found"] = len(self.window.update_info_data["status"]["flatpak"]["packages"])
                    self.window.update_info_data["status"]["flatpak"]["current"] = False
                    # Update display immediately when we find a package
                    self.window.update_info_display()

        # Summary
        match = re.search(
            r"✓.*Updates gefunden:\s+(\d+)\s+Pakete?", text, re.IGNORECASE
        )
        if match:
            self.window.update_info_data["summary"]["total_packages"] = int(
                match.group(1)
            )
            # Update display immediately
            self.window.update_info_display()
        
        # Proton-GE updates - parse from formatted output
        if re.search(r"🎮.*Proton", text, re.IGNORECASE):
            match = re.search(
                r"✓.*Update verfügbar:\s+v?([0-9.]+)\s+→\s+v?([0-9.]+)",
                text,
                re.IGNORECASE,
            )
            if match:
                current = match.group(1)
                available = match.group(2)
                self.window.update_info_data["status"]["proton_ge"]["current_version"] = current
                self.window.update_info_data["status"]["proton_ge"]["available_version"] = available
                self.window.update_info_data["status"]["proton_ge"]["version"] = (
                    f"{current} → {available}"
                )
                self.window.update_info_data["status"]["proton_ge"]["update_available"] = True
                # Update display immediately
                self.window.update_info_display()
            elif re.search(r"○.*aktuell.*v?([0-9.]+)", text, re.IGNORECASE):
                version_match = re.search(r"v?([0-9.]+)", text)
                if version_match:
                    current = version_match.group(1)
                    self.window.update_info_data["status"]["proton_ge"]["current_version"] = current
                    self.window.update_info_data["status"]["proton_ge"]["available_version"] = ""
                    self.window.update_info_data["status"]["proton_ge"]["version"] = current
                self.window.update_info_data["status"]["proton_ge"]["update_available"] = False
                # Update display immediately
                self.window.update_info_display()
