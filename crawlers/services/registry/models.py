"""
Models and implementation for the Crawler Registry Service.
"""

import uuid
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog

from base.interfaces import ICrawlerRegistry, CrawlerInfo, CrawlerStatus
from base.utils import get_config


logger = structlog.get_logger(__name__)


class CrawlerRegistryService(ICrawlerRegistry):
    """Redis-based implementation of the crawler registry."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.redis_client = self._init_redis()
        self.registry_key = "crawler:registry"
        self.heartbeat_key = "crawler:heartbeat"
        self.assignment_key = "crawler:assignments"
        self.heartbeat_timeout = 300  # 5 minutes
        
    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection."""
        redis_config = self.config.get('redis', {})
        return redis.Redis(
            host=redis_config.get('host', 'redis'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_config.get('password'),
            decode_responses=True
        )
    
    def register_crawler(self, crawler_info: CrawlerInfo) -> str:
        """Register a new crawler instance."""
        try:
            crawler_id = crawler_info.crawler_id or str(uuid.uuid4())
            crawler_info.crawler_id = crawler_id
            
            # Store crawler info
            crawler_data = {
                'crawler_id': crawler_id,
                'instance_type': crawler_info.instance_type,
                'status': crawler_info.status.value,
                'assigned_sites': crawler_info.assigned_sites,
                'host_info': crawler_info.host_info,
                'version': crawler_info.version,
                'registered_at': datetime.utcnow().isoformat(),
                'last_heartbeat': datetime.utcnow().isoformat()
            }
            
            # Store in Redis
            self.redis_client.hset(
                self.registry_key,
                crawler_id,
                json.dumps(crawler_data)
            )
            
            # Initialize heartbeat
            self.redis_client.hset(
                self.heartbeat_key,
                crawler_id,
                datetime.utcnow().isoformat()
            )
            
            logger.info("Crawler registered", crawler_id=crawler_id, instance_type=crawler_info.instance_type)
            return crawler_id
            
        except Exception as e:
            logger.error("Failed to register crawler", error=str(e))
            raise
    
    def heartbeat(self, crawler_id: str, metrics: Dict[str, Any]) -> bool:
        """Send heartbeat with performance metrics."""
        try:
            # Check if crawler exists
            if not self.redis_client.hexists(self.registry_key, crawler_id):
                logger.warning("Heartbeat from unregistered crawler", crawler_id=crawler_id)
                return False
            
            # Update heartbeat timestamp
            self.redis_client.hset(
                self.heartbeat_key,
                crawler_id,
                datetime.utcnow().isoformat()
            )
            
            # Update crawler info with metrics
            crawler_data = json.loads(self.redis_client.hget(self.registry_key, crawler_id))
            crawler_data['performance_metrics'] = metrics
            crawler_data['last_heartbeat'] = datetime.utcnow().isoformat()
            
            self.redis_client.hset(
                self.registry_key,
                crawler_id,
                json.dumps(crawler_data)
            )
            
            logger.debug("Heartbeat received", crawler_id=crawler_id)
            return True
            
        except Exception as e:
            logger.error("Failed to process heartbeat", crawler_id=crawler_id, error=str(e))
            return False
    
    def assign_sites(self, crawler_id: str, site_ids: List[str]) -> bool:
        """Assign sites to crawler."""
        try:
            # Check if crawler exists
            if not self.redis_client.hexists(self.registry_key, crawler_id):
                logger.warning("Attempting to assign sites to unregistered crawler", crawler_id=crawler_id)
                return False
            
            # Update crawler info
            crawler_data = json.loads(self.redis_client.hget(self.registry_key, crawler_id))
            current_sites = set(crawler_data.get('assigned_sites', []))
            current_sites.update(site_ids)
            crawler_data['assigned_sites'] = list(current_sites)
            
            self.redis_client.hset(
                self.registry_key,
                crawler_id,
                json.dumps(crawler_data)
            )
            
            # Store assignments mapping
            for site_id in site_ids:
                self.redis_client.hset(
                    self.assignment_key,
                    site_id,
                    crawler_id
                )
            
            logger.info("Sites assigned to crawler", crawler_id=crawler_id, site_ids=site_ids)
            return True
            
        except Exception as e:
            logger.error("Failed to assign sites", crawler_id=crawler_id, error=str(e))
            return False
    
    def unassign_sites(self, crawler_id: str, site_ids: List[str]) -> bool:
        """Unassign sites from crawler."""
        try:
            # Check if crawler exists
            if not self.redis_client.hexists(self.registry_key, crawler_id):
                return False
            
            # Update crawler info
            crawler_data = json.loads(self.redis_client.hget(self.registry_key, crawler_id))
            current_sites = set(crawler_data.get('assigned_sites', []))
            current_sites.difference_update(site_ids)
            crawler_data['assigned_sites'] = list(current_sites)
            
            self.redis_client.hset(
                self.registry_key,
                crawler_id,
                json.dumps(crawler_data)
            )
            
            # Remove assignments mapping
            for site_id in site_ids:
                self.redis_client.hdel(self.assignment_key, site_id)
            
            logger.info("Sites unassigned from crawler", crawler_id=crawler_id, site_ids=site_ids)
            return True
            
        except Exception as e:
            logger.error("Failed to unassign sites", crawler_id=crawler_id, error=str(e))
            return False
    
    def get_active_crawlers(self) -> List[CrawlerInfo]:
        """Get list of active crawlers."""
        try:
            active_crawlers = []
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
            
            # Get all registered crawlers
            crawler_data = self.redis_client.hgetall(self.registry_key)
            
            for crawler_id, data_str in crawler_data.items():
                data = json.loads(data_str)
                last_heartbeat = datetime.fromisoformat(data['last_heartbeat'])
                
                # Check if crawler is active (recent heartbeat)
                if last_heartbeat > cutoff_time:
                    crawler_info = CrawlerInfo(
                        crawler_id=crawler_id,
                        instance_type=data['instance_type'],
                        status=CrawlerStatus(data['status']),
                        assigned_sites=data.get('assigned_sites', []),
                        last_heartbeat=last_heartbeat,
                        performance_metrics=data.get('performance_metrics', {}),
                        host_info=data.get('host_info', {}),
                        version=data.get('version', '1.0.0')
                    )
                    active_crawlers.append(crawler_info)
            
            return active_crawlers
            
        except Exception as e:
            logger.error("Failed to get active crawlers", error=str(e))
            return []
    
    def get_crawler_info(self, crawler_id: str) -> Optional[CrawlerInfo]:
        """Get information about specific crawler."""
        try:
            data_str = self.redis_client.hget(self.registry_key, crawler_id)
            if not data_str:
                return None
            
            data = json.loads(data_str)
            return CrawlerInfo(
                crawler_id=crawler_id,
                instance_type=data['instance_type'],
                status=CrawlerStatus(data['status']),
                assigned_sites=data.get('assigned_sites', []),
                last_heartbeat=datetime.fromisoformat(data['last_heartbeat']),
                performance_metrics=data.get('performance_metrics', {}),
                host_info=data.get('host_info', {}),
                version=data.get('version', '1.0.0')
            )
            
        except Exception as e:
            logger.error("Failed to get crawler info", crawler_id=crawler_id, error=str(e))
            return None
    
    def unregister_crawler(self, crawler_id: str) -> bool:
        """Unregister crawler instance."""
        try:
            # Get assigned sites before removing
            crawler_data = self.redis_client.hget(self.registry_key, crawler_id)
            if crawler_data:
                data = json.loads(crawler_data)
                assigned_sites = data.get('assigned_sites', [])
                
                # Remove site assignments
                for site_id in assigned_sites:
                    self.redis_client.hdel(self.assignment_key, site_id)
            
            # Remove from registry and heartbeat
            self.redis_client.hdel(self.registry_key, crawler_id)
            self.redis_client.hdel(self.heartbeat_key, crawler_id)
            
            logger.info("Crawler unregistered", crawler_id=crawler_id)
            return True
            
        except Exception as e:
            logger.error("Failed to unregister crawler", crawler_id=crawler_id, error=str(e))
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        try:
            total_crawlers = self.redis_client.hlen(self.registry_key)
            active_crawlers = len(self.get_active_crawlers())
            total_assignments = self.redis_client.hlen(self.assignment_key)
            
            # Get crawler types distribution
            crawler_types = {}
            crawler_data = self.redis_client.hgetall(self.registry_key)
            
            for data_str in crawler_data.values():
                data = json.loads(data_str)
                instance_type = data['instance_type']
                crawler_types[instance_type] = crawler_types.get(instance_type, 0) + 1
            
            return {
                'total_crawlers': total_crawlers,
                'active_crawlers': active_crawlers,
                'inactive_crawlers': total_crawlers - active_crawlers,
                'total_assignments': total_assignments,
                'crawler_types': crawler_types,
                'heartbeat_timeout': self.heartbeat_timeout
            }
            
        except Exception as e:
            logger.error("Failed to get registry stats", error=str(e))
            return {}
    
    def cleanup_inactive_crawlers(self) -> int:
        """Remove inactive crawlers from registry."""
        try:
            removed_count = 0
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
            
            crawler_data = self.redis_client.hgetall(self.registry_key)
            
            for crawler_id, data_str in crawler_data.items():
                data = json.loads(data_str)
                last_heartbeat = datetime.fromisoformat(data['last_heartbeat'])
                
                if last_heartbeat <= cutoff_time:
                    self.unregister_crawler(crawler_id)
                    removed_count += 1
            
            logger.info("Cleaned up inactive crawlers", removed_count=removed_count)
            return removed_count
            
        except Exception as e:
            logger.error("Failed to cleanup inactive crawlers", error=str(e))
            return 0 