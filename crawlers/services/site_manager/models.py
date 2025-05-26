"""
Models and implementation for the Site Manager Service.
"""

import uuid
import redis
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import structlog

from base.interfaces import ISiteManager, SiteConfig
from base.utils import get_config, validate_url, extract_domain


logger = structlog.get_logger(__name__)


class SiteManagerService(ISiteManager):
    """Redis-based implementation of the site manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.redis_client = self._init_redis()
        self.sites_key = "sites:config"
        self.domains_key = "sites:domains"
        self.stats_key = "sites:stats"
        
    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection."""
        redis_config = self.config.get('redis', {})
        return redis.Redis(
            host=redis_config.get('host', 'redis'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 1),  # Use different DB for sites
            password=redis_config.get('password'),
            decode_responses=True
        )
    
    def register_site(self, config: SiteConfig) -> str:
        """Register a new site configuration."""
        try:
            # Generate site ID if not provided
            site_id = config.site_id or str(uuid.uuid4())
            config.site_id = site_id
            config.created_at = datetime.utcnow()
            config.updated_at = datetime.utcnow()
            
            # Validate configuration
            self._validate_site_config(config)
            
            # Check for domain conflicts
            if self._has_domain_conflict(config.domain, site_id):
                raise ValueError(f"Domain {config.domain} is already registered")
            
            # Store site configuration
            site_data = {
                'site_id': site_id,
                'domain': config.domain,
                'name': config.name,
                'base_urls': config.base_urls,
                'allowed_domains': config.allowed_domains,
                'crawl_delay': config.crawl_delay,
                'concurrent_requests': config.concurrent_requests,
                'user_agent': config.user_agent,
                'respect_robots_txt': config.respect_robots_txt,
                'custom_headers': config.custom_headers,
                'selectors': config.selectors,
                'rate_limit': config.rate_limit,
                'priority': config.priority,
                'enabled': config.enabled,
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat()
            }
            
            # Store in Redis
            self.redis_client.hset(
                self.sites_key,
                site_id,
                json.dumps(site_data)
            )
            
            # Store domain mapping
            self.redis_client.hset(
                self.domains_key,
                config.domain,
                site_id
            )
            
            # Update stats
            self._update_stats('sites_registered', 1)
            
            logger.info("Site registered", site_id=site_id, domain=config.domain, name=config.name)
            return site_id
            
        except Exception as e:
            logger.error("Failed to register site", error=str(e), domain=config.domain)
            raise
    
    def update_site(self, site_id: str, config: SiteConfig) -> bool:
        """Update existing site configuration."""
        try:
            # Check if site exists
            if not self.redis_client.hexists(self.sites_key, site_id):
                logger.warning("Attempting to update non-existent site", site_id=site_id)
                return False
            
            # Get current configuration
            current_data = json.loads(self.redis_client.hget(self.sites_key, site_id))
            current_domain = current_data['domain']
            
            # Validate new configuration
            self._validate_site_config(config)
            
            # Check for domain conflicts (if domain changed)
            if config.domain != current_domain:
                if self._has_domain_conflict(config.domain, site_id):
                    raise ValueError(f"Domain {config.domain} is already registered")
                
                # Remove old domain mapping
                self.redis_client.hdel(self.domains_key, current_domain)
                
                # Add new domain mapping
                self.redis_client.hset(self.domains_key, config.domain, site_id)
            
            # Update configuration
            config.site_id = site_id
            config.updated_at = datetime.utcnow()
            config.created_at = datetime.fromisoformat(current_data['created_at'])
            
            site_data = {
                'site_id': site_id,
                'domain': config.domain,
                'name': config.name,
                'base_urls': config.base_urls,
                'allowed_domains': config.allowed_domains,
                'crawl_delay': config.crawl_delay,
                'concurrent_requests': config.concurrent_requests,
                'user_agent': config.user_agent,
                'respect_robots_txt': config.respect_robots_txt,
                'custom_headers': config.custom_headers,
                'selectors': config.selectors,
                'rate_limit': config.rate_limit,
                'priority': config.priority,
                'enabled': config.enabled,
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat()
            }
            
            # Store updated configuration
            self.redis_client.hset(
                self.sites_key,
                site_id,
                json.dumps(site_data)
            )
            
            # Update stats
            self._update_stats('sites_updated', 1)
            
            logger.info("Site updated", site_id=site_id, domain=config.domain)
            return True
            
        except Exception as e:
            logger.error("Failed to update site", site_id=site_id, error=str(e))
            raise
    
    def get_site_config(self, site_id: str) -> Optional[SiteConfig]:
        """Get site configuration by ID."""
        try:
            data_str = self.redis_client.hget(self.sites_key, site_id)
            if not data_str:
                return None
            
            data = json.loads(data_str)
            return self._data_to_site_config(data)
            
        except Exception as e:
            logger.error("Failed to get site config", site_id=site_id, error=str(e))
            return None
    
    def get_site_by_domain(self, domain: str) -> Optional[SiteConfig]:
        """Get site configuration by domain."""
        try:
            site_id = self.redis_client.hget(self.domains_key, domain)
            if not site_id:
                return None
            
            return self.get_site_config(site_id)
            
        except Exception as e:
            logger.error("Failed to get site by domain", domain=domain, error=str(e))
            return None
    
    def list_sites(self, enabled_only: bool = True) -> List[SiteConfig]:
        """List all registered sites."""
        try:
            sites = []
            site_data = self.redis_client.hgetall(self.sites_key)
            
            for site_id, data_str in site_data.items():
                data = json.loads(data_str)
                
                # Filter by enabled status if requested
                if enabled_only and not data.get('enabled', True):
                    continue
                
                site_config = self._data_to_site_config(data)
                sites.append(site_config)
            
            # Sort by priority and name
            sites.sort(key=lambda x: (x.priority, x.name))
            return sites
            
        except Exception as e:
            logger.error("Failed to list sites", error=str(e))
            return []
    
    def disable_site(self, site_id: str) -> bool:
        """Disable a site temporarily."""
        return self._update_site_status(site_id, False)
    
    def enable_site(self, site_id: str) -> bool:
        """Enable a site."""
        return self._update_site_status(site_id, True)
    
    def delete_site(self, site_id: str) -> bool:
        """Delete a site configuration."""
        try:
            # Get site data before deletion
            data_str = self.redis_client.hget(self.sites_key, site_id)
            if not data_str:
                return False
            
            data = json.loads(data_str)
            domain = data['domain']
            
            # Remove from Redis
            self.redis_client.hdel(self.sites_key, site_id)
            self.redis_client.hdel(self.domains_key, domain)
            
            # Update stats
            self._update_stats('sites_deleted', 1)
            
            logger.info("Site deleted", site_id=site_id, domain=domain)
            return True
            
        except Exception as e:
            logger.error("Failed to delete site", site_id=site_id, error=str(e))
            return False
    
    def get_sites_stats(self) -> Dict[str, Any]:
        """Get sites statistics."""
        try:
            total_sites = self.redis_client.hlen(self.sites_key)
            enabled_sites = 0
            disabled_sites = 0
            priority_distribution = {}
            domain_distribution = {}
            
            site_data = self.redis_client.hgetall(self.sites_key)
            
            for data_str in site_data.values():
                data = json.loads(data_str)
                
                if data.get('enabled', True):
                    enabled_sites += 1
                else:
                    disabled_sites += 1
                
                priority = data.get('priority', 1)
                priority_distribution[str(priority)] = priority_distribution.get(str(priority), 0) + 1
                
                domain = extract_domain(data['domain'])
                tld = domain.split('.')[-1] if '.' in domain else 'unknown'
                domain_distribution[tld] = domain_distribution.get(tld, 0) + 1
            
            # Get operational stats
            stats_data = self.redis_client.hgetall(self.stats_key)
            operational_stats = {k: int(v) for k, v in stats_data.items()}
            
            return {
                'total_sites': total_sites,
                'enabled_sites': enabled_sites,
                'disabled_sites': disabled_sites,
                'priority_distribution': priority_distribution,
                'domain_distribution': domain_distribution,
                'operational_stats': operational_stats
            }
            
        except Exception as e:
            logger.error("Failed to get sites stats", error=str(e))
            return {}
    
    def _validate_site_config(self, config: SiteConfig) -> None:
        """Validate site configuration."""
        if not config.domain:
            raise ValueError("Domain is required")
        
        if not config.name:
            raise ValueError("Site name is required")
        
        if not config.base_urls:
            raise ValueError("At least one base URL is required")
        
        # Validate URLs
        for url in config.base_urls:
            if not validate_url(url):
                raise ValueError(f"Invalid base URL: {url}")
        
        # Validate domains
        if not config.allowed_domains:
            raise ValueError("At least one allowed domain is required")
        
        # Validate numeric values
        if config.crawl_delay < 0:
            raise ValueError("Crawl delay must be non-negative")
        
        if config.concurrent_requests < 1:
            raise ValueError("Concurrent requests must be at least 1")
        
        if config.rate_limit < 1:
            raise ValueError("Rate limit must be at least 1")
        
        if config.priority < 1:
            raise ValueError("Priority must be at least 1")
    
    def _has_domain_conflict(self, domain: str, exclude_site_id: str = None) -> bool:
        """Check if domain is already registered by another site."""
        existing_site_id = self.redis_client.hget(self.domains_key, domain)
        return existing_site_id is not None and existing_site_id != exclude_site_id
    
    def _update_site_status(self, site_id: str, enabled: bool) -> bool:
        """Update site enabled/disabled status."""
        try:
            data_str = self.redis_client.hget(self.sites_key, site_id)
            if not data_str:
                return False
            
            data = json.loads(data_str)
            data['enabled'] = enabled
            data['updated_at'] = datetime.utcnow().isoformat()
            
            self.redis_client.hset(
                self.sites_key,
                site_id,
                json.dumps(data)
            )
            
            action = "enabled" if enabled else "disabled"
            logger.info(f"Site {action}", site_id=site_id, domain=data['domain'])
            return True
            
        except Exception as e:
            logger.error("Failed to update site status", site_id=site_id, error=str(e))
            return False
    
    def _data_to_site_config(self, data: Dict[str, Any]) -> SiteConfig:
        """Convert Redis data to SiteConfig object."""
        return SiteConfig(
            site_id=data['site_id'],
            domain=data['domain'],
            name=data['name'],
            base_urls=data['base_urls'],
            allowed_domains=data['allowed_domains'],
            crawl_delay=data['crawl_delay'],
            concurrent_requests=data['concurrent_requests'],
            user_agent=data['user_agent'],
            respect_robots_txt=data['respect_robots_txt'],
            custom_headers=data['custom_headers'],
            selectors=data['selectors'],
            rate_limit=data['rate_limit'],
            priority=data['priority'],
            enabled=data['enabled'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def _update_stats(self, metric: str, value: int) -> None:
        """Update operational statistics."""
        try:
            self.redis_client.hincrby(self.stats_key, metric, value)
        except Exception as e:
            logger.warning("Failed to update stats", metric=metric, error=str(e)) 