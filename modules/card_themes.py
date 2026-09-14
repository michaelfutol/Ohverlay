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
    NoteTheme(
        theme_id="floating_text_night",
        label="Floating Text · Night",
        header_title="",
        description="Soft neon text for dark workspaces. Paper vanishes when locked.",
        bg_top=(11, 19, 34),
        bg_bottom=(6, 11, 22),
        border=(80, 136, 214),
        glow=(108, 230, 255),
        accent=(187, 142, 255),
        divider=(34, 52, 88),
        text_head=(228, 244, 255),
        text_label=(156, 192, 234),
        text_value=(219, 249, 255),
        watermark=(80, 120, 170, 138),
        button_primary=(76, 196, 248),
        button_hover=(162, 239, 255),
        button_dismiss=(35, 49, 76),
        button_text=(8, 19, 35),
        dismiss_text=(194, 216, 238),
        progress_track=(13, 22, 38, 180),
        progress_fill=(114, 239, 255, 210),
        title_font_family="Bahnschrift",
        title_font_size=9.2,
        title_font_weight=QFont.DemiBold,
        label_font_family="Segoe UI",
        label_font_size=8.0,
        label_font_weight=QFont.Normal,
        value_font_family="Consolas",
        value_font_size=8.4,
        value_font_weight=QFont.Bold,
        button_font_family="Segoe UI",
        button_font_size=8.0,
        button_font_weight=QFont.Bold,
        brand_font_family="Consolas",
        brand_font_size=7.0,
        brand_font_weight=QFont.Normal,
        aurora_band=True,
        aurora_color=(99, 169, 255, 72),
        floating_lock=True,
    ),
    NoteTheme(
        theme_id="floating_text_light",
        label="Floating Text · Light",
        header_title="",
        description="Dark ink text for light workspaces. Paper vanishes when locked.",
        bg_top=(252, 251, 246),
        bg_bottom=(238, 234, 226),
        border=(200, 192, 179),
        glow=(255, 216, 170),
        accent=(49, 63, 78),
        divider=(219, 213, 201),
        text_head=(26, 33, 42),
        text_label=(76, 88, 102),
        text_value=(18, 25, 33),
        watermark=(166, 154, 138, 128),
        button_primary=(210, 190, 158),
        button_hover=(255, 225, 188),
        button_dismiss=(236, 230, 219),
        button_text=(33, 41, 52),
        dismiss_text=(118, 112, 102),
        progress_track=(225, 219, 209, 180),
        progress_fill=(118, 150, 184, 200),
        title_font_family="Segoe UI Semibold",
        title_font_size=9.0,
        title_font_weight=QFont.DemiBold,
        label_font_family="Segoe UI",
        label_font_size=8.0,
        label_font_weight=QFont.Normal,
        value_font_family="Georgia",
        value_font_size=8.4,
        value_font_weight=QFont.Bold,
        button_font_family="Segoe UI",
        button_font_size=8.0,
        button_font_weight=QFont.Bold,
        brand_font_family="Segoe UI",
        brand_font_size=7.0,
        brand_font_weight=QFont.Normal,
        text_glow_color=(148, 190, 220, 178),
        text_glow_blur=11,
        floating_lock=True,
    ),
    NoteTheme(
        theme_id="biolume_text_night",
        label="Biolume Text · Night",
        header_title="",
        description="Iridescent plankton glow for dark workspaces. Paper disappears completely when locked.",
        bg_top=(6, 16, 28),
        bg_bottom=(3, 10, 18),
        border=(58, 110, 136),
        glow=(111, 244, 235),
        accent=(162, 237, 255),
        divider=(20, 38, 54),
        text_head=(220, 255, 252),
        text_label=(154, 224, 228),
        text_value=(208, 255, 248),
        watermark=(67, 120, 128, 135),
        button_primary=(83, 213, 232),
        button_hover=(150, 255, 245),
        button_dismiss=(24, 42, 58),
        button_text=(5, 19, 28),
        dismiss_text=(189, 225, 233),
        progress_track=(10, 21, 34, 180),
        progress_fill=(136, 255, 247, 220),
        title_font_family="Bahnschrift",
        title_font_size=9.2,
        title_font_weight=QFont.DemiBold,
        label_font_family="Segoe UI",
        label_font_size=8.0,
        label_font_weight=QFont.Normal,
        value_font_family="Consolas",
        value_font_size=8.4,
        value_font_weight=QFont.Bold,
        button_font_family="Segoe UI",
        button_font_size=8.0,
        button_font_weight=QFont.Bold,
        brand_font_family="Consolas",
        brand_font_size=7.0,
        brand_font_weight=QFont.Normal,
        aurora_band=True,
        aurora_color=(66, 255, 225, 76),
        text_glow_color=(122, 255, 240, 220),
        text_glow_blur=18,
        floating_lock=True,
    ),
    NoteTheme(
        theme_id="biolume_text_light",
        label="Biolume Text · Pearl",
        header_title="",
        description="Pearl-white floating text with soft sea-glow edges. Paper disappears completely when locked.",
        bg_top=(247, 249, 247),
        bg_bottom=(227, 235, 234),
        border=(177, 201, 198),
        glow=(126, 236, 221),
        accent=(37, 92, 103),
        divider=(205, 220, 218),
        text_head=(26, 58, 66),
        text_label=(75, 105, 110),
        text_value=(20, 56, 62),
        watermark=(128, 153, 152, 125),
        button_primary=(155, 220, 214),
        button_hover=(204, 248, 240),
        button_dismiss=(231, 239, 237),
        button_text=(26, 50, 54),
        dismiss_text=(102, 122, 120),
        progress_track=(212, 228, 224, 180),
        progress_fill=(86, 189, 179, 205),
        title_font_family="Segoe UI Semibold",
        title_font_size=9.0,
        title_font_weight=QFont.DemiBold,
        label_font_family="Segoe UI",
        label_font_size=8.0,
        label_font_weight=QFont.Normal,
        value_font_family="Georgia",
        value_font_size=8.4,
        value_font_weight=QFont.Bold,
        button_font_family="Segoe UI",
        button_font_size=8.0,
        button_font_weight=QFont.Bold,
        brand_font_family="Segoe UI",
        brand_font_size=7.0,
        brand_font_weight=QFont.Normal,
        text_glow_color=(126, 236, 221, 170),
        text_glow_blur=12,
        floating_lock=True,
    ),
    _sticky_theme(
        "neon_postit_pink",
        "Neon Post-it · Hot Pink",
        bg_top=(255, 42, 133),
        bg_bottom=(248, 28, 120),
        border=(215, 15, 95),
        glow=(255, 100, 165),
        accent=(255, 20, 110),
        fold=(230, 20, 100, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_orange",
        "Neon Post-it · Tangerine",
        bg_top=(255, 115, 40),
        bg_bottom=(245, 95, 20),
        border=(220, 75, 10),
        glow=(255, 160, 80),
        accent=(235, 65, 5),
        fold=(230, 85, 15, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_yellow",
        "Neon Post-it · Canary",
        bg_top=(252, 255, 50),
        bg_bottom=(244, 248, 30),
        border=(210, 215, 20),
        glow=(255, 255, 120),
        accent=(230, 190, 5),
        fold=(235, 235, 25, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_lime",
        "Neon Post-it · Lime",
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
        "Neon Post-it · Electric Sky",
        bg_top=(0, 210, 255),
        bg_bottom=(0, 190, 240),
        border=(0, 160, 215),
        glow=(100, 230, 255),
        accent=(0, 145, 200),
        fold=(0, 170, 225, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "neon_postit_purple",
        "Neon Post-it · Royal Violet",
        bg_top=(190, 110, 255),
        bg_bottom=(170, 85, 245),
        border=(140, 60, 220),
        glow=(215, 150, 255),
        accent=(130, 45, 210),
        fold=(155, 75, 230, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_cream",
        "Pastel Sticky · Cream",
        bg_top=(252, 244, 222),
        bg_bottom=(241, 224, 191),
        border=(201, 177, 126),
        glow=(255, 218, 136),
        accent=(232, 170, 84),
        fold=(255, 246, 224, 210),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_sun",
        "Pastel Sticky · Sun",
        bg_top=(255, 243, 157),
        bg_bottom=(244, 221, 109),
        border=(205, 172, 74),
        glow=(255, 212, 95),
        accent=(255, 160, 51),
        fold=(255, 247, 196, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_peach",
        "Pastel Sticky · Peach",
        bg_top=(255, 223, 203),
        bg_bottom=(244, 197, 170),
        border=(201, 142, 116),
        glow=(255, 190, 148),
        accent=(239, 122, 92),
        fold=(255, 235, 223, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_blush",
        "Pastel Sticky · Blush",
        bg_top=(251, 214, 224),
        bg_bottom=(236, 184, 197),
        border=(190, 128, 143),
        glow=(255, 186, 207),
        accent=(214, 108, 141),
        fold=(255, 234, 242, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_mint",
        "Pastel Sticky · Mint",
        bg_top=(215, 244, 224),
        bg_bottom=(187, 222, 198),
        border=(121, 174, 139),
        glow=(156, 241, 181),
        accent=(84, 172, 122),
        fold=(230, 253, 238, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_sage",
        "Pastel Sticky · Sage",
        bg_top=(200, 222, 197),
        bg_bottom=(170, 193, 166),
        border=(105, 130, 101),
        glow=(172, 215, 163),
        accent=(92, 130, 92),
        fold=(219, 234, 214, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_sky",
        "Pastel Sticky · Sky",
        bg_top=(203, 232, 252),
        bg_bottom=(170, 207, 236),
        border=(109, 154, 196),
        glow=(153, 223, 255),
        accent=(72, 149, 214),
        fold=(225, 244, 255, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_lilac",
        "Pastel Sticky · Lilac",
        bg_top=(226, 216, 250),
        bg_bottom=(199, 183, 233),
        border=(138, 120, 181),
        glow=(205, 186, 255),
        accent=(137, 111, 215),
        fold=(242, 236, 255, 220),
        dark_text=True,
    ),
    _sticky_theme(
        "sticky_paper_rosewood",
        "Pastel Sticky · Rosewood",
        bg_top=(122, 86, 104),
        bg_bottom=(92, 63, 78),
        border=(200, 160, 181),
        glow=(255, 191, 223),
        accent=(236, 147, 192),
        fold=(179, 135, 154, 220),
        dark_text=False,
    ),
    _sticky_theme(
        "sticky_paper_slate",
        "Pastel Sticky · Slate",
        bg_top=(98, 111, 129),
        bg_bottom=(70, 81, 96),
        border=(171, 188, 212),
        glow=(198, 225, 255),
        accent=(132, 170, 224),
        fold=(126, 141, 164, 220),
        dark_text=False,
    ),
    NoteTheme(
        theme_id="fireflies_night",
        label="Starlight Fireflies",
        header_title="",
        description="Relaxing starry-night note with firefly-like glow.",
        bg_top=(7, 16, 24),
        bg_bottom=(13, 24, 20),
        border=(88, 141, 116),
        glow=(154, 255, 184),
        accent=(255, 214, 112),
        divider=(34, 57, 49),
        text_head=(231, 248, 236),
        text_label=(150, 194, 161),
        text_value=(214, 241, 220),
        watermark=(103, 140, 118, 140),
        button_primary=(135, 214, 164),
        button_hover=(255, 226, 153),
        button_dismiss=(28, 44, 38),
        button_text=(14, 28, 20),
        dismiss_text=(196, 227, 204),
        progress_track=(14, 26, 23, 190),
        progress_fill=(171, 255, 188, 210),
        title_font_family="Candara",
        title_font_size=9.2,
        title_font_weight=QFont.DemiBold,
        label_font_family="Segoe UI",
        label_font_size=8.0,
        label_font_weight=QFont.Normal,
        value_font_family="Consolas",
        value_font_size=8.4,
        value_font_weight=QFont.Bold,
        button_font_family="Segoe UI",
        button_font_size=8.0,
        button_font_weight=QFont.Bold,
        brand_font_family="Consolas",
        brand_font_size=7.0,
        brand_font_weight=QFont.Normal,
        aurora_band=True,
        aurora_color=(157, 255, 180, 78),
        starfield=True,
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
    "blueprint_neon": "floating_text_night",
    "aurora_glass": "floating_text_light",
    "space_observatory": "fireflies_night",
    "canary_postit": "sticky_paper_sun",
    "ruled_paper": "sticky_paper_cream",
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
