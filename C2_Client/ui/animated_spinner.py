# C2_Client/ui/animated_spinner.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen

class AnimatedSpinner(QWidget):
    """A simple, custom-drawn animated spinner widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(24, 24)
        # --- ADDED: Custom property for theme-aware color ---
        self._pen_color = QColor("#f0f0f0") # Default to a light color

        self.rotation_animation = QPropertyAnimation(self, b"angle", self)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setDuration(1000)
        self.rotation_animation.setLoopCount(-1)

        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # --- MODIFIED: Use the themeable penColor property directly ---
        pen_width = max(2.0, self.width() / 12.0)
        pen = QPen(self._pen_color, pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        margin = int(pen_width)
        draw_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        painter.drawArc(
            draw_rect,
            self._angle * 16,
            270 * 16
        )

    # --- ADDED: Getter and Setter for the custom penColor property ---
    def getPenColor(self):
        return self._pen_color

    def setPenColor(self, color):
        if self._pen_color != color:
            self._pen_color = color
            self.update()

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    # --- ADDED: Expose penColor to the Qt Property system for stylesheets ---
    penColor = pyqtProperty(QColor, getPenColor, setPenColor)

    def start_animation(self):
        self.show()
        self.rotation_animation.start()

    def stop_animation(self):
        self.rotation_animation.stop()
        self.hide()