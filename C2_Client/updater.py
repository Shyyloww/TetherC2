# C2_Client/updater.py
import requests
import os
import sys
import shutil
import zipfile
import io
import subprocess
from PyQt6.QtWidgets import QMessageBox

# --- Configuration for the updater ---
GITHUB_REPO = "Shyyloww/TetherC2"
VERSION_FILE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.txt"
RELEASE_ASSET_URL = f"https://github.com/{GITHUB_REPO}/releases/latest/download/TetherC2.zip"
CURRENT_VERSION_FILE = "version.txt"

def get_current_version():
    """Reads the version from the local version.txt file."""
    try:
        with open(CURRENT_VERSION_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def check_for_updates():
    """
    Checks GitHub for a new version and prompts the user to update if available.
    Returns True if an update is performed and a restart is needed.
    """
    current_version = get_current_version()
    print(f"[Updater] Current version: {current_version}")
    
    try:
        response = requests.get(VERSION_FILE_URL, timeout=5)
        response.raise_for_status()
        latest_version = response.text.strip()
        print(f"[Updater] Latest version on GitHub: {latest_version}")
    except requests.RequestException as e:
        print(f"[Updater] Could not check for updates: {e}")
        return False # Fail silently if no internet or repo is down

    if latest_version > current_version:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText("A new version of TetherC2 is available!")
        msg_box.setInformativeText(f"Current Version: {current_version}\nLatest Version:  {latest_version}\n\nDo you want to download and install it now? The application will restart.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            return download_and_apply_update()
            
    return False

def download_and_apply_update():
    """Downloads the release zip and replaces the current application files."""
    try:
        print("[Updater] Downloading latest release from GitHub...")
        response = requests.get(RELEASE_ASSET_URL, timeout=60, stream=True)
        response.raise_for_status()
        
        zip_bytes = io.BytesIO(response.content)
        
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            update_dir = "update_temp"
            if os.path.exists(update_dir):
                shutil.rmtree(update_dir)
            os.makedirs(update_dir)
            zf.extractall(path=update_dir)
        
        script_name = "apply_update.bat" if os.name == 'nt' else "apply_update.sh"
        
        executable_path = sys.executable
        # If running as a frozen exe, the path might need adjustment
        if getattr(sys, 'frozen', False):
            executable_path = sys.argv[0]

        restart_command = f'"{executable_path}"' if ' ' in executable_path else executable_path

        if os.name == 'nt':
            script_content = f"""
@echo off
echo Updating TetherC2... Please wait.
timeout /t 3 /nobreak > nul
xcopy "{update_dir}" "." /E /Y /I /Q
rd /s /q "{update_dir}"
echo Update complete. Restarting application...
start "" {restart_command}
del "{script_name}"
"""
        else: # Linux/macOS
            script_content = f"""
#!/bin/bash
echo "Updating TetherC2... Please wait."
sleep 3
cp -rf "{update_dir}/"* .
rm -rf "{update_dir}"
echo "Update complete. Restarting application..."
( "{restart_command}" & )
rm -- "$0"
"""
        with open(script_name, 'w') as f:
            f.write(script_content)

        if os.name != 'nt':
            os.chmod(script_name, 0o755)

        subprocess.Popen([f"./{script_name}"], shell=True)
        return True # Signal that we need to exit the main application

    except Exception as e:
        QMessageBox.critical(None, "Update Failed", f"An error occurred during the update process:\n{e}")
        return False