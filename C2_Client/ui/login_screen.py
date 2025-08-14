# C2_Client/ui/login_screen.py
import webbrowser
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QStackedWidget, QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QColor, QCursor

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
    login_requested = pyqtSignal()
    create_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("WelcomeScreen")
        self.discord_url = "https://discord.gg/BPYscjFkK3"
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # --- Title Block ---
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.welcome_label_top = ClickableLabel("Welcome to", self.discord_url)
        self.welcome_label_top.setObjectName("WelcomeSubLabelTop")
        
        self.title_label = ClickableLabel("Tether C2", self.discord_url)
        self.title_label.setObjectName("TitleLabel")

        self.welcome_label_bottom = ClickableLabel("By <b>ebowluh</b>", self.discord_url)
        self.welcome_label_bottom.setObjectName("WelcomeSubLabelBottom")
        
        title_layout.addWidget(self.welcome_label_top, 0, Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.welcome_label_bottom, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_container)
        
        # --- MODIFIED: Subtle Color Animation Setup ---
        self._color_property = QColor("#d0d0d0") 
        self.title_label.setStyleSheet(f"color: {self._color_property.name()};")
        
        self.animation = QPropertyAnimation(self, b"color")
        self.animation.setDuration(10000) # Faster, more subtle 10-second loop
        self.animation.setLoopCount(-1)

        # A "duller" rainbow palette that gently shifts around a light gray base
        colors = [
            QColor("#d0d0d0"), # Base
            QColor("#c8d0d8"), # Cool tint
            QColor("#d0d0d0"), # Base
            QColor("#d8d0c8"), # Warm tint
            QColor("#d0d0d0"), # Base
            QColor("#d0c8d8"), # Lavender tint
            QColor("#d0d0d0")  # Return to base
        ]
        
        step = 1.0 / (len(colors) - 1)
        for i, color in enumerate(colors):
            self.animation.setKeyValueAt(i * step, color)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        go_to_login_button = QPushButton("Log In")
        go_to_login_button.clicked.connect(self.login_requested.emit)
        
        go_to_create_button = QPushButton("Create Account")
        go_to_create_button.clicked.connect(self.create_requested.emit)
        
        button_layout.addWidget(go_to_login_button)
        button_layout.addWidget(go_to_create_button)
        layout.addLayout(button_layout)

    def get_color(self):
        return self._color_property

    def set_color(self, color):
        self._color_property = color
        self.title_label.setStyleSheet(f"color: {self._color_property.name()};")

    color = pyqtProperty(QColor, get_color, set_color)

    def showEvent(self, event):
        if self.animation.state() != QPropertyAnimation.State.Running:
            self.animation.start()
        super().showEvent(event)

    def hideEvent(self, event):
        # Do not stop the animation so its state persists
        super().hideEvent(event)

class LoginPage(QWidget):
    login_successful = pyqtSignal(str, int)
    create_account_requested = pyqtSignal()
    welcome_requested = pyqtSignal()

    def __init__(self, api_client, db_manager):
        super().__init__()
        self.setObjectName("LoginScreen")
        self.api = api_client
        self.db = db_manager
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
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
        login_button = QPushButton("Log In")
        login_button.clicked.connect(self.handle_login)
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.remember_me_checkbox, 0, Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(login_button)
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

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.feedback_label.clear()
        self.remember_me_checkbox.setChecked(False)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            self.feedback_label.setText("<font color='red'>Username and password are required.</font>")
            return
        
        response = self.api.login(username, password)
        if response and response.get("success"):
            if self.remember_me_checkbox.isChecked():
                self.db.save_setting("auto_login_credentials", {"username": username, "password": password})
            else:
                self.db.save_setting("auto_login_credentials", None)
            
            self.login_successful.emit(response.get("username"), response.get("assigned_line"))
        else:
            error = response.get("error", "Login failed.") if response else "Could not connect to server."
            self.feedback_label.setText(f"<font color='red'>{error}</font>")

class CreateAccountPage(QWidget):
    login_requested = pyqtSignal()
    welcome_requested = pyqtSignal()

    def __init__(self, api_client):
        super().__init__()
        self.setObjectName("CreateScreen")
        self.api = api_client

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_container = QWidget()
        form_container.setFixedWidth(675)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15) # Adjusted spacing
        
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("New Username")
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("New Password (min. 4 chars)")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        create_button = QPushButton("Create Account")
        create_button.clicked.connect(self.handle_create_account)
        self.create_feedback = QLabel("")
        self.create_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_layout.addWidget(self.new_username)
        form_layout.addWidget(self.new_password)
        form_layout.addWidget(create_button)
        form_layout.addWidget(self.create_feedback)

        # --- NEW: Inactivity Policy Label ---
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

    def handle_create_account(self):
        username = self.new_username.text()
        password = self.new_password.text()
        if not username or not password:
            self.create_feedback.setText("<font color='red'>Fields cannot be empty.</font>")
            return

        response = self.api.register(username, password)
        if response and response.get("success"):
            self.login_requested.emit()
        else:
            error = response.get("error", "Registration failed.") if response else "Could not connect to server."
            self.create_feedback.setText(f"<font color='red'>{error}</font>")