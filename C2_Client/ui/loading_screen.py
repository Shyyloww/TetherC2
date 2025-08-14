# C2_Client/ui/loading_screen.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer

class LoadingScreen(QWidget):
    """
    A startup screen that shows a "Connecting..." message for a few seconds.
    """
    def __init__(self):
        super().__init__()
        # Use a specific object name for styling
        self.setObjectName("LoadingScreen")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # Re-use the TitleLabel style for consistency
        self.title_label = QLabel("Tether C2")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Connecting...")
        self.status_label.setObjectName("LoadingStatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)

        self.dot_count = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)

    def update_animation(self):
        """Cycles the dots in 'Connecting...' to create a simple animation."""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        # Use a non-breaking space to prevent minor layout shifts
        self.status_label.setText(f"Connecting{dots}".ljust(13, '\u00A0'))

    def showEvent(self, event):
        """Starts the animation timer when the widget is shown."""
        if not self.animation_timer.isActive():
            self.animation_timer.start(500) # Update text every 500ms
        super().showEvent(event)

    def hideEvent(self, event):
        """Stops the animation timer when the widget is hidden."""
        self.animation_timer.stop()
        super().hideEvent(event)