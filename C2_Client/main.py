# C2_Client/main.py
import sys
import psutil
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QStatusBar, 
                             QMessageBox, QWidget, QVBoxLayout)
from PyQt6.QtCore import QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, Qt
from PyQt6.QtGui import QColor, QPainter

# Import your custom modules
import updater
from ui.login_screen import WelcomePage, LoginPage, CreateAccountPage
from ui.loading_screen import LoadingScreen
from ui.splash_screen import SplashScreen
from ui.dashboard_window import DashboardWindow
from ui.session_view import SessionView
from builder import build_payload
from config import RELAY_URL_FORMAT
from themes import ThemeManager
from api_client import ApiClient

# --- STABLE ANIMATION WIDGET ---
class FadeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVisible(False)
        self.color = QColor(0, 0, 0, 0)

    def set_color(self, color):
        self.color = color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)

class LocalSettingsManager:
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
    log_message = pyqtSignal(str)
    finished = pyqtSignal()
    def __init__(self, settings, relay_url, c2_user):
        super().__init__()
        self.settings, self.relay_url, self.c2_user = settings, relay_url, c2_user
        self.proc = None; self._is_running = True
    def run(self):
        build_payload(self.settings, self.relay_url, self.c2_user, self.log_message.emit, self)
        self.finished.emit()
    def stop(self):
        self._is_running = False
        if self.proc and self.proc.poll() is None:
            try:
                parent = psutil.Process(self.proc.pid)
                for child in parent.children(recursive=True): child.terminate()
                self.proc.terminate(); self.log_message.emit("\n[INFO] Build process termination signal sent.")
                self.proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.subprocess.TimeoutExpired, Exception):
                if self.proc.poll() is None: self.proc.kill()
        self.finished.emit()

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
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0,0,0,0)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # --- Screen Setup ---
        self.loading_screen = LoadingScreen()
        self.welcome_page = WelcomePage()
        self.login_page = LoginPage(self.api, self.db)
        self.create_account_page = CreateAccountPage(self.api)
        self.stack.addWidget(self.loading_screen)
        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.create_account_page)
        
        self.dashboard_view = None
        self.session_view = None

        # --- Stable Animation Setup ---
        self.fade_overlay = FadeOverlay(self.central_widget)
        self.fade_animation = QPropertyAnimation(self, b"fade_color")
        self.fade_animation.setDuration(300)

        # --- Connect Signals ---
        self.welcome_page.login_requested.connect(lambda: self.fade_to_widget(self.login_page))
        self.welcome_page.create_requested.connect(lambda: self.fade_to_widget(self.create_account_page))
        self.login_page.create_account_requested.connect(lambda: self.fade_to_widget(self.create_account_page))
        self.login_page.welcome_requested.connect(lambda: self.fade_to_widget(self.welcome_page))
        self.create_account_page.login_requested.connect(lambda: self.fade_to_widget(self.login_page))
        self.create_account_page.welcome_requested.connect(lambda: self.fade_to_widget(self.welcome_page))
        self.login_page.login_successful.connect(self.show_dashboard_view)
        
        saved_theme = self.db.load_setting("theme", "Dark (Default)")
        self.apply_theme(saved_theme)

    def get_fade_color(self):
        return self.fade_overlay.color
    def set_fade_color(self, color):
        self.fade_overlay.color = color
        self.fade_overlay.update()
    fade_color = pyqtProperty(QColor, get_fade_color, set_fade_color)
    
    def resizeEvent(self, event):
        self.fade_overlay.resize(self.size())
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # --- Start the connecting/login phase after the main window appears ---
        self.stack.setCurrentWidget(self.loading_screen)
        # Give the "Connecting..." screen some time to be visible before auto-login
        QTimer.singleShot(2000, self.attempt_auto_login)

    def attempt_auto_login(self):
        """Attempts to log in with saved credentials."""
        creds = self.db.load_setting("auto_login_credentials")
        if creds and "username" in creds and "password" in creds:
            self.statusBar().showMessage("Auto-logging in...")
            response = self.api.login(creds["username"], creds["password"])
            if response and response.get("success"):
                self.show_dashboard_view(response.get("username"), response.get("assigned_line"), animate=True)
                return
        
        # If auto-login fails, fade to the welcome page
        self.fade_to_widget(self.welcome_page)

    def fade_to_widget(self, new_widget):
        if self.stack.currentWidget() == new_widget: return
        self.fade_overlay.setVisible(True)
        self.fade_overlay.raise_()
        self.fade_animation.stop()
        self.fade_animation.setStartValue(QColor(0, 0, 0, 0))
        self.fade_animation.setEndValue(QColor(0, 0, 0, 255))
        
        def on_fade_out_finished():
            self.stack.setCurrentWidget(new_widget)
            self.fade_animation.setStartValue(QColor(0, 0, 0, 255))
            self.fade_animation.setEndValue(QColor(0, 0, 0, 0))
            self.fade_animation.start()
            self.fade_animation.finished.connect(lambda: self.fade_overlay.setVisible(False))

        try: self.fade_animation.finished.disconnect() 
        except TypeError: pass
        self.fade_animation.finished.connect(on_fade_out_finished)
        self.fade_animation.start()

    def apply_theme(self, theme_name):
        stylesheet = self.theme_manager.get_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        if self.dashboard_view: self.dashboard_view.setStyleSheet(stylesheet)
        if self.session_view: self.session_view.setStyleSheet(stylesheet)

    def show_dashboard_view(self, username, assigned_line, animate=True):
        self.current_user = username
        self.api.set_line(assigned_line)
        
        if not self.dashboard_view:
            self.dashboard_view = DashboardWindow(self.api, self.db, self.current_user)
            self.session_view = SessionView(self.db)
            self.stack.addWidget(self.dashboard_view)
            self.stack.addWidget(self.session_view)
            
            self.dashboard_view.sign_out_requested.connect(self.handle_sign_out)
            self.dashboard_view.setting_changed.connect(self.handle_setting_changed)
            self.dashboard_view.build_requested.connect(self.start_build)
            self.dashboard_view.session_interact_requested.connect(self.open_session_view)
            self.session_view.back_requested.connect(lambda: self.fade_to_widget(self.dashboard_view))
            self.session_view.task_requested.connect(self.dashboard_view.send_task_from_session)
            self.dashboard_view.data_updated_for_session.connect(self.session_view.handle_command_response)

        if animate:
            self.fade_to_widget(self.dashboard_view)
        else:
            self.stack.setCurrentWidget(self.dashboard_view)
            
        self.statusBar().showMessage(f"Logged in as {username}. Using Line #{assigned_line}", 4000)

    def open_session_view(self, session_id, session_data, status):
        self.session_view.load_session(session_id, session_data, status)
        self.fade_to_widget(self.session_view)
        
    def handle_setting_changed(self, key, value):
        self.db.save_setting(key, value)
        if key == "theme": self.apply_theme(value)

    def start_build(self, settings):
        relay_url_for_build = self.api.base_url
        if not relay_url_for_build:
            QMessageBox.critical(self, "Build Error", "Cannot build payload, API client line not set.")
            return
        self.dashboard_view.builder_pane.show_build_log_pane()
        self.dashboard_view.builder_pane.build_button.setEnabled(False)
        self.build_thread = BuildThread(settings, relay_url_for_build, self.current_user)
        self.build_thread.log_message.connect(self.dashboard_view.builder_pane.build_log_output.append)
        self.build_thread.finished.connect(self.on_build_finished)
        self.build_thread.start()

    def stop_build(self):
        if hasattr(self, 'build_thread') and self.build_thread.isRunning():
            self.build_thread.stop()

    def on_build_finished(self):
        if self.dashboard_view:
            self.dashboard_view.builder_pane.build_button.setEnabled(True)
            self.dashboard_view.builder_pane.stop_build_button.setEnabled(False)
            self.dashboard_view.builder_pane.back_to_builder_button.show()
    
    def handle_sign_out(self):
        if self.dashboard_view:
            self.dashboard_view.stop_polling()
        
        self.db.save_setting("auto_login_credentials", None)
        self.login_page.clear_fields()
        
        self.fade_to_widget(self.welcome_page)
        
        def cleanup_dashboard():
            if self.dashboard_view:
                self.stack.removeWidget(self.dashboard_view); self.dashboard_view.deleteLater(); self.dashboard_view = None
            if self.session_view:
                self.stack.removeWidget(self.session_view); self.session_view.deleteLater(); self.session_view = None
            self.current_user = None; self.api.base_url = None; self.api.line_number = None

        QTimer.singleShot(300, cleanup_dashboard)
        self.statusBar().showMessage("Signed out.", 3000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    if updater.check_for_updates():
        sys.exit(0)
    
    splash = SplashScreen()
    splash.setStyleSheet(ThemeManager.get_stylesheet("Dark (Default)"))
    screen_geometry = app.primaryScreen().geometry()
    splash.move(
        (screen_geometry.width() - splash.width()) // 2,
        (screen_geometry.height() - splash.height()) // 2
    )
    
    splash.show()
    splash.start_animation()
    splash.fade_in()

    window = MainWindow()

    def close_splash_and_show_main():
        splash.fade_out()
        splash.fade_out_animation.finished.connect(lambda: (
            splash.stop_animation(),
            splash.close(),
            window.show()
        ))

    QTimer.singleShot(3000, close_splash_and_show_main)
    
    sys.exit(app.exec())