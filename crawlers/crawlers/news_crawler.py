"""
News-specific crawler implementation.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_crawler import BaseCrawler
from base.content_extractor import ContentExtractor
from base.models import Article
from base.interfaces import CrawlResult

logger = logging.getLogger(__name__)


class NewsCrawler(BaseCrawler):
    """Specialized crawler for news websites."""
    
    def __init__(self, crawler_id: str, config: Dict[str, Any]):
        super().__init__(crawler_id, config)
        self.content_extractor = ContentExtractor()
        
    async def extract_content(self, url: str, html: str, site_config: Dict[str, Any]) -> Optional[Article]:
        """Extract article content from HTML."""
        try:
            # Use site-specific selectors if available
            selectors = site_config.get('content_selectors', {})
            
            article = self.content_extractor.extract_article(
                html=html,
                url=url,
                title_selector=selectors.get('title'),
                content_selector=selectors.get('content'),
                author_selector=selectors.get('author'),
                date_selector=selectors.get('date'),
                summary_selector=selectors.get('summary')
            )
            
            if article and self._is_valid_article(article):
                return article
                
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            
        return None
    
    def _is_valid_article(self, article: Article) -> bool:
        """Validate if extracted content is a valid news article."""
        # Minimum content length
        if not article.content or len(article.content.strip()) < 100:
            return False
            
        # Must have a title
        if not article.title or len(article.title.strip()) < 10:
            return False
            
        # Check for common non-article indicators
        non_article_indicators = [
            'privacy policy', 'terms of service', 'cookie policy',
            'about us', 'contact us', 'subscribe', 'newsletter'
        ]
        
        title_lower = article.title.lower()
        if any(indicator in title_lower for indicator in non_article_indicators):
            return False
            
        return True
    
    async def process_crawl_result(self, result: CrawlResult) -> None:
        """Process crawled content and send to appropriate processors."""
        try:
            # Send to content processing pipeline
            await self.send_to_kafka('content.extracted', {
                'url': result.url,
                'article': result.content.dict() if result.content else None,
                'site_id': result.site_id,
                'crawled_at': result.crawled_at.isoformat(),
                'crawler_id': self.crawler_id
            })
            
            # Update crawl statistics
            await self.update_crawl_stats(result)
            
        except Exception as e:
            logger.error(f"Failed to process crawl result for {result.url}: {e}")


async def main():
    """Main entry point for news crawler."""
    import os
    from services.registry.client import RegistryClient
    
    crawler_id = os.getenv('CRAWLER_ID', 'news-crawler-1')
    registry_url = os.getenv('REGISTRY_URL', 'http://localhost:8080')
    
    # Get configuration from registry
    registry_client = RegistryClient(registry_url)
    config = await registry_client.get_crawler_config(crawler_id)
    
    # Create and start crawler
    crawler = NewsCrawler(crawler_id, config)
    
    try:
        await crawler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down news crawler...")
        await crawler.stop()


if __name__ == "__main__":
    asyncio.run(main()) 