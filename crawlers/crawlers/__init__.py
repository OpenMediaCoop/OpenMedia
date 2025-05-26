"""
Crawler implementations package.
"""

from .base_crawler import BaseCrawler
from .news_crawler import NewsCrawler
from .generic_crawler import GenericCrawler

__all__ = ['BaseCrawler', 'NewsCrawler', 'GenericCrawler'] 