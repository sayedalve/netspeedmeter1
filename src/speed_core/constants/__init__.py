"""
Provides centralized, immutable constants for the speed_core application.

This package exposes singleton instances of constant groups, ensuring they
are validated on import and easily accessible from a single namespace.

Usage:
    from speed_core import constants

    # Access application metadata
    print(constants.app.VERSION)

    # Access a translated string
    print(constants.i18n.get_i18n().SETTINGS_WINDOW_TITLE)

    # Access a default configuration value
    if is_dark_mode == constants.config.defaults.DEFAULT_DARK_MODE:
        # ...

    # Access a timer interval in milliseconds
    timer.start(constants.timers.VISIBILITY_CHECK_INTERVAL_MS)
"""

from speed_core.constants.app import app
from speed_core.constants.color import color
from speed_core.constants.config import config
from speed_core.constants.data import data
from speed_core.constants.fonts import fonts
from speed_core.constants.i18n import strings, I18nStrings
from speed_core.constants.layout import layout
from speed_core.constants.logs import logs
from speed_core.constants.network import network
from speed_core.constants.styles import styles
from speed_core.constants.taskbar import taskbar, TaskbarEdge
from speed_core.constants.timeouts import timeouts
from speed_core.constants.timers import timers
from speed_core.constants.ui import ui

# No validation script is needed here; validation happens on instantiation
# of each singleton within its own module.

__all__ = [
    "app",
    "color",
    "config",
    "data",
    "fonts",
    "strings",
    "I18nStrings",
    "layout",
    "logs",
    "network",
    "styles",
    "taskbar",
    "TaskbarEdge",
    "timers",
    "ui",
]