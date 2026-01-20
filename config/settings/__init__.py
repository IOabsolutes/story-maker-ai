"""
Dynamic settings module selection based on DJANGO_ENV environment variable.

Usage:
    - Development (default): DJANGO_ENV=development or unset
    - Production: DJANGO_ENV=production

Alternatively, set DJANGO_SETTINGS_MODULE directly:
    - DJANGO_SETTINGS_MODULE=config.settings.development
    - DJANGO_SETTINGS_MODULE=config.settings.production
"""

import os

environment = os.getenv("DJANGO_ENV", "development").lower()

if environment == "production":
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
