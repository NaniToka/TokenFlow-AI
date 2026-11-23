"""
Configuration re-export for backward compatibility.
Imports settings from modern app.core.config.
"""

from app.core.config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
