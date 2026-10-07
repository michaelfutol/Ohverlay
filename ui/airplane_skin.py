"""
Airplane v1.0 - Non-Biological Object
Realistic aircraft with contrails and navigation lights
"""

import math
import random
from typing import List
from dataclasses import dataclass
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget


@dataclass
class ContrailPoint:
    """Single point in contrail"""
    x: float
    y: float
    life: float = 1.0
    width: float = 4.0


@dataclass
class Cloud:
    """Background cloud for depth"""
    x: float
    y: float
    size: float
    speed: float
    alpha: int = 30
    
    def update(self, dt: float, plane_x: float):
        # Parallax - clouds move slower than plane
        self.x -= self.speed * dt
        
        # Wrap around
        if self.x < -200:
            self.x = 1500
            self.y = random.uniform(50, 350)


class Airplane(QWidget):
    """
    Realistic jet airplane
    Flies across desktop with contrails and banking turns
    """
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        
        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Physics
        self.x = 1920.0
        self.y = 300.0
        self.vx = 150.0  # Forward speed
        self.vy = 0.0
        self.altitude = 300.0  # For parallax effect
        self.target_altitude = 300.0
        
        # Rotation and banking
        self.angle = 0.0  # Direction
        self.bank_angle = 0.0  # Roll for turning
        self.target_bank = 0.0
        
        # Visual
        self.plane_scale = 1.0
        self.contrails: List[List[ContrailPoint]] = [[], []]  # Left and right engines
        self.clouds: List[Cloud] = []
        self._spawn_clouds()
        
        # Lights
        self.strobe_timer = 0.0
        self.strobe_on = True
        self.beacon_timer = 0.0
        self.beacon_on = True
        
        # Colors
        self.fuselage_color = QColor(230, 235, 240)
        self.wing_color = QColor(210, 215, 220)
        self.cockpit_color = QColor(50, 60, 80)
        
        self.time = 0.0
        self.resize(300, 200)
        self.move(int(self.x - 150), int(self.y - 100))
    
    def _spawn_clouds(self):
        """Create background clouds"""
        for i in range(8):
            cloud = Cloud(
                x=random.uniform(0, 1500),
                y=random.uniform(50, 350),
                size=random.uniform(40, 80),
                speed=random.uniform(20, 40)
            )
            self.clouds.append(cloud)
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update airplane physics"""
        self.time += dt
        
        # Altitude control (smooth follow)
        self.target_altitude = target_y
        alt_diff = self.target_altitude - self.altitude
        self.altitude += alt_diff * 1.0 * dt
        self.y = self.altitude
        
        # Horizontal movement (always moving forward)
        self.x += self.vx * dt
        
        # Wrap around screen
        if self.x > 4000:
            self.x = -200
        
        # Calculate bank angle based on altitude change
        self.target_bank = max(-30, min(30, alt_diff * 0.5))
        bank_diff = self.target_bank - self.bank_angle
        self.bank_angle += bank_diff * 2.0 * dt
        
        # Update contrails
        self._update_contrails(dt)
        
        # Update clouds
        for cloud in self.clouds:
            cloud.update(dt, self.x)
        
        # Update lights
        self.strobe_timer += dt
        if self.strobe_timer > 0.1:
            self.strobe_timer = 0.0
            self.strobe_on = not self.strobe_on
        
        self.beacon_timer += dt
        if self.beacon_timer > 1.0:
            self.beacon_timer = 0.0
            self.beacon_on = not self.beacon_on
        
        self.move(int(self.x - 150), int(self.y - 100))
        self.update()
    
    def _update_contrails(self, dt: float):
        """Update engine contrails"""
        # Engine positions (relative to plane center)
        engine_offset_x = -60
        engine_offset_y = 15
        
        for i, trail in enumerate(self.contrails):
            # Add new point
            offset_y = engine_offset_y if i == 0 else -engine_offset_y
            
            # Account for bank angle
            rad_bank = math.radians(self.bank_angle)
            rotated_y = offset_y * math.cos(rad_bank)
            
            trail.append(ContrailPoint(
                x=self.x + engine_offset_x,
                y=self.y + rotated_y,
                life=1.0,
                width=6.0
            ))
            
            # Update and remove old points
            for point in trail:
                point.life -= dt * 0.3
                point.width *= 0.995
            
            self.contrails[i] = [p for p in trail if p.life > 0]
            
            # Limit trail length
            if len(self.contrails[i]) > 100:
                self.contrails[i] = self.contrails[i][-100:]
    
    def paintEvent(self, event):
        """Render airplane"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Draw clouds (background)
        self._draw_clouds(painter)
        
        # Draw contrails (behind plane)
        self._draw_contrails(painter)
        
        # Draw airplane
        self._draw_airplane(painter)
    
    def _draw_clouds(self, painter: QPainter):
        """Draw background clouds"""
        for cloud in self.clouds:
            cx = cloud.x - self.x + 150
            cy = cloud.y - self.y + 100
            
            # Skip if out of view
            if cx < -100 or cx > 400:
                continue
            
            cloud_color = QColor(255, 255, 255, cloud.alpha)
            painter.setBrush(QBrush(cloud_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Puffy cloud shape
            for i in range(3):
                offset_x = math.sin(i * 2) * cloud.size * 0.3
                offset_y = math.cos(i * 1.5) * cloud.size * 0.2
                painter.drawEllipse(
                    int(cx + offset_x - cloud.size * 0.4),
                    int(cy + offset_y - cloud.size * 0.3),
                    int(cloud.size * 0.8),
                    int(cloud.size * 0.6)
                )
    
    def _draw_contrails(self, painter: QPainter):
        """Draw engine contrails"""
        for trail in self.contrails:
            if len(trail) < 2:
                continue
            
            for i in range(len(trail) - 1):
                p1 = trail[i]
                p2 = trail[i + 1]
                
                x1 = p1.x - self.x + 150
                y1 = p1.y - self.y + 100
                x2 = p2.x - self.x + 150
                y2 = p2.y - self.y + 100
                
                # Fade with life
                alpha = int(100 * p1.life)
                width = p1.width * p1.life
                
                contrail_color = QColor(255, 255, 255, alpha)
                painter.setPen(QPen(contrail_color, width, 
                                   Qt.PenStyle.SolidLine,
                                   Qt.PenCapStyle.RoundCap))
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_airplane(self, painter: QPainter):
        """Draw the airplane with banking"""
        cx = 150
        cy = 100
        
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.bank_angle * 0.3)  # Slight visual rotation
        
        # Scale based on bank (perspective effect)
        scale_y = math.cos(math.radians(abs(self.bank_angle) * 0.5))
        painter.scale(1.0, scale_y)
        
        # Shadow (offset based on altitude)
        shadow_offset = 20
        painter.save()
        painter.translate(shadow_offset, shadow_offset)
        painter.setBrush(QBrush(QColor(0, 20, 40, 40)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(-80, -10, 160, 20)
        painter.restore()
        
        # Main wings
        wing_gradient = QLinearGradient(0, -40, 0, 40)
        wing_gradient.setColorAt(0.0, self.wing_color.lighter(120))
        wing_gradient.setColorAt(0.5, self.wing_color)
        wing_gradient.setColorAt(1.0, self.wing_color.darker(120))
        
        painter.setBrush(QBrush(wing_gradient))
        painter.setPen(QPen(QColor(180, 185, 190), 1.0))
        
        # Wing shape (swept back)
        wing_path = QPainterPath()
        wing_path.moveTo(-20, -5)
        wing_path.lineTo(30, -45)  # Wing tip
        wing_path.lineTo(40, -45)
        wing_path.lineTo(10, -5)
        wing_path.closeSubpath()
        painter.drawPath(wing_path)
        
        # Other wing (mirrored)
        wing_path2 = QPainterPath()
        wing_path2.moveTo(-20, 5)
        wing_path2.lineTo(30, 45)
        wing_path2.lineTo(40, 45)
        wing_path2.lineTo(10, 5)
        wing_path2.closeSubpath()
        painter.drawPath(wing_path2)
        
        # Fuselage (body)
        body_gradient = QLinearGradient(-60, 0, 70, 0)
        body_gradient.setColorAt(0.0, self.fuselage_color.darker(110))
        body_gradient.setColorAt(0.3, self.fuselage_color)
        body_gradient.setColorAt(0.7, self.fuselage_color)
        body_gradient.setColorAt(1.0, self.fuselage_color.lighter(120))
        
        painter.setBrush(QBrush(body_gradient))
        painter.setPen(QPen(QColor(200, 205, 210), 1.0))
        
        # Fuselage shape
        body_path = QPainterPath()
        body_path.moveTo(70, 0)  # Nose
        body_path.cubicTo(70, 10, 40, 12, -20, 10)  # Top curve
        body_path.lineTo(-60, 8)  # Taper to tail
        body_path.lineTo(-70, 0)  # Tail tip
        body_path.lineTo(-60, -8)
        body_path.lineTo(-20, -10)
        body_path.cubicTo(40, -12, 70, -10, 70, 0)
        body_path.closeSubpath()
        painter.drawPath(body_path)
        
        # Cockpit windows
        cockpit_gradient = QLinearGradient(35, -6, 35, 6)
        cockpit_gradient.setColorAt(0.0, self.cockpit_color.lighter(150))
        cockpit_gradient.setColorAt(0.5, self.cockpit_color)
        cockpit_gradient.setColorAt(1.0, self.cockpit_color.darker(120))
        
        painter.setBrush(QBrush(cockpit_gradient))
        painter.setPen(QPen(QColor(30, 40, 60), 1.0))
        
        # Cockpit shape
        cockpit_path = QPainterPath()
        cockpit_path.moveTo(50, -4)
        cockpit_path.quadTo(45, -6, 30, -5)
        cockpit_path.lineTo(25, -4)
        cockpit_path.lineTo(25, 4)
        cockpit_path.lineTo(30, 5)
        cockpit_path.quadTo(45, 6, 50, 4)
        cockpit_path.closeSubpath()
        painter.drawPath(cockpit_path)
        
        # Engine nacelles
        for offset in [-15, 15]:
            painter.setBrush(QBrush(QColor(200, 205, 210)))
            painter.setPen(QPen(QColor(180, 185, 190), 1.0))
            
            # Engine pod
            engine_path = QPainterPath()
            engine_path.moveTo(-10, offset - 4)
            engine_path.lineTo(-35, offset - 5)
            engine_path.quadTo(-40, offset, -35, offset + 5)
            engine_path.lineTo(-10, offset + 4)
            engine_path.closeSubpath()
            painter.drawPath(engine_path)
            
            # Engine intake
            intake_gradient = QRadialGradient(-10, offset, 4)
            intake_gradient.setColorAt(0.0, QColor(40, 45, 50))
            intake_gradient.setColorAt(1.0, QColor(80, 85, 90))
            painter.setBrush(QBrush(intake_gradient))
            painter.drawEllipse(int(-14), int(offset - 4), 8, 8)
        
        # Vertical stabilizer (tail fin)
        tail_gradient = QLinearGradient(-60, -25, -55, 0)
        tail_gradient.setColorAt(0.0, self.fuselage_color.lighter(110))
        tail_gradient.setColorAt(1.0, self.fuselage_color)
        
        painter.setBrush(QBrush(tail_gradient))
        painter.setPen(QPen(QColor(180, 185, 190), 1.0))
        
        tail_path = QPainterPath()
        tail_path.moveTo(-55, -8)
        tail_path.lineTo(-45, -30)
        tail_path.lineTo(-35, -28)
        tail_path.lineTo(-45, -8)
        tail_path.closeSubpath()
        painter.drawPath(tail_path)
        
        # Horizontal stabilizers
        painter.setBrush(QBrush(self.wing_color.darker(105)))
        
        stab_path = QPainterPath()
        stab_path.moveTo(-55, -8)
        stab_path.lineTo(-70, -15)
        stab_path.lineTo(-68, -12)
        stab_path.lineTo(-55, -8)
        painter.drawPath(stab_path)
        
        stab_path2 = QPainterPath()
        stab_path2.moveTo(-55, 8)
        stab_path2.lineTo(-70, 15)
        stab_path2.lineTo(-68, 12)
        stab_path2.lineTo(-55, 8)
        painter.drawPath(stab_path2)
        
        # Navigation lights
        # Red on left (port)
        if self.beacon_on:
            red_light = QRadialGradient(-15, -45, 6)
            red_light.setColorAt(0.0, QColor(255, 50, 50, 200))
            red_light.setColorAt(1.0, QColor(255, 0, 0, 0))
            painter.setBrush(QBrush(red_light))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(-21), int(-51), 12, 12)
        
        # Green on right (starboard)
        green_light = QRadialGradient(-15, 45, 6)
        green_light.setColorAt(0.0, QColor(50, 255, 50, 200))
        green_light.setColorAt(1.0, QColor(0, 255, 0, 0))
        painter.setBrush(QBrush(green_light))
        painter.drawEllipse(int(-21), int(39), 12, 12)
        
        # White strobe on tail
        if self.strobe_on:
            strobe = QRadialGradient(-65, 0, 8)
            strobe.setColorAt(0.0, QColor(255, 255, 255, 220))
            strobe.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(strobe))
            painter.drawEllipse(int(-73), int(-8), 16, 16)
        
        # Airline stripe detail
        painter.setPen(QPen(QColor(50, 100, 180), 2.0))
        painter.drawLine(-40, 0, 20, 0)
        
        painter.restore()
