"""
UI styling engine for Internet Speed Meter.

Provides Red & Black QSS stylesheets for the context menu and any dialog
components that need programmatic theming. Dead graph/hardware style
functions from the original NetSpeedTray have been removed.
"""

from PyQt6.QtGui import QColor
import winreg

from netspeedtray.constants import color as color_constants

# ── Red & Black palette (local references for speed) ─────────────────────────
_RED       = color_constants.RED_PRIMARY   # #E53935
_RED_BRIG  = color_constants.RED_BRIGHT    # #FF1744
_RED_DIM   = color_constants.RED_DARK      # #B71C1C
_RED_SUB   = color_constants.RED_SUBTLE    # #FF5252
_BLACK     = color_constants.BLACK         # #000000
_NEAR_BLK  = color_constants.NEAR_BLACK    # #0D0D0D
_SURF_DARK = color_constants.SURFACE_DARK  # #1A1A1A
_SURF_MID  = color_constants.SURFACE_MID   # #242424
_TEXT      = color_constants.OFF_WHITE     # #F5F5F5
_SUBTEXT   = color_constants.GREY_TEXT     # #9E9E9E
_BORDER    = "#3A0000"


# ─────────────────────────────────────────────────────────────────────────────
#  Windows registry helpers (kept — still used by WidgetThemeManager)
# ─────────────────────────────────────────────────────────────────────────────

def is_dark_mode() -> bool:
    """Always returns True for Internet Speed Meter — it runs a dark theme only."""
    return True


def get_accent_color() -> QColor:
    """
    Returns the Red primary color as the application accent.
    Windows accent color is intentionally ignored — the Red & Black theme
    uses its own fixed accent.
    """
    return QColor(_RED)


# ─────────────────────────────────────────────────────────────────────────────
#  Context menu  (used by TrayIconManager)
# ─────────────────────────────────────────────────────────────────────────────

def context_menu_style() -> str:
    """Red & Black QSS for the right-click context menu."""
    return f"""
        QMenu {{
            background-color: {_NEAR_BLK};
            color: {_TEXT};
            border: 1px solid {_BORDER};
            border-radius: 6px;
            padding: 4px 0;
            font-family: "Segoe UI", "Segoe UI Variable";
            font-size: 12px;
        }}
        QMenu::item {{
            padding: 7px 20px 7px 14px;
            background-color: transparent;
        }}
        QMenu::item:selected {{
            background-color: {_RED_DIM};
            color: {_TEXT};
        }}
        QMenu::item:pressed {{
            background-color: {_RED};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {_BORDER};
            margin: 4px 10px;
        }}
    """


# ─────────────────────────────────────────────────────────────────────────────
#  Dialog base style  (used by any modal that needs programmatic theming)
# ─────────────────────────────────────────────────────────────────────────────

def dialog_style() -> str:
    """Base Red & Black QSS for generic dialogs."""
    return f"""
        QDialog {{
            background-color: {_NEAR_BLK};
            color: {_TEXT};
            font-family: "Segoe UI", "Segoe UI Variable";
        }}
        QLabel {{
            color: {_TEXT};
            background-color: transparent;
            font-size: 13px;
        }}
        QGroupBox {{
            color: {_RED};
            font-size: 11px;
            font-weight: 700;
            border: 1px solid {_BORDER};
            border-radius: 6px;
            margin-top: 14px;
            padding-top: 8px;
            background-color: {_SURF_DARK};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 6px;
            background-color: {_SURF_DARK};
        }}
        QCheckBox, QRadioButton {{
            color: {_TEXT};
            font-size: 13px;
            spacing: 8px;
            background-color: transparent;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid #5A0000;
            border-radius: 3px;
            background-color: {_SURF_MID};
        }}
        QRadioButton::indicator {{ border-radius: 8px; }}
        QCheckBox::indicator:checked {{
            background-color: {_RED};
            border-color: {_RED};
        }}
        QRadioButton::indicator:checked {{
            background-color: {_TEXT};
            border: 4px solid {_RED};
            border-radius: 8px;
        }}
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {_RED_BRIG};
        }}
        QWidget:focus {{ outline: none; }}
    """


# ─────────────────────────────────────────────────────────────────────────────
#  Button styles
# ─────────────────────────────────────────────────────────────────────────────

