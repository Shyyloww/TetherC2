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

        self.rotation_animation = QPropertyAnimation(self, b"angle", self)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setDuration(1000)
        self.rotation_animation.setLoopCount(-1)

        self.hide() # <-- ADDED: Start hidden

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen_color = self.palette().color(self.foregroundRole())
        
        pen = QPen(pen_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        painter.drawArc(
            self.rect().adjusted(2, 2, -2, -2),
            self._angle * 16,
            270 * 16
        )

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    def start_animation(self):
        self.show()
        self.rotation_animation.start()

    def stop_animation(self):
        self.rotation_animation.stop()
        self.hide()