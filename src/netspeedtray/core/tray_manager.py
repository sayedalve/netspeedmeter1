"""
Tray Icon Manager for Internet Speed Meter.

Handles icon loading, context-menu creation, and smart menu positioning.
Stripped to only the items actually present in the focused speed-meter app:
  Settings | ─── | Exit
"""

import os
import sys
import logging
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import QObject, QPoint, Qt, QRect
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMenu, QApplication, QWidget

from netspeedtray import constants
from netspeedtray.utils import styles as style_utils

if TYPE_CHECKING:
    from netspeedtray.views.widget import NetworkSpeedWidget
    from netspeedtray.constants.i18n import I18nStrings


# ── Red & Black context-menu QSS ─────────────────────────────────────────────
_MENU_QSS = """
QMenu {
    background-color: #0D0D0D;
    color: #E53935;
    border: 1px solid #B71C1C;
    border-radius: 4px;
    padding: 4px 0px;
    font-family: "Segoe UI";
    font-size: 9pt;
}

QMenu::item {
    background-color: transparent;
    color: #E53935;
    padding: 6px 20px 6px 14px;
    border-radius: 2px;
    margin: 1px 4px;
}

QMenu::item:selected {
    background-color: #1A0000;
    color: #FF5252;
    border-left: 2px solid #E53935;
}

QMenu::item:disabled {
    color: #5C1A1A;
}

QMenu::separator {
    height: 1px;
    background-color: #3D0000;
    margin: 3px 8px;
}
"""


class TrayIconManager(QObject):
    """Manages the application icon and context menu."""

    def __init__(self, parent_widget: "NetworkSpeedWidget", i18n: "I18nStrings"):
        super().__init__(parent_widget)
        self.widget = parent_widget
        self.i18n = i18n
        self.logger = logging.getLogger("InternetSpeedMeter.TrayIconManager")

        self.context_menu: Optional[QMenu] = None
        self.app_icon: Optional[QIcon] = None
        self.is_context_menu_visible: bool = False

    def initialize(self) -> None:
        """Loads the icon and initializes the context menu."""
        self._load_and_set_icon()
        self._init_context_menu()

    def _load_and_set_icon(self) -> None:
        """Loads the application icon and sets it on the parent widget."""
        try:
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                base_path = sys._MEIPASS
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
                base_path = project_root

            icon_filename = constants.app.ICON_FILENAME
            icon_path = os.path.normpath(os.path.join(base_path, "assets", icon_filename))

            if os.path.exists(icon_path):
                self.app_icon = QIcon(icon_path)
                self.widget.setWindowIcon(self.app_icon)
                self.logger.debug("Application icon loaded successfully.")
            else:
                self.logger.warning("Icon not found at '%s'. Using default.", icon_path)
        except Exception as e:
            self.logger.error("Error loading application icon: %s", e, exc_info=True)

    def _init_context_menu(self) -> None:
        """Build the minimal Red & Black context menu."""
        self.logger.debug("Initializing context menu...")
        try:
            self.context_menu = QMenu(self.widget)
            self.context_menu.setStyleSheet(_MENU_QSS)

            # Settings ─ the only primary action
            settings_action = self.context_menu.addAction(self.i18n.SETTINGS_MENU_ITEM)
            if hasattr(self.widget, "show_settings"):
                settings_action.triggered.connect(self.widget.show_settings)

            self.context_menu.addSeparator()

            # Exit
            exit_action = self.context_menu.addAction(self.i18n.EXIT_MENU_ITEM)
            app_instance = QApplication.instance()
            if app_instance:
                exit_action.triggered.connect(self.widget.fully_exit_application)
            else:
                exit_action.setEnabled(False)

            self.logger.debug("Context menu initialized.")
        except Exception as e:
            self.logger.error("Error initializing context menu: %s", e, exc_info=True)

    def show_context_menu(self) -> None:
        """Calculate position and show the context menu."""
        if not self.context_menu:
            return

        try:
            menu_pos = self._calculate_menu_position()

            self.is_context_menu_visible = True
            if hasattr(self.widget, "_is_context_menu_visible"):
                self.widget._is_context_menu_visible = True

            self.context_menu.exec(menu_pos)

            self.is_context_menu_visible = False
            if hasattr(self.widget, "_is_context_menu_visible"):
                self.widget._is_context_menu_visible = False

            # Trigger visibility refresh after close
            if hasattr(self.widget, "_execute_refresh"):
                self.widget._execute_refresh()

        except Exception as e:
            self.logger.error("Error showing context menu: %s", e, exc_info=True)

    def _calculate_menu_position(self) -> QPoint:
        """Calculate the optimal global position for the context menu."""
        try:
            renderer = getattr(self.widget, "renderer", None)
            text_rect_local = renderer.get_last_text_rect() if renderer else QRect()

            if not text_rect_local.isValid() or text_rect_local.isEmpty():
                ref_global_pos   = self.widget.mapToGlobal(self.widget.rect().center())
                ref_top_global_y = self.widget.mapToGlobal(self.widget.rect().topLeft()).y()
            else:
                ref_global_pos   = self.widget.mapToGlobal(text_rect_local.center())
                ref_top_global_y = self.widget.mapToGlobal(text_rect_local.topLeft()).y()

            menu_size   = self.context_menu.sizeHint()
            menu_width  = menu_size.width() if menu_size.width() > 0 else constants.ui.general.ESTIMATED_MENU_WIDTH
            menu_height = menu_size.height()

            target_x   = ref_global_pos.x() - menu_width // 2
            target_y   = ref_top_global_y - menu_height - constants.ui.general.MENU_PADDING_ABOVE
            target_pos = QPoint(int(round(target_x)), int(round(target_y)))

            screen = self.widget.screen() or QApplication.primaryScreen()
            if screen:
                screen_rect  = screen.availableGeometry()
                validated_x  = max(screen_rect.left(), min(target_pos.x(), screen_rect.right() - menu_width + 1))
                validated_y  = max(screen_rect.top(),  min(target_pos.y(), screen_rect.bottom() - menu_height + 1))
                target_pos.setX(validated_x)
                target_pos.setY(validated_y)

            return target_pos
        except Exception as e:
            self.logger.error("Error calculating menu position: %s", e, exc_info=True)
            return self.widget.mapToGlobal(self.widget.rect().center())