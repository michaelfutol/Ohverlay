"""
Standalone sticky notes for the NetShare / Ohverlay branch.
"""

from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timedelta

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QCursor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from modules.card_themes import (
    DEFAULT_FONT_PRESET_ID,
    DEFAULT_NOTE_THEME_ID,
    get_font_preset,
    get_note_theme,
    list_font_presets,
    list_note_themes,
    qcolor,
    resolve_font_preset_id,
    resolve_theme_id,
)


def _hex_rgb(spec):
    return f"rgb({spec[0]}, {spec[1]}, {spec[2]})"


def _rgba(spec, alpha_override=None):
    alpha = alpha_override if alpha_override is not None else (spec[3] / 255.0 if len(spec) > 3 else 1.0)
    return f"rgba({spec[0]}, {spec[1]}, {spec[2]}, {alpha:.3f})"


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _format_seconds(total_seconds):
    seconds = abs(int(total_seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    prefix = "-" if total_seconds < 0 else ""
    return f"{prefix}{hours:02d}:{minutes:02d}:{secs:02d}"


def _parse_duration_input(value):
    raw = (value or "").strip().lower()
    if not raw:
        return None

    if ":" in raw:
        parts = raw.split(":")
        if len(parts) in (2, 3) and all(part.strip().isdigit() for part in parts):
            numbers = [int(part.strip()) for part in parts]
            if len(numbers) == 2:
                minutes, seconds = numbers
                total = (minutes * 60) + seconds
            else:
                hours, minutes, seconds = numbers
                total = (hours * 3600) + (minutes * 60) + seconds
            return total if total > 0 else None

    if raw.isdigit():
        minutes = int(raw)
        return minutes * 60 if minutes > 0 else None

    total = 0
    for amount, unit in re.findall(r"(\d+)\s*([hms])", raw):
        amount_int = int(amount)
        if unit == "h":
            total += amount_int * 3600
        elif unit == "m":
            total += amount_int * 60
        else:
            total += amount_int
    return total if total > 0 else None


def _transparent_input_flag():
    return getattr(Qt, "WindowTransparentForInput", None) or getattr(
        getattr(Qt, "WindowType", object()),
        "WindowTransparentForInput",
        None,
    )


def _mix_rgb(left, right, amount):
    amount = max(0.0, min(1.0, float(amount)))
    return tuple(int(left[i] + (right[i] - left[i]) * amount) for i in range(3))


def _make_mode_icon(rgb_spec, *, mode="pin", size=16):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    color = QColor(rgb_spec[0], rgb_spec[1], rgb_spec[2])
    stroke = QPen(color, 1.5)
    stroke.setJoinStyle(Qt.RoundJoin)
    stroke.setCapStyle(Qt.RoundCap)
    painter.setPen(stroke)
    painter.setBrush(Qt.NoBrush)
    if mode == "edit":
        painter.drawLine(4.0, 12.0, 11.2, 4.8)
        painter.drawLine(11.2, 4.8, 12.7, 6.3)
        painter.drawLine(5.2, 13.2, 3.6, 13.6)
        painter.drawLine(3.6, 13.6, 4.0, 12.0)
        painter.drawLine(4.9, 11.1, 6.4, 12.6)
    else:
        painter.drawEllipse(5.1, 2.9, 5.0, 5.0)
        painter.drawLine(7.6, 7.2, 7.6, 11.0)
        painter.drawLine(7.6, 11.0, 4.8, 13.6)
        painter.drawLine(7.6, 11.0, 10.2, 13.2)
        painter.drawLine(6.0, 5.1, 9.2, 5.1)
    painter.end()
    return QIcon(pixmap)


class StickyUnlockChip(QWidget):
    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton("", self)
        self.button.setObjectName("stickyUnlockChip")
        self.button.setToolTip("Edit note")
        self.button.setFixedSize(20, 20)
        self.button.setCursor(QCursor(Qt.PointingHandCursor))
        self.button.clicked.connect(
            lambda: self.owner.manager.set_note_locked(self.owner.state.get("id"), False)
        )
        layout.addWidget(self.button)
        self.hide()

    def apply_theme(self, theme):
        icon_color = theme.text_value if theme.theme_id == "floating_text_light" else theme.text_head
        self.button.setIcon(_make_mode_icon(icon_color, mode="edit"))
        self.button.setIconSize(self.button.size())
        self.button.setStyleSheet(
            f"""
            QPushButton#stickyUnlockChip {{
                background: {_rgba(theme.button_dismiss, 0.82)};
                color: {_hex_rgb(icon_color)};
                border: 1px solid {_rgba(theme.divider, 0.90)};
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton#stickyUnlockChip:hover {{
                background: {_rgba(theme.button_hover, 0.92)};
                color: {_hex_rgb(theme.button_text)};
            }}
            """
        )
        self.adjustSize()


class StickyFrame(QFrame):
    """Custom frame for realistic sticky notes with adhesive top band and curled corner."""

    def __init__(self, note_widget: StickyNoteWidget, parent=None):
        super().__init__(parent)
        self.note_widget = note_widget

    def paintEvent(self, event):
        super().paintEvent(event)
        theme = get_note_theme(self.note_widget.state.get("theme_id", DEFAULT_NOTE_THEME_ID))
        locked = bool(self.note_widget.state.get("locked", False))
        if locked and theme.floating_lock:
            return

        is_paper = (
            theme.theme_id.startswith("sticky_paper_")
            or theme.theme_id.startswith("neon_postit_")
            or theme.sticky_fold
        )
        if not is_paper:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        # 1. Subtle matte top adhesive strip giving authentic Post-it note pad look (no glass shine)
        strip_h = min(18, max(8, int(h * 0.07)))
        adhesive_grad = QLinearGradient(0, 0, 0, strip_h)
        adhesive_grad.setColorAt(0.0, QColor(0, 0, 0, 14))
        adhesive_grad.setColorAt(0.85, QColor(0, 0, 0, 6))
        adhesive_grad.setColorAt(1.0, QColor(0, 0, 0, 20))
        painter.fillRect(1, 1, w - 2, strip_h, adhesive_grad)

        # 2. Curled / peeled bottom-right corner
        if theme.sticky_fold and w >= 120 and h >= 70:
            fold_size = min(22, max(11, int(min(w, h) * 0.10)))
            fold_raw = theme.fold_color or (255, 255, 255, 210)
            fold_col = qcolor(fold_raw)

            # Soft drop shadow under the curled flap
            shadow_path = QPainterPath()
            shadow_path.moveTo(w - fold_size - 4, h)
            shadow_path.lineTo(w, h - fold_size - 4)
            shadow_path.lineTo(w, h)
            shadow_path.closeSubpath()
            painter.fillPath(shadow_path, QColor(0, 0, 0, 36))

            # Lifted curl flap
            curl_path = QPainterPath()
            curl_path.moveTo(w - fold_size, h)
            curl_path.lineTo(w, h - fold_size)
            curl_path.lineTo(w - fold_size, h - fold_size)
            curl_path.closeSubpath()

            curl_grad = QLinearGradient(w - fold_size, h - fold_size, w, h)
            curl_grad.setColorAt(0.0, fold_col.lighter(118))
            curl_grad.setColorAt(0.45, fold_col)
            curl_grad.setColorAt(1.0, fold_col.darker(124))
            painter.fillPath(curl_path, curl_grad)

            # Fold crease highlight line
            crease_pen = QPen(QColor(theme.border[0], theme.border[1], theme.border[2], 110), 1)
            painter.setPen(crease_pen)
            painter.drawLine(w - fold_size, h, w, h - fold_size)

        painter.end()


class StickyNoteWidget(QWidget):
    def __init__(self, manager, state, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.state = dict(state)
        self._base_window_flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self._drag_origin = None
        self._drag_pos = None
        self._overdue_active = False
        self._visual_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timer_label)
        self._timer.start(1000)
        self._visual_timer = QTimer(self)
        self._visual_timer.timeout.connect(self._tick_visuals)
        self._visual_timer.start(180)
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setOffset(0, 0)
        self._glow.setBlurRadius(18)
        self._title_glow = QGraphicsDropShadowEffect(self)
        self._title_glow.setOffset(0, 0)
        self._title_glow.setBlurRadius(0)
        self._title_glow.setEnabled(False)
        self._timer_glow = QGraphicsDropShadowEffect(self)
        self._timer_glow.setOffset(0, 0)
        self._timer_glow.setBlurRadius(0)
        self._timer_glow.setEnabled(False)
        self._text_glow = QGraphicsDropShadowEffect(self)
        self._text_glow.setOffset(0, 0)
        self._text_glow.setBlurRadius(0)
        self._text_glow.setEnabled(False)
        self._unlock_chip = StickyUnlockChip(self)
        self._resize_active = False
        self._resize_mode = None
        self._resize_start_pos = None
        self._resize_start_size = None

        self.setWindowFlags(self._base_window_flags)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setMinimumSize(100, 50)

        self._build_ui()
        self._apply_state()

    def _build_ui(self):
        self.setObjectName("stickyNoteWindow")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.frame = StickyFrame(self, self)
        self.frame.setObjectName("stickyFrame")
        self.frame.setMouseTracking(True)
        self.frame.installEventFilter(self)
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 8, 10, 8)
        frame_layout.setSpacing(4)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        # Title label kept hidden internally for compatibility
        self.title_label = QLabel("")
        self.title_label.setObjectName("stickyTitle")
        self.title_label.hide()

        self.lock_btn = QPushButton("")
        self.lock_btn.setObjectName("stickyMiniButton")
        self.lock_btn.setToolTip("Pin note as overlay")
        self.lock_btn.setFixedSize(20, 20)
        self.lock_btn.clicked.connect(
            lambda: self.manager.set_note_locked(self.state.get("id"), True)
        )
        header.addWidget(self.lock_btn)

        header.addStretch(1)

        self.timer_label = QLabel("--:--:--")
        self.timer_label.setObjectName("stickyTimer")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setGraphicsEffect(self._timer_glow)
        header.addWidget(self.timer_label)

        header.addStretch(1)

        self._header_spacer = QWidget()
        self._header_spacer.setFixedSize(20, 20)
        header.addWidget(self._header_spacer)

        frame_layout.addLayout(header)

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("stickyText")
        self.text_edit.setPlaceholderText("Type your note here...")
        self.text_edit.textChanged.connect(self._on_text_changed)
        frame_layout.addWidget(self.text_edit, 1)

        self.locked_text_label = QLabel("")
        self.locked_text_label.setObjectName("stickyLockedText")
        self.locked_text_label.setWordWrap(True)
        self.locked_text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.locked_text_label.setGraphicsEffect(self._text_glow)
        self.locked_text_label.hide()
        frame_layout.addWidget(self.locked_text_label, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)

        self.meta_label = QLabel("Right-click for options")
        self.meta_label.setObjectName("stickyMeta")
        footer.addWidget(self.meta_label, 1)

        self.action_btn = QPushButton("")
        self.action_btn.setObjectName("stickyActionButton")
        self.action_btn.setVisible(False)
        self.action_btn.clicked.connect(self._trigger_primary_action)
        footer.addWidget(self.action_btn)

        self.secondary_action_btn = QPushButton("")
        self.secondary_action_btn.setObjectName("stickyActionButton")
        self.secondary_action_btn.setVisible(False)
        self.secondary_action_btn.clicked.connect(self._trigger_secondary_action)
        footer.addWidget(self.secondary_action_btn)

        self.menu_btn = QPushButton("⋯")
        self.menu_btn.setObjectName("stickyMiniButton")
        self.menu_btn.setFixedSize(22, 20)
        self.menu_btn.clicked.connect(self._show_options_menu)
        footer.addWidget(self.menu_btn)

        self.smaller_btn = QPushButton("−")
        self.smaller_btn.setObjectName("stickyMiniButton")
        self.smaller_btn.setFixedSize(20, 20)
        self.smaller_btn.clicked.connect(lambda: self._resize_by(-20, -20))
        footer.addWidget(self.smaller_btn)

        self.bigger_btn = QPushButton("+")
        self.bigger_btn.setObjectName("stickyMiniButton")
        self.bigger_btn.setFixedSize(20, 20)
        self.bigger_btn.clicked.connect(lambda: self._resize_by(20, 20))
        footer.addWidget(self.bigger_btn)

        self.send_btn = QPushButton("↗")
        self.send_btn.setObjectName("stickyMiniButton")
        self.send_btn.setToolTip("Send note")
        self.send_btn.setFixedSize(20, 20)
        self.send_btn.clicked.connect(lambda: self.manager.request_share(self))
        footer.addWidget(self.send_btn)

        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("stickyCloseButton")
        self.close_btn.setToolTip("Close note")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self._close_note)
        footer.addWidget(self.close_btn)

        self.size_grip = QSizeGrip(self)
        self.size_grip.setObjectName("stickySizeGrip")
        self.size_grip.setFixedSize(14, 14)
        self.size_grip.setToolTip("Drag corner to resize height and width")
        footer.addWidget(self.size_grip)

        frame_layout.addLayout(footer)
        outer.addWidget(self.frame)
        self.frame.setGraphicsEffect(self._glow)
        self.title_label.setGraphicsEffect(self._title_glow)
        self._unlock_chip.button.setFixedSize(self.lock_btn.size())

    def _apply_state(self):
        self.state["theme_id"] = resolve_theme_id(self.state.get("theme_id", DEFAULT_NOTE_THEME_ID))
        self.state["font_preset"] = resolve_font_preset_id(
            self.state.get("font_preset", DEFAULT_FONT_PRESET_ID)
        )
        if "font_size_px" not in self.state:
            scale = float(self.state.get("font_scale", 1.0))
            self.state["font_size_px"] = max(11, int(15 * scale))
        self.title_label.setText(self.state.get("title", "Sticky Note"))
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(self.state.get("text", ""))
        self.text_edit.blockSignals(False)
        self.resize(max(100, int(self.state.get("width", 240))), max(50, int(self.state.get("height", 260))))
        self.move(int(self.state.get("x", 90)), int(self.state.get("y", 90)))
        self._apply_theme()
        self._refresh_action_button()
        self._update_timer_label()
        self._apply_lock_state(persist=False)
        self.show()

    def _apply_theme(self):
        theme = get_note_theme(self.state.get("theme_id", DEFAULT_NOTE_THEME_ID))
        font_preset = get_font_preset(self.state.get("font_preset", DEFAULT_FONT_PRESET_ID))
        locked = bool(self.state.get("locked", False))
        float_on_lock = locked and theme.floating_lock
        is_paper_theme = theme.theme_id.startswith("sticky_paper_") or theme.theme_id.startswith("neon_postit_")
        base_opacity = max(0.15, min(1.0, float(self.state.get("opacity", 0.95))))
        font_scale = max(0.75, min(2.5, float(self.state.get("font_scale", 1.0))))
        font_size_px = int(self.state.get("font_size_px") or max(11, int(15 * font_scale)))
        accent_spec = theme.accent
        border_spec = theme.border
        title_spec = theme.text_head
        meta_spec = theme.text_label
        glow_spec = theme.glow
        shimmer_spec = theme.border
        pulse_factor = 0.0
        if self._overdue_active:
            pulse_factor = (math.sin(self._visual_phase) + 1.0) / 2.0
            accent_spec = _mix_rgb((255, 210, 122), (186, 245, 255), pulse_factor * 0.60)
            border_spec = _mix_rgb((110, 210, 255), (255, 210, 122), pulse_factor * 0.55)
            title_spec = (246, 250, 255)
            meta_spec = (179, 224, 240)
            glow_spec = _mix_rgb((120, 235, 255), (255, 224, 165), pulse_factor * 0.45)
            shimmer_spec = _mix_rgb((72, 138, 190), (148, 232, 255), pulse_factor)
        pulse_drop = 0.018 + (0.028 * pulse_factor) if self._overdue_active else 0.0
        self.setWindowOpacity(max(0.15, min(1.0, base_opacity - pulse_drop)))

        # Realistic paper shadow lifting sticky note from desktop
        if is_paper_theme and not float_on_lock:
            self._glow.setOffset(0, 5)
            self._glow.setColor(QColor(0, 0, 0, int(85 * base_opacity)))
            self._glow.setBlurRadius(16)
        else:
            self._glow.setOffset(0, 0)
            glow_alpha = int(118 + (42 * pulse_factor)) if self._overdue_active else (46 if is_paper_theme else 80)
            glow_blur = int(24 + (18 * pulse_factor)) if self._overdue_active else (12 if is_paper_theme else 18)
            self._glow.setColor(qcolor(glow_spec, 92 if float_on_lock else glow_alpha))
            self._glow.setBlurRadius(24 if float_on_lock else glow_blur)
        self._glow.setEnabled(True)

        text_glow_color = theme.text_glow_color or (glow_spec + (210,) if len(glow_spec) == 3 else glow_spec)
        text_glow_blur = int(theme.text_glow_blur or 0)
        if float_on_lock and text_glow_blur <= 0:
            text_glow_blur = 14
        enable_text_glow = (text_glow_blur > 0) and (not is_paper_theme)
        for effect in (self._title_glow, self._timer_glow, self._text_glow):
            effect.setEnabled(enable_text_glow)
            if enable_text_glow:
                effect.setColor(qcolor(text_glow_color[:3] if len(text_glow_color) >= 3 else glow_spec, text_glow_color[3] if len(text_glow_color) == 4 else 190))
                effect.setBlurRadius(text_glow_blur)

        body_top_spec = theme.bg_top
        body_bottom_spec = theme.bg_bottom
        if self._overdue_active:
            body_top_spec = _mix_rgb(theme.bg_top[:3], (20, 48, 70), 0.35 + (pulse_factor * 0.12))
            body_bottom_spec = _mix_rgb(theme.bg_bottom[:3], (10, 22, 36), 0.24 + (pulse_factor * 0.10))

        title_font_family = font_preset.title_family or theme.title_font_family
        label_font_family = font_preset.label_family or theme.label_font_family
        value_font_family = font_preset.value_family or theme.value_font_family
        button_font_family = font_preset.button_family or theme.button_font_family

        if is_paper_theme:
            frame_bg = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {_hex_rgb(body_top_spec)}, stop:1 {_hex_rgb(body_bottom_spec)})"
            editor_bg = "transparent"
            editor_border = "transparent"
            text_color = "#111111"
            timer_color = "#111111" if not self._overdue_active else "#dc2626"
            timer_bg = "transparent"
            timer_border = "transparent"
            meta_color = "#374151"
            button_bg = "rgba(0, 0, 0, 0.05)"
            button_border = "rgba(0, 0, 0, 0.10)"
            button_hover_bg = "rgba(0, 0, 0, 0.14)"
            button_text_color = "#111111"
            frame_border = _rgba(border_spec, 0.45)
            frame_border_width = "1px"
            frame_radius = "4px"
            title_color = "#111111"
        elif float_on_lock:
            frame_bg = "rgba(0, 0, 0, 0.0)"
            editor_bg = "rgba(0, 0, 0, 0.0)"
            editor_border = "rgba(0, 0, 0, 0.0)"
            text_color = _hex_rgb(theme.text_value)
            timer_color = _hex_rgb(accent_spec)
            timer_bg = "transparent"
            timer_border = "transparent"
            button_bg = "rgba(0, 0, 0, 0.0)"
            button_border = "rgba(0, 0, 0, 0.0)"
            button_hover_bg = "rgba(0, 0, 0, 0.0)"
            button_text_color = _hex_rgb(theme.button_text)
            frame_border = "rgba(0, 0, 0, 0.0)"
            frame_border_width = "0px"
            frame_radius = "0px"
            title_color = _hex_rgb(title_spec)
            if theme.theme_id == "floating_text_light":
                meta_color = "rgba(48, 56, 64, 0.86)"
            else:
                meta_color = _rgba(meta_spec, 0.95)
        else:
            body_bg = _rgba(body_top_spec, 0.95)
            body_bg2 = _rgba(body_bottom_spec, 0.985)
            halo_bar = _rgba(glow_spec, 0.22 + (0.12 * pulse_factor)) if self._overdue_active else _rgba(theme.divider, 0.0)
            title_bg = _rgba(glow_spec, 0.08 + (0.06 * pulse_factor)) if self._overdue_active else _rgba(theme.bg_top, 0.0)
            frame_bg = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {body_bg}, stop:0.08 {halo_bar}, stop:0.18 {title_bg}, stop:1 {body_bg2})"
            editor_bg = _rgba(theme.bg_top, 0.26)
            editor_border = _rgba(_mix_rgb(theme.divider[:3], border_spec, 0.45), 0.58 if self._overdue_active else 0.55)
            text_color = _hex_rgb(theme.text_value)
            timer_color = _hex_rgb(accent_spec)
            timer_bg = _rgba(glow_spec, 0.08 + (0.06 * pulse_factor)) if self._overdue_active else "transparent"
            timer_border = _rgba(shimmer_spec, 0.24 + (0.18 * pulse_factor)) if self._overdue_active else "transparent"
            meta_color = _hex_rgb(meta_spec)
            button_bg = _rgba(theme.button_dismiss, 0.78)
            button_border = editor_border
            button_hover_bg = _rgba(theme.button_hover, 0.82)
            button_text_color = _hex_rgb(meta_spec)
            frame_border = _hex_rgb(border_spec)
            frame_border_width = "1px"
            frame_radius = "8px"
            title_color = _hex_rgb(title_spec)

        self.frame.setStyleSheet(
            f"""
            QFrame#stickyFrame {{
                background: {frame_bg};
                border: {frame_border_width} solid {frame_border};
                border-radius: {frame_radius};
            }}
            QLabel#stickyTitle {{
                color: {title_color};
                font-family: "{title_font_family}";
                font-size: {max(9, int(theme.title_font_size * font_scale))}pt;
                font-weight: {theme.title_font_weight};
            }}
            QLabel#stickyTimer {{
                color: {timer_color};
                font-family: "{value_font_family}";
                font-size: {max(11, int(13.0 * font_scale))}pt;
                font-weight: {theme.value_font_weight};
                background: {timer_bg};
                border: 1px solid {timer_border};
                border-radius: 6px;
                padding: 1px 6px;
            }}
            QTextEdit#stickyText {{
                background: {editor_bg};
                color: {text_color};
                border: 1px solid {editor_border};
                border-radius: 4px;
                padding: 4px 6px;
                selection-background-color: rgba(0, 0, 0, 0.20);
                selection-color: #000000;
                font-family: "{value_font_family}";
                font-size: {font_size_px}px;
            }}
            QLabel#stickyMeta {{
                color: {meta_color};
                font-family: "{label_font_family}";
                font-size: {max(7, int(theme.label_font_size * font_scale))}pt;
            }}
            QLabel#stickyLockedText {{
                background: transparent;
                color: {text_color};
                border: none;
                padding: 4px 4px;
                font-family: "{value_font_family}";
                font-size: {font_size_px}px;
                font-weight: {theme.value_font_weight};
            }}
            QPushButton#stickyCloseButton, QPushButton#stickyMiniButton {{
                background: {button_bg};
                color: {button_text_color};
                border: 1px solid {button_border};
                border-radius: 4px;
                font-family: "{button_font_family}";
                font-size: {max(8, int(8.0 * font_scale))}pt;
                padding: 0px;
            }}
            QPushButton#stickyCloseButton:hover, QPushButton#stickyMiniButton:hover {{
                background: {button_hover_bg};
                color: {_hex_rgb(theme.button_text) if not is_paper_theme else '#000000'};
            }}
            QPushButton#stickyActionButton {{
                background: {_rgba(theme.button_primary, 0.84)};
                color: {_hex_rgb(theme.button_text)};
                border: 1px solid {_rgba(theme.button_hover, 0.80)};
                border-radius: 8px;
                padding: 3px 10px;
                font-family: "{button_font_family}";
                font-weight: bold;
            }}
            QPushButton#stickyActionButton:hover {{
                background: {_rgba(theme.button_hover, 0.92)};
            }}
            """
        )
        self.text_edit.viewport().setStyleSheet(f"background: {editor_bg};")
        self.text_edit.setFrameStyle(QFrame.NoFrame if float_on_lock else QFrame.StyledPanel)
        self.text_edit.setVisible(not float_on_lock)
        self.locked_text_label.setVisible(float_on_lock)
        self.locked_text_label.setText(self.state.get("text", ""))
        self.meta_label.setVisible(not float_on_lock)
        self._unlock_chip.apply_theme(theme)

    def _tick_visuals(self):
        self._visual_phase = (self._visual_phase + 0.32) % (math.pi * 2.0)
        if self._overdue_active:
            self._apply_theme()

    def _refresh_action_button(self):
        locked = self.state.get("locked", False)
        primary_label = self._primary_action_label()
        self.action_btn.setVisible(bool(primary_label) and not locked)
        if primary_label:
            self.action_btn.setText(primary_label)
            self.action_btn.adjustSize()

        secondary_label = self._secondary_action_label()
        self.secondary_action_btn.setVisible(bool(secondary_label) and not locked)
        if secondary_label:
            self.secondary_action_btn.setText(secondary_label)
            self.secondary_action_btn.adjustSize()

    def _primary_action_label(self):
        note_kind = self.state.get("note_kind", "sticky_note")
        imported = bool(self.state.get("source_sender"))
        if note_kind == "job_note" and imported and self.state.get("job_status", "pending") != "done":
            return "Done"
        if note_kind == "instant_message" and self.state.get("message_mode") == "chat" and self.state.get("reply_target", ""):
            return "Reply"
        return ""

    def _secondary_action_label(self):
        if self.state.get("timer_mode") == "countdown" and self._overdue_active:
            return "Extend"
        return ""

    def _trigger_primary_action(self):
        label = self._primary_action_label()
        if not label:
            return
        action = "job_done" if label == "Done" else "reply"
        if action == "job_done":
            self.state["job_status"] = "done"
            self.meta_label.setText("Job done · feedback sent")
            self._refresh_action_button()
            self._save_state()
        self.manager.dispatch_note_action(action, self)

    def _trigger_secondary_action(self):
        label = self._secondary_action_label()
        if label != "Extend":
            return
        if not self._prompt_extend_deadline():
            return
        self.manager.dispatch_note_action("deadline_extended", self)

    def _prompt_extend_deadline(self):
        text, ok = QInputDialog.getText(
            self,
            "Extend Deadline",
            "Add time like 30m, 1h, 2h, or 00:30:00",
            text="30m",
        )
        if not ok:
            return False
        seconds = _parse_duration_input(text)
        if not seconds:
            self.meta_label.setText("Invalid deadline extension")
            return False
        self._set_countdown_seconds(seconds)
        self.state["last_extension_seconds"] = int(seconds)
        self.state["last_extension_at"] = _now_iso()
        self.meta_label.setText(f"Deadline extended by {_format_seconds(seconds)}")
        self._refresh_action_button()
        self._save_state()
        return True

    def _save_state(self):
        self.state["x"] = int(self.x())
        self.state["y"] = int(self.y())
        self.state["width"] = int(self.width())
        self.state["height"] = int(self.height())
        self.manager.save_notes()

    def set_locked(self, locked):
        self.manager.set_note_locked(self.state.get("id"), locked)

    def _apply_lock_state(self, *, persist=False):
        locked = bool(self.state.get("locked", False))
        pos = QPoint(self.x(), self.y())
        size = self.size()
        visible = self.isVisible()
        transparent_flag = _transparent_input_flag()
        flags = self._base_window_flags
        if locked and transparent_flag is not None:
            flags |= transparent_flag
        if visible:
            self.hide()
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, locked)
        self.text_edit.setReadOnly(locked)
        self.close_btn.setVisible(not locked)
        self.menu_btn.setVisible(not locked)
        self.smaller_btn.setVisible(not locked)
        self.bigger_btn.setVisible(not locked)
        self.send_btn.setVisible(not locked and not bool(self.state.get("source_sender")))
        self.lock_btn.setVisible(not locked)
        if hasattr(self, "_header_spacer"):
            self._header_spacer.setVisible(not locked)
        self._refresh_action_button()
        if locked:
            self.meta_label.setText("Locked overlay - click passes through to the app below")
            self.setCursor(QCursor(Qt.ArrowCursor))
        else:
            self._update_timer_label()
        self.resize(size)
        self.move(pos)
        if visible:
            self.show()
            self.raise_()
        self._sync_unlock_chip()
        if persist:
            self._save_state()

    def _sync_unlock_chip(self):
        if self.state.get("locked", False) and self.isVisible():
            anchor = self._lock_anchor_global()
            chip_x = anchor.x()
            chip_y = anchor.y()
            self._unlock_chip.move(chip_x, chip_y)
            self._unlock_chip.show()
            self._unlock_chip.raise_()
        else:
            self._unlock_chip.hide()

    def _lock_anchor_global(self):
        try:
            local_x = max(0, self.width() - self._unlock_chip.width() - 12)
            local_y = max(0, self.height() - 2)
            return self.mapToGlobal(QPoint(local_x, local_y))
        except RuntimeError:
            return QPoint(self.x() + self.width() - 32, self.y() + self.height() - 2)

    def _on_text_changed(self):
        self.state["text"] = self.text_edit.toPlainText()
        self.locked_text_label.setText(self.state["text"])
        self._save_state()

    def _set_theme(self, theme_id):
        self.state["theme_id"] = theme_id
        self._apply_theme()
        self._save_state()

    def _set_opacity(self, value):
        self.state["opacity"] = float(value)
        self._apply_theme()
        self._save_state()

    def _set_font_scale(self, value):
        self.state["font_scale"] = float(value)
        self.state["font_size_px"] = max(11, int(15 * float(value)))
        self._apply_theme()
        self._save_state()

    def _set_font_size_px(self, px):
        self.state["font_size_px"] = max(8, min(72, int(px)))
        self._apply_theme()
        self._save_state()

    def _prompt_custom_font_size(self):
        current = int(self.state.get("font_size_px") or 15)
        val, ok = QInputDialog.getInt(self, "Custom Text Size", "Enter font size in pixels (8 - 64):", current, 8, 64)
        if ok:
            self._set_font_size_px(val)

    def _prompt_custom_opacity(self):
        current = int(float(self.state.get("opacity", 0.95)) * 100)
        val, ok = QInputDialog.getInt(self, "Custom Transparency", "Enter opacity percentage (15 - 100%):", current, 15, 100)
        if ok:
            self._set_opacity(val / 100.0)

    def _resize_to(self, w, h):
        self.resize(max(100, int(w)), max(50, int(h)))
        self._save_state()

    def _set_font_preset(self, preset_id):
        self.state["font_preset"] = resolve_font_preset_id(preset_id)
        self._apply_theme()
        self._save_state()

    def _set_timer_off(self):
        self.state["timer_mode"] = "off"
        self.state["deadline_at"] = ""
        self.state["overdue_notified"] = False
        self._update_timer_label()
        self._save_state()

    def _set_timer_elapsed(self):
        self.state["timer_mode"] = "elapsed"
        self.state["deadline_at"] = ""
        self.state.setdefault("created_at", _now_iso())
        self.state["overdue_notified"] = False
        self._update_timer_label()
        self._save_state()

    def _set_countdown_minutes(self, minutes):
        self.state["timer_mode"] = "countdown"
        self.state["deadline_at"] = (datetime.now() + timedelta(minutes=minutes)).isoformat(timespec="seconds")
        self.state["overdue_notified"] = False
        self._update_timer_label()
        self._refresh_action_button()
        self._save_state()

    def _set_countdown_seconds(self, seconds):
        self.state["timer_mode"] = "countdown"
        self.state["deadline_at"] = (datetime.now() + timedelta(seconds=int(seconds))).isoformat(timespec="seconds")
        self.state["overdue_notified"] = False
        self._update_timer_label()
        self._refresh_action_button()
        self._save_state()

    def _set_countdown_end_of_day(self):
        now = datetime.now()
        deadline = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if deadline <= now:
            deadline += timedelta(days=1)
        self.state["timer_mode"] = "countdown"
        self.state["deadline_at"] = deadline.isoformat(timespec="seconds")
        self.state["overdue_notified"] = False
        self._update_timer_label()
        self._refresh_action_button()
        self._save_state()

    def _cycle_timer_mode(self):
        mode = self.state.get("timer_mode", "off")
        if mode == "off":
            self._set_timer_elapsed()
        elif mode == "elapsed":
            self._set_countdown_minutes(60)
        else:
            self._set_timer_off()

    def _set_custom_countdown(self):
        text, ok = QInputDialog.getText(
            self,
            "Custom Countdown",
            "Enter duration like 45s, 15m, 2h, 1h 30m, or 01:15:00",
        )
        if not ok:
            return
        seconds = _parse_duration_input(text)
        if not seconds:
            self.meta_label.setText("Invalid custom countdown")
            return
        self._set_countdown_seconds(seconds)

    def _resize_by(self, dw, dh):
        new_w = max(100, min(1200, self.width() + dw))
        new_h = max(50, min(1200, self.height() + dh))
        self.resize(new_w, new_h)
        self._save_state()

    def _update_timer_label(self):
        mode = self.state.get("timer_mode", "off")
        note_kind = self.state.get("note_kind", "sticky_note")
        overdue = False
        auto_close_seconds = int(self.state.get("auto_close_seconds", 0) or 0)
        if note_kind == "instant_message" and auto_close_seconds > 0:
            created = _parse_dt(self.state.get("created_at")) or datetime.now()
            remaining = auto_close_seconds - (datetime.now() - created).total_seconds()
            if remaining <= 0:
                self.manager.record_note_event("instant_message_auto_closed", self)
                self.manager.remove_note(self.state.get("id"))
                self.hide()
                self.deleteLater()
                return
            self.timer_label.setText(_format_seconds(remaining))
            self.meta_label.setText("Instant message · auto-dismiss window")
            self.title_label.setText(self.state.get("title", "Instant Message"))
        elif mode == "elapsed":
            created = _parse_dt(self.state.get("created_at")) or datetime.now()
            self.timer_label.setText(_format_seconds((datetime.now() - created).total_seconds()))
            self.meta_label.setText("Elapsed time")
            self.title_label.setText(self.state.get("title", "Sticky Note"))
        elif mode == "countdown":
            deadline = _parse_dt(self.state.get("deadline_at"))
            if deadline:
                remaining = (deadline - datetime.now()).total_seconds()
                self.timer_label.setText(_format_seconds(remaining))
                if remaining < 0:
                    overdue = True
                    self.title_label.setText("REMINDER DUE")
                    self.meta_label.setText("Past due - calm breathing reminder")
                    if not self.state.get("overdue_notified", False):
                        self.state["overdue_notified"] = True
                        self.manager.save_notes()
                        self.manager.handle_overdue(self)
                else:
                    self.title_label.setText(self.state.get("title", "Sticky Note"))
                    self.meta_label.setText("Countdown")
                    self.state["overdue_notified"] = False
            else:
                self.timer_label.setText("--:--:--")
                self.meta_label.setText("Timer unset")
                self.title_label.setText(self.state.get("title", "Sticky Note"))
        else:
            self.timer_label.setText("--:--:--")
            self.meta_label.setText("Right-click for options")
            self.title_label.setText(self.state.get("title", "Sticky Note"))

        if overdue != self._overdue_active:
            self._overdue_active = overdue
            self._apply_theme()
        elif overdue:
            self._apply_theme()
        self._refresh_action_button()

    def _close_note(self):
        self._timer.stop()
        self._visual_timer.stop()
        self._unlock_chip.hide()
        self._unlock_chip.deleteLater()
        self.manager.record_note_event("sticky_closed", self)
        self.manager.remove_note(self.state.get("id"))
        self.hide()
        self.deleteLater()

    def retire_for_rebuild(self):
        self._timer.stop()
        self._visual_timer.stop()
        self._unlock_chip.hide()
        self._unlock_chip.deleteLater()
        self.hide()

    def _build_options_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background: #18181b;
                color: #f4f4f5;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 4px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 4px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #27272a;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #27272a;
                margin: 4px 6px;
            }
            """
        )

        theme_menu = menu.addMenu("Theme")
        theme_group = QActionGroup(theme_menu)
        theme_group.setExclusive(True)
        for theme in list_note_themes():
            action = theme_menu.addAction(theme.label)
            action.setCheckable(True)
            action.setChecked(theme.theme_id == self.state.get("theme_id"))
            theme_group.addAction(action)
            action.triggered.connect(lambda checked, theme_id=theme.theme_id: self._set_theme(theme_id))

        opacity_menu = menu.addMenu("Transparency")
        current_op = float(self.state.get("opacity", 0.95))
        for label, val in [
            ("100% · Solid Paper", 1.0),
            ("95% · Realistic", 0.95),
            ("85% · Soft Glow", 0.85),
            ("75% · Transparent", 0.75),
            ("60% · See-Through", 0.60),
            ("45% · Ghost", 0.45),
            ("30% · Faint", 0.30),
        ]:
            act = opacity_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(abs(current_op - val) < 0.04)
            act.triggered.connect(lambda checked, v=val: self._set_opacity(v))
        opacity_menu.addSeparator()
        opacity_menu.addAction("Custom Opacity...", self._prompt_custom_opacity)

        text_size_menu = menu.addMenu("Text Size")
        current_px = int(self.state.get("font_size_px") or 15)
        for label, px in [
            ("11px · Compact", 11),
            ("13px · Small", 13),
            ("15px · Normal", 15),
            ("18px · Medium", 18),
            ("22px · Large", 22),
            ("26px · Extra Large", 26),
            ("30px · Huge", 30),
            ("36px · Maximum (36px)", 36),
        ]:
            act = text_size_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(abs(current_px - px) <= 1)
            act.triggered.connect(lambda checked, p=px: self._set_font_size_px(p))
        text_size_menu.addSeparator()
        text_size_menu.addAction("Custom Size (px)...", self._prompt_custom_font_size)

        font_style_menu = menu.addMenu("Font Style")
        font_style_group = QActionGroup(font_style_menu)
        font_style_group.setExclusive(True)
        for preset in list_font_presets():
            action = font_style_menu.addAction(preset.label)
            action.setCheckable(True)
            action.setChecked(
                preset.preset_id == self.state.get("font_preset", DEFAULT_FONT_PRESET_ID)
            )
            font_style_group.addAction(action)
            action.triggered.connect(
                lambda checked, preset_id=preset.preset_id: self._set_font_preset(preset_id)
            )

        timer_menu = menu.addMenu("Timer")
        timer_menu.addAction("Off", self._set_timer_off)
        timer_menu.addAction("Elapsed", self._set_timer_elapsed)
        timer_menu.addAction("Countdown 30 min", lambda: self._set_countdown_minutes(30))
        timer_menu.addAction("Countdown 1 hour", lambda: self._set_countdown_minutes(60))
        timer_menu.addAction("Countdown 4 hours", lambda: self._set_countdown_minutes(240))
        timer_menu.addAction("Custom...", self._set_custom_countdown)
        timer_menu.addAction("Until 6:00 PM", self._set_countdown_end_of_day)

        size_menu = menu.addMenu("Dimensions & Presets")
        size_menu.addAction("💡 Drag bottom edge / corner to resize", lambda: None).setEnabled(False)
        size_menu.addSeparator()
        size_menu.addAction("Mini Strip (200x70)", lambda: self._resize_to(200, 70))
        size_menu.addAction("Compact Note (180x110)", lambda: self._resize_to(180, 110))
        size_menu.addAction("Square Post-it (220x220)", lambda: self._resize_to(220, 220))
        size_menu.addAction("Standard Note (270x290)", lambda: self._resize_to(270, 290))
        size_menu.addAction("Large Memo (360x380)", lambda: self._resize_to(360, 380))
        size_menu.addSeparator()
        size_menu.addAction("Shorter Height (-25px)", lambda: self._resize_by(0, -25))
        size_menu.addAction("Taller Height (+25px)", lambda: self._resize_by(0, 25))
        size_menu.addAction("Narrower Width (-25px)", lambda: self._resize_by(-25, 0))
        size_menu.addAction("Wider Width (+25px)", lambda: self._resize_by(25, 0))

        menu.addSeparator()
        if self.state.get("locked", False):
            menu.addAction("Unlock Overlay", lambda: self.set_locked(False))
        else:
            menu.addAction("Lock Overlay", lambda: self.set_locked(True))

        menu.addSeparator()
        menu.addAction("Close Note", self._close_note)
        return menu

    def _show_options_menu(self):
        menu = self._build_options_menu()
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    def contextMenuEvent(self, event):
        menu = self._build_options_menu()
        menu.exec(event.globalPos())

    def _get_resize_mode(self, pos):
        w = self.width()
        h = self.height()
        near_right = pos.x() >= w - 14
        near_bottom = pos.y() >= h - 14
        if near_right and near_bottom:
            return "corner"
        if near_bottom:
            return "bottom"
        if near_right:
            return "right"
        return None

    def _do_resize(self, global_pos):
        delta = global_pos - self._resize_start_pos
        w = self._resize_start_size.width()
        h = self._resize_start_size.height()
        if "bottom" in self._resize_mode or self._resize_mode == "corner":
            h = max(50, min(1200, h + delta.y()))
        if "right" in self._resize_mode or self._resize_mode == "corner":
            w = max(100, min(1200, w + delta.x()))
        self.resize(w, h)

    def eventFilter(self, obj, event):
        if obj == self.frame and not self.state.get("locked", False):
            if event.type() == QEvent.MouseMove:
                local_pos = event.position().toPoint()
                global_pt = self.frame.mapTo(self, local_pos)
                if getattr(self, "_resize_active", False):
                    self._do_resize(event.globalPosition().toPoint())
                    return True
                else:
                    mode = self._get_resize_mode(global_pt)
                    if mode == "corner":
                        self.setCursor(QCursor(Qt.SizeFDiagCursor))
                    elif mode == "bottom":
                        self.setCursor(QCursor(Qt.SizeVerCursor))
                    elif mode == "right":
                        self.setCursor(QCursor(Qt.SizeHorCursor))
                    else:
                        self.setCursor(QCursor(Qt.ArrowCursor))
            elif event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    local_pos = event.position().toPoint()
                    global_pt = self.frame.mapTo(self, local_pos)
                    mode = self._get_resize_mode(global_pt)
                    if mode:
                        self._resize_active = True
                        self._resize_mode = mode
                        self._resize_start_pos = event.globalPosition().toPoint()
                        self._resize_start_size = self.size()
                        return True
            elif event.type() == QEvent.MouseButtonRelease:
                if getattr(self, "_resize_active", False):
                    self._resize_active = False
                    self._resize_mode = None
                    self.setCursor(QCursor(Qt.ArrowCursor))
                    self._save_state()
                    return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if self.state.get("locked", False):
            event.ignore()
            return
        if event.button() == Qt.LeftButton:
            mode = self._get_resize_mode(event.position().toPoint())
            if mode:
                self._resize_active = True
                self._resize_mode = mode
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_size = self.size()
                event.accept()
                return

            if not self.text_edit.geometry().contains(event.position().toPoint()):
                self._drag_origin = event.globalPosition().toPoint()
                self._drag_pos = self.frameGeometry().topLeft()
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.state.get("locked", False):
            event.ignore()
            return

        if getattr(self, "_resize_active", False):
            self._do_resize(event.globalPosition().toPoint())
            event.accept()
            return

        if self._drag_origin is not None:
            delta = event.globalPosition().toPoint() - self._drag_origin
            self.move(self._drag_pos + delta)
            event.accept()
            return

        mode = self._get_resize_mode(event.position().toPoint())
        if mode == "corner":
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        elif mode == "bottom":
            self.setCursor(QCursor(Qt.SizeVerCursor))
        elif mode == "right":
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.state.get("locked", False):
            event.ignore()
            return
        if getattr(self, "_resize_active", False):
            self._resize_active = False
            self._resize_mode = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            self._save_state()
            event.accept()
            return
        if self._drag_origin is not None:
            self._drag_origin = None
            self._drag_pos = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            self._save_state()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            # Ctrl + Scroll: adjust font size dynamically up to 48px
            delta = 1 if event.angleDelta().y() > 0 else -1
            current = int(self.state.get("font_size_px") or 15)
            new_size = max(9, min(48, current + delta))
            self._set_font_size_px(new_size)
            event.accept()
            return
        elif modifiers & Qt.AltModifier:
            # Alt + Scroll: adjust opacity dynamically
            delta = 0.05 if event.angleDelta().y() > 0 else -0.05
            current = float(self.state.get("opacity", 0.95))
            new_op = max(0.15, min(1.0, current + delta))
            self._set_opacity(new_op)
            event.accept()
            return
        super().wheelEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._sync_unlock_chip()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_unlock_chip()
        # Adapt UI when dragged down to small heights
        is_compact = self.height() < 140
        is_tiny = self.height() < 95
        if hasattr(self, 'meta_label'):
            self.meta_label.setVisible(not is_compact and not self.state.get("locked", False))
        if hasattr(self, 'smaller_btn'):
            self.smaller_btn.setVisible(not is_compact and not self.state.get("locked", False))
        if hasattr(self, 'bigger_btn'):
            self.bigger_btn.setVisible(not is_compact and not self.state.get("locked", False))
        if hasattr(self, 'title_label'):
            self.title_label.setVisible(False)
        if hasattr(self, 'timer_label'):
            self.timer_label.setVisible(not is_tiny or self.state.get("timer_mode") != "off")

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_unlock_chip()

    def hideEvent(self, event):
        self._unlock_chip.hide()
        super().hideEvent(event)


class NetShareStickyNoteManager:
    def __init__(self, config, audit_store=None, on_overdue=None, on_note_action=None, on_share_requested=None):
        self.config = config
        self.audit_store = audit_store
        self.on_overdue = on_overdue
        self.on_note_action = on_note_action
        self.on_share_requested = on_share_requested
        self._notes = {}
        self.load_notes()

    def _settings_notes(self):
        notes = self.config.get("sticky_notes", "notes")
        return notes if isinstance(notes, list) else []

    def load_notes(self):
        saved = self._settings_notes()
        for state in saved:
            note_id = state.get("id")
            if not note_id:
                continue
            self._notes[note_id] = StickyNoteWidget(self, state)

    def create_note(self):
        default_theme = resolve_theme_id(self.config.get("bubbles", "note_theme") or DEFAULT_NOTE_THEME_ID)
        default_opacity = float(self.config.get("bubbles", "overlay_opacity") or 0.94)
        default_font_scale = float(self.config.get("bubbles", "font_scale") or 1.0)
        default_font_preset = resolve_font_preset_id(
            self.config.get("bubbles", "font_preset") or DEFAULT_FONT_PRESET_ID
        )
        offset = len(self._notes) * 26
        state = {
            "id": uuid.uuid4().hex[:10],
            "title": "Sticky Note",
            "text": "",
            "theme_id": default_theme,
            "font_preset": default_font_preset,
            "opacity": default_opacity,
            "font_scale": default_font_scale,
            "note_kind": "sticky_note",
            "message_mode": "single",
            "thread_id": "",
            "timer_mode": "off",
            "deadline_at": "",
            "auto_close_seconds": 0,
            "locked": False,
            "overdue_notified": False,
            "created_at": _now_iso(),
            "x": 120 + offset,
            "y": 120 + offset,
            "width": 270,
            "height": 290,
            "job_status": "pending",
        }
        widget = StickyNoteWidget(self, state)
        self._notes[state["id"]] = widget
        self.save_notes()
        self.record_note_event("sticky_created", widget)
        return widget

    def create_note_from_payload(self, payload):
        note_id = payload.get("id") or uuid.uuid4().hex[:10]
        thread_id = payload.get("thread_id", "") or ""
        if note_id in self._notes:
            return self._notes[note_id]
        if payload.get("note_kind") == "instant_message" and payload.get("message_mode") == "chat" and thread_id:
            existing = self.find_note_by_thread(thread_id)
            if existing:
                self.append_chat_message(existing, payload)
                return existing

        offset = len(self._notes) * 26
        state = {
            "id": note_id,
            "title": payload.get("title", "Sticky Note"),
            "text": self._initial_note_text(payload),
            "theme_id": resolve_theme_id(payload.get("theme_id", DEFAULT_NOTE_THEME_ID)),
            "font_preset": resolve_font_preset_id(payload.get("font_preset", DEFAULT_FONT_PRESET_ID)),
            "opacity": float(payload.get("opacity", 0.94) or 0.94),
            "font_scale": float(payload.get("font_scale", 1.0) or 1.0),
            "note_kind": payload.get("note_kind", "sticky_note"),
            "message_mode": payload.get("message_mode", "single"),
            "thread_id": thread_id,
            "timer_mode": payload.get("timer_mode", "off") or "off",
            "deadline_at": payload.get("deadline_at", ""),
            "auto_close_seconds": int(payload.get("auto_close_seconds", 0) or 0),
            "locked": False,
            "overdue_notified": False,
            "created_at": payload.get("timestamp", _now_iso()),
            "x": 180 + offset,
            "y": 140 + offset,
            "width": 270,
            "height": 290,
            "source_sender": payload.get("sender", ""),
            "source_recipient": payload.get("recipient", ""),
            "source_notification_id": note_id,
            "job_status": payload.get("job_status", "pending"),
            "reply_target": payload.get("sender", "") if payload.get("note_kind") == "instant_message" else "",
        }
        widget = StickyNoteWidget(self, state)
        self._notes[state["id"]] = widget
        self.save_notes()
        self.record_note_event("sticky_imported", widget)
        return widget

    def mirror_outbound_payload(self, payload):
        note_id = payload.get("thread_id") or payload.get("id") or uuid.uuid4().hex[:10]
        if note_id in self._notes:
            existing = self._notes[note_id]
            self.append_chat_message(
                existing,
                {
                    "sender": "you",
                    "text": payload.get("text", ""),
                    "title": payload.get("title", ""),
                },
            )
            return existing

        state = {
            "id": note_id,
            "title": payload.get("title", "Chat Thread"),
            "text": self._initial_note_text({"sender": "you", **payload}),
            "theme_id": resolve_theme_id(payload.get("theme_id", DEFAULT_NOTE_THEME_ID)),
            "font_preset": resolve_font_preset_id(payload.get("font_preset", DEFAULT_FONT_PRESET_ID)),
            "opacity": float(payload.get("opacity", 0.94) or 0.94),
            "font_scale": float(payload.get("font_scale", 1.0) or 1.0),
            "note_kind": payload.get("note_kind", "instant_message"),
            "message_mode": payload.get("message_mode", "chat"),
            "thread_id": payload.get("thread_id", note_id),
            "timer_mode": "off",
            "deadline_at": "",
            "auto_close_seconds": 0,
            "locked": False,
            "overdue_notified": False,
            "created_at": payload.get("timestamp", _now_iso()),
            "x": 180,
            "y": 140,
            "width": 290,
            "height": 320,
            "source_sender": payload.get("sender", "you"),
            "source_recipient": payload.get("recipient", ""),
            "source_notification_id": payload.get("id", note_id),
            "job_status": "pending",
            "reply_target": payload.get("recipient", ""),
        }
        widget = StickyNoteWidget(self, state)
        self._notes[state["id"]] = widget
        self.save_notes()
        self.record_note_event("sticky_thread_created", widget)
        return widget

    def remove_note(self, note_id):
        self._notes.pop(note_id, None)
        self.save_notes()

    def set_note_locked(self, note_id, locked):
        widget = self._notes.get(note_id)
        if not widget:
            return None
        locked = bool(locked)
        if bool(widget.state.get("locked", False)) == locked:
            widget._sync_unlock_chip()
            return widget
        state = self._capture_widget_state(widget)
        state["locked"] = locked
        was_visible = widget.isVisible()
        widget.retire_for_rebuild()
        replacement = StickyNoteWidget(self, state)
        self._notes[note_id] = replacement
        if not was_visible:
            replacement.hide()
        self.save_notes()
        widget.deleteLater()
        return replacement

    def save_notes(self):
        payload = []
        for widget in self._notes.values():
            payload.append(self._capture_widget_state(widget))
        self.config.set("sticky_notes", "notes", payload)

    def show_all(self):
        for widget in self._notes.values():
            widget.show()
            widget.raise_()

    def hide_all(self):
        for widget in self._notes.values():
            widget.hide()

    def clear_all(self):
        note_ids = list(self._notes.keys())
        for note_id in note_ids:
            widget = self._notes.pop(note_id, None)
            if not widget:
                continue
            try:
                widget._timer.stop()
                widget._visual_timer.stop()
                widget._unlock_chip.hide()
                widget._unlock_chip.deleteLater()
                widget.hide()
                widget.deleteLater()
            except RuntimeError:
                continue
        self.save_notes()

    def handle_overdue(self, widget):
        widget.raise_()
        widget.activateWindow()
        self.record_note_event("sticky_overdue", widget)
        if self.on_overdue:
            self.on_overdue(dict(widget.state))

    def record_note_event(self, event, widget):
        if not self.audit_store:
            return
        sender = widget.state.get("source_sender") or "local"
        recipient = widget.state.get("source_recipient") or "local"
        self.audit_store.record_event(
            event,
            sender=sender,
            recipient=recipient,
            filename=widget.state.get("title", "Sticky Note"),
            file_path=f"sticky://{widget.state.get('id', '')}",
            notification_id=widget.state.get("source_notification_id", widget.state.get("id", "")),
            details={
                "text": widget.state.get("text", "")[:160],
                "theme_id": widget.state.get("theme_id", ""),
                "font_preset": widget.state.get("font_preset", DEFAULT_FONT_PRESET_ID),
                "note_kind": widget.state.get("note_kind", "sticky_note"),
                "message_mode": widget.state.get("message_mode", "single"),
                "thread_id": widget.state.get("thread_id", ""),
                "timer_mode": widget.state.get("timer_mode", ""),
                "deadline_at": widget.state.get("deadline_at", ""),
                "job_status": widget.state.get("job_status", "pending"),
            },
        )

    def dashboard_rows(self):
        rows = []
        for widget in self._notes.values():
            state = widget.state
            timer_mode = state.get("timer_mode", "off")
            timer_label = "--:--:--"
            if timer_mode == "elapsed":
                created = _parse_dt(state.get("created_at")) or datetime.now()
                timer_label = _format_seconds((datetime.now() - created).total_seconds())
            elif timer_mode == "countdown":
                deadline = _parse_dt(state.get("deadline_at"))
                if deadline:
                    timer_label = _format_seconds((deadline - datetime.now()).total_seconds())
            is_overdue = timer_mode == "countdown" and str(timer_label).startswith("-")
            rows.append(
                {
                    "title": state.get("title", "Sticky Note"),
                    "note_id": state.get("id", ""),
                    "owner": state.get("source_sender", "local") or "local",
                    "recipient": state.get("source_recipient", "local") or "local",
                    "member": state.get("source_recipient", "") or state.get("source_sender", "local") or "local",
                    "note_kind": state.get("note_kind", "sticky_note"),
                    "job_status": state.get("job_status", "pending"),
                    "locked": bool(state.get("locked", False)),
                    "timer_mode": timer_mode,
                    "timer_label": timer_label,
                    "deadline_at": state.get("deadline_at", ""),
                    "is_overdue": is_overdue,
                    "theme_id": state.get("theme_id", ""),
                }
            )
        return rows

    def apply_global_preferences(self, *, theme_id=None, opacity=None, font_scale=None, font_preset=None):
        for widget in self._notes.values():
            if theme_id is not None:
                widget.state["theme_id"] = theme_id
            if opacity is not None:
                widget.state["opacity"] = float(opacity)
            if font_scale is not None:
                widget.state["font_scale"] = float(font_scale)
            if font_preset is not None:
                widget.state["font_preset"] = resolve_font_preset_id(font_preset)
            widget._apply_theme()
            widget._refresh_action_button()
        self.save_notes()

    def dispatch_note_action(self, action, widget):
        if self.on_note_action:
            self.on_note_action(action, widget)

    def request_share(self, widget):
        if self.on_share_requested:
            self.on_share_requested(widget)

    def find_note_by_thread(self, thread_id):
        if not thread_id:
            return None
        for widget in self._notes.values():
            if widget.state.get("thread_id") == thread_id:
                return widget
        return None

    def has_note(self, note_id):
        return bool(note_id) and note_id in self._notes

    def get_note(self, note_id):
        return self._notes.get(note_id)

    def append_chat_message(self, widget, payload):
        sender = (payload.get("sender") or "peer").strip() or "peer"
        text = (payload.get("text") or "").strip()
        if not text:
            return
        current = widget.text_edit.toPlainText().strip()
        addition = f"{sender}: {text}"
        widget.text_edit.blockSignals(True)
        widget.text_edit.setPlainText(f"{current}\n\n{addition}".strip())
        widget.text_edit.blockSignals(False)
        widget.state["text"] = widget.text_edit.toPlainText()
        widget.state["title"] = payload.get("title", widget.state.get("title", "Chat Thread"))
        widget.state["created_at"] = payload.get("timestamp", widget.state.get("created_at", _now_iso()))
        self.save_notes()
        self.record_note_event("sticky_thread_appended", widget)
        widget.raise_()
        widget.activateWindow()

    @staticmethod
    def _capture_widget_state(widget):
        state = dict(widget.state)
        try:
            state["text"] = widget.text_edit.toPlainText()
            state["x"] = int(widget.x())
            state["y"] = int(widget.y())
            state["width"] = int(widget.width())
            state["height"] = int(widget.height())
        except RuntimeError:
            pass
        return state

    @staticmethod
    def _initial_note_text(payload):
        note_kind = payload.get("note_kind", "sticky_note")
        message_mode = payload.get("message_mode", "single")
        text = payload.get("text", "")
        sender = payload.get("sender", "")
        if note_kind == "instant_message" and message_mode == "chat" and text:
            return f"{sender}: {text}"
        return text


StickyNoteManager = NetShareStickyNoteManager

