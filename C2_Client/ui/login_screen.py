# C2_Client/ui/login_screen.py
import webbrowser
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QStackedWidget, QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, pyqtProperty, QTimer, QThread
from PyQt6.QtGui import QColor, QCursor
from .animated_spinner import AnimatedSpinner
from .api_worker import ApiWorker

class ClickableLabel(QLabel):
    """A QLabel that can be clicked to open a URL."""
    def __init__(self, text, url=None):
        super().__init__(text)
        self.url = url
        if self.url:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.setToolTip(f"Open link: {self.url}")

    def mousePressEvent(self, event):
        if self.url:
            webbrowser.open(self.url)
        super().mousePressEvent(event)

class WelcomePage(QWidget):
    """The initial screen with options to log in or create an account."""
    login_requested = pyqtSignal()
    create_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("WelcomeScreen")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.welcome_label_top = QLabel("Welcome to")
        self.welcome_label_top.setObjectName("WelcomeSubLabelTop")
        
        self.title_label = QLabel("Tether C2")
        self.title_label.setObjectName("TitleLabel")

        self.welcome_label_bottom = QLabel("By <b>ebowluh</b>")
        self.welcome_label_bottom.setObjectName("WelcomeSubLabelBottom")
        
        title_layout.addWidget(self.welcome_label_top, 0, Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.welcome_label_bottom, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_container)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        go_to_login_button = QPushButton("Log In")
        go_to_login_button.clicked.connect(self.login_requested.emit)
        
        go_to_create_button = QPushButton("Create Account")
        go_to_create_button.clicked.connect(self.create_requested.emit)
        
        button_layout.addWidget(go_to_login_button)
        button_layout.addWidget(go_to_create_button)
        layout.addLayout(button_layout)


class LoginPage(QWidget):
    """The login screen with username, password, and a delayed loading indicator."""
    login_successful = pyqtSignal(str, int)
    create_account_requested = pyqtSignal()
    welcome_requested = pyqtSignal()

    def __init__(self, api_client, db_manager):
        super().__init__()
        self.setObjectName("LoginScreen")
        self.api = api_client
        self.db = db_manager
        self.thread = None
        self.worker = None
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        title_label = QLabel("Tether C2")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        form_container = QWidget()
        form_container.setFixedWidth(675)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.remember_me_checkbox = QCheckBox("Remember Me (Auto-Login Next Time)")
        
        self.action_stack = QStackedWidget()
        self.login_button = QPushButton("Log In")
        self.action_stack.addWidget(self.login_button)

        loading_widget = QWidget()
        loading_layout = QHBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner = AnimatedSpinner()
        loading_layout.addWidget(self.spinner)
        loading_layout.addWidget(QLabel("Awakening Line..."))
        self.action_stack.addWidget(loading_widget)
        
        self.action_stack.setSizePolicy(self.login_button.sizePolicy())
        self.action_stack.setMinimumSize(self.login_button.sizeHint())
        
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.remember_me_checkbox, 0, Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.action_stack)
        form_layout.addWidget(self.feedback_label)
        layout.addWidget(form_container)

        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(5)
        go_to_create_from_login = QPushButton("Don't have an account? Create one.")
        go_to_create_from_login.setObjectName("SubtleButton")
        go_to_create_from_login.clicked.connect(self.create_account_requested.emit)
        
        back_button = QPushButton("< Back")
        back_button.setObjectName("SubtleButton")
        back_button.clicked.connect(self.welcome_requested.emit)
        
        nav_layout.addWidget(go_to_create_from_login, 0, Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(nav_layout)
        
        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.show_awakening_spinner)
        
        # --- MODIFIED: Connect Enter key press to login action ---
        self.login_button.clicked.connect(self.handle_login)
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    def show_awakening_spinner(self):
        """Shows the spinner and 'Awakening...' text."""
        self.action_stack.setCurrentIndex(1)
        self.spinner.start_animation()

    def clear_fields(self):
        """Resets the input fields."""
        self.username_input.clear()
        self.password_input.clear()
        self.feedback_label.clear()
        self.remember_me_checkbox.setChecked(False)

    def handle_login(self):
        """Initiates the login process by starting the API worker thread."""
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            self.feedback_label.setText("<font color='red'>Username and password are required.</font>")
            return
        
        self.login_button.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.feedback_label.clear()
        self.wait_timer.start(5000)

        self.thread = QThread()
        self.worker = ApiWorker(self.api, "login", username, password)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_login_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_login_finished(self, response):
        """Handles the result from the API worker thread."""
        self.wait_timer.stop()
        if self.action_stack.currentIndex() == 1:
            self.spinner.stop_animation()
        self.action_stack.setCurrentIndex(0)
        
        if response and response.get("success"):
            if self.remember_me_checkbox.isChecked():
                self.db.save_setting("auto_login_credentials", {"username": response.get("username"), "password": self.password_input.text()})
            else:
                self.db.save_setting("auto_login_credentials", None)
            self.login_successful.emit(response.get("username"), response.get("assigned_line"))
        else:
            error = response.get("error", "Login failed.") if response else "Could not connect to any C2 line. Please wait and try again."
            self.feedback_label.setText(f"<font color='red'>{error}</font>")

        self.login_button.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.thread.quit()

