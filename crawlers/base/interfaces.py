"""
Core interfaces for the distributed crawler system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CrawlerStatus(Enum):
    """Crawler instance status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class CrawlRequest:
    """Request object for crawling a URL."""
    url: str
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    crawl_delay: float = 1.0
    site_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CrawlResult:
    """Result object from crawling a URL."""
    url: str
    status_code: int
    content: str
    extracted_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time: float = 0.0
    error_message: Optional[str] = None
    site_id: Optional[str] = None


@dataclass
class SiteConfig:
    """Configuration for a crawling site."""
    domain: str
    name: str
    base_urls: List[str]
    allowed_domains: List[str]
    crawl_delay: float = 1.0
    concurrent_requests: int = 1
    user_agent: str = "OpenMedia-Crawler/1.0"
    respect_robots_txt: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    selectors: Dict[str, str] = field(default_factory=dict)  # CSS/XPath selectors
    rate_limit: int = 60  # requests per minute
    priority: int = 1
    enabled: bool = True
    site_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CrawlerInfo:
    """Information about a crawler instance."""
    crawler_id: str
    instance_type: str
    status: CrawlerStatus
    assigned_sites: List[str] = field(default_factory=list)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    host_info: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"


class ICrawler(ABC):
    """Base interface that all crawlers must implement."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize crawler with configuration."""
        pass
    
    @abstractmethod
    def crawl(self, request: CrawlRequest) -> CrawlResult:
        """Crawl a single URL and return results."""
        pass
    
    @abstractmethod
    def get_status(self) -> CrawlerStatus:
        """Get current crawler status."""
        pass
    
    @abstractmethod
    def pause(self) -> bool:
        """Pause crawler operations."""
        pass
    
    @abstractmethod
    def resume(self) -> bool:
        """Resume crawler operations."""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop crawler gracefully."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        pass


class ISiteManager(ABC):
    """Interface for managing site configurations."""
    
    @abstractmethod
    def register_site(self, config: SiteConfig) -> str:
        """Register a new site configuration."""
        pass
    
    @abstractmethod
    def update_site(self, site_id: str, config: SiteConfig) -> bool:
        """Update existing site configuration."""
        pass
    
    @abstractmethod
    def get_site_config(self, site_id: str) -> Optional[SiteConfig]:
        """Get site configuration by ID."""
        pass
    
    @abstractmethod
    def list_sites(self, enabled_only: bool = True) -> List[SiteConfig]:
        """List all registered sites."""
        pass
    
    @abstractmethod
    def disable_site(self, site_id: str) -> bool:
        """Disable a site temporarily."""
        pass
    
    @abstractmethod
    def enable_site(self, site_id: str) -> bool:
        """Enable a site."""
        pass
    
    @abstractmethod
    def delete_site(self, site_id: str) -> bool:
        """Delete a site configuration."""
        pass


class IURLFrontier(ABC):
    """Interface for URL frontier management."""
    
    @abstractmethod
    def add_url(self, url: str, priority: int = 1, metadata: Dict = None) -> bool:
        """Add URL to frontier."""
        pass
    
    @abstractmethod
    def add_urls(self, urls: List[str], priority: int = 1) -> int:
        """Add multiple URLs to frontier."""
        pass
    
    @abstractmethod
    def get_next_url(self, crawler_id: str) -> Optional[CrawlRequest]:
        """Get next URL for crawling."""
        pass
    
    @abstractmethod
    def mark_completed(self, url: str, success: bool) -> bool:
        """Mark URL as completed."""
        pass
    
    @abstractmethod
    def mark_failed(self, url: str, error: str) -> bool:
        """Mark URL as failed."""
        pass
    
    @abstractmethod
    def is_visited(self, url: str) -> bool:
        """Check if URL has been visited."""
        pass
    
    @abstractmethod
    def get_queue_size(self, priority: Optional[int] = None) -> int:
        """Get current queue size."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get frontier statistics."""
        pass


class ICrawlerRegistry(ABC):
    """Interface for crawler instance management."""
    
    @abstractmethod
    def register_crawler(self, crawler_info: CrawlerInfo) -> str:
        """Register a new crawler instance."""
        pass
    
    @abstractmethod
    def heartbeat(self, crawler_id: str, metrics: Dict[str, Any]) -> bool:
        """Send heartbeat with performance metrics."""
        pass
    
    @abstractmethod
    def assign_sites(self, crawler_id: str, site_ids: List[str]) -> bool:
        """Assign sites to crawler."""
        pass
    
    @abstractmethod
    def unassign_sites(self, crawler_id: str, site_ids: List[str]) -> bool:
        """Unassign sites from crawler."""
        pass
    
    @abstractmethod
    def get_active_crawlers(self) -> List[CrawlerInfo]:
        """Get list of active crawlers."""
        pass
    
    @abstractmethod
    def get_crawler_info(self, crawler_id: str) -> Optional[CrawlerInfo]:
        """Get information about specific crawler."""
        pass
    
    @abstractmethod
    def unregister_crawler(self, crawler_id: str) -> bool:
        """Unregister crawler instance."""
        pass
    
    @abstractmethod
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        pass 