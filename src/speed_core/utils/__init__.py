"""
Utilities submodule for speed_core.

Provides helper functions and configuration management.
"""

from speed_core.core.database import DatabaseWorker
from speed_core.utils.config import ConfigManager
from speed_core.utils.helpers import get_app_data_path
from speed_core.utils.styles import is_dark_mode

__all__ = ["ConfigManager", "DatabaseWorker", "get_app_data_path", "is_dark_mode"]
