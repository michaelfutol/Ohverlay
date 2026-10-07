"""
Hot Air Balloon v1.0 - Non-Biological Object
Colorful floating balloon that drifts across the sky
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
class Cloud:
    """Background cloud"""
    x: float
    y: float
    size: float
    alpha: int
    speed: float
    
    def update(self, dt: float):
        self.x -= self.speed * dt
        if self.x < -200:
            self.x = 4000


class HotAirBalloon(QWidget):
    """
    Colorful hot air balloon that floats across the desktop
    Gentle drifting motion with flame animation
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
        
        # Position - start from bottom left
        self.x = 100.0
        self.y = 800.0
        
        # Movement - gentle floating
        self.vx = 30.0  # Wind speed (horizontal)
        self.vy = -5.0  # Slight upward drift
        self.bob_phase = 0.0
        
        # Screen bounds
        self.screen_width = 3840
        self.screen_height = 1080
        
        # Animation
        self.time = 0.0
        self.flame_intensity = 0.0
        
        # Colors - rainbow stripes
        self.stripe_colors = [
            QColor(255, 100, 100),  # Red
            QColor(255, 180, 50),   # Orange
            QColor(255, 255, 80),   # Yellow
            QColor(100, 255, 100),  # Green
            QColor(80, 180, 255),   # Blue
            QColor(180, 100, 255),  # Purple
        ]
        
        # Clouds for atmosphere
        self.clouds: List[Cloud] = []
        self._init_clouds()
        
        # Particles (sparkles)
        self.sparkles: List[dict] = []
        
        self.resize(200, 280)
        self.move(int(self.x - 100), int(self.y - 140))
    
    def _init_clouds(self):
        """Initialize background clouds"""
        for i in range(5):
            self.clouds.append(Cloud(
                x=random.uniform(0, self.screen_width),
                y=random.uniform(100, 600),
                size=random.uniform(60, 120),
                alpha=random.randint(30, 60),
                speed=random.uniform(10, 25)
            ))
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update balloon floating motion"""
        self.time += dt
        
        # Bobbing motion (gentle up and down)
        self.bob_phase += dt * 1.5
        bob_offset = math.sin(self.bob_phase) * 15
        
        # Horizontal drift with wind
        self.x += self.vx * dt
        
        # Vertical drift with bobbing
        self.y += (self.vy + bob_offset * 0.1) * dt
        
        # Wrap around screen
        if self.x > self.screen_width + 150:
            self.x = -150
            self.y = random.uniform(300, 900)  # Random height on respawn
        
        # Keep in vertical bounds
        self.y = max(200, min(self.screen_height - 200, self.y))
        
        # Flame animation
        self.flame_intensity = 0.6 + 0.4 * math.sin(self.time * 8)
        
        # Update clouds
        for cloud in self.clouds:
            cloud.update(dt)
        
        # Add sparkles occasionally
        if random.random() < 0.1:
            self.sparkles.append({
                'x': self.x + random.uniform(-60, 60),
                'y': self.y + random.uniform(-80, 80),
                'life': 1.0,
                'size': random.uniform(2, 5)
            })
        
        # Update sparkles
        for sparkle in self.sparkles[:]:
            sparkle['life'] -= dt * 0.5
            if sparkle['life'] <= 0:
                self.sparkles.remove(sparkle)
        
        self.move(int(self.x - 100), int(self.y - 140))
        self.update()
    
    def paintEvent(self, event):
        """Render hot air balloon"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        cx = 100
        cy = 100
        
        # Draw clouds (background)
        self._draw_clouds(painter)
        
        # Draw balloon shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 30, cy + 120, 60, 20)
        
        # Draw balloon envelope (main balloon)
        self._draw_balloon_envelope(painter, cx, cy)
        
        # Draw basket
        self._draw_basket(painter, cx, cy + 100)
        
        # Draw ropes
        self._draw_ropes(painter, cx, cy)
        
        # Draw flame
        self._draw_flame(painter, cx, cy + 85)
        
        # Draw sparkles
        self._draw_sparkles(painter)
    
    def _draw_clouds(self, painter: QPainter):
        """Draw background clouds"""
        for cloud in self.clouds:
            # Transform to local coordinates
            local_x = cloud.x - self.x + 100
            local_y = cloud.y - self.y + 100
            
            if -200 < local_x < 400 and -100 < local_y < 300:
                gradient = QRadialGradient(local_x, local_y, cloud.size)
                gradient.setColorAt(0.0, QColor(255, 255, 255, cloud.alpha))
                gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
                
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                
                # Puffy cloud shape
                for i in range(3):
                    offset_x = math.sin(i * 2) * cloud.size * 0.3
                    offset_y = math.cos(i * 1.5) * cloud.size * 0.2
                    painter.drawEllipse(
                        int(local_x + offset_x - cloud.size * 0.4),
                        int(local_y + offset_y - cloud.size * 0.3),
                        int(cloud.size * 0.8),
                        int(cloud.size * 0.6)
                    )
    
    def _draw_balloon_envelope(self, painter: QPainter, cx: float, cy: float):
        """Draw the main balloon with colorful stripes"""
        # Balloon dimensions
        balloon_w = 80
        balloon_h = 90
        
        # Draw each stripe
        num_stripes = len(self.stripe_colors)
        stripe_angle = 180 / num_stripes
        
        for i, color in enumerate(self.stripe_colors):
            painter.save()
            
            # Create gradient for 3D effect
            gradient = QRadialGradient(cx - 10, cy - 10, balloon_w)
            gradient.setColorAt(0.0, color.lighter(120))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1.0, color.darker(120))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(color.darker(120), 1))
            
            # Draw stripe as pie slice
            
            # Create stripe path
            stripe_path = QPainterPath()
            stripe_path.moveTo(cx, cy + 80)  # Bottom center
            
            # Arc for top of balloon
            stripe_path.arcTo(
                cx - balloon_w, cy - balloon_h,
                balloon_w * 2, balloon_h * 2,
                180 + i * stripe_angle, stripe_angle
            )
            
            stripe_path.closeSubpath()
            painter.drawPath(stripe_path)
            
            painter.restore()
        
        # Highlight (glossy effect)
        highlight = QRadialGradient(cx - 20, cy - 20, 40)
        highlight.setColorAt(0.0, QColor(255, 255, 255, 80))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 35), int(cy - 45), 40, 50)
    
    def _draw_basket(self, painter: QPainter, cx: float, cy: float):
        """Draw wicker basket"""
        # Basket body
        basket_gradient = QLinearGradient(cx - 15, cy, cx + 15, cy + 30)
        basket_gradient.setColorAt(0.0, QColor(139, 90, 43))  # Light brown
        basket_gradient.setColorAt(0.5, QColor(101, 67, 33))  # Dark brown
        basket_gradient.setColorAt(1.0, QColor(139, 90, 43))
        
        painter.setBrush(QBrush(basket_gradient))
        painter.setPen(QPen(QColor(80, 50, 20), 2))
        
        # Basket shape (trapezoid)
        basket_path = QPainterPath()
        basket_path.moveTo(cx - 15, cy)
        basket_path.lineTo(cx + 15, cy)
        basket_path.lineTo(cx + 18, cy + 30)
        basket_path.lineTo(cx - 18, cy + 30)
        basket_path.closeSubpath()
        painter.drawPath(basket_path)
        
        # Wicker texture lines
        painter.setPen(QPen(QColor(60, 40, 15), 1))
        for i in range(4):
            y = cy + 5 + i * 7
            painter.drawLine(int(cx - 14), int(y), int(cx + 14), int(y))
    
    def _draw_ropes(self, painter: QPainter, cx: float, cy: float):
        """Draw suspension ropes"""
        painter.setPen(QPen(QColor(80, 60, 40), 2))
        
        # Four main ropes from balloon to basket
        rope_points = [
            (cx - 30, cy + 70, cx - 15, cy + 100),  # Left
            (cx + 30, cy + 70, cx + 15, cy + 100),  # Right
            (cx - 15, cy + 75, cx - 10, cy + 100),  # Inner left
            (cx + 15, cy + 75, cx + 10, cy + 100),  # Inner right
        ]
        
        for x1, y1, x2, y2 in rope_points:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_flame(self, painter: QPainter, cx: float, cy: float):
        """Draw burner flame"""
        flame_h = 15 + self.flame_intensity * 10
        
        # Outer flame (orange)
        outer_grad = QRadialGradient(cx, cy - flame_h/2, flame_h)
        outer_grad.setColorAt(0.0, QColor(255, 200, 50, 200))
        outer_grad.setColorAt(0.5, QColor(255, 100, 20, 150))
        outer_grad.setColorAt(1.0, QColor(255, 50, 0, 0))
        
        painter.setBrush(QBrush(outer_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        
        flame_path = QPainterPath()
        flame_path.moveTo(cx - 8, cy)
        flame_path.quadTo(cx - 5, cy - flame_h * 0.5, cx, cy - flame_h)
        flame_path.quadTo(cx + 5, cy - flame_h * 0.5, cx + 8, cy)
        flame_path.closeSubpath()
        painter.drawPath(flame_path)
        
        # Inner flame (white/blue core)
        inner_h = flame_h * 0.6
        inner_grad = QRadialGradient(cx, cy - inner_h/2, inner_h)
        inner_grad.setColorAt(0.0, QColor(255, 255, 200, 220))
        inner_grad.setColorAt(1.0, QColor(255, 200, 100, 0))
        
        painter.setBrush(QBrush(inner_grad))
        inner_path = QPainterPath()
        inner_path.moveTo(cx - 4, cy)
        inner_path.quadTo(cx - 2, cy - inner_h * 0.5, cx, cy - inner_h)
        inner_path.quadTo(cx + 2, cy - inner_h * 0.5, cx + 4, cy)
        inner_path.closeSubpath()
        painter.drawPath(inner_path)
    
    def _draw_sparkles(self, painter: QPainter):
        """Draw sparkle effects"""
        for sparkle in self.sparkles:
            sx = sparkle['x'] - self.x + 100
            sy = sparkle['y'] - self.y + 100
            
            alpha = int(200 * sparkle['life'])
            size = sparkle['size'] * sparkle['life']
            
            gradient = QRadialGradient(sx, sy, size * 2)
            gradient.setColorAt(0.0, QColor(255, 255, 255, alpha))
            gradient.setColorAt(1.0, QColor(255, 255, 200, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(sx - size), int(sy - size), int(size * 2), int(size * 2))
