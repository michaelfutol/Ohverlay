"""
Persistent Ohverlay Control Center.
A compact, floating panel anchored near the taskbar for controlling nature overlays.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QFrame, QRadioButton, QButtonGroup, QSlider, QGraphicsDropShadowEffect,
    QScrollArea, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor, QFont, QGuiApplication
from utils.logger import logger


class ControlCenterSignals(QWidget):
    pass


XMAS_THEMES = [
    ("multicolor", "🌈 Rainbow"),
    ("warm_gold", "✨ Warm Gold"),
    ("candy_cane", "🍬 Candy Cane"),
    ("winter_frost", "❄️ Winter Frost"),
    ("mistletoe", "🌿 Mistletoe"),
]

BETTA_BREEDS = [
    ("sunburst", "Sunburst Butterfly (Halfmoon) 🌺"),
    ("buttercup", "Platinum Buttercup (Pastel) ⭐"),
    ("mustard_gas", "Mustard Gas (Halfmoon)"),
    ("koi", "Galaxy Koi (Calico)"),
    ("samurai", "Black Samurai (Platinum)"),
    ("super_red", "Super Red (Crimson)"),
    ("royal_blue", "Royal Blue (Sapphire)"),
    ("copper", "Dragon Copper (Emerald)"),
    ("abyssal_glass", "Abyssal Glass (Bioluminescent) 🪼✨"),
    ("mix", "Mix (Distinct Breeds)"),
]

ORCHID_COLORS = [
    ("fuchsia", "Fuchsia"),
    ("blush", "Blush Pink"),
    ("white", "Pearl White"),
    ("violet", "Violet"),
    ("sunset", "Sunset Coral"),
]


DRAGONFLY_PALETTES = [
    ("mixed", "Mixed Collection 🎨"),
    ("reference", "Original Reference"),
    ("emperor-male", "Emperor (Male · Blue/Green)"),
    ("emperor-female", "Emperor (Female · Green)"),
    ("ruddy-male", "Ruddy Darter (Male · Red)"),
    ("ruddy-female", "Ruddy Darter (Female · Ochre)"),
    ("skimmer-male", "Black-tailed Skimmer (Male · Blue)"),
    ("skimmer-female", "Black-tailed Skimmer (Female · Yellow)"),
    ("keeled-male", "Keeled Skimmer (Male · Powder Blue)"),
    ("keeled-female", "Keeled Skimmer (Female · Ochre)"),
]

DRAGONFLY_STYLES = [
    ("percher", "Percher Study (Territorial)"),
    ("patrol", "Patrol Study (Active)"),
]

DANDELION_STYLES = [
    ("cyan", "Bioluminescent Cyan (Avatar) 🪼✨"),
    ("violet", "Celestial Violet (Fairy Glow) 🔮✨"),
    ("emerald", "Stardust Emerald (Enchanted) 🍃✨"),
    ("mix", "Bioluminescent Mix (All Glow) 🌈✨"),
    ("classic", "Classic Sunlight (Golden Cream) 🌾"),
]


class ControlCenter(QWidget):
    """Persistent control panel for Ohverlay settings and species management."""

    show_welcome_requested = Signal()
    open_master_dashboard_requested = Signal()
    new_sticky_requested = Signal()
    toggle_all_requested = Signal()
    quit_requested = Signal()
    overlay_toggled = Signal(str, bool)     # (species_id, enabled)
    count_changed = Signal(str, int)        # (species_id, count)
    scale_changed = Signal(str, float)      # (species_id, scale)
    physics_preset_changed = Signal(str)    # ("calm" | "lively" | "dramatic")
    interaction_strength_changed = Signal(float)  # (0.25 to 2.0)

    def __init__(self, config=None, overlay_manager=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.overlay_manager = overlay_manager

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        self._species_widgets = {}

        self._build_ui()
        self._update_from_config()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        card = QFrame(self)
        card.setObjectName("controlCard")
        card.setStyleSheet("""
            #controlCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            QLabel {
                color: #0f172a;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QPushButton {
                background-color: #f8fafc;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
                color: #0f172a;
            }
            QPushButton:checked {
                background-color: #10b981;
                border-color: #059669;
                color: #ffffff;
            }
            QPushButton[class="stepBtn"], QPushButton.stepBtn {
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
                padding: 0px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
                text-align: center;
            }
            QPushButton[class="stepBtn"]:hover, QPushButton.stepBtn:hover {
                background-color: #e2e8f0;
                border-color: #94a3b8;
                color: #0f172a;
            }
            QPushButton[class="stepBtn"]:disabled, QPushButton.stepBtn:disabled {
                color: #cbd5e1;
                border-color: #f1f5f9;
                background-color: #f8fafc;
            }
            QRadioButton {
                color: #64748b;
                font-size: 10px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QRadioButton:hover {
                color: #0f172a;
            }
            QRadioButton::indicator:checked {
                background-color: #2563eb;
                border: 2px solid #ffffff;
                border-radius: 5px;
                width: 10px;
                height: 10px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #e2e8f0;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #3b82f6;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QCheckBox {
                color: #64748b;
                font-size: 11px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QCheckBox:hover {
                color: #0f172a;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f8fafc;
                width: 6px;
                margin: 2px 0 2px 0;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 28px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Soft drop shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(15, 23, 42, 35))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        # ── Header ──
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        title_label = QLabel("Ohverlay", card)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #0f172a;")

        subtitle_label = QLabel("Nature is alive", card)
        subtitle_label.setFont(QFont("Segoe UI", 8))
        subtitle_label.setStyleSheet("color: #64748b;")

        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Pin checkbox
        self.pin_btn = QCheckBox("Pin", card)
        self.pin_btn.setToolTip("Keep controls open when clicking elsewhere")
        self.pin_btn.toggled.connect(self._on_pin_toggled)
        header_layout.addWidget(self.pin_btn)

        close_btn = QPushButton("×", card)
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #0f172a;
                background: #f1f5f9;
                border-radius: 11px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)

        card_layout.addLayout(header_layout)

        # Separator line
        card_layout.addWidget(self._make_h_line())

        # ── Scrollable Species Container ──
        scroll_area = QScrollArea(card)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(440)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 2, 4, 2)
        scroll_layout.setSpacing(8)

        # ── Species Rows ──
        species_list = [
            ("Fireflies", "fireflies", 6),
            ("Dragonflies", "dragonflies", 2),
            ("Dandelions", "dandelions", 3),
            ("Living Orchid", "orchid", 1),
            ("Local Moon", "moon", 1),
            ("Blue Butterfly", "butterfly_blue", 1),
            ("Yellow Butterfly", "butterfly_yellow", 1),
            ("Orange Butterfly", "butterfly_orange", 1),
            ("Hornwort Plant", "hornwort", 4),
            ("Neon Tetra", "neon_tetra", 2),
            ("Betta Fish", "betta_fish", 1),
            ("Jewel Cichlid", "cichlid", 1),
            ("Telegrama Card", "telegrama", 1),
        ]

        for label_text, oid, default_count in species_list:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(4)
            row_layout.setContentsMargins(0, 0, 2, 0)

            sp_label = QLabel(label_text, scroll_content)
            sp_label.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
            sp_label.setStyleSheet("color: #0f172a;")

            toggle_btn = QPushButton("OFF", scroll_content)
            toggle_btn.setCheckable(True)
            toggle_btn.setFixedWidth(44)
            toggle_btn.setFixedHeight(22)
            toggle_btn.setStyleSheet("padding: 2px 4px; font-size: 10px; font-weight: 600;")
            toggle_btn.toggled.connect(lambda checked, s_id=oid: self._on_species_toggled(s_id, checked))

            step_style = (
                "min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; "
                "padding: 0px; font-size: 13px; font-weight: bold; border-radius: 5px; "
                "text-align: center;"
            )

            minus_btn = QPushButton("−", scroll_content)
            minus_btn.setProperty("class", "stepBtn")
            minus_btn.setFixedSize(22, 22)
            minus_btn.setStyleSheet(step_style)

            count_label = QLabel(str(default_count), scroll_content)
            count_label.setFixedWidth(20)
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            count_label.setStyleSheet("color: #0f172a;")

            plus_btn = QPushButton("+", scroll_content)
            plus_btn.setProperty("class", "stepBtn")
            plus_btn.setFixedSize(22, 22)
            plus_btn.setStyleSheet(step_style)

            if oid == "moon":
                minus_btn.setEnabled(False)
                plus_btn.setEnabled(False)
                count_label.setToolTip("One local Moon")

            minus_btn.clicked.connect(lambda _, s_id=oid: self._adjust_count(s_id, -1))
            plus_btn.clicked.connect(lambda _, s_id=oid: self._adjust_count(s_id, +1))

            row_layout.addWidget(sp_label, 1)
            row_layout.addWidget(toggle_btn)
            row_layout.addSpacing(2)

            counter_box = QHBoxLayout()
            counter_box.setSpacing(2)
            counter_box.setContentsMargins(0, 0, 0, 0)
            counter_box.addWidget(minus_btn)
            counter_box.addWidget(count_label)
            counter_box.addWidget(plus_btn)

            row_layout.addLayout(counter_box)

            scroll_layout.addLayout(row_layout)

            # Sub-row for individual size
            size_subrow = QHBoxLayout()
            size_subrow.setContentsMargins(14, 0, 0, 0)
            
            size_lbl = QLabel("Size:", scroll_content)
            size_lbl.setFont(QFont("Segoe UI", 8))
            size_lbl.setStyleSheet("color: #64748b;")
            size_subrow.addWidget(size_lbl)
            
            bg = QButtonGroup(self)
            for sz_label, sz_val in [("Small", 0.5), ("Normal", 1.0), ("Large", 1.5)]:
                rb = QRadioButton(sz_label, scroll_content)
                rb.setProperty("scaleValue", sz_val)
                rb.setProperty("speciesId", oid)
                if sz_val == 1.0:
                    rb.setChecked(True)
                bg.addButton(rb)
                size_subrow.addWidget(rb)
                
            size_subrow.addStretch()
            scroll_layout.addLayout(size_subrow)
            bg.buttonToggled.connect(self._on_species_size_toggled)

            # Sub-row for opacity / transparency
            op_subrow = QHBoxLayout()
            op_subrow.setContentsMargins(14, 0, 0, 0)
            op_subrow.setSpacing(6)

            op_lbl = QLabel("Opacity:", scroll_content)
            op_lbl.setFont(QFont("Segoe UI", 8))
            op_lbl.setStyleSheet("color: #64748b;")
            op_subrow.addWidget(op_lbl)

            op_slider = QSlider(Qt.Horizontal, scroll_content)
            op_slider.setRange(10, 100)
            op_slider.setValue(100)
            op_slider.setFixedHeight(14)
            op_subrow.addWidget(op_slider)

            op_val_lbl = QLabel("100%", scroll_content)
            op_val_lbl.setFont(QFont("Segoe UI", 8))
            op_val_lbl.setStyleSheet("color: #64748b;")
            op_val_lbl.setFixedWidth(30)
            op_subrow.addWidget(op_val_lbl)

            scroll_layout.addLayout(op_subrow)

            op_slider.valueChanged.connect(lambda val, s_id=oid, lbl=op_val_lbl: self._on_species_opacity_changed(s_id, val, lbl))

            speed_bg = None
            xmas_toggle_btn = None
            xmas_mode_btn = None
            xmas_theme_btn = None
            betta_breed_combo = None
            dandelion_style_combo = None
            orchid_color_combo = None
            moon_location_edit = None
            dragonfly_palette_combo = None
            dragonfly_style_combo = None
            dragonfly_startle_btn = None
            dragonfly_roam_btn = None
            if oid == "moon":
                location_subrow = QHBoxLayout()
                location_subrow.setContentsMargins(14, 0, 0, 0)
                location_subrow.setSpacing(5)
                location_lbl = QLabel("Location:", scroll_content)
                location_lbl.setFont(QFont("Segoe UI", 8))
                location_lbl.setStyleSheet("color: #64748b;")
                moon_location_edit = QLineEdit(scroll_content)
                moon_location_edit.setPlaceholderText("latitude, longitude")
                moon_location_edit.setToolTip("Stored only on this computer. Example: 14.5995, 120.9842")
                moon_location_edit.setFixedHeight(22)
                moon_location_edit.setStyleSheet("font-size: 9px; padding: 1px 5px; border: 1px solid #cbd5e1; border-radius: 4px;")
                location_save = QPushButton("Save", scroll_content)
                location_save.setFixedHeight(22)
                location_save.setStyleSheet("font-size: 9px; padding: 1px 7px; min-height: 18px; border-radius: 4px;")
                location_save.clicked.connect(lambda _, edit=moon_location_edit: self._on_moon_location_saved(edit))
                moon_location_edit.returnPressed.connect(lambda edit=moon_location_edit: self._on_moon_location_saved(edit))
                location_subrow.addWidget(location_lbl)
                location_subrow.addWidget(moon_location_edit)
                location_subrow.addWidget(location_save)
                scroll_layout.addLayout(location_subrow)

                moon_actions_subrow = QHBoxLayout()
                moon_actions_subrow.setContentsMargins(14, 0, 0, 0)
                moon_actions_subrow.setSpacing(4)

                manila_btn = QPushButton("📍 Manila", scroll_content)
                manila_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f0fdf4;
                        border: 1px solid #bbf7d0;
                        color: #166534;
                    }
                    QPushButton:hover { background: #dcfce7; }
                """)
                manila_btn.setToolTip("Set coordinates to Manila, Philippines (14.60°N, 120.98°E)")
                manila_btn.clicked.connect(lambda _, edit=moon_location_edit: self._on_moon_manila_clicked(edit))
                moon_actions_subrow.addWidget(manila_btn)

                dock_btn = QPushButton("📌 Tray", scroll_content)
                dock_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f8fafc;
                        border: 1px solid #cbd5e1;
                        color: #334155;
                    }
                    QPushButton:hover { background: #e2e8f0; }
                """)
                dock_btn.setToolTip("Toggle docking right above taskbar tray icons vs astronomical altitude")
                dock_btn.clicked.connect(self._on_moon_dock_clicked)
                moon_actions_subrow.addWidget(dock_btn)

                preview_btn = QPushButton("👁️ View", scroll_content)
                preview_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f8fafc;
                        border: 1px solid #cbd5e1;
                        color: #334155;
                    }
                    QPushButton:hover { background: #e2e8f0; }
                """)
                preview_btn.setToolTip("Toggle Always Visible (Preview) vs Astronomical Sky")
                preview_btn.clicked.connect(self._on_moon_preview_clicked)
                moon_actions_subrow.addWidget(preview_btn)

                clouds_btn = QPushButton("☁️ Clouds", scroll_content)
                clouds_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f8fafc;
                        border: 1px solid #cbd5e1;
                        color: #334155;
                    }
                    QPushButton:hover { background: #e2e8f0; }
                """)
                clouds_btn.setToolTip("Toggle drifting clouds across the moon")
                clouds_btn.clicked.connect(self._on_moon_clouds_clicked)
                moon_actions_subrow.addWidget(clouds_btn)

                moon_hud_btn = QPushButton("🎛️ HUD", scroll_content)
                moon_hud_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #334155;
                    }
                    QPushButton:hover { background: #e2e8f0; }
                """)
                moon_hud_btn.setToolTip("Toggle on-screen Lunar Ephemeris HUD control panel")
                moon_hud_btn.clicked.connect(self._on_moon_hud_clicked)
                moon_actions_subrow.addWidget(moon_hud_btn)

                moon_actions_subrow.addStretch()
                scroll_layout.addLayout(moon_actions_subrow)
            if oid == "hornwort":
                # Growth Speed row
                speed_subrow = QHBoxLayout()
                speed_subrow.setContentsMargins(14, 0, 0, 0)
                speed_subrow.setSpacing(4)

                speed_lbl = QLabel("Growth:", scroll_content)
                speed_lbl.setFont(QFont("Segoe UI", 8))
                speed_lbl.setStyleSheet("color: #64748b;")
                speed_subrow.addWidget(speed_lbl)

                speed_bg = QButtonGroup(self)
                for sp_label, sp_val in [("1x", 1.0), ("2x", 2.0), ("3x", 3.0), ("4x", 4.0), ("5x", 5.0)]:
                    rb = QRadioButton(sp_label, scroll_content)
                    rb.setProperty("speedValue", sp_val)
                    if sp_val == 1.0:
                        rb.setChecked(True)
                    speed_bg.addButton(rb)
                    speed_subrow.addWidget(rb)

                speed_subrow.addStretch()
                restart_btn = QPushButton("Restart", scroll_content)
                restart_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 6px;
                        min-height: 18px;
                        background: #f0fdf4;
                        border: 1px solid #bbf7d0;
                        border-radius: 4px;
                        color: #166534;
                    }
                    QPushButton:hover {
                        background: #dcfce7;
                        border-color: #86efac;
                    }
                """)
                restart_btn.setToolTip("Restart Hornwort growth from age 00:00:00")
                restart_btn.clicked.connect(self._on_restart_hornwort_clicked)
                speed_subrow.addWidget(restart_btn)

                scroll_layout.addLayout(speed_subrow)
                speed_bg.buttonToggled.connect(self._on_hornwort_speed_toggled)

                # Christmas LED Lights row
                xmas_subrow = QHBoxLayout()
                xmas_subrow.setContentsMargins(14, 0, 0, 0)
                xmas_subrow.setSpacing(6)

                xmas_lbl = QLabel("Xmas Lights:", scroll_content)
                xmas_lbl.setFont(QFont("Segoe UI", 8))
                xmas_lbl.setStyleSheet("color: #64748b;")
                xmas_subrow.addWidget(xmas_lbl)

                xmas_toggle_btn = QPushButton("OFF", scroll_content)
                xmas_toggle_btn.setCheckable(True)
                xmas_toggle_btn.setFixedWidth(42)
                xmas_toggle_btn.setStyleSheet("""
                    QPushButton { font-size: 9px; padding: 2px 4px; min-height: 18px; border-radius: 4px; }
                    QPushButton:checked { background-color: #10b981; border-color: #059669; color: #ffffff; }
                """)
                xmas_toggle_btn.toggled.connect(self._on_hornwort_xmas_toggled)

                xmas_mode_btn = QPushButton("Twinkle", scroll_content)
                xmas_mode_btn.setFixedWidth(56)
                xmas_mode_btn.setStyleSheet("font-size: 9px; padding: 2px 4px; min-height: 18px; border-radius: 4px;")
                xmas_mode_btn.setToolTip("Toggle between calm Twinkle and Steady fairy glow")
                xmas_mode_btn.clicked.connect(self._on_hornwort_xmas_mode_clicked)

                xmas_subrow.addWidget(xmas_toggle_btn)
                xmas_subrow.addWidget(xmas_mode_btn)
                xmas_subrow.addStretch()

                scroll_layout.addLayout(xmas_subrow)

                # Christmas Color Combination Theme row
                theme_subrow = QHBoxLayout()
                theme_subrow.setContentsMargins(14, 0, 0, 0)
                theme_subrow.setSpacing(6)

                theme_lbl = QLabel("Colors:", scroll_content)
                theme_lbl.setFont(QFont("Segoe UI", 8))
                theme_lbl.setStyleSheet("color: #64748b;")
                theme_subrow.addWidget(theme_lbl)

                xmas_theme_btn = QPushButton("🌈 Rainbow", scroll_content)
                xmas_theme_btn.setFixedHeight(20)
                xmas_theme_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 1px 8px;
                        border-radius: 4px;
                        background-color: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #0f172a;
                    }
                    QPushButton:hover {
                        background-color: #e2e8f0;
                    }
                """)
                xmas_theme_btn.setToolTip("Click to cycle holiday color combination: Rainbow, Warm Gold, Candy Cane, Winter Frost, Mistletoe")
                xmas_theme_btn.clicked.connect(self._on_hornwort_xmas_theme_clicked)

                theme_subrow.addWidget(xmas_theme_btn)
                theme_subrow.addStretch()

                scroll_layout.addLayout(theme_subrow)

            if oid == "dandelions":
                dan_style_subrow = QHBoxLayout()
                dan_style_subrow.setContentsMargins(14, 0, 0, 0)
                dan_style_subrow.setSpacing(6)

                dan_style_lbl = QLabel("Style:", scroll_content)
                dan_style_lbl.setFont(QFont("Segoe UI", 8))
                dan_style_lbl.setStyleSheet("color: #64748b;")
                dan_style_subrow.addWidget(dan_style_lbl)

                dandelion_style_combo = QComboBox(scroll_content)
                dandelion_style_combo.setFixedHeight(22)
                dandelion_style_combo.setMaximumWidth(220)
                dandelion_style_combo.setStyleSheet("""
                    QComboBox {
                        font-size: 9px;
                        padding: 1px 6px;
                        border-radius: 4px;
                        background-color: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #0f172a;
                    }
                    QComboBox:hover {
                        background-color: #e2e8f0;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #ffffff;
                        color: #0f172a;
                        selection-background-color: #e2e8f0;
                        selection-color: #0f172a;
                    }
                """)
                for s_id, s_label in DANDELION_STYLES:
                    dandelion_style_combo.addItem(s_label, s_id)
                dandelion_style_combo.currentIndexChanged.connect(self._on_dandelion_style_changed)

                dan_style_subrow.addWidget(dandelion_style_combo)
                dan_style_subrow.addStretch()

                scroll_layout.addLayout(dan_style_subrow)

            if oid == "betta_fish":
                breed_subrow = QHBoxLayout()
                breed_subrow.setContentsMargins(14, 0, 0, 0)
                breed_subrow.setSpacing(6)

                breed_lbl = QLabel("Breed:", scroll_content)
                breed_lbl.setFont(QFont("Segoe UI", 8))
                breed_lbl.setStyleSheet("color: #64748b;")
                breed_subrow.addWidget(breed_lbl)

                betta_breed_combo = QComboBox(scroll_content)
                betta_breed_combo.setFixedHeight(22)
                betta_breed_combo.setMaximumWidth(220)
                betta_breed_combo.setStyleSheet("""
                    QComboBox {
                        font-size: 9px;
                        padding: 1px 6px;
                        border-radius: 4px;
                        background-color: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #0f172a;
                    }
                    QComboBox:hover {
                        background-color: #e2e8f0;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #ffffff;
                        color: #0f172a;
                        selection-background-color: #e2e8f0;
                        selection-color: #0f172a;
                    }
                """)
                for b_id, b_label in BETTA_BREEDS:
                    betta_breed_combo.addItem(b_label, b_id)
                betta_breed_combo.currentIndexChanged.connect(self._on_betta_breed_changed)

                breed_subrow.addWidget(betta_breed_combo)
                breed_subrow.addStretch()

                scroll_layout.addLayout(breed_subrow)

            if oid == "orchid":
                color_subrow = QHBoxLayout()
                color_subrow.setContentsMargins(14, 0, 0, 0)
                color_subrow.setSpacing(6)
                color_lbl = QLabel("Color:", scroll_content)
                color_lbl.setFont(QFont("Segoe UI", 8))
                color_lbl.setStyleSheet("color: #64748b;")
                orchid_color_combo = QComboBox(scroll_content)
                orchid_color_combo.setFixedHeight(22)
                orchid_color_combo.setStyleSheet("font-size: 9px; padding: 1px 6px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; color: #0f172a;")
                for color_id, color_label in ORCHID_COLORS:
                    orchid_color_combo.addItem(color_label, color_id)
                orchid_color_combo.currentIndexChanged.connect(self._on_orchid_color_changed)
                color_subrow.addWidget(color_lbl)
                color_subrow.addWidget(orchid_color_combo)
                color_subrow.addStretch()
                scroll_layout.addLayout(color_subrow)

            if oid == "dragonflies":
                # Species / Color Preset dropdown
                df_palette_subrow = QHBoxLayout()
                df_palette_subrow.setContentsMargins(14, 0, 0, 0)
                df_palette_subrow.setSpacing(6)

                df_palette_lbl = QLabel("Species:", scroll_content)
                df_palette_lbl.setFont(QFont("Segoe UI", 8))
                df_palette_lbl.setStyleSheet("color: #64748b;")
                df_palette_subrow.addWidget(df_palette_lbl)

                dragonfly_palette_combo = QComboBox(scroll_content)
                dragonfly_palette_combo.setFixedHeight(22)
                dragonfly_palette_combo.setMaximumWidth(210)
                dragonfly_palette_combo.setStyleSheet("""
                    QComboBox {
                        font-size: 9px;
                        padding: 1px 6px;
                        border-radius: 4px;
                        background-color: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #0f172a;
                    }
                    QComboBox:hover {
                        background-color: #e2e8f0;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #ffffff;
                        color: #0f172a;
                        selection-background-color: #e2e8f0;
                        selection-color: #0f172a;
                    }
                """)
                for p_id, p_label in DRAGONFLY_PALETTES:
                    dragonfly_palette_combo.addItem(p_label, p_id)
                dragonfly_palette_combo.currentIndexChanged.connect(self._on_dragonfly_palette_changed)

                df_palette_subrow.addWidget(dragonfly_palette_combo)
                df_palette_subrow.addStretch()
                scroll_layout.addLayout(df_palette_subrow)

                # Style and Actions (Startle, Fly All, HUD)
                df_action_subrow = QHBoxLayout()
                df_action_subrow.setContentsMargins(14, 0, 0, 0)
                df_action_subrow.setSpacing(4)

                df_style_lbl = QLabel("Style:", scroll_content)
                df_style_lbl.setFont(QFont("Segoe UI", 8))
                df_style_lbl.setStyleSheet("color: #64748b;")
                df_action_subrow.addWidget(df_style_lbl)

                dragonfly_style_combo = QComboBox(scroll_content)
                dragonfly_style_combo.setFixedHeight(20)
                dragonfly_style_combo.setMaximumWidth(125)
                dragonfly_style_combo.setStyleSheet("""
                    QComboBox {
                        font-size: 9px;
                        padding: 1px 4px;
                        border-radius: 4px;
                        background-color: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #0f172a;
                    }
                """)
                for s_id, s_label in DRAGONFLY_STYLES:
                    dragonfly_style_combo.addItem(s_label, s_id)
                dragonfly_style_combo.currentIndexChanged.connect(self._on_dragonfly_style_changed)
                df_action_subrow.addWidget(dragonfly_style_combo)
                df_action_subrow.addSpacing(2)

                dragonfly_startle_btn = QPushButton("⚡ Dart", scroll_content)
                dragonfly_startle_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #fef3c7;
                        border: 1px solid #fde68a;
                        color: #92400e;
                    }
                    QPushButton:hover {
                        background: #fde68a;
                    }
                """)
                dragonfly_startle_btn.setToolTip("Startle all dragonflies into evasive flight")
                dragonfly_startle_btn.clicked.connect(self._on_dragonfly_startle_clicked)
                df_action_subrow.addWidget(dragonfly_startle_btn)

                dragonfly_roam_btn = QPushButton("✈️ Fly", scroll_content)
                dragonfly_roam_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f0fdf4;
                        border: 1px solid #bbf7d0;
                        color: #166534;
                    }
                    QPushButton:hover {
                        background: #dcfce7;
                    }
                """)
                dragonfly_roam_btn.setToolTip("Fly all resting dragonflies")
                dragonfly_roam_btn.clicked.connect(self._on_dragonfly_roam_clicked)
                df_action_subrow.addWidget(dragonfly_roam_btn)

                hud_btn = QPushButton("🎛️ HUD", scroll_content)
                hud_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 5px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #f1f5f9;
                        border: 1px solid #cbd5e1;
                        color: #334155;
                    }
                    QPushButton:hover {
                        background: #e2e8f0;
                    }
                """)
                hud_btn.setToolTip("Toggle on-screen Flight Study HUD control panel")
                hud_btn.clicked.connect(self._on_dragonfly_hud_clicked)
                df_action_subrow.addWidget(hud_btn)

                df_action_subrow.addStretch()
                scroll_layout.addLayout(df_action_subrow)

            if oid == "cichlid":
                cichlid_action_subrow = QHBoxLayout()
                cichlid_action_subrow.setContentsMargins(14, 0, 0, 0)
                cichlid_action_subrow.setSpacing(4)

                cichlid_breed_btn = QPushButton("🥚 Breed", scroll_content)
                cichlid_breed_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 9px;
                        padding: 2px 8px;
                        min-height: 18px;
                        border-radius: 4px;
                        background: #fef3c7;
                        border: 1px solid #fde68a;
                        color: #b45309;
                    }
                    QPushButton:hover { background: #fde68a; }
                """)
                cichlid_breed_btn.setToolTip("Cycle breeding stage (Courtship -> Eggs -> Eyed -> Wrigglers -> Fry -> 8h Auto)")
                cichlid_breed_btn.clicked.connect(self._on_cichlid_breed_clicked)
                cichlid_action_subrow.addWidget(cichlid_breed_btn)

                cichlid_action_subrow.addStretch()
                scroll_layout.addLayout(cichlid_action_subrow)

            self._species_widgets[oid] = {
                "toggle": toggle_btn,
                "count_label": count_label,
                "minus": minus_btn,
                "plus": plus_btn,
                "size_group": bg,
                "opacity_slider": op_slider,
                "opacity_label": op_val_lbl,
                "speed_group": speed_bg,
                "xmas_toggle": xmas_toggle_btn,
                "xmas_mode": xmas_mode_btn,
                "xmas_theme": xmas_theme_btn,
                "betta_breed": betta_breed_combo,
                "dandelion_style": dandelion_style_combo,
                "orchid_color": orchid_color_combo,
                "moon_location": moon_location_edit,
                "dragonfly_palette": dragonfly_palette_combo,
                "dragonfly_style": dragonfly_style_combo,
                "dragonfly_startle": dragonfly_startle_btn,
                "dragonfly_roam": dragonfly_roam_btn,
            }

        scroll_area.setWidget(scroll_content)
        card_layout.addWidget(scroll_area)

        # Separator line
        card_layout.addWidget(self._make_h_line())

        # ── Action Buttons Footer ──
        act_layout = QHBoxLayout()

        self.hide_all_btn = QPushButton("Hide All", card)
        self.hide_all_btn.clicked.connect(self._on_hide_all_clicked)

        welcome_btn = QPushButton("Welcome Guide", card)
        welcome_btn.clicked.connect(self.show_welcome_requested.emit)

        quit_btn = QPushButton("Quit", card)
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                border: 1px solid #fca5a5;
                color: #b91c1c;
            }
            QPushButton:hover {
                background-color: #fecaca;
                border-color: #f87171;
                color: #991b1b;
            }
        """)
        quit_btn.clicked.connect(self.quit_requested.emit)

        act_layout.addWidget(self.hide_all_btn)
        act_layout.addWidget(welcome_btn)
        act_layout.addWidget(quit_btn)

        card_layout.addLayout(act_layout)

        main_layout.addWidget(card)
        self.setFixedWidth(395)

    def _make_h_line(self):
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e2e8f0; border: none; min-height: 1px; max-height: 1px;")
        return line

    def _position_above_taskbar(self):
        """Calculate primary screen bounds and position Control Center near tray area."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.geometry()
        avail = screen.availableGeometry()

        # Default width/height
        panel_w = self.width()
        panel_h = self.sizeHint().height()

        # Inquire taskbar position by comparing total vs available geometry
        x = avail.right() - panel_w - 12
        y = avail.bottom() - panel_h - 12

        # Clamp safely within available display coordinates
        x = max(avail.left() + 10, min(x, avail.right() - panel_w - 10))
        y = max(avail.top() + 10, min(y, avail.bottom() - panel_h - 10))

        self.move(x, y)

    def show_panel(self):
        """Show and position the Control Center."""
        self._update_from_config()
        self._position_above_taskbar()
        self.show()
        self.raise_()
        self.activateWindow()

    def is_pinned(self):
        return self.pin_btn.isChecked()

    def _on_pin_toggled(self, checked):
        if self.config:
            self.config.set("control_center", "pinned", checked)
            self.config.save()

    def changeEvent(self, event):
        """Close on focus loss if not pinned."""
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow() and not self.is_pinned():
                self.hide()
        super().changeEvent(event)

    def _update_from_config(self):
        if not self.config:
            return

        # Pin state
        pinned = self.config.get("control_center", "pinned") or False
        self.pin_btn.setChecked(bool(pinned))

        # Species state
        species_defaults = {
            "fireflies": 6,
            "dragonflies": 2,
            "dandelions": 3,
            "cosmos": 7,
            "moon": 1,
            "butterfly_blue": 1,
            "butterfly_yellow": 1,
            "butterfly_orange": 1,
            "hornwort": 4,
            "neon_tetra": 2,
            "mermaid": 1,
            "telegrama": 1,
            "betta_fish": 1,
            "cat": 1,
        }
        for oid, widgets in self._species_widgets.items():
            active = self.config.get("overlays", oid) or False
            count = self.config.get("overlays", f"{oid}_count")
            if count is None:
                count = species_defaults.get(oid, 3)

            widgets["toggle"].blockSignals(True)
            widgets["toggle"].setChecked(bool(active))
            widgets["toggle"].setText("ON" if active else "OFF")
            widgets["toggle"].blockSignals(False)

            widgets["count_label"].setText(str(count))
            widgets["count_label"].setToolTip(
                f"{count} flower sites on one branching plant" if oid == "cosmos"
                else f"{oid.capitalize()}: {count} of 12"
            )

        # Species scale/size
        for oid, widgets in self._species_widgets.items():
            scale_val = float(self.config.get("overlays", f"{oid}_scale") or 1.0)
            for btn in widgets["size_group"].buttons():
                val = float(btn.property("scaleValue"))
                if abs(val - scale_val) < 0.05:
                    btn.blockSignals(True)
                    btn.setChecked(True)
                    btn.blockSignals(False)

        # Species opacity
        for oid, widgets in self._species_widgets.items():
            op_val = float(self.config.get("overlays", f"{oid}_opacity") or 1.0)
            op_int = int(round(max(0.1, min(1.0, op_val)) * 100))
            if "opacity_slider" in widgets:
                widgets["opacity_slider"].blockSignals(True)
                widgets["opacity_slider"].setValue(op_int)
                widgets["opacity_slider"].blockSignals(False)
            if "opacity_label" in widgets:
                widgets["opacity_label"].setText(f"{op_int}%")

        # Moon observer location
        if "moon" in self._species_widgets:
            location_edit = self._species_widgets["moon"].get("moon_location")
            if location_edit:
                latitude = self.config.get("overlays", "moon_latitude")
                longitude = self.config.get("overlays", "moon_longitude")
                location_edit.setText("" if latitude is None or longitude is None else f"{latitude:.5f}, {longitude:.5f}")

        # Hornwort growth speed
        if "hornwort" in self._species_widgets and self._species_widgets["hornwort"].get("speed_group"):
            spd_val = float(self.config.get("overlays", "hornwort_growth_speed") or 1.0)
            for btn in self._species_widgets["hornwort"]["speed_group"].buttons():
                val = float(btn.property("speedValue"))
                if abs(val - spd_val) < 0.05:
                    btn.blockSignals(True)
                    btn.setChecked(True)
                    btn.blockSignals(False)

        # Hornwort Christmas Lights
        if "hornwort" in self._species_widgets:
            hw_widgets = self._species_widgets["hornwort"]
            if hw_widgets.get("xmas_toggle") and hw_widgets.get("xmas_mode"):
                x_active = bool(self.config.get("overlays", "hornwort_xmas_lights") or False)
                x_mode = str(self.config.get("overlays", "hornwort_xmas_mode") or "twinkle")
                x_theme = str(self.config.get("overlays", "hornwort_xmas_theme") or "multicolor")
                hw_widgets["xmas_toggle"].blockSignals(True)
                hw_widgets["xmas_toggle"].setChecked(x_active)
                hw_widgets["xmas_toggle"].setText("ON" if x_active else "OFF")
                hw_widgets["xmas_toggle"].blockSignals(False)
                hw_widgets["xmas_mode"].setText("Twinkle" if x_mode == "twinkle" else "Steady")
                if hw_widgets.get("xmas_theme"):
                    theme_dict = dict(XMAS_THEMES)
                    hw_widgets["xmas_theme"].setText(theme_dict.get(x_theme, "🌈 Rainbow"))

        # Betta Fish breed
        if "betta_fish" in self._species_widgets:
            bf_widgets = self._species_widgets["betta_fish"]
            if bf_widgets.get("betta_breed"):
                saved_breed = str(self.config.get("overlays", "betta_fish_breed") or "buttercup")
                combo = bf_widgets["betta_breed"]
                idx = combo.findData(saved_breed)
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)

        if "orchid" in self._species_widgets:
            combo = self._species_widgets["orchid"].get("orchid_color")
            if combo:
                saved_color = str(self.config.get("overlays", "orchid_color") or "fuchsia")
                idx = combo.findData(saved_color)
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)


        if "dragonflies" in self._species_widgets:
            df_widgets = self._species_widgets["dragonflies"]
            if df_widgets.get("dragonfly_palette"):
                saved_pal = str(self.config.get("overlays", "dragonflies_palette") or "mixed")
                combo = df_widgets["dragonfly_palette"]
                idx = combo.findData(saved_pal)
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)
            if df_widgets.get("dragonfly_style"):
                saved_style = str(self.config.get("overlays", "dragonflies_style") or "percher")
                combo = df_widgets["dragonfly_style"]
                idx = combo.findData(saved_style)
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)

        if "dandelions" in self._species_widgets:
            dan_widgets = self._species_widgets["dandelions"]
            if dan_widgets.get("dandelion_style"):
                saved_style = str(self.config.get("overlays", "dandelions_style") or "cyan")
                combo = dan_widgets["dandelion_style"]
                idx = combo.findData(saved_style)
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)

    def _on_hornwort_xmas_toggled(self, checked):
        if "hornwort" in self._species_widgets:
            hw = self._species_widgets["hornwort"]
            hw["xmas_toggle"].setText("ON" if checked else "OFF")
            mode = hw["xmas_mode"].text().lower()
            theme = str(self.config.get("overlays", "hornwort_xmas_theme") or "multicolor") if self.config else "multicolor"
            if self.config:
                self.config.set("overlays", "hornwort_xmas_lights", checked)
                self.config.save()
            if self.overlay_manager:
                self.overlay_manager.set_hornwort_xmas_lights(checked, mode, theme)

    def _on_hornwort_xmas_mode_clicked(self):
        if "hornwort" in self._species_widgets:
            hw = self._species_widgets["hornwort"]
            current_mode = hw["xmas_mode"].text()
            new_mode = "Steady" if current_mode == "Twinkle" else "Twinkle"
            hw["xmas_mode"].setText(new_mode)
            checked = hw["xmas_toggle"].isChecked()
            mode_val = new_mode.lower()
            theme = str(self.config.get("overlays", "hornwort_xmas_theme") or "multicolor") if self.config else "multicolor"
            if self.config:
                self.config.set("overlays", "hornwort_xmas_mode", mode_val)
                self.config.save()
            if self.overlay_manager:
                self.overlay_manager.set_hornwort_xmas_lights(checked, mode_val, theme)

    def _on_hornwort_xmas_theme_clicked(self):
        if "hornwort" in self._species_widgets:
            hw = self._species_widgets["hornwort"]
            current_theme = str(self.config.get("overlays", "hornwort_xmas_theme") or "multicolor") if self.config else "multicolor"
            theme_keys = [k for k, _ in XMAS_THEMES]
            next_idx = (theme_keys.index(current_theme) + 1) % len(theme_keys) if current_theme in theme_keys else 0
            new_theme, new_label = XMAS_THEMES[next_idx]
            if hw.get("xmas_theme"):
                hw["xmas_theme"].setText(new_label)
            if self.config:
                self.config.set("overlays", "hornwort_xmas_theme", new_theme)
                self.config.save()
            checked = hw["xmas_toggle"].isChecked()
            mode = hw["xmas_mode"].text().lower()
            if self.overlay_manager:
                self.overlay_manager.set_hornwort_xmas_lights(checked, mode, new_theme)

    def _on_hornwort_speed_toggled(self, button, checked):
        if not checked:
            return
        val = float(button.property("speedValue"))
        if self.config:
            self.config.set("overlays", "hornwort_growth_speed", val)
            self.config.save()
        if self.overlay_manager:
            self.overlay_manager.set_hornwort_growth_speed(val)

    def _on_restart_hornwort_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.restart_hornwort_growth()

    def _on_betta_breed_changed(self, index):
        if "betta_fish" in self._species_widgets:
            combo = self._species_widgets["betta_fish"].get("betta_breed")
            if combo:
                breed_id = combo.currentData()
                if self.config:
                    self.config.set("overlays", "betta_fish_breed", breed_id)
                    self.config.save()
                if self.overlay_manager:
                    self.overlay_manager.set_betta_fish_breed(breed_id)

    def _on_orchid_color_changed(self, index):
        combo = self._species_widgets.get("orchid", {}).get("orchid_color")
        if not combo:
            return
        color_id = combo.currentData()
        if self.config:
            self.config.set("overlays", "orchid_color", color_id)
            self.config.save()
        if self.overlay_manager:
            self.overlay_manager.set_orchid_color(color_id)

    def _on_dandelion_style_changed(self, index):
        combo = self._species_widgets.get("dandelions", {}).get("dandelion_style")
        if not combo:
            return
        style_id = combo.currentData()
        if self.config:
            self.config.set("overlays", "dandelions_style", style_id)
            self.config.save()
        if self.overlay_manager:
            self.overlay_manager.set_dandelions_style(style_id)

    def _on_dragonfly_palette_changed(self, index):
        combo = self._species_widgets.get("dragonflies", {}).get("dragonfly_palette")
        if not combo:
            return
        palette_id = combo.currentData()
        if self.config:
            self.config.set("overlays", "dragonflies_palette", palette_id)
            self.config.save()
        if self.overlay_manager:
            self.overlay_manager.set_dragonflies_palette(palette_id)

    def _on_dragonfly_style_changed(self, index):
        combo = self._species_widgets.get("dragonflies", {}).get("dragonfly_style")
        if not combo:
            return
        style_id = combo.currentData()
        if self.config:
            self.config.set("overlays", "dragonflies_style", style_id)
            self.config.save()
        if self.overlay_manager:
            self.overlay_manager.set_dragonflies_style(style_id)

    def _on_dragonfly_startle_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.dragonflies_startle()

    def _on_dragonfly_roam_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.dragonflies_roam()

    def _on_dragonfly_hud_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.toggle_dragonflies_controls()

    def _on_moon_manila_clicked(self, location_edit):
        location_edit.setText("14.5995, 120.9842")
        self._on_moon_location_saved(location_edit)

    def _on_moon_dock_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.toggle_moon_dock()

    def _on_moon_preview_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.toggle_moon_preview()

    def _on_moon_clouds_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.toggle_moon_clouds()

    def _on_moon_hud_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.toggle_moon_controls()

    def _on_cichlid_dart_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.cichlid_dart()

    def _on_cichlid_turn_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.cichlid_turn()

    def _on_cichlid_dig_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.cichlid_dig()

    def _on_cichlid_front_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.cichlid_front_view()

    def _on_cichlid_pair_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.cichlid_toggle_pair()

    def _on_cichlid_breed_clicked(self):
        if not hasattr(self, "_cichlid_breed_stage_idx"):
            self._cichlid_breed_stage_idx = 0
        stages = ["courtship", "eggs", "eyed", "wrigglers", "fry", "auto"]
        self._cichlid_breed_stage_idx = (self._cichlid_breed_stage_idx + 1) % len(stages)
        stage = stages[self._cichlid_breed_stage_idx]
        if self.overlay_manager:
            self.overlay_manager.cichlid_set_breeding_stage(stage)

    def _on_cichlid_hud_clicked(self):
        if self.overlay_manager:
            self.overlay_manager.toggle_cichlid_controls()

    def _on_species_opacity_changed(self, species_id, value, label_widget):
        label_widget.setText(f"{value}%")
        op_float = value / 100.0
        if self.config:
            self.config.set("overlays", f"{species_id}_opacity", op_float)
            self.config.save()
        if self.overlay_manager:
            self.overlay_manager.set_overlay_opacity(species_id, op_float)

    def _on_moon_location_saved(self, location_edit):
        raw = location_edit.text().strip()
        try:
            parts = [part.strip() for part in raw.split(",")]
            if len(parts) != 2:
                raise ValueError
            latitude, longitude = float(parts[0]), float(parts[1])
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError
        except (TypeError, ValueError):
            location_edit.setStyleSheet("font-size: 9px; padding: 1px 5px; border: 1px solid #ef4444; border-radius: 4px;")
            location_edit.setToolTip("Enter decimal coordinates as latitude, longitude")
            return

        location_edit.setStyleSheet("font-size: 9px; padding: 1px 5px; border: 1px solid #86efac; border-radius: 4px;")
        location_edit.setToolTip("Location is stored only on this computer")
        if self.config:
            self.config.set("overlays", "moon_latitude", latitude)
            self.config.set("overlays", "moon_longitude", longitude)
            self.config.save()
        if self.overlay_manager and self.config.get("overlays", "moon"):
            if self.overlay_manager.is_active("moon"):
                self.overlay_manager.set_moon_location(latitude, longitude)
            else:
                self.overlay_manager.reload_overlay("moon")

    def _on_species_toggled(self, species_id, checked):
        widgets = self._species_widgets.get(species_id)
        if widgets:
            widgets["toggle"].setText("ON" if checked else "OFF")

        if self.config:
            self.config.set("overlays", species_id, checked)
            self.config.save()

        if self.overlay_manager:
            if checked:
                self.overlay_manager.open_overlay(species_id)
            else:
                self.overlay_manager.close_overlay(species_id)

        self.overlay_toggled.emit(species_id, checked)

    def _adjust_count(self, species_id, delta):
        widgets = self._species_widgets.get(species_id)
        if not widgets:
            return

        current = int(widgets["count_label"].text())
        new_count = max(1, min(12, current + delta))
        if new_count == current:
            return

        widgets["count_label"].setText(str(new_count))
        widgets["count_label"].setToolTip(
            f"{species_id.capitalize()}: {new_count} of 12"
        )

        if self.config:
            self.config.set("overlays", f"{species_id}_count", new_count)
            self.config.save()

        # Reload active overlay to apply count
        if self.overlay_manager and self.overlay_manager.is_active(species_id):
            self.overlay_manager.close_overlay(species_id)
            self.overlay_manager.open_overlay(species_id)

        self.count_changed.emit(species_id, new_count)

    def _on_species_size_toggled(self, button, checked):
        if not checked:
            return
        species_id = button.property("speciesId")
        val = float(button.property("scaleValue"))
        if self.config:
            self.config.set("overlays", f"{species_id}_scale", val)
            self.config.save()

        # Live scale update if active without closing/destroying window
        if self.overlay_manager and self.overlay_manager.is_active(species_id):
            self.overlay_manager.set_overlay_scale(species_id, val)

        self.scale_changed.emit(species_id, val)

    def _on_physics_preset_toggled(self, button, checked):
        if not checked:
            return
        mode = str(button.property("physicsMode")).lower()
        if self.config:
            self.config.set("nature", "physics_preset", mode)
            self.config.save()
        self.physics_preset_changed.emit(mode)

    def _on_slider_changed(self, value):
        self.strength_val_lbl.setText(f"{value}%")
        multiplier = value / 100.0
        if self.config:
            self.config.set("nature", "interaction_strength", multiplier)
            self.config.save()
        self.interaction_strength_changed.emit(multiplier)

    def _on_hide_all_clicked(self):
        self.toggle_all_requested.emit()
        is_visible = getattr(self.overlay_manager, "_global_visible", True)
        self.hide_all_btn.setText("Show All" if not is_visible else "Hide All")
