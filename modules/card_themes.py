"""
Theme registry for NetShare / Ohverlay notification notes.
"""

from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont


@dataclass(frozen=True)
class NoteTheme:
    theme_id: str
    label: str
    header_title: str
    description: str
    bg_top: tuple
    bg_bottom: tuple
    border: tuple
    glow: tuple
    accent: tuple
    divider: tuple
    text_head: tuple
    text_label: tuple
    text_value: tuple
    watermark: tuple
    button_primary: tuple
    button_hover: tuple
    button_dismiss: tuple
    button_text: tuple
    dismiss_text: tuple
    progress_track: tuple
    progress_fill: tuple
    title_font_family: str
    title_font_size: float
    title_font_weight: int
    label_font_family: str
    label_font_size: float
    label_font_weight: int
    value_font_family: str
    value_font_size: float
    value_font_weight: int
    button_font_family: str
    button_font_size: float
    button_font_weight: int
    brand_font_family: str
    brand_font_size: float
    brand_font_weight: int
    line_color: tuple | None = None
    margin_color: tuple | None = None
    fold_color: tuple | None = None
    aurora_color: tuple | None = None
    text_glow_color: tuple | None = None
    text_glow_blur: int = 0
    starfield: bool = False
    paper_lines: bool = False
    sticky_fold: bool = False
    aurora_band: bool = False
    floating_lock: bool = False


@dataclass(frozen=True)
class FontPreset:
    preset_id: str
    label: str
    description: str
    title_family: str | None = None
    label_family: str | None = None
    value_family: str | None = None
    button_family: str | None = None
    brand_family: str | None = None


def qcolor(spec, alpha=None):
    if len(spec) == 4:
        color = QColor(spec[0], spec[1], spec[2], spec[3])
    else:
        color = QColor(spec[0], spec[1], spec[2])
    if alpha is not None:
        color.setAlpha(alpha)
    return color


def build_font(family, point_size, weight, scale=1.0, italic=False):
    font = QFont(family)
    font.setPointSizeF(max(6.0, float(point_size) * float(scale)))
    font.setWeight(weight)
    font.setItalic(italic)
    return font


DEFAULT_NOTE_THEME_ID = "neon_postit_yellow"
DEFAULT_FONT_PRESET_ID = "theme_default"


def _sticky_theme(
    theme_id,
    label,
    *,
    bg_top,
    bg_bottom,
    border,
    glow,
    accent,
    fold,
    dark_text=True,
):
    if dark_text:
        text_head = (17, 17, 17)
        text_label = (50, 50, 50)
        text_value = (17, 17, 17)
        button_text = (17, 17, 17)
        dismiss_text = (60, 60, 60)
        watermark = (80, 80, 80, 110)
    else:
        text_head = (242, 247, 251)
        text_label = (207, 221, 234)
        text_value = (231, 240, 248)
        button_text = (20, 28, 40)
        dismiss_text = (214, 223, 235)
        watermark = (210, 221, 235, 118)

    return NoteTheme(
        theme_id=theme_id,
        label=label,
        header_title="",
        description="Realistic colored paper sticky note.",
        bg_top=bg_top,
        bg_bottom=bg_bottom,
        border=border,
        glow=glow,
        accent=accent,
        divider=border,
        text_head=text_head,
        text_label=text_label,
        text_value=text_value,
        watermark=watermark,
        button_primary=accent,
        button_hover=glow,
        button_dismiss=fold,
        button_text=button_text,
        dismiss_text=dismiss_text,
        progress_track=(border[0], border[1], border[2], 120),
        progress_fill=(glow[0], glow[1], glow[2], 210),
        title_font_family="Segoe Print",
        title_font_size=9.0,
        title_font_weight=QFont.Bold,
        label_font_family="Segoe UI",
        label_font_size=8.0,
        label_font_weight=QFont.Normal,
        value_font_family="Segoe Print",
        value_font_size=8.2,
        value_font_weight=QFont.DemiBold,
        button_font_family="Segoe UI",
        button_font_size=8.0,
        button_font_weight=QFont.Bold,
        brand_font_family="Segoe UI",
        brand_font_size=7.0,
        brand_font_weight=QFont.Normal,
        sticky_fold=True,
        fold_color=fold,
    )


