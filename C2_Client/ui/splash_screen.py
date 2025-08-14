# C2_Client/ui/splash_screen.py
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, pyqtProperty, 
                          QPointF, QEasingCurve)
from PyQt6.QtGui import QPainter, QColor, QConicalGradient, QPen, QPixmap

class SplashScreen(QWidget):
    """A standalone splash screen window with fade effects."""
    def __init__(self):
        super().__init__()
        self.setObjectName("SplashScreen")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.animation_widget = AnimatedRingWidget()
        layout.addWidget(self.animation_widget)
        
        # Animations for fading the entire window
        self.setWindowOpacity(0.0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)

        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(500)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)

    def start_animation(self):
        self.animation_widget.start_animation()

    def stop_animation(self):
        self.animation_widget.stop_animation()

    def fade_in(self):
        self.fade_in_animation.start()
        
    def fade_out(self):
        self.fade_out_animation.start()

class AnimatedRingWidget(QWidget):
    """A widget that draws a spinning ring without sparkles."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)
        self._angle = 0.0
        
        self.icon_pixmap = QPixmap("tether_icon.png")
        if self.icon_pixmap.isNull():
            print("Warning: tether_icon.png not found. Displaying placeholder.")
            self.icon_pixmap = QPixmap(320, 320)
            self.icon_pixmap.fill(Qt.GlobalColor.transparent)

        self.colors = [QColor("#389cdc"), QColor("#f89c14"), QColor("#a05cb4")]
        
        self.rotation_animation = QPropertyAnimation(self, b"_rotation_angle")
        self.rotation_animation.setDuration(4000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)
        self.rotation_animation.setEasingCurve(QEasingCurve.Type.InOutSine)

    def start_animation(self):
        self.rotation_animation.start()

    def stop_animation(self):
        self.rotation_animation.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x, center_y = self.width() // 2, self.height() // 2
        
        icon_size = 320 
        painter.drawPixmap(
            center_x - icon_size // 2, center_y - icon_size // 2,
            icon_size, icon_size,
            self.icon_pixmap
        )

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self._angle)
        
        gradient = QConicalGradient(QPointF(0, 0), 90)
        gradient.setColorAt(0.0, self.colors[0])
        gradient.setColorAt(0.33, self.colors[1])
        gradient.setColorAt(0.66, self.colors[2])
        gradient.setColorAt(1.0, self.colors[0])
        
        pen = QPen(gradient, 14)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        ring_radius = 180
        painter.drawArc(
            -ring_radius, -ring_radius, ring_radius * 2, ring_radius * 2,
            0, 360 * 16
        )
        painter.restore()
            
    def get_rotation_angle(self):
        return self._angle
        
    def set_rotation_angle(self, angle):
        self._angle = angle
        self.update()

    _rotation_angle = pyqtProperty(float, get_rotation_angle, set_rotation_angle)