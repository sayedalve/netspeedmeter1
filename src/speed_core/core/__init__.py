"""
Core submodule for speed_core.

Contains the controller and potentially other core logic components.
Exports the main classes for use by other parts of the application.
"""

# Import using the actual class name defined in controller.py
from speed_core.core.controller import StatsController

# Export the correct class names
__all__ = [
    "StatsController",
]