def button_style(accent: bool = False) -> str:
    """Red & Black button style. Pass accent=True for the primary action button."""
    if accent:
        return f"""
            QPushButton {{
                background-color: {_RED};
                color: #FFFFFF;
                border: 1px solid {_RED_DIM};
                border-radius: 4px;
                padding: 5px 16px;
                font-size: 13px;
                font-weight: 600;
                min-height: 22px;
            }}
            QPushButton:hover {{ background-color: {_RED_BRIG}; }}
            QPushButton:pressed {{ background-color: {_RED_DIM}; }}
            QPushButton:disabled {{
                background-color: #3A0000;
                color: {_SUBTEXT};
                border-color: #2A0000;
            }}
        """
    return f"""
        QPushButton {{
            background-color: {_SURF_MID};
            color: {_TEXT};
            border: 1px solid {_BORDER};
            border-radius: 4px;
            padding: 5px 16px;
            font-size: 13px;
            min-height: 22px;
        }}
        QPushButton:hover {{
            background-color: {_RED_DIM};
            border-color: {_RED};
        }}
        QPushButton:pressed {{ background-color: {_RED}; }}
        QPushButton:disabled {{
            background-color: {_SURF_DARK};
            color: {_SUBTEXT};
            border-color: {_BORDER};
        }}
    """


def color_button_style(color_hex: str) -> str:
    """Style for color picker preview buttons."""
    if not (isinstance(color_hex, str) and color_hex.startswith("#") and len(color_hex) == 7):
        color_hex = _RED
    return (
        f"QPushButton {{ background-color: {color_hex}; border: 1px solid {_BORDER}; "
        f"min-width: 40px; max-width: 40px; min-height: 18px; max-height: 18px; "
        f"border-radius: 4px; }}"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Toggle / Slider  (kept for any settings page that uses Win11-style widgets)
# ─────────────────────────────────────────────────────────────────────────────

def toggle_style(total_track_width: int, total_track_height: int) -> str:
    """Red & Black toggle-switch style for QCheckBox acting as a track."""
    track_border_width = 1
    iw = max(0, total_track_width  - (2 * track_border_width))
    ih = max(0, total_track_height - (2 * track_border_width))
    return f"""
        QCheckBox {{
            color: {_TEXT};
            background-color: transparent;
            border: none;
            padding: 0; margin: 0; spacing: 0;
        }}
        QCheckBox::indicator {{
            width: {iw}px; height: {ih}px;
            background-color: #3A0000;
            border-radius: {total_track_height // 2}px;
            border: {track_border_width}px solid #5A0000;
        }}
        QCheckBox::indicator:checked {{
            background-color: {_RED};
            border: {track_border_width}px solid {_RED_DIM};
        }}
        QCheckBox::indicator:unchecked:hover {{ background-color: #4A0000; }}
        QCheckBox::indicator:checked:hover   {{ background-color: {_RED_BRIG}; }}
    """


def slider_style() -> str:
    """Red & Black slider style."""
    groove_h    = 4
    handle_size = 18
    margin      = (handle_size - groove_h) // 2
    total_h     = handle_size + 2
    return f"""
        QSlider {{
            min-height: {total_h}px;
            max-height: {total_h}px;
            background: transparent;
        }}
        QSlider::groove:horizontal {{
            background: #3A0000;
            height: {groove_h}px;
            border-radius: {groove_h // 2}px;
            margin: {margin}px 0;
        }}
        QSlider::sub-page:horizontal {{
            background: {_RED};
            height: {groove_h}px;
            border-radius: {groove_h // 2}px;
            margin: {margin}px 0;
        }}
        QSlider::add-page:horizontal {{
            background: #3A0000;
            height: {groove_h}px;
            border-radius: {groove_h // 2}px;
            margin: {margin}px 0;
        }}
        QSlider::handle:horizontal {{
            background: {_RED};
            border: none;
            width: {handle_size}px;
            height: {handle_size}px;
            margin: -{margin}px 0;
            border-radius: {handle_size // 2}px;
        }}
        QSlider::handle:horizontal:hover  {{ background: {_RED_BRIG}; }}
        QSlider::handle:horizontal:pressed {{ background: {_RED_DIM}; }}
    """


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar style  (kept for any future settings expansion)
# ─────────────────────────────────────────────────────────────────────────────

def sidebar_style() -> str:
    """Red & Black QListWidget sidebar style."""
    return f"""
        QListWidget {{
            background-color: {_NEAR_BLK};
            border: none;
            font-family: "Segoe UI", "Segoe UI Variable";
            font-size: 13px;
            padding: 8px 0;
            outline: none;
        }}
        QListWidget::item {{
            padding: 8px 12px;
            color: {_TEXT};
            border: none;
            border-radius: 4px;
            margin: 2px 6px;
        }}
        QListWidget::item:selected {{
            background-color: {_RED_DIM};
            color: {_TEXT};
        }}
        QListWidget::item:hover:!selected {{
            background-color: {_SURF_MID};
        }}
        QListWidget:focus, QListWidget::item:focus {{
            outline: none;
            border: none;
        }}
    """