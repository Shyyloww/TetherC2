# C2_Client/ui/info_dialog.py
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, 
                             QLabel, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class InfoDialog(QDialog):
    """
    A dialog to display detailed session, client, and developer information.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Developer Information & Logs")
        self.setMinimumSize(800, 600)

        main_layout = QVBoxLayout(self)

        # --- Information Section ---
        info_group = QGroupBox("Live Information")
        form_layout = QFormLayout(info_group)
        
        # We'll create labels that the MainWindow can update
        self.username_label = QLabel("N/A")
        self.line_number_label = QLabel("N/A")
        self.base_url_label = QLabel("N/A")
        self.client_version_label = QLabel("N/A")
        self.theme_label = QLabel("N/A")
        self.db_path_label = QLabel("N/A")
        self.python_version_label = QLabel(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

        form_layout.addRow("Current User:", self.username_label)
        form_layout.addRow("Connected C2 Line:", self.line_number_label)
        form_layout.addRow("Full Relay URL:", self.base_url_label)
        form_layout.addRow("Client Version:", self.client_version_label)
        form_layout.addRow("Current Theme:", self.theme_label)
        form_layout.addRow("Settings DB Path:", self.db_path_label)
        form_layout.addRow("Python Version:", self.python_version_label)
        
        main_layout.addWidget(info_group)
        
        # --- Live Log Output ---
        log_group = QGroupBox("Live Event Log")
        log_layout = QVBoxLayout(log_group)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 10))
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        log_layout.addWidget(self.log_output)
        
        main_layout.addWidget(log_group, 1) # Give log output more space

        # --- Close Button ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def update_info(self, main_window):
        """Pulls the latest info from the main window and updates the labels."""
        self.username_label.setText(main_window.current_user or "Not Logged In")
        
        line_num = main_window.api.line_number
        self.line_number_label.setText(str(line_num) if line_num else "Not Connected")
        self.base_url_label.setText(main_window.api.base_url or "N/A")

        try:
            # Dynamically import to avoid circular dependencies
            from updater import get_current_version
            self.client_version_label.setText(get_current_version())
        except ImportError:
            self.client_version_label.setText("Unknown")
            
        self.theme_label.setText(main_window.db.load_setting("theme", "N/A"))
        self.db_path_label.setText(main_window.db.db_file)

    def exec(self):
        # Override exec to ensure info is updated right before showing
        self.update_info(self.parent())
        super().exec()