THEME_LIST = [
    _sticky_theme(
        "neon_postit_yellow",
        "Canary Yellow (Classic)",
        bg_top=(252, 255, 50),
        bg_bottom=(244, 248, 30),
        border=(210, 215, 20),
        glow=(255, 255, 120),
        accent=(230, 190, 5),
        fold=(235, 235, 25, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_pink",
        "Neon Rose Pink",
        bg_top=(255, 42, 133),
        bg_bottom=(248, 28, 120),
        border=(215, 15, 95),
        glow=(255, 100, 165),
        accent=(255, 20, 110),
        fold=(230, 20, 100, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_lime",
        "Neon Lime Green",
        bg_top=(66, 245, 84),
        bg_bottom=(50, 230, 70),
        border=(35, 190, 55),
        glow=(120, 255, 135),
        accent=(20, 170, 40),
        fold=(45, 210, 60, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_cyan",
        "Electric Sky Blue",
        bg_top=(0, 210, 255),
        bg_bottom=(0, 190, 240),
        border=(0, 160, 215),
        glow=(100, 230, 255),
        accent=(0, 145, 200),
        fold=(0, 170, 225, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_orange",
        "Tangerine Peach",
        bg_top=(255, 115, 40),
        bg_bottom=(245, 95, 20),
        border=(220, 75, 10),
        glow=(255, 160, 80),
        accent=(235, 65, 5),
        fold=(230, 85, 15, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_purple",
        "Royal Lavender",
        bg_top=(190, 110, 255),
        bg_bottom=(170, 85, 245),
        border=(140, 60, 220),
        glow=(215, 150, 255),
        accent=(130, 45, 210),
        fold=(155, 75, 230, 220),
        dark_text=True,
    ),
    _sticky_paper_cream := _sticky_theme(
        "sticky_paper_cream",
        "Pastel Cream",
        bg_top=(252, 244, 222),
        bg_bottom=(241, 224, 191),
        border=(201, 177, 126),
        glow=(255, 218, 136),
        accent=(232, 170, 84),
        fold=(255, 246, 224, 210),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_mint",
        "Pastel Mint",
        bg_top=(215, 244, 224),
        bg_bottom=(187, 222, 198),
        border=(121, 174, 139),
        glow=(156, 241, 181),
        accent=(84, 172, 122),
        fold=(230, 253, 238, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_blush",
        "Pastel Blush Pink",
        bg_top=(251, 214, 224),
        bg_bottom=(236, 184, 197),
        border=(190, 128, 143),
        glow=(255, 186, 207),
        accent=(214, 108, 141),
        fold=(255, 234, 242, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_peach",
        "Pastel Peach",
        bg_top=(255, 223, 203),
        bg_bottom=(244, 197, 170),
        border=(201, 142, 116),
        glow=(255, 190, 148),
        accent=(239, 122, 92),
        fold=(255, 235, 223, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_sky",
        "Pastel Sky Blue",
        bg_top=(203, 232, 252),
        bg_bottom=(170, 207, 236),
        border=(109, 154, 196),
        glow=(153, 223, 255),
        accent=(72, 149, 214),
        fold=(225, 244, 255, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_slate",
        "Pastel Slate Paper",
        bg_top=(98, 111, 129),
        bg_bottom=(70, 81, 96),
        border=(171, 188, 212),
        glow=(198, 225, 255),
        accent=(132, 170, 224),
        fold=(126, 141, 164, 220),
        dark_text=False,
    ),
]


NOTE_THEMES = {theme.theme_id: theme for theme in THEME_LIST}

FONT_PRESET_LIST = [
    FontPreset(
        preset_id="theme_default",
        label="Theme Default",
        description="Use the font pairing designed for the current theme.",
    ),
    FontPreset(
        preset_id="marker_ink",
        label="Marker Hand (Segoe Print)",
        description="Authentic handwritten marker style on real sticky notes.",
        title_family="Segoe Print",
        label_family="Segoe UI",
        value_family="Segoe Print",
        button_family="Segoe UI",
        brand_family="Segoe Print",
    ),
    FontPreset(
        preset_id="handwriting_casual",
        label="Casual Ink (Ink Free)",
        description="Natural fluid handwriting style.",
        title_family="Ink Free",
        label_family="Segoe UI",
        value_family="Ink Free",
        button_family="Segoe UI",
        brand_family="Ink Free",
    ),
    FontPreset(
        preset_id="comic_hand",
        label="Playful Pen (Comic Sans MS)",
        description="Casual friendly marker pen style.",
        title_family="Comic Sans MS",
        label_family="Segoe UI",
        value_family="Comic Sans MS",
        button_family="Segoe UI",
        brand_family="Comic Sans MS",
    ),
    FontPreset(
        preset_id="calligraphy",
        label="Cursive Script (Segoe Script)",
        description="Elegant flowing handwriting with loops.",
        title_family="Segoe Script",
        label_family="Segoe UI",
        value_family="Segoe Script",
        button_family="Segoe UI",
        brand_family="Segoe Script",
    ),
    FontPreset(
        preset_id="clean_sans",
        label="Modern Clean (Segoe UI)",
        description="Crisp modern typography for clear reading.",
        title_family="Segoe UI Semibold",
        label_family="Segoe UI",
        value_family="Segoe UI",
        button_family="Segoe UI",
        brand_family="Segoe UI",
    ),
    FontPreset(
        preset_id="modern_bold",
        label="Bold Tech (Bahnschrift)",
        description="High-contrast geometric bold sans.",
        title_family="Bahnschrift",
        label_family="Segoe UI",
        value_family="Bahnschrift",
        button_family="Segoe UI",
        brand_family="Bahnschrift",
    ),
    FontPreset(
        preset_id="soft_humanist",
        label="Humanist (Candara)",
        description="Warm rounded curves with great legibility.",
        title_family="Candara",
        label_family="Segoe UI",
        value_family="Candara",
        button_family="Segoe UI",
        brand_family="Candara",
    ),
    FontPreset(
        preset_id="corporate_clean",
        label="Office Clean (Calibri)",
        description="Standard clean document typography.",
        title_family="Calibri",
        label_family="Segoe UI",
        value_family="Calibri",
        button_family="Segoe UI",
        brand_family="Calibri",
    ),
    FontPreset(
        preset_id="classic_arial",
        label="Classic Sans (Arial)",
        description="Standard neutral sans-serif font.",
        title_family="Arial",
        label_family="Arial",
        value_family="Arial",
        button_family="Arial",
        brand_family="Arial",
    ),
    FontPreset(
        preset_id="editorial_serif",
        label="Editorial Serif (Georgia)",
        description="Warm, readable literary serif body.",
        title_family="Georgia",
        label_family="Segoe UI",
        value_family="Georgia",
        button_family="Segoe UI",
        brand_family="Georgia",
    ),
    FontPreset(
        preset_id="antique_book",
        label="Vintage Antique (Book Antiqua)",
        description="Classic retro book aesthetic.",
        title_family="Book Antiqua",
        label_family="Book Antiqua",
        value_family="Book Antiqua",
        button_family="Book Antiqua",
        brand_family="Book Antiqua",
    ),
    FontPreset(
        preset_id="roman_serif",
        label="Times Roman (Times New Roman)",
        description="Traditional newspaper serif font.",
        title_family="Times New Roman",
        label_family="Segoe UI",
        value_family="Times New Roman",
        button_family="Segoe UI",
        brand_family="Times New Roman",
    ),
    FontPreset(
        preset_id="blueprint_mono",
        label="Terminal Mono (Consolas)",
        description="Code editor and terminal monospaced text.",
        title_family="Consolas",
        label_family="Segoe UI",
        value_family="Consolas",
        button_family="Segoe UI",
        brand_family="Consolas",
    ),
    FontPreset(
        preset_id="typewriter",
        label="Typewriter (Courier New)",
        description="Vintage mechanical typewriter aesthetic.",
        title_family="Courier New",
        label_family="Segoe UI",
        value_family="Courier New",
        button_family="Segoe UI",
        brand_family="Courier New",
    ),
]

FONT_PRESETS = {preset.preset_id: preset for preset in FONT_PRESET_LIST}

THEME_ALIASES = {
    "floating_text_night": "sticky_paper_slate",
    "floating_text_light": "sticky_paper_cream",
    "biolume_text_night": "neon_postit_cyan",
    "biolume_text_light": "sticky_paper_mint",
    "fireflies_night": "neon_postit_yellow",
    "blueprint_neon": "neon_postit_cyan",
    "aurora_glass": "sticky_paper_cream",
    "space_observatory": "sticky_paper_slate",
    "canary_postit": "neon_postit_yellow",
    "ruled_paper": "sticky_paper_cream",
    "sticky_paper_sun": "neon_postit_yellow",
    "sticky_paper_sage": "sticky_paper_mint",
    "sticky_paper_lilac": "neon_postit_purple",
    "sticky_paper_rosewood": "sticky_paper_slate",
}


def resolve_theme_id(theme_id):
    requested = (theme_id or "").strip()
    if requested in NOTE_THEMES:
        return requested
    aliased = THEME_ALIASES.get(requested)
    if aliased in NOTE_THEMES:
        return aliased
    return DEFAULT_NOTE_THEME_ID


def get_note_theme(theme_id):
    return NOTE_THEMES[resolve_theme_id(theme_id)]


def list_note_themes():
    return list(THEME_LIST)


def resolve_font_preset_id(preset_id):
    requested = (preset_id or "").strip()
    if requested in FONT_PRESETS:
        return requested
    return DEFAULT_FONT_PRESET_ID


def get_font_preset(preset_id):
    return FONT_PRESETS[resolve_font_preset_id(preset_id)]


def list_font_presets():
    return list(FONT_PRESET_LIST)
