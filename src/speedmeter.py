"""
Internet Speed Meter — dedicated internet speed meter entry point.

All hardware monitoring (CPU / GPU / RAM / temperature / power / app-activity)
has been removed. Only network upload/download speeds remain.
"""

try:
    import matplotlib
    matplotlib.use("QtAgg")
    matplotlib.interactive(False)
except ImportError:
    pass

import warnings
warnings.filterwarnings("ignore", "Tight layout not applied")
warnings.filterwarnings("ignore", "constrained_layout not applied")

import logging
import os
import signal
import sys
from typing import Optional

import win32api
import win32con
import win32event
import win32gui
import winerror
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from netspeedtray import constants
from netspeedtray.utils.config import ConfigManager, ConfigError
from netspeedtray.utils.taskbar_utils import get_taskbar_height
from netspeedtray.views.speed_widget import NetSpeedMeterWidget


# ─────────────────────────────────────────────────────────────────────────────
#  Single-instance guard
# ─────────────────────────────────────────────────────────────────────────────

class SingleInstanceChecker:
    """Prevents multiple instances using a system-wide mutex."""

    def __init__(self):
        self.mutex = None
        self.logger = logging.getLogger("InternetSpeedMeter.SingleInstance")
        try:
            self.mutex = win32event.CreateMutex(None, False, constants.app.MUTEX_NAME)
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                self.logger.error("Another instance is already running.")
                raise RuntimeError("Application is already running.")
        except win32api.error as e:
            self.logger.error("Failed to create mutex: %s", e)
            raise RuntimeError(f"Failed to create mutex: {e}") from e

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.mutex:
            try:
                win32api.CloseHandle(self.mutex)
            except win32api.error as e:
                logging.getLogger("InternetSpeedMeter.SingleInstance").error(
                    "Failed to release mutex: %s", e
                )


# ─────────────────────────────────────────────────────────────────────────────
#  Working-directory normalisation
# ─────────────────────────────────────────────────────────────────────────────

def _set_working_directory() -> None:
    try:
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
        else:
            script_path = os.path.abspath(sys.argv[0])
            src_dir     = os.path.dirname(script_path)
            app_dir     = os.path.dirname(src_dir)
        os.chdir(app_dir)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    _set_working_directory()
    ConfigManager.setup_logging()
    logger = logging.getLogger("InternetSpeedMeter.Main")

    def _excepthook(exc_type, exc_value, exc_tb):
        logger.critical("Unhandled exception:", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _excepthook

    app = QApplication(sys.argv)

    # ── Shutdown broadcast (from installer) ──────────────────────────────
    if "--shutdown" in sys.argv:
        logger.info("Shutdown command received — broadcasting WM_USER_SHUTDOWN.")
        try:
            msg = win32gui.RegisterWindowMessageW("InternetSpeedMeter_WM_SHUTDOWN")
            win32gui.PostMessage(win32con.HWND_BROADCAST, msg, 0, 0)
            return 0
        except Exception as e:
            logger.error("Shutdown broadcast error: %s", e, exc_info=True)
            return 1

    # ── Normal startup ───────────────────────────────────────────────────
    try:
        with SingleInstanceChecker():
            config_manager = ConfigManager()
            config         = config_manager.load()

            i18n = constants.i18n.get_i18n(config.get("language"))

            taskbar_height = get_taskbar_height()
            widget = NetSpeedMeterWidget(
                taskbar_height=taskbar_height,
                config=config,
                i18n=i18n,
            )

            # App icon
            try:
                from netspeedtray.utils.helpers import get_app_asset_path
                from PyQt6.QtGui import QIcon
                icon_path = get_app_asset_path(constants.app.ICON_FILENAME)
                if icon_path.exists():
                    app.setWindowIcon(QIcon(str(icon_path)))
            except Exception:
                pass

            app.setQuitOnLastWindowClosed(False)
            app.aboutToQuit.connect(widget.cleanup)

            signal.signal(signal.SIGINT,  lambda s, f: QApplication.instance().quit())
            signal.signal(signal.SIGTERM, lambda s, f: QApplication.instance().quit())

            QTimer.singleShot(500, widget.show)
            return app.exec()

    except Exception as e:
        logger.critical("Critical startup error: %s", e, exc_info=True)
        QMessageBox.critical(
            None,
            "Internet Speed Meter — Error",
            f"A critical error occurred and the application must close:\n\n{e}",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())