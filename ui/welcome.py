"""
First-Run Welcome Guide for Ohverlay.
Displays onboarding instructions directing the user to the system tray.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication
from utils.logger import logger


class WelcomeGuide(QWidget):
    """Compact onboarding window that guides users to the system tray icon."""

    open_control_center_requested = Signal()

    def __init__(self, config=None, tray=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.tray = tray

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        self._build_ui()
        self._position_near_tray()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        card = QFrame(self)
        card.setObjectName("cardFrame")
        card.setStyleSheet("""
            #cardFrame {
                background-color: rgba(17, 19, 24, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            QLabel {
                color: #f0f2f5;
                font-family: 'Arial', sans-serif;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
                font-family: 'Arial', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton#gotItBtn {
                background-color: #2563eb;
                border: 1px solid #3b82f6;
                color: #ffffff;
            }
            QPushButton#gotItBtn:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
            }
        """)

        # Glow shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Welcome to Ohverlay", card)
        title_font = QFont("Arial", 13, QFont.Bold)
        title_label.setFont(title_font)

        close_btn = QPushButton("×", card)
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9ea4b0;
                font-size: 16px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 11px;
            }
        """)
        close_btn.clicked.connect(self.close)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)

        # Body text
        body_label = QLabel(
            "Ohverlay is running quietly in your system tray.<br/>"
            "Look for the glowing <b>O</b> icon near the clock—or inside the <b>^</b> hidden-icons menu to open your Vintage Controls.",
            card
        )
        body_label.setTextFormat(Qt.RichText)
        body_label.setWordWrap(True)
        body_label.setFont(QFont("Arial", 10))

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_controls = QPushButton("Open Vintage Controls", card)
        btn_controls.clicked.connect(self._on_open_controls)

        btn_show = QPushButton("Show Me Where", card)
        btn_show.clicked.connect(self._on_show_me_where)

        btn_gotit = QPushButton("Got It", card)
        btn_gotit.setObjectName("gotItBtn")
        btn_gotit.clicked.connect(self._on_got_it)

        btn_layout.addWidget(btn_controls)
        btn_layout.addWidget(btn_show)
        btn_layout.addWidget(btn_gotit)

        card_layout.addLayout(header_layout)
        card_layout.addWidget(body_label)
        card_layout.addLayout(btn_layout)

        main_layout.addWidget(card)
        self.setFixedWidth(380)

    def _position_near_tray(self):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - 16
        y = geo.bottom() - self.sizeHint().height() - 16
        self.move(max(geo.left() + 16, x), max(geo.top() + 16, y))

    def _on_open_controls(self):
        self.open_control_center_requested.emit()
        self.close()

    def _on_show_me_where(self):
        if self.tray:
            self.tray.showMessage(
                "Ohverlay",
                "Ohverlay is running here! Click the glowing O or ^ menu to open controls.",
                self.tray.icon(),
                4000
            )

    def _on_got_it(self):
        if self.config:
            self.config.set("onboarding", "welcome_completed", True)
            self.config.save()
        logger.info("Onboarding completed by user.")
        self.close()
