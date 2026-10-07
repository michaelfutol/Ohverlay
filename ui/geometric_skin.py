"""
Geometric Shapes v1.0 - Non-Biological Objects
Floating crystals, polygons, sacred geometry
"""

import math
import random
from typing import List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QConicalGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget


class FloatingCrystal:
    """Individual crystal with its own behavior"""
    
    def __init__(self, x: float, y: float, crystal_type: str = "diamond"):
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.crystal_type = crystal_type
        
        # Dimensions
        self.size = random.uniform(30, 60)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-20, 20)
        
        # Floating animation
        self.float_offset = random.uniform(0, math.pi * 2)
        self.float_speed = random.uniform(0.5, 1.5)
        self.float_amplitude = random.uniform(10, 25)
        
        # Color scheme
        hue = random.choice([200, 280, 320, 60, 180])  # Blue, purple, pink, gold, cyan
        self.base_color = QColor.fromHsv(hue, 200, 255)
        self.glow_color = QColor.fromHsv(hue, 150, 255, 150)
        
        # Facets for realistic crystal look
        self.facets = self._generate_facets()
    
    def _generate_facets(self) -> List[Tuple[float, float]]:
        """Generate crystal facet points"""
        facets = []
        num_facets = random.randint(5, 8)
        for i in range(num_facets):
            angle = (i / num_facets) * math.pi * 2
            r = self.size * random.uniform(0.7, 1.0)
            facets.append((math.cos(angle) * r, math.sin(angle) * r))
        return facets
    
    def update(self, dt: float, time: float):
        """Update crystal position and rotation"""
        self.rotation += self.rotation_speed * dt
        
        # Floating motion
        float_y = math.sin(time * self.float_speed + self.float_offset) * self.float_amplitude
        float_x = math.cos(time * self.float_speed * 0.5 + self.float_offset) * self.float_amplitude * 0.3
        
        self.x = self.base_x + float_x
        self.y = self.base_y + float_y
    
    def draw(self, painter: QPainter, center_x: float, center_y: float):
        """Draw the crystal with all facets"""
        painter.save()
        painter.translate(self.x - center_x + 150, self.y - center_y + 100)
        painter.rotate(self.rotation)
        
        # Outer glow
        glow_gradient = QRadialGradient(0, 0, self.size * 1.5)
        glow_gradient.setColorAt(0.0, QColor(self.glow_color.red(), 
                                              self.glow_color.green(), 
                                              self.glow_color.blue(), 100))
        glow_gradient.setColorAt(1.0, QColor(self.glow_color.red(), 
                                              self.glow_color.green(), 
                                              self.glow_color.blue(), 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(-self.size * 1.5), int(-self.size * 1.5), 
                           int(self.size * 3), int(self.size * 3))
        
        # Draw main crystal body
        if self.crystal_type == "diamond":
            self._draw_diamond(painter)
        elif self.crystal_type == "hexagon":
            self._draw_hexagon(painter)
        elif self.crystal_type == "triangle":
            self._draw_triangle(painter)
        else:
            self._draw_polygon(painter)
        
        painter.restore()
    
    def _draw_diamond(self, painter: QPainter):
        """Draw diamond-shaped crystal with facets"""
        # Top half (crown)
        crown_gradient = QLinearGradient(0, -self.size, 0, 0)
        crown_gradient.setColorAt(0.0, self.base_color.lighter(150))
        crown_gradient.setColorAt(0.5, self.base_color)
        crown_gradient.setColorAt(1.0, self.base_color.darker(120))
        
        crown = QPainterPath()
        crown.moveTo(0, -self.size)
        crown.lineTo(-self.size * 0.6, 0)
        crown.lineTo(self.size * 0.6, 0)
        crown.closeSubpath()
        painter.fillPath(crown, QBrush(crown_gradient))
        painter.setPen(QPen(self.base_color.darker(150), 1.5))
        painter.drawPath(crown)
        
        # Bottom half (pavilion)
        pavilion_gradient = QLinearGradient(0, 0, 0, self.size)
        pavilion_gradient.setColorAt(0.0, self.base_color)
        pavilion_gradient.setColorAt(1.0, self.base_color.darker(180))
        
        pavilion = QPainterPath()
        pavilion.moveTo(-self.size * 0.6, 0)
        pavilion.lineTo(0, self.size)
        pavilion.lineTo(self.size * 0.6, 0)
        pavilion.closeSubpath()
        painter.fillPath(pavilion, QBrush(pavilion_gradient))
        painter.drawPath(pavilion)
        
        # Facet lines for sparkle
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1.0))
        painter.drawLine(0, int(-self.size), 0, 0)
        painter.drawLine(int(-self.size * 0.6), 0, int(self.size * 0.6), 0)
    
    def _draw_hexagon(self, painter: QPainter):
        """Draw hexagonal crystal"""
        path = QPainterPath()
        for i in range(6):
            angle = i * math.pi / 3
            x = math.cos(angle) * self.size
            y = math.sin(angle) * self.size
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        
        # Gradient fill
        gradient = QConicalGradient(0, 0, self.rotation)
        gradient.setColorAt(0.0, self.base_color.lighter(120))
        gradient.setColorAt(0.5, self.base_color)
        gradient.setColorAt(1.0, self.base_color.lighter(120))
        
        painter.fillPath(path, QBrush(gradient))
        painter.setPen(QPen(self.base_color.darker(150), 2.0))
        painter.drawPath(path)
        
        # Inner hexagon
        inner_path = QPainterPath()
        for i in range(6):
            angle = i * math.pi / 3
            x = math.cos(angle) * self.size * 0.5
            y = math.sin(angle) * self.size * 0.5
            if i == 0:
                inner_path.moveTo(x, y)
            else:
                inner_path.lineTo(x, y)
        inner_path.closeSubpath()
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1.0))
        painter.drawPath(inner_path)
    
    def _draw_triangle(self, painter: QPainter):
        """Draw triangular crystal (tetrahedron-like)"""
        gradient = QLinearGradient(0, -self.size, 0, self.size * 0.5)
        gradient.setColorAt(0.0, self.base_color.lighter(180))
        gradient.setColorAt(0.5, self.base_color)
        gradient.setColorAt(1.0, self.base_color.darker(150))
        
        path = QPainterPath()
        path.moveTo(0, -self.size)
        path.lineTo(-self.size * 0.8, self.size * 0.5)
        path.lineTo(self.size * 0.8, self.size * 0.5)
        path.closeSubpath()
        
        painter.fillPath(path, QBrush(gradient))
        painter.setPen(QPen(self.base_color.darker(150), 2.0))
        painter.drawPath(path)
        
        # Inner facet
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.0))
        painter.drawLine(0, int(-self.size * 0.3), 
                        int(-self.size * 0.4), int(self.size * 0.3))
        painter.drawLine(0, int(-self.size * 0.3), 
                        int(self.size * 0.4), int(self.size * 0.3))
    
    def _draw_polygon(self, painter: QPainter):
        """Draw custom polygon crystal"""
        path = QPainterPath()
        for i, (x, y) in enumerate(self.facets):
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        
        gradient = QRadialGradient(0, 0, self.size)
        gradient.setColorAt(0.0, self.base_color.lighter(150))
        gradient.setColorAt(0.7, self.base_color)
        gradient.setColorAt(1.0, self.base_color.darker(150))
        
        painter.fillPath(path, QBrush(gradient))
        painter.setPen(QPen(self.base_color.darker(150), 1.5))
        painter.drawPath(path)


