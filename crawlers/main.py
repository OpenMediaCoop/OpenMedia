#!/usr/bin/env python3
"""
Main entry point for OpenMedia crawlers.
Supports both news and generic crawlers.
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from base.interfaces import CrawlerStatus
from crawlers.base_crawler import BaseCrawler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for crawlers."""
    try:
        # Get crawler configuration from environment
        crawler_id = os.getenv('CRAWLER_ID', 'crawler-1')
        crawler_type = os.getenv('CRAWLER_TYPE', 'generic')  # 'news' or 'generic'
        
        logger.info(f"Starting {crawler_type} crawler with ID: {crawler_id}")
        
        # Create crawler instance
        crawler = BaseCrawler(crawler_type=crawler_type)
        crawler.crawler_id = crawler_id
        
        # Initialize crawler with configuration
        config = {
            'registry_url': os.getenv('REGISTRY_URL', 'http://crawler-registry:8080'),
            'site_manager_url': os.getenv('SITE_MANAGER_URL', 'http://site-manager:8081'),
            'scheduler_url': os.getenv('SCHEDULER_URL', 'http://url-scheduler:8082'),
            'redis_host': os.getenv('REDIS_HOST', 'redis'),
            'kafka_bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
        }
        
        if not crawler.initialize(config):
            logger.error("Failed to initialize crawler")
            sys.exit(1)
        
        logger.info("Crawler initialized successfully")
        
        # Start the crawler main loop
        crawler.run()
        
    except KeyboardInterrupt:
        logger.info("Shutting down crawler...")
        if 'crawler' in locals():
            crawler.stop()
    except Exception as e:
        logger.error(f"Fatal error in crawler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 