"""
Energy Orbs v1.0 - Non-Biological Objects
Glowing orbs with dynamic light trails and particle bursts
"""

import math
import random
from typing import List
from dataclasses import dataclass, field
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter, QColor, QRadialGradient, 
    QLinearGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget


@dataclass
class TrailPoint:
    """Single point in a light trail"""
    x: float
    y: float
    life: float = 1.0
    size: float = 4.0


@dataclass
class EnergyOrb:
    """Individual energy orb with trail"""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    hue: int = 200
    size: float = 15.0
    trail: List[TrailPoint] = field(default_factory=list)
    pulse_phase: float = 0.0
    
    def __post_init__(self):
        self.base_size = self.size
        self.trail_color = QColor.fromHsv(self.hue, 200, 255)
        self.core_color = QColor.fromHsv(self.hue, 100, 255)
    
    def update(self, dt: float, target_x: float, target_y: float):
        """Update orb physics and trail"""
        # Seek target with some noise
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Add some chaotic movement
            noise_x = math.sin(self.pulse_phase * 2) * 50
            noise_y = math.cos(self.pulse_phase * 1.5) * 50
            
            ax = (dx / dist) * 80 + noise_x
            ay = (dy / dist) * 80 + noise_y
            
            self.vx += ax * dt
            self.vy += ay * dt
        
        # Damping
        self.vx *= 0.92
        self.vy *= 0.92
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Update pulse
        self.pulse_phase += dt * 3
        
        # Pulsing size
        pulse = 1.0 + 0.2 * math.sin(self.pulse_phase)
        self.size = self.base_size * pulse
        
        # Add trail point
        if dist > 5 or random.random() < 0.3:
            self.trail.append(TrailPoint(
                x=self.x,
                y=self.y,
                life=1.0,
                size=self.size * 0.6
            ))
        
        # Update trail
        for point in self.trail:
            point.life -= dt * 0.8
        
        # Remove dead trail points
        self.trail = [p for p in self.trail if p.life > 0]
    
    def draw(self, painter: QPainter, offset_x: float, offset_y: float):
        """Draw orb and its trail"""
        # Draw trail first (behind orb)
        if len(self.trail) > 1:
            self._draw_trail(painter, offset_x, offset_y)
        
        # Draw orb glow
        cx = self.x - offset_x + 200
        cy = self.y - offset_y + 150
        
        # Outer glow
        outer_glow = QRadialGradient(cx, cy, self.size * 3)
        outer_glow.setColorAt(0.0, QColor(self.core_color.red(),
                                           self.core_color.green(),
                                           self.core_color.blue(), 80))
        outer_glow.setColorAt(0.5, QColor(self.trail_color.red(),
                                           self.trail_color.green(),
                                           self.trail_color.blue(), 40))
        outer_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(outer_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - self.size * 3), int(cy - self.size * 3),
                           int(self.size * 6), int(self.size * 6))
        
        # Middle glow
        mid_glow = QRadialGradient(cx, cy, self.size * 1.5)
        mid_glow.setColorAt(0.0, QColor(255, 255, 255, 200))
        mid_glow.setColorAt(0.3, self.core_color)
        mid_glow.setColorAt(1.0, QColor(self.trail_color.red(),
                                         self.trail_color.green(),
                                         self.trail_color.blue(), 0))
        
        painter.setBrush(QBrush(mid_glow))
        painter.drawEllipse(int(cx - self.size * 1.5), int(cy - self.size * 1.5),
                           int(self.size * 3), int(self.size * 3))
        
        # Core
        core_gradient = QRadialGradient(cx - self.size*0.2, cy - self.size*0.2, self.size * 0.5)
        core_gradient.setColorAt(0.0, QColor(255, 255, 255, 250))
        core_gradient.setColorAt(1.0, self.core_color)
        
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(int(cx - self.size * 0.5), int(cy - self.size * 0.5),
                           int(self.size), int(self.size))
    
    def _draw_trail(self, painter: QPainter, offset_x: float, offset_y: float):
        """Draw the light trail"""
        if len(self.trail) < 2:
            return
        
        # Draw as connected curves
        for i in range(len(self.trail) - 1):
            p1 = self.trail[i]
            p2 = self.trail[i + 1]
            
            # Calculate positions
            x1 = p1.x - offset_x + 200
            y1 = p1.y - offset_y + 150
            x2 = p2.x - offset_x + 200
            y2 = p2.y - offset_y + 150
            
            # Alpha based on life
            alpha = int(200 * p1.life)
            width = p1.size * p1.life
            
            # Gradient color along trail
            trail_color = QColor.fromHsv(
                self.hue,
                int(200 * p1.life),
                255,
                alpha
            )
            
            painter.setPen(QPen(trail_color, width, 
                               Qt.PenStyle.SolidLine, 
                               Qt.PenCapStyle.RoundCap))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))