class GeometricShapes(QWidget):
    """
    Floating geometric crystals and shapes
    Non-biological, abstract aesthetic
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
        
        # Position
        self.x = 1920.0
        self.y = 540.0
        self.target_x = self.x
        self.target_y = self.y
        
        # Animation
        self.time = 0.0
        
        # Crystals collection
        self.crystals: List[FloatingCrystal] = []
        self._spawn_crystals()
        
        # Connection lines between crystals
        self.connections_enabled = True
        self.max_connection_dist = 150
        
        self.resize(300, 200)
        self.move(int(self.x - 150), int(self.y - 100))
    
    def _spawn_crystals(self):
        """Create initial crystal formation"""
        crystal_types = ["diamond", "hexagon", "triangle", "polygon"]
        
        # Spawn 5-7 crystals in a cluster
        for i in range(random.randint(5, 7)):
            offset_x = random.uniform(-100, 100)
            offset_y = random.uniform(-60, 60)
            crystal_type = random.choice(crystal_types)
            
            crystal = FloatingCrystal(
                x=150 + offset_x,
                y=100 + offset_y,
                crystal_type=crystal_type
            )
            self.crystals.append(crystal)
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update geometric formation"""
        self.time += dt
        
        # Smooth movement to target
        dx = target_x - self.x
        dy = target_y - self.y
        
        self.x += dx * 2.0 * dt
        self.y += dy * 2.0 * dt
        
        # Update all crystals
        for crystal in self.crystals:
            crystal.update(dt, self.time)
        
        # Update window position
        self.move(int(self.x - 150), int(self.y - 100))
        self.update()
    
    def paintEvent(self, event):
        """Render geometric shapes"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Draw connection lines
        if self.connections_enabled:
            self._draw_connections(painter)
        
        # Draw all crystals
        for crystal in self.crystals:
            crystal.draw(painter, self.x, self.y)
        
        # Draw sacred geometry overlay
        self._draw_sacred_geometry(painter)
    
    def _draw_connections(self, painter: QPainter):
        """Draw energy lines between nearby crystals"""
        for i, c1 in enumerate(self.crystals):
            for c2 in self.crystals[i+1:]:
                dist = math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2)
                
                if dist < self.max_connection_dist:
                    alpha = int(100 * (1 - dist / self.max_connection_dist))
                    
                    # Pulsing effect
                    pulse = 0.7 + 0.3 * math.sin(self.time * 3 + i)
                    alpha = int(alpha * pulse)
                    
                    line_color = QColor(200, 220, 255, alpha)
                    painter.setPen(QPen(line_color, 1.5))
                    
                    painter.drawLine(
                        int(c1.x - self.x + 150), int(c1.y - self.y + 100),
                        int(c2.x - self.x + 150), int(c2.y - self.y + 100)
                    )
    
    def _draw_sacred_geometry(self, painter: QPainter):
        """Draw subtle sacred geometry pattern"""
        center_x = 150
        center_y = 100
        
        # Rotating flower of life pattern
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.time * 5)
        
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw seed of life
        radius = 80
        for i in range(6):
            angle = i * math.pi / 3
            cx = math.cos(angle) * radius * 0.5
            cy = math.sin(angle) * radius * 0.5
            painter.drawEllipse(int(cx - radius * 0.5), int(cy - radius * 0.5),
                               int(radius), int(radius))
        
        painter.restore()
