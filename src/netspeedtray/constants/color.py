"""
Defines the Red & Black color palette for Internet Speed Meter.

Design tokens:
  Primary red   #E53935  — default text / speed values
  Bright red    #FF1744  — high-speed accent / graph highlight
  Dark red      #B71C1C  — low-speed warning / muted accent
  Pure black    #000000  — widget background
  Off-white     #F5F5F5  — light-mode fallback text (kept for WidgetThemeManager)
"""
from typing import Final


class ColorConstants:
    """Defines the static Red & Black palette."""

    # ── Reds ──────────────────────────────────────────────────────────────────
    RED_PRIMARY: Final[str] = "#E53935"   # Default speed text
    RED_BRIGHT:  Final[str] = "#FF1744"   # High-speed / graph line accent
    RED_DARK:    Final[str] = "#B71C1C"   # Low-speed / muted
    RED_SUBTLE:  Final[str] = "#FF5252"   # Mid-tone for hover / borders

    # ── Backgrounds ───────────────────────────────────────────────────────────
    BLACK:        Final[str] = "#000000"
    NEAR_BLACK:   Final[str] = "#0D0D0D"  # Dialog / panel base
    SURFACE_DARK: Final[str] = "#1A1A1A"  # Card / section surface
    SURFACE_MID:  Final[str] = "#242424"  # Slightly lighter card

    # ── Text ──────────────────────────────────────────────────────────────────
    WHITE:      Final[str] = "#FFFFFF"
    OFF_WHITE:  Final[str] = "#F5F5F5"   # Light-mode fallback text
    GREY_TEXT:  Final[str] = "#9E9E9E"   # Subtle / disabled labels
    GREY_DIM:   Final[str] = "#616161"   # Dimmer hints

    # ── Legacy aliases (kept so other modules that import these don't break) ──
    GREEN:  Final[str] = RED_BRIGHT   # high-speed color now maps to bright red
    ORANGE: Final[str] = RED_DARK     # low-speed color now maps to dark red
    RED:    Final[str] = RED_PRIMARY
    BLUE:   Final[str] = RED_SUBTLE   # no blue in this theme; map to subtle red

    # ── Graph line colors ─────────────────────────────────────────────────────
    UPLOAD_LINE_COLOR:   Final[str] = RED_BRIGHT    # Upload graph line
    DOWNLOAD_LINE_COLOR: Final[str] = RED_PRIMARY   # Download graph line

    # ── Progress / App-usage ─────────────────────────────────────────────────
    APP_USAGE_PROGRESS_CHUNK:    Final[str] = RED_PRIMARY
    APP_USAGE_PROGRESS_BG_DARK:  Final[str] = SURFACE_MID
    APP_USAGE_PROGRESS_BG_LIGHT: Final[str] = "#2A2A2A"  # stays dark; no light mode in this app

    # ── UI Text ───────────────────────────────────────────────────────────────
    SUBTLE_TEXT_COLOR_LIGHT: Final[str] = GREY_TEXT
    SUBTLE_TEXT_COLOR_DARK:  Final[str] = GREY_DIM

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for attr_name in dir(self):
            if not attr_name.startswith("_") and attr_name.isupper():
                value = getattr(self, attr_name)
                if not (isinstance(value, str) and value.startswith("#") and len(value) == 7):
                    raise ValueError(
                        f"Color '{attr_name}' must be a 7-character hex string, got: {value!r}"
                    )


# Singleton instance for easy access
color = ColorConstants()