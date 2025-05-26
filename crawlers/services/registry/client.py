"""
Registry client for crawler communication.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class RegistryClient:
    """Client for communicating with the crawler registry service."""
    
    def __init__(self, registry_url: str):
        self.registry_url = registry_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_crawler_config(self, crawler_id: str) -> Dict[str, Any]:
        """Get configuration for a specific crawler."""
        try:
            session = await self._get_session()
            url = f"{self.registry_url}/crawlers/{crawler_id}/config"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.warning(f"Crawler {crawler_id} not found in registry")
                    # Return default configuration
                    return self._get_default_config(crawler_id)
                else:
                    logger.error(f"Failed to get config for {crawler_id}: {response.status}")
                    return self._get_default_config(crawler_id)
                    
        except Exception as e:
            logger.error(f"Error getting crawler config: {e}")
            return self._get_default_config(crawler_id)
    
    async def register_crawler(self, crawler_info: Dict[str, Any]) -> bool:
        """Register a crawler with the registry."""
        try:
            session = await self._get_session()
            url = f"{self.registry_url}/crawlers"
            
            async with session.post(url, json=crawler_info) as response:
                if response.status in [200, 201]:
                    logger.info(f"Crawler {crawler_info.get('crawler_id')} registered successfully")
                    return True
                else:
                    logger.error(f"Failed to register crawler: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error registering crawler: {e}")
            return False
    
    async def heartbeat(self, crawler_id: str, metrics: Dict[str, Any]) -> bool:
        """Send heartbeat to registry."""
        try:
            session = await self._get_session()
            url = f"{self.registry_url}/crawlers/{crawler_id}/heartbeat"
            
            async with session.post(url, json=metrics) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    async def unregister_crawler(self, crawler_id: str) -> bool:
        """Unregister a crawler from the registry."""
        try:
            session = await self._get_session()
            url = f"{self.registry_url}/crawlers/{crawler_id}"
            
            async with session.delete(url) as response:
                if response.status == 200:
                    logger.info(f"Crawler {crawler_id} unregistered successfully")
                    return True
                else:
                    logger.error(f"Failed to unregister crawler: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unregistering crawler: {e}")
            return False
    
    def _get_default_config(self, crawler_id: str) -> Dict[str, Any]:
        """Get default configuration when registry is unavailable."""
        return {
            "crawler_id": crawler_id,
            "max_concurrent_requests": 5,
            "request_delay": 1.0,
            "timeout": 30,
            "retry_attempts": 3,
            "user_agent": "OpenMedia-Crawler/1.0",
            "respect_robots_txt": True,
            "sites": [],
            "kafka_topics": {
                "content_extracted": "content.extracted",
                "content_news": "content.news"
            }
        }
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None 