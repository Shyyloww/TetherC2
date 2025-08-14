# C2_Client/ui/events_pane.py
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont

class EventsPane(QTextEdit):
    """
    A simple text edit widget to display important, non-interactive events 
    from a session, such as errors or status updates.
    """
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 11))
        self.append("--- Session Event Log ---")

    def add_event(self, message):
        """Appends a new event message to the view."""
        self.append(message)

    def clear_events(self):
        """Clears all events for a new session."""
        self.clear()
        self.append("--- Session Event Log ---")