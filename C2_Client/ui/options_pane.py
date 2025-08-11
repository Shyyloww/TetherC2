# C2_Client/ui/options_pane.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QComboBox, 
                             QPushButton, QLabel, QMessageBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal

class OptionsPane(QWidget):
    sign_out_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>OPTIONS</h2>"))
        
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        self.theme_selector = QComboBox()
        self.theme_selector.addItems([
            "Dark (Default)", "Light", "Cyber", "Matrix", 
            "Sunrise", "Sunset", "Jungle", "Ocean", "Galaxy", "Candy"
        ])
        self.theme_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("theme", val))
        appearance_layout.addRow("Theme:", self.theme_selector)
        layout.addWidget(appearance_group)
        
        layout.addStretch()
        
        self.sign_out_button = QPushButton("Sign Out")
        self.sign_out_button.clicked.connect(self.sign_out_requested)
        layout.addWidget(self.sign_out_button)
        
        self.load_settings()
        
    def load_settings(self):
        self.theme_selector.setCurrentText(self.db.load_setting("theme", "Dark (Default)"))