#!/usr/bin/env python3
"""
CachyOS Multi-Updater - Update Dialog
Dialog for updating the tool itself
"""

from pathlib import Path
import tempfile
import shutil
import zipfile
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QProgressDialog, QMessageBox,
    QFileDialog, QGroupBox, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from urllib.request import urlretrieve

# Handle imports for both direct execution and module import
try:
    from .i18n import t
    from .version_checker import VersionChecker
    from .debug_logger import get_logger
except ImportError:
    from i18n import t
    from version_checker import VersionChecker
    try:
        from debug_logger import get_logger
    except ImportError:
        def get_logger():
            class DummyLogger:
                def debug(self, *args, **kwargs): pass
                def info(self, *args, **kwargs): pass
                def warning(self, *args, **kwargs): pass
                def error(self, *args, **kwargs): pass
                def exception(self, *args, **kwargs): pass
            return DummyLogger()


class UpdateDownloadThread(QThread):
    """Thread for downloading update ZIP"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)  # zip_path, error
    
    def __init__(self, url: str, temp_dir: Path):
        super().__init__()
        self.url = url
        self.temp_dir = temp_dir
        self.zip_path = temp_dir / "update.zip"
    
    def run(self):
        """Download ZIP file"""
        try:
            def report_hook(blocknum, blocksize, totalsize):
                if totalsize > 0:
                    percent = int((blocknum * blocksize * 100) / totalsize)
                    self.progress.emit(min(percent, 100))
            
            urlretrieve(self.url, str(self.zip_path), report_hook)
            self.finished.emit(str(self.zip_path), "")
        except Exception as e:
            self.finished.emit("", str(e))


class UpdateDialog(QDialog):
    """Dialog for updating the tool"""
    
    def __init__(self, script_dir: str, local_version: str, github_version: str, 
                 version_checker: VersionChecker, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.logger.debug(f"UpdateDialog initialized: local={local_version}, github={github_version}")
        self.script_dir = Path(script_dir)
        self.local_version = local_version
        self.github_version = github_version
        self.version_checker = version_checker
        self.root_dir = self.script_dir.parent
        
        self.setWindowTitle(t("gui_update_dialog_title", "Tool Update"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Check if .git exists
        self.has_git = (self.root_dir / ".git").exists()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Version info
        version_group = QGroupBox(t("gui_version_info", "Version Information"))
        version_layout = QVBoxLayout()
        
        local_label = QLabel(f"{t('gui_local_version', 'Local Version')}: v{self.local_version}")
        github_label = QLabel(f"{t('gui_github_version', 'GitHub Version')}: v{self.github_version}")
        
        version_layout.addWidget(local_label)
        version_layout.addWidget(github_label)
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # Update method selection
        method_group = QGroupBox(t("gui_update_method", "Update Method"))
        method_layout = QVBoxLayout()
        
        self.button_group = QButtonGroup()
        
        # Automatic ZIP update (default)
        self.radio_zip = QRadioButton(t("gui_auto_update", "Automatic Update (ZIP Download)"))
        self.radio_zip.setChecked(True)
        self.button_group.addButton(self.radio_zip, 0)
        method_layout.addWidget(self.radio_zip)
        
        # Asset selection (if multiple assets available)
        self.asset_combo = QComboBox()
        self.asset_combo.setVisible(False)
        self.asset_combo.setToolTip(t("gui_select_asset", "Select release asset to download"))
        method_layout.addWidget(self.asset_combo)
        
        # Check for assets when ZIP is selected
        self.radio_zip.toggled.connect(self.on_zip_selected)
        self.on_zip_selected(True)  # Initial check
        
        # Manual file selection
        self.radio_manual = QRadioButton(t("gui_manual_update", "Manual Update (Select ZIP File)"))
        self.button_group.addButton(self.radio_manual, 1)
        method_layout.addWidget(self.radio_manual)
        
        # Git Pull (only if .git exists)
        if self.has_git:
            self.radio_git = QRadioButton(t("gui_git_pull_update", "Git Pull Update"))
            self.button_group.addButton(self.radio_git, 2)
            method_layout.addWidget(self.radio_git)
        else:
            self.radio_git = None
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.update_button = QPushButton(t("gui_start_update", "Start Update"))
        self.update_button.clicked.connect(self.start_update)
        button_layout.addWidget(self.update_button)
        
        self.cancel_button = QPushButton(t("gui_cancel", "Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_zip_selected(self, checked: bool):
        """Handle ZIP radio button selection - check for assets"""
        if not checked:
            self.asset_combo.setVisible(False)
            return
        
        # Check for release assets
        assets = self.version_checker.get_release_assets(self.github_version)
        
        # Filter for ZIP files
        zip_assets = [a for a in assets if a.get('name', '').endswith('.zip')]
        
        if len(zip_assets) > 0:
            # Multiple assets available - show combo box
            self.asset_combo.clear()
            self.asset_combo.addItem(
                t("gui_use_archive", "Use archive (recommended)"),
                None  # None means use archive URL
            )
            for asset in zip_assets:
                asset_name = asset.get('name', 'unknown')
                asset_size = asset.get('size', 0)
                # Format size
                if asset_size > 1024 * 1024:
                    size_str = f"{asset_size / (1024 * 1024):.1f} MB"
                elif asset_size > 1024:
                    size_str = f"{asset_size / 1024:.1f} KB"
                else:
                    size_str = f"{asset_size} B"
                
                display_text = f"{asset_name} ({size_str})"
                self.asset_combo.addItem(display_text, asset.get('browser_download_url'))
            
            self.asset_combo.setVisible(True)
        else:
            # No assets or single asset - hide combo box
            self.asset_combo.setVisible(False)
    
    def start_update(self):
        """Start the update process"""
        selected_id = self.button_group.checkedId()
        
        if selected_id == 0:
            # Automatic ZIP update
            self.perform_zip_update()
        elif selected_id == 1:
            # Manual file selection
            self.perform_manual_update()
        elif selected_id == 2:
            # Git Pull
            self.perform_git_pull_update()
    
    def perform_zip_update(self):
        """Perform automatic ZIP update"""
        # Get ZIP URL - check if asset is selected
        selected_asset_url = self.asset_combo.currentData()
        
        if selected_asset_url:
            # Use selected asset URL
            zip_url = selected_asset_url
        else:
            # Use archive URL (default)
            zip_url = self.version_checker.get_release_zip_url(self.github_version)
        
        # Create progress dialog
        progress = QProgressDialog(
            t("gui_downloading_update", "Downloading update..."),
            t("gui_cancel", "Cancel"),
            0, 100,
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix="cachyos-updater-"))
        zip_file = temp_dir / "update.zip"
        
        try:
            # Download ZIP
            download_thread = UpdateDownloadThread(str(zip_url), temp_dir)
            
            def update_progress(value):
                progress.setValue(value)
            
            def download_finished(zip_path, error):
                progress.close()
                if error:
                    QMessageBox.critical(
                        self,
                        t("gui_update_failed", "Update Failed"),
                        t("gui_download_failed", "Failed to download update:\n\n{error}").format(error=error)
                    )
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return
                
                # Extract and install
                self.install_from_zip(Path(zip_path), temp_dir)
            
            download_thread.progress.connect(update_progress)
            download_thread.finished.connect(download_finished)
            download_thread.start()
            
            # Show progress dialog
            progress.exec()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_error", "Error during update:\n\n{error}").format(error=str(e))
            )
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def perform_manual_update(self):
        """Perform manual update from selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("gui_select_zip_file", "Select ZIP File"),
            "",
            "ZIP Files (*.zip);;All Files (*)"
        )
        
        if not file_path:
            return
        
        zip_path = Path(file_path)
        if not zip_path.exists():
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_file_not_found", "File not found: {path}").format(path=file_path)
            )
            return
        
        # Create temp directory for extraction
        temp_dir = Path(tempfile.mkdtemp(prefix="cachyos-updater-"))
        
        try:
            # Copy ZIP to temp directory
            temp_zip = temp_dir / "update.zip"
            shutil.copy2(zip_path, temp_zip)
            
            # Install from ZIP
            self.install_from_zip(temp_zip, temp_dir)
        except Exception as e:
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_error", "Error during update:\n\n{error}").format(error=str(e))
            )
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def perform_git_pull_update(self):
        """Perform Git Pull update"""
        if not self.has_git:
            QMessageBox.warning(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_git_not_available", "Git repository not found. Cannot perform Git Pull update.")
            )
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            t("gui_git_pull_confirm", "Confirm Git Pull"),
            t("gui_git_pull_warning", "This will reset your local repository to match GitHub.\n\nAny uncommitted changes will be lost.\n\nContinue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create progress dialog
        progress = QProgressDialog(
            t("gui_git_pulling", "Pulling from GitHub..."),
            t("gui_cancel", "Cancel"),
            0, 0,
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        progress.show()
        
        try:
            # Change to root directory
            import os
            old_cwd = os.getcwd()
            os.chdir(self.root_dir)
            
            try:
                # Fetch and reset
                subprocess.run(
                    ["git", "fetch", "origin", "main"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                subprocess.run(
                    ["git", "reset", "--hard", "origin/main"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Update VERSION file
                self._update_version_file()
                
                progress.close()
                
                QMessageBox.information(
                    self,
                    t("gui_update_success", "Update Successful"),
                    t("gui_git_pull_success", "Successfully updated via Git Pull.\n\nPlease restart the application.")
                )
                
                self.accept()
                
            finally:
                os.chdir(old_cwd)
                
        except subprocess.CalledProcessError as e:
            progress.close()
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_git_pull_failed", "Git Pull failed:\n\n{error}").format(error=e.stderr or str(e))
            )
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_error", "Error during update:\n\n{error}").format(error=str(e))
            )
    
    def install_from_zip(self, zip_path: Path, temp_dir: Path):
        """Install update from ZIP file"""
        progress = QProgressDialog(
            t("gui_installing_update", "Installing update..."),
            t("gui_cancel", "Cancel"),
            0, 0,
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        progress.show()
        
        target_dir = self.root_dir / "cachyos-multi-updater"
        backup_dir = None
        
        try:
            # Create backup
            if target_dir.exists():
                backup_dir = self.root_dir / f"cachyos-multi-updater.backup-{int(__import__('time').time())}"
                shutil.copytree(target_dir, backup_dir)
            
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find cachyos-multi-updater directory in extracted files
            extracted_dir = None
            for item in temp_dir.iterdir():
                if item.is_dir() and item.name.startswith("sc-cachyos-multi-updater"):
                    # Check if it contains update-all.sh
                    if (item / "cachyos-multi-updater" / "update-all.sh").exists():
                        extracted_dir = item / "cachyos-multi-updater"
                        break
                    elif (item / "update-all.sh").exists():
                        extracted_dir = item
                        break
            
            if not extracted_dir:
                raise Exception("cachyos-multi-updater directory not found in ZIP")
            
            # Remove old directory
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            # Copy new directory
            shutil.copytree(extracted_dir, target_dir)
            
            # Update VERSION file
            self._update_version_file()
            
            # Cleanup backup
            if backup_dir and backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            progress.close()
            
            QMessageBox.information(
                self,
                t("gui_update_success", "Update Successful"),
                t("gui_update_success_msg", "Script updated successfully!\n\nPlease restart the application to use the new version.")
            )
            
            self.accept()
            
        except Exception as e:
            progress.close()
            
            # Rollback: restore backup
            if backup_dir and backup_dir.exists():
                try:
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(backup_dir, target_dir)
                except Exception:
                    pass
            
            QMessageBox.critical(
                self,
                t("gui_update_failed", "Update Failed"),
                t("gui_update_error", "Error during update:\n\n{error}").format(error=str(e))
            )
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _update_version_file(self):
        """Update VERSION file with GitHub version"""
        version_file = self.root_dir / "VERSION"
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(self.github_version)
        except Exception:
            pass  # Non-critical

