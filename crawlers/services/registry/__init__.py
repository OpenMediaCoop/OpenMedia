"""
Crawler Registry Service - Manages crawler instances and their assignments.
"""

from .main import app
from .models import CrawlerRegistryService

__all__ = ['app', 'CrawlerRegistryService'] 