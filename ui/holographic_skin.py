"""
Holographic Interface v1.0 - Non-Biological Objects
Sci-fi holographic displays with data visualization
"""

import math
import random
from typing import List
from dataclasses import dataclass
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, 
    QRadialGradient, QPen, QBrush, QFont
)
from PySide6.QtWidgets import QWidget


@dataclass
class HologramElement:
    """Individual holographic UI element"""
    x: float
    y: float
    element_type: str = "ring"  # ring, bar, hex, text
    size: float = 50.0
    rotation: float = 0.0
    rotation_speed: float = 10.0
    color_hue: int = 180
    data_value: float = 0.5  # For bars/graphs
    
    def __post_init__(self):
        self.base_color = QColor.fromHsv(self.color_hue, 150, 255)
        self.glow_color = QColor.fromHsv(self.color_hue, 100, 255, 150)
        self.glitch_timer = 0.0
        self.glitch_active = False
    
    def update(self, dt: float, time: float):
        self.rotation += self.rotation_speed * dt
        self.glitch_timer -= dt
        
        # Random glitch effect
        if self.glitch_timer <= 0:
            self.glitch_active = random.random() < 0.05
            self.glitch_timer = random.uniform(0.1, 0.5)
        
        # Data animation
        if self.element_type == "bar":
            self.data_value = 0.3 + 0.4 * (0.5 + 0.5 * math.sin(time * 2 + self.x * 0.01))
    
    def draw(self, painter: QPainter, offset_x: float, offset_y: float, time: float):
        """Draw holographic element"""
        cx = self.x - offset_x + 200
        cy = self.y - offset_y + 150
        
        if self.element_type == "ring":
            self._draw_ring(painter, cx, cy, time)
        elif self.element_type == "hex":
            self._draw_hex(painter, cx, cy, time)
        elif self.element_type == "bar":
            self._draw_bar(painter, cx, cy, time)
        elif self.element_type == "text":
            self._draw_text(painter, cx, cy, time)
        elif self.element_type == "wave":
            self._draw_wave(painter, cx, cy, time)
    
    def _draw_ring(self, painter: QPainter, cx: float, cy: float, time: float):
        """Draw rotating holographic ring"""
        # Outer glow
        glow = QRadialGradient(cx, cy, self.size * 1.2)
        glow.setColorAt(0.0, QColor(self.glow_color.red(),
                                     self.glow_color.green(),
                                     self.glow_color.blue(), 50))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - self.size * 1.2), int(cy - self.size * 1.2),
                           int(self.size * 2.4), int(self.size * 2.4))
        
        # Main ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation)
        
        # Arc segments
        segments = 4
        for i in range(segments):
            angle_start = i * (360 / segments) + 10
            angle_span = (360 / segments) - 20
            
            alpha = 200 if not self.glitch_active else 100
            color = QColor(self.base_color.red(),
                          self.base_color.green(),
                          self.base_color.blue(), alpha)
            
            pen = QPen(color, 2.0)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            painter.drawArc(int(-self.size), int(-self.size),
                           int(self.size * 2), int(self.size * 2),
                           int(angle_start * 16), int(angle_span * 16))
        
        # Inner rotating ring (opposite direction)
        painter.rotate(-self.rotation * 2)
        inner_color = QColor(self.base_color.red(),
                            self.base_color.green(),
                            self.base_color.blue(), 150)
        painter.setPen(QPen(inner_color, 1.5))
        painter.drawEllipse(int(-self.size * 0.6), int(-self.size * 0.6),
                           int(self.size * 1.2), int(self.size * 1.2))
        
        painter.restore()
        
        # Scan line effect
        scan_y = cy - self.size + (self.size * 2) * ((time * 0.5 + self.x * 0.001) % 1.0)
        scan_color = QColor(self.base_color.red(),
                           self.base_color.green(),
                           self.base_color.blue(), 100)
        painter.setPen(QPen(scan_color, 2.0))
        painter.drawLine(int(cx - self.size * 0.8), int(scan_y),
                        int(cx + self.size * 0.8), int(scan_y))
    
    def _draw_hex(self, painter: QPainter, cx: float, cy: float, time: float):
        """Draw hexagonal holographic node"""
        # Glow
        glow = QRadialGradient(cx, cy, self.size)
        glow.setColorAt(0.0, QColor(self.glow_color.red(),
                                     self.glow_color.green(),
                                     self.glow_color.blue(), 100))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - self.size), int(cy - self.size),
                           int(self.size * 2), int(self.size * 2))
        
        # Hexagon
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation * 0.3)
        
        path = QPainterPath()
        for i in range(6):
            angle = i * math.pi / 3
            x = math.cos(angle) * self.size * 0.7
            y = math.sin(angle) * self.size * 0.7
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        
        alpha = 180 if not self.glitch_active else 80
        color = QColor(self.base_color.red(),
                      self.base_color.green(),
                      self.base_color.blue(), alpha)
        
        painter.setPen(QPen(color, 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Inner hexagon
        inner_path = QPainterPath()
        for i in range(6):
            angle = i * math.pi / 3
            x = math.cos(angle) * self.size * 0.4
            y = math.sin(angle) * self.size * 0.4
            if i == 0:
                inner_path.moveTo(x, y)
            else:
                inner_path.lineTo(x, y)
        inner_path.closeSubpath()
        
        inner_alpha = 120 if not self.glitch_active else 60
        inner_color = QColor(self.base_color.red(),
                            self.base_color.green(),
                            self.base_color.blue(), inner_alpha)
        painter.setPen(QPen(inner_color, 1.5))
        painter.drawPath(inner_path)
        
        # Center point
        painter.setBrush(QBrush(self.base_color))
        painter.drawEllipse(int(-3), int(-3), 6, 6)
        
        painter.restore()
    
    def _draw_bar(self, painter: QPainter, cx: float, cy: float, time: float):
        """Draw holographic data bar"""
        bar_width = self.size * 0.3
        bar_height = self.size * 1.5
        
        # Background bar
        bg_color = QColor(self.base_color.red(),
                         self.base_color.green(),
                         self.base_color.blue(), 50)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(int(cx - bar_width/2), int(cy - bar_height/2),
                        int(bar_width), int(bar_height))
        
        # Active bar
        active_height = bar_height * self.data_value
        
        gradient = QLinearGradient(cx, cy + bar_height/2, cx, cy + bar_height/2 - active_height)
        gradient.setColorAt(0.0, self.base_color)
        gradient.setColorAt(1.0, self.base_color.lighter(150))
        
        painter.setBrush(QBrush(gradient))
        painter.drawRect(int(cx - bar_width/2), int(cy + bar_height/2 - active_height),
                        int(bar_width), int(active_height))
        
        # Value indicator
        indicator_y = cy + bar_height/2 - active_height
        painter.setPen(QPen(QColor(255, 255, 255, 200), 2.0))
        painter.drawLine(int(cx - bar_width), int(indicator_y),
                        int(cx + bar_width), int(indicator_y))
    
    def _draw_text(self, painter: QPainter, cx: float, cy: float, time: float):
        """Draw holographic text/data"""
        # Simplified binary/data visualization
        font = QFont("Consolas", 8)
        painter.setFont(font)
        
        alpha = 200 if not self.glitch_active else 100
        color = QColor(self.base_color.red(),
                      self.base_color.green(),
                      self.base_color.blue(), alpha)
        painter.setPen(QPen(color))
        
        # Draw random-looking data
        for i in range(3):
            y = cy - 10 + i * 10
            text = "".join([str(random.randint(0, 1)) for _ in range(8)])
            painter.drawText(int(cx - 30), int(y), text)
    
    def _draw_wave(self, painter: QPainter, cx: float, cy: float, time: float):
        """Draw waveform visualization"""
        wave_width = self.size * 2
        wave_height = self.size * 0.5
        
        path = QPainterPath()
        path.moveTo(cx - wave_width/2, cy)
        
        points = 50
        for i in range(points):
            x = cx - wave_width/2 + (wave_width / points) * i
            # Combine sine waves for complex pattern
            y = cy + math.sin(i * 0.3 + time * 3) * wave_height * 0.3
            y += math.sin(i * 0.1 + time * 2) * wave_height * 0.2
            y += math.sin(i * 0.5 - time * 4) * wave_height * 0.15
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        alpha = 220 if not self.glitch_active else 120
        color = QColor(self.base_color.red(),
                      self.base_color.green(),
                      self.base_color.blue(), alpha)
        
        painter.setPen(QPen(color, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Fill under wave
        fill_path = QPainterPath(path)
        fill_path.lineTo(cx + wave_width/2, cy + wave_height)
        fill_path.lineTo(cx - wave_width/2, cy + wave_height)
        fill_path.closeSubpath()
        
        fill_color = QColor(self.base_color.red(),
                           self.base_color.green(),
                           self.base_color.blue(), 40)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(fill_path)


class HolographicInterface(QWidget):
    """
    Sci-fi holographic interface display
    Multiple holographic UI elements floating in space
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
        
        # Elements
        self.elements: List[HologramElement] = []
        self._create_elements()
        
        # Grid lines
        self.grid_alpha = 30
        self.time = 0.0
        
        self.resize(400, 300)
        self.move(int(self.x - 200), int(self.y - 150))
    
    def _create_elements(self):
        """Create holographic UI elements"""
        element_configs = [
            ("ring", 100, 75, 60, 20, 180),
            ("hex", 300, 75, 40, -30, 200),
            ("bar", 200, 200, 35, 0, 280),
            ("wave", 100, 225, 50, 0, 320),
            ("text", 300, 200, 30, 0, 60),
        ]
        
        for elem_type, x, y, size, rot_speed, hue in element_configs:
            elem = HologramElement(
                x=x, y=y,
                element_type=elem_type,
                size=size,
                rotation_speed=rot_speed,
                color_hue=hue
            )
            self.elements.append(elem)
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update holographic interface"""
        self.time += dt
        
        # Smooth follow
        dx = target_x - self.x
        dy = target_y - self.y
        self.x += dx * 1.0 * dt
        self.y += dy * 1.0 * dt
        
        # Update elements
        for elem in self.elements:
            elem.update(dt, self.time)
        
        self.move(int(self.x - 200), int(self.y - 150))
        self.update()
    
    def paintEvent(self, event):
        """Render holographic interface"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Draw grid background
        self._draw_grid(painter)
        
        # Draw connecting lines between elements
        self._draw_connections(painter)
        
        # Draw elements
        for elem in self.elements:
            elem.draw(painter, self.x, self.y, self.time)
        
        # Draw scanlines overlay
        self._draw_scanlines(painter)
    
    def _draw_grid(self, painter: QPainter):
        """Draw holographic grid"""
        grid_color = QColor(100, 200, 255, self.grid_alpha)
        painter.setPen(QPen(grid_color, 1.0))
        
        # Perspective grid effect
        center_x = 200
        center_y = 150
        
        # Horizontal lines
        for i in range(-3, 4):
            y = center_y + i * 40
            # Fade edges
            painter.setPen(QPen(grid_color, 1.0))
            painter.drawLine(50, int(y), 350, int(y))
        
        # Vertical lines
        for i in range(-4, 5):
            x = center_x + i * 40
            painter.drawLine(int(x), 50, int(x), 250)
    
    def _draw_connections(self, painter: QPainter):
        """Draw data connections between elements"""
        if len(self.elements) < 2:
            return
        
        for i in range(len(self.elements)):
            elem1 = self.elements[i]
            elem2 = self.elements[(i + 1) % len(self.elements)]
            
            x1 = elem1.x - self.x + 200
            y1 = elem1.y - self.y + 150
            x2 = elem2.x - self.x + 200
            y2 = elem2.y - self.y + 150
            
            # Animated data flow
            flow = (self.time * 2) % 1.0
            mid_x = x1 + (x2 - x1) * flow
            mid_y = y1 + (y2 - y1) * flow
            
            # Connection line
            line_color = QColor(100, 200, 255, 60)
            painter.setPen(QPen(line_color, 1.0))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Data packet
            packet_color = QColor(200, 255, 255, 200)
            painter.setBrush(QBrush(packet_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(mid_x - 3), int(mid_y - 3), 6, 6)
    
    def _draw_scanlines(self, painter: QPainter):
        """Draw CRT scanline effect"""
        scan_color = QColor(0, 255, 255, 10)
        painter.setPen(QPen(scan_color, 1.0))
        
        for y in range(0, 300, 4):
            painter.drawLine(0, y, 400, y)
