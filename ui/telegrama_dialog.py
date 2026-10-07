"""Telegrama pairing dialog — enable the service, pair a phone (QR or link), tune privacy."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QClipboard, QGuiApplication, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

_STYLE = """
QDialog { background: #fbf7ef; }
QLabel { color: #2c251e; font-family: 'Segoe UI'; }
QLabel#title { font-size: 17px; font-weight: 800; letter-spacing: 1px; }
QLabel#hint { color: #7c7062; font-size: 11px; }
QLabel#status { font-size: 12px; font-weight: 600; }
QCheckBox { color: #2c251e; font-family: 'Segoe UI'; font-size: 12px; spacing: 8px; }
QLineEdit { background: #fff; border: 1px solid #e2d7c3; border-radius: 6px; padding: 6px 8px; color: #2c251e; }
QPushButton { background: #c0392b; color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-weight: 600; }
QPushButton:hover { background: #a93226; }
QPushButton#ghost { background: #efe6d6; color: #2c251e; }
QPushButton#ghost:hover { background: #e6dac5; }
"""


def make_qr_pixmap(url: str, size: int = 190) -> Optional[QPixmap]:
    """Render ``url`` as a QR code. Returns None when the optional ``segno`` package is missing."""
    try:
        import io

        import segno
        from PySide6.QtSvg import QSvgRenderer
    except ImportError:
        return None
    try:
        buf = io.BytesIO()
        segno.make(url, error="m").save(buf, kind="svg", scale=8, border=2, dark="#2c251e", light="#ffffff")
        renderer = QSvgRenderer(QByteArray(buf.getvalue()))
        pix = QPixmap(size, size)
        pix.fill(Qt.white)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return pix
    except Exception:
        return None


class TelegramaDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Telegrama — Phone Dispatch")
        self.setStyleSheet(_STYLE)
        self.setMinimumWidth(400)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        title = QLabel("✈️  TELEGRAMA")
        title.setObjectName("title")
        root.addWidget(title)
        hint = QLabel("Receive short, loving reminders from family on your desktop — "
                      "private by default, nothing is online until you turn it on.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.enable_box = QCheckBox("Enable Telegrama on this PC")
        self.lan_box = QCheckBox("Allow phones on my Wi-Fi (requires the pairing link below)")
        self.notify_box = QCheckBox("Show a notification when a telegram arrives")
        for box in (self.enable_box, self.lan_box, self.notify_box):
            root.addWidget(box)

        self.status = QLabel("")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.qr_label)

        self.url_edit = QLineEdit()
        self.url_edit.setReadOnly(True)
        root.addWidget(self.url_edit)

        row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy phone link")
        self.copy_btn.clicked.connect(self._copy)
        self.regen_btn = QPushButton("Reset pairing")
        self.regen_btn.setObjectName("ghost")
        self.regen_btn.setToolTip("Creates a new link. Phones paired with the old link stop working.")
        self.regen_btn.clicked.connect(controller.regenerate_token)
        row.addWidget(self.copy_btn)
        row.addWidget(self.regen_btn)
        root.addLayout(row)

        self.fw_hint = QLabel("Tip: Windows may ask to allow network access the first time you enable Wi-Fi mode — "
                              "choose “Private networks” only.")
        self.fw_hint.setObjectName("hint")
        self.fw_hint.setWordWrap(True)
        root.addWidget(self.fw_hint)

        self.enable_box.toggled.connect(controller.set_enabled)
        self.lan_box.toggled.connect(controller.set_allow_lan)
        self.notify_box.toggled.connect(controller.set_notify)
        controller.state_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        c = self.controller
        for box, value in ((self.enable_box, c.enabled), (self.lan_box, c.allow_lan), (self.notify_box, c.notify)):
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)
        self.lan_box.setEnabled(c.enabled)

        if not c.enabled:
            self.status.setText("● Off — no network listener is running.")
            self.status.setStyleSheet("color:#7c7062;")
        elif not c.running:
            self.status.setText("● Could not start — the port may be in use. Try again in a moment.")
            self.status.setStyleSheet("color:#c0392b;")
        elif c.allow_lan:
            self.status.setText("● On — phones on your Wi-Fi can send with the pairing link.")
            self.status.setStyleSheet("color:#1e8449;")
        else:
            self.status.setText("● On — this PC only (turn on Wi-Fi mode to receive from a phone).")
            self.status.setStyleSheet("color:#b9770e;")

        show_pair = c.running and c.allow_lan
        url = c.phone_url if show_pair else ""
        self.url_edit.setVisible(show_pair)
        self.copy_btn.setVisible(show_pair)
        self.regen_btn.setVisible(show_pair)
        self.fw_hint.setVisible(c.enabled)
        self.url_edit.setText(url)
        pix = make_qr_pixmap(url) if url else None
        self.qr_label.setVisible(pix is not None)
        if pix is not None:
            self.qr_label.setPixmap(pix)

    def _copy(self):
        QGuiApplication.clipboard().setText(self.url_edit.text(), QClipboard.Clipboard)
        self.copy_btn.setText("Copied ✓")
