"""
Base interfaces and utilities for the distributed crawler system.
"""

from .interfaces import (
    ICrawler,
    ISiteManager,
    IURLFrontier,
    ICrawlerRegistry,
    CrawlerStatus,
    CrawlRequest,
    CrawlResult,
    SiteConfig,
    CrawlerInfo
)

from .utils import (
    setup_logging,
    get_config,
    validate_url,
    extract_domain,
    normalize_url
)

from .models import (
    Article,
    WebPage
)

from .content_extractor import ContentExtractor

__all__ = [
    'ICrawler',
    'ISiteManager', 
    'IURLFrontier',
    'ICrawlerRegistry',
    'CrawlerStatus',
    'CrawlRequest',
    'CrawlResult',
    'SiteConfig',
    'CrawlerInfo',
    'setup_logging',
    'get_config',
    'validate_url',
    'extract_domain',
    'normalize_url',
    'Article',
    'WebPage',
    'ContentExtractor'
] 