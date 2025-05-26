"""
Generic web crawler implementation.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_crawler import BaseCrawler
from crawlers.base.content_extractor import ContentExtractor
from crawlers.base.models import WebPage
from crawlers.base.interfaces import CrawlResult

logger = logging.getLogger(__name__)


class GenericCrawler(BaseCrawler):
    """General purpose web crawler for any website."""
    
    def __init__(self, crawler_id: str, config: Dict[str, Any]):
        super().__init__(crawler_id, config)
        self.content_extractor = ContentExtractor()
        
    async def extract_content(self, url: str, html: str, site_config: Dict[str, Any]) -> Optional[WebPage]:
        """Extract general content from HTML."""
        try:
            # Use site-specific selectors if available
            selectors = site_config.get('content_selectors', {})
            
            webpage = self.content_extractor.extract_webpage(
                html=html,
                url=url,
                title_selector=selectors.get('title'),
                content_selector=selectors.get('content'),
                meta_selector=selectors.get('meta')
            )
            
            if webpage and self._is_valid_content(webpage):
                return webpage
                
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            
        return None
    
    def _is_valid_content(self, webpage: WebPage) -> bool:
        """Validate if extracted content is meaningful."""
        # Minimum content length
        if not webpage.content or len(webpage.content.strip()) < 50:
            return False
            
        # Must have a title
        if not webpage.title or len(webpage.title.strip()) < 5:
            return False
            
        # Check for error pages
        error_indicators = [
            '404', 'not found', 'page not found', 'error',
            'access denied', 'forbidden', 'unauthorized'
        ]
        
        title_lower = webpage.title.lower()
        content_lower = webpage.content.lower()[:200]  # Check first 200 chars
        
        if any(indicator in title_lower or indicator in content_lower 
               for indicator in error_indicators):
            return False
            
        return True
    
    async def process_crawl_result(self, result: CrawlResult) -> None:
        """Process crawled content and send to appropriate processors."""
        try:
            # Send to general content processing pipeline
            await self.send_to_kafka('content.generic', {
                'url': result.url,
                'webpage': result.content.dict() if result.content else None,
                'site_id': result.site_id,
                'crawled_at': result.crawled_at.isoformat(),
                'crawler_id': self.crawler_id
            })
            
            # Update crawl statistics
            await self.update_crawl_stats(result)
            
        except Exception as e:
            logger.error(f"Failed to process crawl result for {result.url}: {e}")


async def main():
    """Main entry point for generic crawler."""
    import os
    from crawlers.services.registry.client import RegistryClient
    
    crawler_id = os.getenv('CRAWLER_ID', 'generic-crawler-1')
    registry_url = os.getenv('REGISTRY_URL', 'http://localhost:8080')
    
    # Get configuration from registry
    registry_client = RegistryClient(registry_url)
    config = await registry_client.get_crawler_config(crawler_id)
    
    # Create and start crawler
    crawler = GenericCrawler(crawler_id, config)
    
    try:
        await crawler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down generic crawler...")
        await crawler.stop()


if __name__ == "__main__":
    asyncio.run(main()) 