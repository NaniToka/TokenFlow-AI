"""
Configuration re-export for backward compatibility.
Imports settings from modern app.core.config.
"""

from app.core.config import Settings, settings, get_settings

__all__ = ["Settings", "settings", "get_settings"]
