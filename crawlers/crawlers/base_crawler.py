"""
Base crawler implementation using Scrapy framework.
"""

import asyncio
import time
import uuid
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import structlog
from kafka import KafkaProducer

import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.http import Request
from twisted.internet import reactor, defer

from base.interfaces import ICrawler, CrawlRequest, CrawlResult, CrawlerStatus, SiteConfig
from base.utils import (
    setup_logging, get_config, get_host_info, normalize_url, 
    extract_domain, is_allowed_domain, calculate_crawl_delay
)


logger = structlog.get_logger(__name__)


class OpenMediaSpider(scrapy.Spider):
    """Scrapy spider for OpenMedia crawler."""
    
    name = 'openmedia_spider'
    
    def __init__(self, crawler_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawler_instance = crawler_instance
        self.site_configs = {}
        self.kafka_producer = None
        self._init_kafka()
    
    def _init_kafka(self):
        """Initialize Kafka producer."""
        try:
            kafka_config = self.crawler_instance.config.get('kafka', {})
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=kafka_config.get('bootstrap_servers', 'kafka:9092'),
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info("Kafka producer initialized")
        except Exception as e:
            logger.error("Failed to initialize Kafka producer", error=str(e))
    
    def start_requests(self):
        """Generate initial requests from crawler instance."""
        # This will be called by the crawler instance
        return []
    
    def parse(self, response):
        """Parse response and extract content."""
        try:
            url = response.url
            site_id = response.meta.get('site_id')
            site_config = self.site_configs.get(site_id)
            
            if not site_config:
                logger.warning("No site config found", url=url, site_id=site_id)
                return
            
            # Extract content using configured selectors
            content_data = self._extract_content(response, site_config)
            
            # Send to Kafka
            if self.kafka_producer and content_data:
                self._send_to_kafka(content_data)
            
            # Extract and follow links
            extracted_urls = self._extract_links(response, site_config)
            
            # Yield follow-up requests
            for link_url in extracted_urls:
                if self._should_follow_link(link_url, site_config):
                    yield Request(
                        url=link_url,
                        callback=self.parse,
                        meta={'site_id': site_id},
                        dont_filter=False
                    )
            
            # Report success to crawler instance
            self.crawler_instance._report_success(url, len(extracted_urls))
            
        except Exception as e:
            logger.error("Failed to parse response", url=response.url, error=str(e))
            self.crawler_instance._report_failure(response.url, str(e))
    
    def _extract_content(self, response, site_config: SiteConfig) -> Dict[str, Any]:
        """Extract content using site-specific selectors."""
        try:
            selectors = site_config.selectors
            
            content_data = {
                'url': response.url,
                'site_id': site_config.site_id,
                'site_name': site_config.name,
                'domain': site_config.domain,
                'title': self._extract_with_selector(response, selectors.get('title')),
                'content': self._extract_with_selector(response, selectors.get('content')),
                'author': self._extract_with_selector(response, selectors.get('author')),
                'publish_date': self._extract_with_selector(response, selectors.get('date')),
                'category': self._extract_with_selector(response, selectors.get('category')),
                'timestamp': datetime.utcnow().isoformat(),
                'crawler_id': self.crawler_instance.crawler_id,
                'status_code': response.status,
                'content_length': len(response.text),
                'language': response.meta.get('language', 'unknown')
            }
            
            # Clean and validate content
            if content_data['title'] and content_data['content']:
                return content_data
            else:
                logger.debug("Insufficient content extracted", url=response.url)
                return None
                
        except Exception as e:
            logger.error("Failed to extract content", url=response.url, error=str(e))
            return None
    
    def _extract_with_selector(self, response, selector):
        """Extract text using CSS or XPath selector."""
        if not selector:
            return None
        
        try:
            if selector.startswith('//'):
                # XPath selector
                result = response.xpath(selector).getall()
            else:
                # CSS selector
                result = response.css(selector).getall()
            
            if result:
                # Join multiple results and clean
                text = ' '.join(result).strip()
                return text if text else None
            
            return None
            
        except Exception as e:
            logger.warning("Failed to extract with selector", selector=selector, error=str(e))
            return None
    
    def _extract_links(self, response, site_config: SiteConfig) -> List[str]:
        """Extract links from the page."""
        try:
            links = []
            
            # Extract all links
            for link in response.css('a::attr(href)').getall():
                absolute_url = response.urljoin(link)
                normalized_url = normalize_url(absolute_url)
                
                if normalized_url and normalized_url not in links:
                    links.append(normalized_url)
            
            return links
            
        except Exception as e:
            logger.error("Failed to extract links", url=response.url, error=str(e))
            return []
    
    def _should_follow_link(self, url: str, site_config: SiteConfig) -> bool:
        """Check if URL should be followed."""
        try:
            # Check if domain is allowed
            if not is_allowed_domain(url, site_config.allowed_domains):
                return False
            
            # Additional filtering logic can be added here
            # e.g., check for specific URL patterns, file extensions, etc.
            
            return True
            
        except Exception as e:
            logger.warning("Error checking if should follow link", url=url, error=str(e))
            return False
    
    def _send_to_kafka(self, content_data: Dict[str, Any]):
        """Send extracted content to Kafka."""
        try:
            topic = 'news_content'
            key = content_data.get('site_id', 'unknown')
            
            self.kafka_producer.send(topic, value=content_data, key=key)
            logger.debug("Content sent to Kafka", url=content_data['url'], topic=topic)
            
        except Exception as e:
            logger.error("Failed to send to Kafka", error=str(e))


class BaseCrawler(ICrawler):
    """Base crawler implementation using Scrapy."""
    
    def __init__(self, crawler_id: str = None, crawler_type: str = "base"):
        self.crawler_id = crawler_id or str(uuid.uuid4())
        self.crawler_type = crawler_type
        self.status = CrawlerStatus.IDLE
        self.config = get_config()
        setup_logging(service_name=f"crawler-{crawler_type}")
        self.logger = structlog.get_logger(f"crawler-{crawler_type}")
        
        # Service URLs
        self.registry_url = self.config.get('registry_url', 'http://crawler-registry:8080')
        self.site_manager_url = self.config.get('site_manager_url', 'http://site-manager:8081')
        self.scheduler_url = self.config.get('scheduler_url', 'http://url-scheduler:8082')
        
        # Scrapy components
        self.runner = None
        self.spider = None
        self.site_configs = {}
        
        # Metrics
        self.metrics = {
            'requests_made': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'urls_extracted': 0,
            'start_time': None,
            'last_request_time': None
        }
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize crawler with configuration."""
        try:
            self.config.update(config)
            
            # Setup Scrapy settings
            settings = get_project_settings()
            settings.setdict({
                'ROBOTSTXT_OBEY': True,
                'DOWNLOAD_DELAY': 1.0,
                'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
                'CONCURRENT_REQUESTS': 1,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
                'USER_AGENT': 'OpenMedia-Crawler/1.0',
                'TELNETCONSOLE_ENABLED': False,
                'LOG_LEVEL': 'INFO'
            })
            
            # Initialize Scrapy runner
            self.runner = CrawlerRunner(settings)
            
            # Register with crawler registry
            self._register_with_registry()
            
            # Load site configurations
            self._load_site_configs()
            
            self.status = CrawlerStatus.IDLE
            self.logger.info("Crawler initialized", crawler_id=self.crawler_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize crawler", error=str(e))
            self.status = CrawlerStatus.ERROR
            return False
    
    def crawl(self, request: CrawlRequest) -> CrawlResult:
        """Crawl a single URL and return results."""
        try:
            start_time = time.time()
            self.metrics['requests_made'] += 1
            self.metrics['last_request_time'] = datetime.utcnow().isoformat()
            
            # This is a simplified implementation
            # In practice, you'd integrate this with the Scrapy spider
            
            result = CrawlResult(
                url=request.url,
                status_code=200,  # Placeholder
                content="",  # Would be extracted by spider
                extracted_urls=[],  # Would be extracted by spider
                metadata=request.metadata,
                timestamp=datetime.utcnow(),
                processing_time=time.time() - start_time,
                site_id=request.site_id
            )
            
            self.metrics['requests_successful'] += 1
            return result
            
        except Exception as e:
            self.metrics['requests_failed'] += 1
            self.logger.error("Failed to crawl URL", url=request.url, error=str(e))
            
            return CrawlResult(
                url=request.url,
                status_code=500,
                content="",
                extracted_urls=[],
                metadata=request.metadata,
                timestamp=datetime.utcnow(),
                processing_time=time.time() - start_time if 'start_time' in locals() else 0,
                error_message=str(e),
                site_id=request.site_id
            )
    
    def get_status(self) -> CrawlerStatus:
        """Get current crawler status."""
        return self.status
    
    def pause(self) -> bool:
        """Pause crawler operations."""
        try:
            if self.status == CrawlerStatus.RUNNING:
                self.status = CrawlerStatus.PAUSED
                self.logger.info("Crawler paused")
                return True
            return False
        except Exception as e:
            self.logger.error("Failed to pause crawler", error=str(e))
            return False
    
    def resume(self) -> bool:
        """Resume crawler operations."""
        try:
            if self.status == CrawlerStatus.PAUSED:
                self.status = CrawlerStatus.RUNNING
                self.logger.info("Crawler resumed")
                return True
            return False
        except Exception as e:
            self.logger.error("Failed to resume crawler", error=str(e))
            return False
    
    def stop(self) -> bool:
        """Stop crawler gracefully."""
        try:
            self.status = CrawlerStatus.STOPPED
            
            # Stop Scrapy runner if running
            if self.runner and hasattr(self.runner, 'stop'):
                self.runner.stop()
            
            # Unregister from registry
            self._unregister_from_registry()
            
            self.logger.info("Crawler stopped")
            return True
            
        except Exception as e:
            self.logger.error("Failed to stop crawler", error=str(e))
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self.metrics,
            'status': self.status.value,
            'crawler_id': self.crawler_id,
            'crawler_type': self.crawler_type,
            'assigned_sites': list(self.site_configs.keys())
        }
    
    def run(self):
        """Main crawler loop."""
        try:
            self.status = CrawlerStatus.RUNNING
            self.metrics['start_time'] = datetime.utcnow().isoformat()
            
            self.logger.info("Starting crawler main loop")
            
            while self.status == CrawlerStatus.RUNNING:
                try:
                    # Get next URL from scheduler
                    request = self._get_next_url()
                    
                    if request:
                        # Process the request using Scrapy
                        self._process_request_with_scrapy(request)
                    else:
                        # No URLs available, wait a bit
                        time.sleep(5)
                    
                    # Send heartbeat
                    self._send_heartbeat()
                    
                except Exception as e:
                    self.logger.error("Error in crawler loop", error=str(e))
                    time.sleep(10)  # Wait before retrying
            
        except Exception as e:
            self.logger.error("Fatal error in crawler", error=str(e))
            self.status = CrawlerStatus.ERROR
    
    def _register_with_registry(self):
        """Register crawler with the registry service."""
        try:
            registration_data = {
                'instance_type': self.crawler_type,
                'crawler_id': self.crawler_id,
                'host_info': get_host_info(),
                'version': '1.0.0'
            }
            
            response = requests.post(
                f"{self.registry_url}/crawlers/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Registered with crawler registry")
            else:
                self.logger.error("Failed to register with registry", status_code=response.status_code)
                
        except Exception as e:
            self.logger.error("Failed to register with registry", error=str(e))
    
    def _unregister_from_registry(self):
        """Unregister crawler from the registry service."""
        try:
            response = requests.delete(
                f"{self.registry_url}/crawlers/{self.crawler_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Unregistered from crawler registry")
            else:
                self.logger.warning("Failed to unregister from registry", status_code=response.status_code)
                
        except Exception as e:
            self.logger.warning("Failed to unregister from registry", error=str(e))
    
    def _load_site_configs(self):
        """Load site configurations from site manager."""
        try:
            response = requests.get(f"{self.site_manager_url}/sites", timeout=10)
            
            if response.status_code == 200:
                sites_data = response.json()
                for site_data in sites_data:
                    site_config = SiteConfig(**site_data)
                    self.site_configs[site_config.site_id] = site_config
                
                self.logger.info("Loaded site configurations", count=len(self.site_configs))
            else:
                self.logger.error("Failed to load site configs", status_code=response.status_code)
                
        except Exception as e:
            self.logger.error("Failed to load site configs", error=str(e))
    
    def _get_next_url(self) -> Optional[CrawlRequest]:
        """Get next URL from scheduler."""
        try:
            response = requests.get(
                f"{self.scheduler_url}/urls/next/{self.crawler_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return CrawlRequest(**data)
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to get next URL", error=str(e))
            return None
    
    def _process_request_with_scrapy(self, request: CrawlRequest):
        """Process crawl request using Scrapy."""
        try:
            # Get site configuration
            site_config = self.site_configs.get(request.site_id)
            if not site_config:
                self._report_failure(request.url, "No site configuration found")
                return
            
            # Create and configure spider
            spider = OpenMediaSpider(self)
            spider.site_configs[request.site_id] = site_config
            
            # Create Scrapy request
            scrapy_request = Request(
                url=request.url,
                callback=spider.parse,
                meta={'site_id': request.site_id},
                dont_filter=False
            )
            
            # Start crawling (this is simplified - in practice you'd use the runner)
            # For now, we'll just simulate the process
            self._simulate_crawl(request, site_config)
            
        except Exception as e:
            self.logger.error("Failed to process request with Scrapy", url=request.url, error=str(e))
            self._report_failure(request.url, str(e))
    
    def _simulate_crawl(self, request: CrawlRequest, site_config: SiteConfig):
        """Simulate crawling process (placeholder for actual Scrapy integration)."""
        try:
            # Apply crawl delay
            delay = calculate_crawl_delay(site_config.__dict__)
            time.sleep(delay)
            
            # Simulate successful crawl
            self._report_success(request.url, 0)  # 0 extracted URLs for simulation
            
        except Exception as e:
            self._report_failure(request.url, str(e))
    
    def _report_success(self, url: str, extracted_urls_count: int):
        """Report successful crawl to scheduler."""
        try:
            self.metrics['urls_extracted'] += extracted_urls_count
            
            response = requests.post(
                f"{self.scheduler_url}/urls/complete",
                json={'url': url, 'success': True},
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.warning("Failed to report success", url=url, status_code=response.status_code)
                
        except Exception as e:
            self.logger.error("Failed to report success", url=url, error=str(e))
    
    def _report_failure(self, url: str, error_message: str):
        """Report failed crawl to scheduler."""
        try:
            response = requests.post(
                f"{self.scheduler_url}/urls/complete",
                json={'url': url, 'success': False, 'error_message': error_message},
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.warning("Failed to report failure", url=url, status_code=response.status_code)
                
        except Exception as e:
            self.logger.error("Failed to report failure", url=url, error=str(e))
    
    def _send_heartbeat(self):
        """Send heartbeat to registry."""
        try:
            metrics = self.get_metrics()
            
            response = requests.post(
                f"{self.registry_url}/crawlers/{self.crawler_id}/heartbeat",
                json={'metrics': metrics},
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.warning("Failed to send heartbeat", status_code=response.status_code)
                
        except Exception as e:
            self.logger.warning("Failed to send heartbeat", error=str(e)) 