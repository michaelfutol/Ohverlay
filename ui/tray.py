"""
System tray icon and menu for Ohverlay.
Provides a minimal fallback right-click menu and left-click activation for the Control Center.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QPen, QDesktopServices
from PySide6.QtCore import Qt, Signal, QObject, QUrl
import os
from utils.logger import logger


class TraySignals(QObject):
    """Signals emitted by tray actions."""
    open_control_center = Signal()
    open_master_dashboard = Signal()
    new_sticky_note = Signal()
    show_welcome = Signal()
    toggle_visibility = Signal()
    quit_app = Signal()
    debug_canvas_extents = Signal()


class SystemTray(QSystemTrayIcon):
    """System tray icon with minimal fallback menu and left-click Control Center activation."""

    def __init__(self, config=None, overlay_manager=None, parent=None):
        super().__init__(parent)
        self.signals = TraySignals()
        self.config = config
        self.overlay_manager = overlay_manager

        self._create_icon()
        self._create_menu()
        self.setToolTip("Ohverlay — Vintage Controls")
        self.activated.connect(self._on_activated)

    def _create_icon(self):
        """Generate the Ohverlay tray icon — a stylized 'O' with glow."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Outer glow
        glow = QRadialGradient(16, 16, 16)
        glow.setColorAt(0.0, QColor(80, 160, 255, 60))
        glow.setColorAt(0.7, QColor(60, 120, 255, 30))
        glow.setColorAt(1.0, QColor(40, 80, 200, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)

        # Ring (the "O")
        painter.setPen(QPen(QColor(100, 180, 255, 230), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(7, 7, 18, 18)

        # Inner accent dot
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(140, 200, 255, 200))
        painter.drawEllipse(13, 13, 6, 6)

        painter.end()
        self.setIcon(QIcon(pixmap))

    def _create_menu(self):
        """Build minimal fallback right-click context menu."""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px;
                color: #0f172a;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 4px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QMenu::item:disabled {
                color: #94a3b8;
                font-weight: 600;
            }
            QMenu::separator {
                height: 1px;
                background: #e2e8f0;
                margin: 4px 6px;
            }
        """)

        header = menu.addAction("Ohverlay")
        header.setEnabled(False)
        menu.addSeparator()

        dash_action = menu.addAction("Master Task Dashboard")
        dash_action.triggered.connect(self.signals.open_master_dashboard.emit)

        new_note_action = menu.addAction("New Sticky Note")
        new_note_action.triggered.connect(self.signals.new_sticky_note.emit)

        menu.addSeparator()

        ctrl_action = menu.addAction("Open Controls")
        ctrl_action.triggered.connect(self.signals.open_control_center.emit)

        visibility_action = menu.addAction("Toggle All Overlays (Ctrl+Alt+H)")
        visibility_action.triggered.connect(self.signals.toggle_visibility.emit)

        welcome_action = menu.addAction("Show Welcome Guide")
        welcome_action.triggered.connect(self.signals.show_welcome.emit)

        telegrama_action = menu.addAction("Telegrama Mobile Dispatcher ✈️")
        telegrama_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("http://localhost:54321/telegrama")))

        if os.environ.get("OHVERLAY_DEBUG") == "1":
            debug_action = menu.addAction("Debug: Show Canvas Extent")
            debug_action.triggered.connect(self.signals.debug_canvas_extents.emit)

        menu.addSeparator()

        quit_action = menu.addAction("Quit Ohverlay")
        quit_action.triggered.connect(self.signals.quit_app.emit)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        """Handle tray icon clicks."""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.signals.open_control_center.emit()
