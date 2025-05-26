"""
Models and implementation for the URL Scheduler Service.
"""

import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog

from base.interfaces import IURLFrontier, CrawlRequest
from base.utils import get_config, normalize_url, extract_domain


logger = structlog.get_logger(__name__)


class URLSchedulerService(IURLFrontier):
    """Redis-based implementation of the URL frontier and scheduler."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.redis_client = self._init_redis()
        
        # Redis keys
        self.queue_key = "url:queue"
        self.visited_key = "url:visited"
        self.in_progress_key = "url:in_progress"
        self.failed_key = "url:failed"
        self.stats_key = "url:stats"
        self.domain_delay_key = "url:domain_delay"
        
        # Configuration
        self.max_retries = 3
        self.default_priority = 1
        self.dedup_window = 86400  # 24 hours in seconds
        
    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection."""
        redis_config = self.config.get('redis', {})
        return redis.Redis(
            host=redis_config.get('host', 'redis'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 2),  # Use different DB for URL frontier
            password=redis_config.get('password'),
            decode_responses=True
        )
    
    def add_url(self, url: str, priority: int = 1, metadata: Dict = None) -> bool:
        """Add URL to frontier."""
        try:
            normalized_url = normalize_url(url)
            
            # Check if already visited or in queue
            if self.is_visited(normalized_url):
                logger.debug("URL already visited", url=normalized_url)
                return False
            
            # Create crawl request
            request = CrawlRequest(
                url=normalized_url,
                priority=priority,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            # Add to priority queue
            score = self._calculate_score(request)
            self.redis_client.zadd(
                self.queue_key,
                {json.dumps(request.__dict__, default=str): score}
            )
            
            # Mark as queued
            url_hash = self._hash_url(normalized_url)
            self.redis_client.setex(
                f"{self.visited_key}:{url_hash}",
                self.dedup_window,
                "queued"
            )
            
            # Update stats
            self._update_stats('urls_added', 1)
            
            logger.debug("URL added to queue", url=normalized_url, priority=priority)
            return True
            
        except Exception as e:
            logger.error("Failed to add URL", url=url, error=str(e))
            return False
    
    def add_urls(self, urls: List[str], priority: int = 1) -> int:
        """Add multiple URLs to frontier."""
        added_count = 0
        
        for url in urls:
            if self.add_url(url, priority):
                added_count += 1
        
        return added_count
    
    def get_next_url(self, crawler_id: str) -> Optional[CrawlRequest]:
        """Get next URL for crawling."""
        try:
            # Get highest priority URL
            items = self.redis_client.zrevrange(
                self.queue_key, 0, 0, withscores=True
            )
            
            if not items:
                return None
            
            request_json, score = items[0]
            request_data = json.loads(request_json)
            
            # Check domain delay
            domain = extract_domain(request_data['url'])
            if not self._can_crawl_domain(domain):
                # Re-queue with lower priority and return None
                self.redis_client.zrem(self.queue_key, request_json)
                new_score = score - 1000  # Lower priority
                self.redis_client.zadd(self.queue_key, {request_json: new_score})
                return None
            
            # Remove from queue and add to in-progress
            self.redis_client.zrem(self.queue_key, request_json)
            
            # Create crawl request object
            request = CrawlRequest(
                url=request_data['url'],
                priority=request_data['priority'],
                metadata=request_data.get('metadata', {}),
                retry_count=request_data.get('retry_count', 0),
                max_retries=request_data.get('max_retries', self.max_retries),
                crawl_delay=request_data.get('crawl_delay', 1.0),
                site_id=request_data.get('site_id'),
                created_at=datetime.fromisoformat(request_data['created_at'])
            )
            
            # Mark as in progress
            self.redis_client.setex(
                f"{self.in_progress_key}:{crawler_id}:{self._hash_url(request.url)}",
                3600,  # 1 hour timeout
                json.dumps(request.__dict__, default=str)
            )
            
            # Set domain delay
            self._set_domain_delay(domain, request.crawl_delay)
            
            # Update stats
            self._update_stats('urls_dispatched', 1)
            
            logger.debug("URL dispatched", url=request.url, crawler_id=crawler_id)
            return request
            
        except Exception as e:
            logger.error("Failed to get next URL", crawler_id=crawler_id, error=str(e))
            return None
    
    def mark_completed(self, url: str, success: bool) -> bool:
        """Mark URL as completed."""
        try:
            normalized_url = normalize_url(url)
            url_hash = self._hash_url(normalized_url)
            
            # Remove from in-progress (all crawler instances)
            pattern = f"{self.in_progress_key}:*:{url_hash}"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # Mark as visited
            status = "completed" if success else "failed"
            self.redis_client.setex(
                f"{self.visited_key}:{url_hash}",
                self.dedup_window,
                status
            )
            
            # Update stats
            if success:
                self._update_stats('urls_completed', 1)
            else:
                self._update_stats('urls_failed', 1)
            
            logger.debug("URL marked as completed", url=normalized_url, success=success)
            return True
            
        except Exception as e:
            logger.error("Failed to mark URL as completed", url=url, error=str(e))
            return False
    
    def mark_failed(self, url: str, error: str) -> bool:
        """Mark URL as failed."""
        try:
            normalized_url = normalize_url(url)
            url_hash = self._hash_url(normalized_url)
            
            # Get original request from in-progress
            pattern = f"{self.in_progress_key}:*:{url_hash}"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                request_json = self.redis_client.get(keys[0])
                if request_json:
                    request_data = json.loads(request_json)
                    retry_count = request_data.get('retry_count', 0)
                    max_retries = request_data.get('max_retries', self.max_retries)
                    
                    # Check if we should retry
                    if retry_count < max_retries:
                        # Re-queue with incremented retry count
                        request_data['retry_count'] = retry_count + 1
                        request_data['metadata']['last_error'] = error
                        request_data['metadata']['failed_at'] = datetime.utcnow().isoformat()
                        
                        # Lower priority for retries
                        score = self._calculate_score_from_data(request_data) - (retry_count + 1) * 100
                        
                        self.redis_client.zadd(
                            self.queue_key,
                            {json.dumps(request_data, default=str): score}
                        )
                        
                        logger.info("URL re-queued for retry", 
                                  url=normalized_url, 
                                  retry_count=retry_count + 1,
                                  max_retries=max_retries)
                    else:
                        # Max retries reached, mark as permanently failed
                        self.redis_client.setex(
                            f"{self.failed_key}:{url_hash}",
                            self.dedup_window * 7,  # Keep failed URLs longer
                            json.dumps({
                                'url': normalized_url,
                                'error': error,
                                'retry_count': retry_count,
                                'failed_at': datetime.utcnow().isoformat()
                            })
                        )
                        
                        self._update_stats('urls_permanently_failed', 1)
                        logger.warning("URL permanently failed", 
                                     url=normalized_url, 
                                     retry_count=retry_count,
                                     error=error)
                
                # Remove from in-progress
                self.redis_client.delete(*keys)
            
            # Mark as visited with failed status
            self.redis_client.setex(
                f"{self.visited_key}:{url_hash}",
                self.dedup_window,
                "failed"
            )
            
            self._update_stats('urls_failed', 1)
            return True
            
        except Exception as e:
            logger.error("Failed to mark URL as failed", url=url, error=str(e))
            return False
    
    def is_visited(self, url: str) -> bool:
        """Check if URL has been visited."""
        try:
            normalized_url = normalize_url(url)
            url_hash = self._hash_url(normalized_url)
            
            # Check visited set
            visited_key = f"{self.visited_key}:{url_hash}"
            return self.redis_client.exists(visited_key) > 0
            
        except Exception as e:
            logger.error("Failed to check if URL is visited", url=url, error=str(e))
            return False
    
    def get_queue_size(self, priority: Optional[int] = None) -> int:
        """Get current queue size."""
        try:
            if priority is None:
                return self.redis_client.zcard(self.queue_key)
            else:
                # Count URLs with specific priority
                # This is approximate since we use calculated scores
                return self.redis_client.zcount(
                    self.queue_key,
                    priority * 1000,
                    (priority + 1) * 1000 - 1
                )
                
        except Exception as e:
            logger.error("Failed to get queue size", error=str(e))
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get frontier statistics."""
        try:
            queue_size = self.get_queue_size()
            in_progress_count = len(self.redis_client.keys(f"{self.in_progress_key}:*"))
            failed_count = len(self.redis_client.keys(f"{self.failed_key}:*"))
            
            # Get operational stats
            stats_data = self.redis_client.hgetall(self.stats_key)
            operational_stats = {k: int(v) for k, v in stats_data.items()}
            
            # Get priority distribution
            priority_distribution = {}
            queue_items = self.redis_client.zrange(self.queue_key, 0, -1, withscores=True)
            
            for item_json, score in queue_items:
                try:
                    item_data = json.loads(item_json)
                    priority = item_data.get('priority', 1)
                    priority_distribution[str(priority)] = priority_distribution.get(str(priority), 0) + 1
                except:
                    continue
            
            return {
                'queue_size': queue_size,
                'in_progress_count': in_progress_count,
                'failed_count': failed_count,
                'priority_distribution': priority_distribution,
                'operational_stats': operational_stats,
                'dedup_window_hours': self.dedup_window / 3600
            }
            
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {}
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Cleanup expired URLs and return counts."""
        try:
            cleaned_counts = {
                'expired_in_progress': 0,
                'expired_failed': 0
            }
            
            # Cleanup expired in-progress URLs
            in_progress_keys = self.redis_client.keys(f"{self.in_progress_key}:*")
            for key in in_progress_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    self.redis_client.expire(key, 3600)  # Set 1 hour expiration
                elif ttl == -2:  # Key doesn't exist
                    cleaned_counts['expired_in_progress'] += 1
            
            # Cleanup old failed URLs
            failed_keys = self.redis_client.keys(f"{self.failed_key}:*")
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            for key in failed_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        failed_data = json.loads(data)
                        failed_at = datetime.fromisoformat(failed_data['failed_at'])
                        if failed_at < cutoff_time:
                            self.redis_client.delete(key)
                            cleaned_counts['expired_failed'] += 1
                except:
                    # Delete corrupted entries
                    self.redis_client.delete(key)
                    cleaned_counts['expired_failed'] += 1
            
            logger.info("Cleanup completed", cleaned_counts=cleaned_counts)
            return cleaned_counts
            
        except Exception as e:
            logger.error("Failed to cleanup expired URLs", error=str(e))
            return {}
    
    def _hash_url(self, url: str) -> str:
        """Create hash for URL deduplication."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _calculate_score(self, request: CrawlRequest) -> float:
        """Calculate priority score for URL."""
        # Base score from priority (higher priority = higher score)
        score = request.priority * 1000
        
        # Time-based component (newer URLs get slight boost)
        time_component = datetime.utcnow().timestamp() / 1000000
        score += time_component
        
        # Penalty for retries
        score -= request.retry_count * 100
        
        return score
    
    def _calculate_score_from_data(self, request_data: Dict[str, Any]) -> float:
        """Calculate priority score from request data."""
        priority = request_data.get('priority', 1)
        retry_count = request_data.get('retry_count', 0)
        
        score = priority * 1000
        score += datetime.utcnow().timestamp() / 1000000
        score -= retry_count * 100
        
        return score
    
    def _can_crawl_domain(self, domain: str) -> bool:
        """Check if domain can be crawled based on delay settings."""
        try:
            delay_key = f"{self.domain_delay_key}:{domain}"
            last_crawl = self.redis_client.get(delay_key)
            
            if not last_crawl:
                return True
            
            last_crawl_time = datetime.fromisoformat(last_crawl)
            # Default 1 second delay between requests to same domain
            min_delay = timedelta(seconds=1)
            
            return datetime.utcnow() - last_crawl_time >= min_delay
            
        except Exception as e:
            logger.error("Failed to check domain delay", domain=domain, error=str(e))
            return True
    
    def _set_domain_delay(self, domain: str, delay: float) -> None:
        """Set domain delay timestamp."""
        try:
            delay_key = f"{self.domain_delay_key}:{domain}"
            self.redis_client.setex(
                delay_key,
                int(delay * 2),  # Keep delay info for 2x the delay time
                datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.warning("Failed to set domain delay", domain=domain, error=str(e))
    
    def _update_stats(self, metric: str, value: int) -> None:
        """Update operational statistics."""
        try:
            self.redis_client.hincrby(self.stats_key, metric, value)
        except Exception as e:
            logger.warning("Failed to update stats", metric=metric, error=str(e)) 