# C2_Client/main.py
import sys
import psutil
import json
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget,
                             QMessageBox, QWidget, QVBoxLayout, QLabel)
from PyQt6.QtCore import (QThread, pyqtSignal, QPropertyAnimation, QEasingCurve,
                          QTimer, pyqtProperty, Qt, QPoint, QParallelAnimationGroup)
from PyQt6.QtGui import QColor, QPainter, QKeySequence

# Import your custom modules
import updater
from ui.login_screen import WelcomePage, LoginPage, CreateAccountPage
from ui.loading_screen import LoadingScreen
from ui.splash_screen import SplashScreen
from ui.dashboard_window import DashboardWindow
from ui.session_view import SessionView
from ui.info_dialog import InfoDialog
from ui.logging_handler import QtLogHandler
from builder import build_payload
from config import RELAY_URL_FORMAT
from themes import ThemeManager
from api_client import ApiClient

class FadeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVisible(False)
        self.color = QColor(0, 0, 0, 0)

    def set_color(self, color):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)

class LocalSettingsManager:
    def __init__(self, db_file="tether_client_settings.db"):
        import sqlite3
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        self.db_file = db_file
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
                parent = psutil.Process(self.proc.pid); [child.terminate() for child in parent.children(recursive=True)]; parent.terminate()
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

        # --- Screen Hierarchy for Smart Transitions ---
        self.screen_layers = {
            self.welcome_page: 0,
            self.login_page: 1,
            self.create_account_page: 1
        }

        self.dashboard_view = None
        self.session_view = None
        self.info_dialog = InfoDialog(self)

        # --- Animation attributes ---
        self.animation_group = None
        self.fade_animation = None
        self._animation_callback = None
        self.animation_placeholder = None
        self.fade_overlay = FadeOverlay(self.central_widget)

        # --- Connect Signals to the main transition router ---
        self.welcome_page.login_requested.connect(lambda: self.transition_to_widget(self.login_page))
        self.welcome_page.create_requested.connect(lambda: self.transition_to_widget(self.create_account_page))
        self.login_page.create_account_requested.connect(lambda: self.transition_to_widget(self.create_account_page))
        self.login_page.welcome_requested.connect(lambda: self.transition_to_widget(self.welcome_page)) # Will fade
        self.create_account_page.login_requested.connect(lambda: self.transition_to_widget(self.login_page))
        self.create_account_page.welcome_requested.connect(lambda: self.transition_to_widget(self.welcome_page)) # Will fade
        self.login_page.login_successful.connect(self.show_dashboard_view)

        saved_theme = self.db.load_setting("theme", "Dark (Default)")
        self.apply_theme(saved_theme)

    def get_fade_color(self): return self.fade_overlay.color
    def set_fade_color(self, color): self.fade_overlay.color = color; self.fade_overlay.update()
    fade_color = pyqtProperty(QColor, get_fade_color, set_fade_color)

    def resizeEvent(self, event):
        self.fade_overlay.resize(self.size())
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_I and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_info_dialog()
        else:
            super().keyPressEvent(event)
    def show_info_dialog(self):
        self.info_dialog.update_info(self)
        self.info_dialog.show(); self.info_dialog.raise_(); self.info_dialog.activateWindow()
    def showEvent(self, event):
        super().showEvent(event)
        self.stack.setCurrentWidget(self.loading_screen)
        QTimer.singleShot(2000, self.attempt_auto_login)
    def attempt_auto_login(self):
        creds = self.db.load_setting("auto_login_credentials")
        if creds and "username" in creds and "password" in creds:
            logging.info("Attempting auto-login...")
            response = self.api.login(creds["username"], creds["password"])
            if response and response.get("success"):
                self.show_dashboard_view(response.get("username"), response.get("assigned_line"), animate=False)
                return
        self.stack.setCurrentWidget(self.welcome_page)

    # --- MAIN TRANSITION ROUTER ---
    def transition_to_widget(self, new_widget, animate=True, on_finished=None):
        if (self.animation_group and self.animation_group.state() == QParallelAnimationGroup.State.Running) or \
           (self.fade_animation and self.fade_animation.state() == QPropertyAnimation.State.Running):
            return
        
        if self.stack.currentWidget() == new_widget: return

        animations_enabled = self.db.load_setting("animations_enabled", True)
        if not animations_enabled or not animate:
            self.stack.setCurrentWidget(new_widget)
            if on_finished: on_finished()
            return

        old_widget = self.stack.currentWidget()
        old_layer = self.screen_layers.get(old_widget, 0)
        new_layer = self.screen_layers.get(new_widget, 0)

        # If going to a deeper layer, slide. Otherwise (back or cancel), fade.
        if new_layer > old_layer:
            self._slide_to_widget(old_widget, new_widget, on_finished)
        else:
            self._fade_to_widget(new_widget, on_finished)

    def _fade_to_widget(self, new_widget, on_finished=None):
        self.fade_overlay.setVisible(True)
        self.fade_overlay.raise_()
        
        self.fade_animation = QPropertyAnimation(self, b"fade_color")
        self.fade_animation.setDuration(250)
        self.fade_animation.setStartValue(QColor(0, 0, 0, 0))
        self.fade_animation.setEndValue(QColor(0, 0, 0, 255))
        
        def on_fade_out_finished():
            self.stack.setCurrentWidget(new_widget)
            self.fade_animation.setDirection(QPropertyAnimation.Direction.Backward); self.fade_animation.start()
            try: self.fade_animation.finished.disconnect()
            except TypeError: pass
            self.fade_animation.finished.connect(lambda: self.fade_overlay.setVisible(False))
            if on_finished: self.fade_animation.finished.connect(on_finished)

        try: self.fade_animation.finished.disconnect() 
        except TypeError: pass
        self.fade_animation.finished.connect(on_fade_out_finished)
        self.fade_animation.start()

    def _slide_to_widget(self, old_widget, new_widget, on_finished=None):
        pixmap = old_widget.grab()
        self.animation_placeholder = QLabel(self.stack)
        self.animation_placeholder.setPixmap(pixmap)
        self.animation_placeholder.setGeometry(old_widget.geometry())
        self.animation_placeholder.show(); self.animation_placeholder.raise_()
        self.stack.setCurrentWidget(new_widget)

        start_pos_new = QPoint(self.width(), 0)
        end_pos_old_placeholder = QPoint(-self.width(), 0)
        new_widget.move(start_pos_new)

        anim_new = QPropertyAnimation(new_widget, b"pos"); anim_new.setStartValue(start_pos_new)
        anim_new.setEndValue(QPoint(0, 0)); anim_new.setDuration(300); anim_new.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_old = QPropertyAnimation(self.animation_placeholder, b"pos"); anim_old.setStartValue(QPoint(0, 0))
        anim_old.setEndValue(end_pos_old_placeholder); anim_old.setDuration(300); anim_old.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.animation_group = QParallelAnimationGroup(); self.animation_group.addAnimation(anim_new)
        self.animation_group.addAnimation(anim_old)
        self._animation_callback = on_finished
        self.animation_group.finished.connect(self.on_animation_finished)
        self.animation_group.start()
        
    def on_animation_finished(self):
        if self.animation_placeholder: self.animation_placeholder.deleteLater(); self.animation_placeholder = None
        if self._animation_callback: self._animation_callback()
        self._animation_callback = None

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
            
            self.screen_layers[self.dashboard_view] = 2
            self.screen_layers[self.session_view] = 3

            self.dashboard_view.sign_out_requested.connect(self.handle_sign_out)
            self.dashboard_view.setting_changed.connect(self.handle_setting_changed)
            self.dashboard_view.build_requested.connect(self.start_build)
            self.dashboard_view.session_interact_requested.connect(self.open_session_view)
            self.session_view.back_requested.connect(lambda: self.transition_to_widget(self.dashboard_view)) # Will fade
            self.session_view.task_requested.connect(self.dashboard_view.send_task_from_session)
            self.dashboard_view.data_updated_for_session.connect(self.session_view.handle_command_response)

        self.transition_to_widget(self.dashboard_view, animate=animate)
        logging.info(f"Logged in as {username}. Using Line #{assigned_line}")

    def open_session_view(self, session_id, session_data, status):
        self.session_view.load_session(session_id, session_data, status)
        self.transition_to_widget(self.session_view)

    def handle_setting_changed(self, key, value):
        self.db.save_setting(key, value)
        if key == "theme": self.apply_theme(value)

    def handle_sign_out(self):
        if self.dashboard_view: self.dashboard_view.stop_polling()
        self.db.save_setting("auto_login_credentials", None)
        self.login_page.clear_fields()

        def cleanup_dashboard():
            logging.debug("Cleanup function called after sign-out animation.")
            self.screen_layers.pop(self.dashboard_view, None); self.screen_layers.pop(self.session_view, None)
            if self.dashboard_view: self.stack.removeWidget(self.dashboard_view); self.dashboard_view.deleteLater(); self.dashboard_view = None
            if self.session_view: self.stack.removeWidget(self.session_view); self.session_view.deleteLater(); self.session_view = None
            self.current_user = None; self.api.base_url = None; self.api.line_number = None

        self.transition_to_widget(self.welcome_page, on_finished=cleanup_dashboard) # Will fade
        logging.info("Signed out.")

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    log_handler = QtLogHandler()
    log_format = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s', datefmt='%H:%M:%S')
    log_handler.setFormatter(log_format)
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().setLevel(logging.DEBUG)
    if updater.check_for_updates(): sys.exit(0)
    splash = SplashScreen()
    splash.setStyleSheet(ThemeManager.get_stylesheet("Dark (Default)"))
    screen_geometry = app.primaryScreen().geometry()
    splash.move((screen_geometry.width() - splash.width()) // 2, (screen_geometry.height() - splash.height()) // 2)
    splash.show(); splash.start_animation(); splash.fade_in()
    window = MainWindow()
    log_handler.log_signal.connect(window.info_dialog.log_output.append)
    def close_splash_and_show_main():
        splash.fade_out()
        splash.fade_out_animation.finished.connect(lambda: (
            splash.stop_animation(), splash.close(), window.show()
        ))
    QTimer.singleShot(3000, close_splash_and_show_main)
    sys.exit(app.exec())