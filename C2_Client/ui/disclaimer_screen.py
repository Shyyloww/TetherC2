# C2_Client/ui/disclaimer_screen.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class DisclaimerScreen(QWidget):
    """
    A screen that displays a legal and ethical use disclaimer on first launch.
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("DisclaimerScreen")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)

        disclaimer_text = (
            "<b>Tether C2 is a professional tool intended solely for legal and ethical purposes.</b> "
            "It may only be used with explicit consent for system administration, educational "
            "purposes, or professional security testing.<br><br>"
            "Unauthorized access to any computer system is a crime. "
            "By using this software, you agree that you are fully responsible for "
            "your actions in compliance with all applicable laws."
        )
        
        self.disclaimer_label = QLabel(disclaimer_text)
        self.disclaimer_label.setObjectName("DisclaimerLabel")
        self.disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disclaimer_label.setWordWrap(True)
        
        layout.addWidget(self.disclaimer_label)