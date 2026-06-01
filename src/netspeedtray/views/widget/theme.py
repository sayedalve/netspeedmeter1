"""
Widget Theme Manager for Internet Speed Meter.

The app ships with a fixed Red & Black identity — color_is_automatic is always
False in the default config (set in Batch 1's constants/config.py), so the
auto-theme registry dance is bypassed entirely.  This module is retained for
structural compatibility; on_theme_changed() simply triggers a repaint.
"""

import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QColor

from netspeedtray import constants

if TYPE_CHECKING:
    from netspeedtray.views.speed_widget import NetSpeedMeterWidget

# Fixed Red & Black palette (mirrors constants/color.py Batch 1 values)
_RED_PRIMARY = "#E53935"


class WidgetThemeManager:
    """
    Manages theme synchronization for NetSpeedMeterWidget.

    Because Internet Speed Meter uses a fixed Red & Black design, the
    Windows Light/Dark mode auto-color logic has been removed.  If the
    user explicitly enables color_is_automatic in Settings (advanced use),
    the default_color in config is still respected as-is.
    """

    def __init__(self, widget: "NetSpeedMeterWidget"):
        self.widget = widget
        self.logger = logging.getLogger("InternetSpeedMeter.ThemeManager")

    def apply_theme_aware_defaults(self) -> None:
        """
        Ensures the widget uses the Red primary color on startup.

        If color_is_automatic is False (the default for Internet Speed Meter),
        this is a no-op — the color already set in the config is used directly.
        If somehow color_is_automatic is True, we still force red so the
        Windows Light/Dark mode never overrides our brand color.
        """
        try:
            config = self.widget.config
            is_automatic = config.get("color_is_automatic", False)

            if not is_automatic:
                # Explicit color — nothing to adjust
                self.logger.debug("color_is_automatic=False; keeping configured color.")
                return

            # Automatic mode: pin to Red regardless of Windows theme
            current_color = config.get("default_color", "")
            if current_color.upper() != _RED_PRIMARY.upper():
                self.logger.debug(
                    "color_is_automatic=True but color was %s; pinning to %s.",
                    current_color, _RED_PRIMARY,
                )
                updates = {
                    "default_color": _RED_PRIMARY,
                    "color_is_automatic": False,   # lock it so it won't drift again
                }
                config.update(updates)
                self.widget.update_config(updates)

        except Exception as e:
            self.logger.warning("apply_theme_aware_defaults failed: %s", e)

    def on_theme_changed(self) -> None:
        """
        Handles Windows theme-change events.

        Internet Speed Meter has a fixed Red & Black color identity, so we
        do not alter the widget color on theme changes — we just trigger a
        repaint to keep the display fresh.
        """
        self.logger.debug("Windows theme change detected — repainting (color unchanged).")
        self.widget.update()

    def update_color_for_live_theme(self) -> None:
        """
        Legacy method retained for call-site compatibility.

        The live-theme registry check is not needed for Internet Speed Meter's
        fixed color scheme.  This is intentionally a no-op.
        """
        pass