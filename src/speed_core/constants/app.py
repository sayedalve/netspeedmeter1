"""
Constants for application metadata and lifecycle management.
"""

from typing import Final
import speed_core


class AppConstants:
    """Defines application metadata and the single-instance mutex name."""
    APP_NAME: Final[str] = "Internet Speed Meter"
    VERSION: Final[str] = speed_core.__version__
    MUTEX_NAME: Final[str] = "Global\\InternetSpeedMeter_SingleInstanceMutex"
    ICON_FILENAME: Final[str] = "speed_core.ico"
    GITHUB_OWNER: Final[str] = "sayedalve"
    GITHUB_REPO: Final[str] = "netspeedmeter1"

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate the constants to ensure they meet constraints."""
        if not self.APP_NAME:
            raise ValueError("APP_NAME must not be empty")
        if not self.VERSION:
            raise ValueError("VERSION must not be empty")
        if not self.MUTEX_NAME:
            raise ValueError("MUTEX_NAME must not be empty")
        if not self.ICON_FILENAME:
            raise ValueError("ICON_FILENAME must not be empty")


# Singleton instance for easy access
app = AppConstants()