class CreateAccountPage(QWidget):
    """The account creation screen with a delayed loading indicator."""
    login_requested = pyqtSignal()
    welcome_requested = pyqtSignal()

    def __init__(self, api_client):
        super().__init__()
        self.setObjectName("CreateScreen")
        self.api = api_client
        self.thread = None
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("Tether C2")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        form_container = QWidget()
        form_container.setFixedWidth(675)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("New Username")
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("New Password (min. 6 chars)")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.action_stack = QStackedWidget()
        self.create_button = QPushButton("Create Account")
        self.action_stack.addWidget(self.create_button)

        loading_widget = QWidget()
        loading_layout = QHBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner = AnimatedSpinner()
        loading_layout.addWidget(self.spinner)
        loading_layout.addWidget(QLabel("Awakening Line..."))
        self.action_stack.addWidget(loading_widget)
        
        self.action_stack.setSizePolicy(self.create_button.sizePolicy())
        self.action_stack.setMinimumSize(self.create_button.sizeHint())
        
        self.create_feedback = QLabel("")
        self.create_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_layout.addWidget(self.new_username)
        form_layout.addWidget(self.new_password)
        form_layout.addWidget(self.action_stack)
        form_layout.addWidget(self.create_feedback)
        
        inactivity_notice_label = QLabel("Note: Accounts inactive for over 6 months will be automatically deleted.")
        inactivity_notice_label.setObjectName("InactivityNoticeLabel")
        inactivity_notice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(inactivity_notice_label)
        layout.addWidget(form_container)
        
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(5)
        go_to_login_from_create = QPushButton("Already have an account? Log In.")
        go_to_login_from_create.setObjectName("SubtleButton")
        go_to_login_from_create.clicked.connect(self.login_requested.emit)
        
        back_button = QPushButton("< Back")
        back_button.setObjectName("SubtleButton")
        back_button.clicked.connect(self.welcome_requested.emit)
        
        nav_layout.addWidget(go_to_login_from_create, 0, Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(nav_layout)

        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.show_awakening_spinner)
        
        # --- MODIFIED: Connect Enter key press to create account action ---
        self.create_button.clicked.connect(self.handle_create_account)
        self.new_username.returnPressed.connect(self.handle_create_account)
        self.new_password.returnPressed.connect(self.handle_create_account)

    def show_awakening_spinner(self):
        """Shows the spinner and 'Awakening...' text."""
        self.action_stack.setCurrentIndex(1)
        self.spinner.start_animation()

    def handle_create_account(self):
        """Initiates the account creation process by starting the API worker thread."""
        username = self.new_username.text()
        password = self.new_password.text()
        if not username or not password:
            self.create_feedback.setText("<font color='red'>Fields cannot be empty.</font>")
            return

        self.create_button.setEnabled(False)
        self.new_username.setEnabled(False)
        self.new_password.setEnabled(False)
        self.create_feedback.clear()
        self.wait_timer.start(5000)

        self.thread = QThread()
        self.worker = ApiWorker(self.api, "register", username, password)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_create_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_create_finished(self, response):
        """Handles the result from the API worker thread."""
        self.wait_timer.stop()
        if self.action_stack.currentIndex() == 1:
            self.spinner.stop_animation()
        self.action_stack.setCurrentIndex(0)

        if response and response.get("success"):
            self.login_requested.emit()
        else:
            error = response.get("error", "Registration failed.") if response else "Could not connect to any C2 line. Please wait and try again."
            self.create_feedback.setText(f"<font color='red'>{error}</font>")

        self.create_button.setEnabled(True)
        self.new_username.setEnabled(True)
        self.new_password.setEnabled(True)
        self.thread.quit()