@dataclass
class Particle:
    """Burst particle"""
    x: float
    y: float
    vx: float
    vy: float
    life: float = 1.0
    hue: int = 200
    size: float = 3.0
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= dt
        self.size *= 0.98


class EnergyOrbSystem(QWidget):
    """
    System of energy orbs with light trails
    Creates flowing, organic light patterns
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
        
        # Orbs collection
        self.orbs: List[EnergyOrb] = []
        self.particles: List[Particle] = []
        
        # Create orb swarm
        hues = [200, 280, 320, 60, 180]  # Blue, purple, pink, gold, cyan
        for i, hue in enumerate(hues):
            angle = (i / len(hues)) * math.pi * 2
            dist = 80
            orb = EnergyOrb(
                x=self.x + math.cos(angle) * dist,
                y=self.y + math.sin(angle) * dist,
                hue=hue,
                size=random.uniform(12, 20)
            )
            self.orbs.append(orb)
        
        # Burst timer
        self.burst_timer = 0.0
        self.time = 0.0
        
        self.resize(400, 300)
        self.move(int(self.x - 200), int(self.y - 150))
    
    def trigger_burst(self):
        """Create particle burst at each orb"""
        for orb in self.orbs:
            for _ in range(8):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(50, 150)
                particle = Particle(
                    x=orb.x,
                    y=orb.y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    hue=orb.hue,
                    size=random.uniform(2, 5)
                )
                self.particles.append(particle)
    
    def update_state(self, dt: float, target_x: float, target_y: float):
        """Update energy orb system"""
        self.time += dt
        
        # Smooth follow with delay
        dx = target_x - self.x
        dy = target_y - self.y
        self.x += dx * 1.5 * dt
        self.y += dy * 1.5 * dt
        
        # Orbiting target positions for each orb
        for i, orb in enumerate(self.orbs):
            angle = (i / len(self.orbs)) * math.pi * 2 + self.time * 0.5
            orbit_dist = 60 + 20 * math.sin(self.time + i)
            
            target_orb_x = self.x + math.cos(angle) * orbit_dist
            target_orb_y = self.y + math.sin(angle) * orbit_dist
            
            orb.update(dt, target_orb_x, target_orb_y)
        
        # Update particles
        for particle in self.particles:
            particle.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]
        
        # Random bursts
        self.burst_timer += dt
        if self.burst_timer > 3.0:
            self.trigger_burst()
            self.burst_timer = 0.0
        
        # Update window position (follow smoothly)
        self.move(int(self.x - 200), int(self.y - 150))
        self.update()
    
    def paintEvent(self, event):
        """Render energy orbs and effects"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Draw particles first (behind orbs)
        for particle in self.particles:
            if particle.life <= 0:
                continue
            
            px = particle.x - self.x + 200
            py = particle.y - self.y + 150
            
            alpha = int(255 * particle.life)
            color = QColor.fromHsv(particle.hue, 200, 255, alpha)
            
            # Glow
            glow = QRadialGradient(px, py, particle.size * 3)
            glow.setColorAt(0.0, color)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(px - particle.size * 3), int(py - particle.size * 3),
                               int(particle.size * 6), int(particle.size * 6))
        
        # Draw connection lines between orbs
        self._draw_orb_connections(painter)
        
        # Draw orbs
        for orb in self.orbs:
            orb.draw(painter, self.x, self.y)
    
    def _draw_orb_connections(self, painter: QPainter):
        """Draw energy connections between orbs"""
        if len(self.orbs) < 2:
            return
        
        # Draw pentagon connections
        for i in range(len(self.orbs)):
            orb1 = self.orbs[i]
            orb2 = self.orbs[(i + 1) % len(self.orbs)]
            
            x1 = orb1.x - self.x + 200
            y1 = orb1.y - self.y + 150
            x2 = orb2.x - self.x + 200
            y2 = orb2.y - self.y + 150
            
            # Pulsing alpha
            alpha = int(60 + 40 * math.sin(self.time * 2 + i))
            
            # Gradient line
            gradient = QLinearGradient(x1, y1, x2, y2)
            gradient.setColorAt(0.0, QColor(orb1.trail_color.red(),
                                             orb1.trail_color.green(),
                                             orb1.trail_color.blue(), alpha))
            gradient.setColorAt(1.0, QColor(orb2.trail_color.red(),
                                             orb2.trail_color.green(),
                                             orb2.trail_color.blue(), alpha))
            
            painter.setPen(QPen(QBrush(gradient), 2.0))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
