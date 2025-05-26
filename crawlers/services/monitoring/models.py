"""
Models and implementation for the Monitoring Service.
"""

import redis
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from base.utils import get_config


logger = structlog.get_logger(__name__)


# Prometheus metrics
CRAWL_REQUESTS_TOTAL = Counter('crawler_requests_total', 'Total crawl requests', ['site', 'status'])
CRAWL_DURATION = Histogram('crawler_request_duration_seconds', 'Crawl request duration')
ACTIVE_CRAWLERS = Gauge('crawler_active_instances', 'Number of active crawler instances')
QUEUE_SIZE = Gauge('crawler_queue_size', 'Current URL queue size')
SITES_REGISTERED = Gauge('crawler_sites_registered', 'Number of registered sites')
URLS_IN_PROGRESS = Gauge('crawler_urls_in_progress', 'URLs currently being crawled')


class MonitoringService:
    """Service for collecting and aggregating metrics from all crawler components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.redis_client = self._init_redis()
        
        # Service URLs
        self.registry_url = "http://crawler-registry:8080"
        self.site_manager_url = "http://site-manager:8081"
        self.scheduler_url = "http://url-scheduler:8082"
        
        # Metrics storage
        self.metrics_key = "monitoring:metrics"
        self.health_key = "monitoring:health"
        self.alerts_key = "monitoring:alerts"
        
    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection."""
        redis_config = self.config.get('redis', {})
        return redis.Redis(
            host=redis_config.get('host', 'redis'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 3),  # Use different DB for monitoring
            password=redis_config.get('password'),
            decode_responses=True
        )
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all services."""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'registry': self._collect_registry_metrics(),
                'site_manager': self._collect_site_manager_metrics(),
                'scheduler': self._collect_scheduler_metrics(),
                'system': self._collect_system_metrics()
            }
            
            # Store metrics
            self.redis_client.setex(
                f"{self.metrics_key}:{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                3600,  # Keep for 1 hour
                json.dumps(metrics)
            )
            
            # Update Prometheus metrics
            self._update_prometheus_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to collect metrics", error=str(e))
            return {}
    
    def _collect_registry_metrics(self) -> Dict[str, Any]:
        """Collect metrics from crawler registry."""
        try:
            response = requests.get(f"{self.registry_url}/stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Failed to get registry stats", status_code=response.status_code)
                return {}
        except Exception as e:
            logger.error("Failed to collect registry metrics", error=str(e))
            return {}
    
    def _collect_site_manager_metrics(self) -> Dict[str, Any]:
        """Collect metrics from site manager."""
        try:
            response = requests.get(f"{self.site_manager_url}/stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Failed to get site manager stats", status_code=response.status_code)
                return {}
        except Exception as e:
            logger.error("Failed to collect site manager metrics", error=str(e))
            return {}
    
    def _collect_scheduler_metrics(self) -> Dict[str, Any]:
        """Collect metrics from URL scheduler."""
        try:
            response = requests.get(f"{self.scheduler_url}/stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Failed to get scheduler stats", status_code=response.status_code)
                return {}
        except Exception as e:
            logger.error("Failed to collect scheduler metrics", error=str(e))
            return {}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv
                }
            }
        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
            return {}
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            return {}
    
    def _update_prometheus_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update Prometheus metrics."""
        try:
            # Update active crawlers
            registry_metrics = metrics.get('registry', {})
            if 'active_crawlers' in registry_metrics:
                ACTIVE_CRAWLERS.set(registry_metrics['active_crawlers'])
            
            # Update queue size
            scheduler_metrics = metrics.get('scheduler', {})
            if 'queue_size' in scheduler_metrics:
                QUEUE_SIZE.set(scheduler_metrics['queue_size'])
            
            # Update sites registered
            site_manager_metrics = metrics.get('site_manager', {})
            if 'total_sites' in site_manager_metrics:
                SITES_REGISTERED.set(site_manager_metrics['total_sites'])
            
            # Update URLs in progress
            if 'in_progress_count' in scheduler_metrics:
                URLS_IN_PROGRESS.set(scheduler_metrics['in_progress_count'])
                
        except Exception as e:
            logger.error("Failed to update Prometheus metrics", error=str(e))
    
    def check_service_health(self) -> Dict[str, Any]:
        """Check health of all services."""
        try:
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'healthy',
                'services': {}
            }
            
            services = [
                ('registry', f"{self.registry_url}/health"),
                ('site_manager', f"{self.site_manager_url}/health"),
                ('scheduler', f"{self.scheduler_url}/health")
            ]
            
            unhealthy_count = 0
            
            for service_name, health_url in services:
                try:
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200:
                        health_status['services'][service_name] = {
                            'status': 'healthy',
                            'response_time': response.elapsed.total_seconds(),
                            'last_check': datetime.utcnow().isoformat()
                        }
                    else:
                        health_status['services'][service_name] = {
                            'status': 'unhealthy',
                            'error': f"HTTP {response.status_code}",
                            'last_check': datetime.utcnow().isoformat()
                        }
                        unhealthy_count += 1
                except Exception as e:
                    health_status['services'][service_name] = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'last_check': datetime.utcnow().isoformat()
                    }
                    unhealthy_count += 1
            
            # Determine overall status
            if unhealthy_count == 0:
                health_status['overall_status'] = 'healthy'
            elif unhealthy_count < len(services):
                health_status['overall_status'] = 'degraded'
            else:
                health_status['overall_status'] = 'unhealthy'
            
            # Store health status
            self.redis_client.setex(
                self.health_key,
                300,  # Keep for 5 minutes
                json.dumps(health_status)
            )
            
            return health_status
            
        except Exception as e:
            logger.error("Failed to check service health", error=str(e))
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'unknown',
                'error': str(e)
            }
    
    def get_historical_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for the specified number of hours."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics_list = []
            current_time = start_time
            
            while current_time <= end_time:
                key = f"{self.metrics_key}:{current_time.strftime('%Y%m%d%H%M')}"
                data = self.redis_client.get(key)
                
                if data:
                    try:
                        metrics_list.append(json.loads(data))
                    except json.JSONDecodeError:
                        continue
                
                current_time += timedelta(minutes=1)
            
            return metrics_list
            
        except Exception as e:
            logger.error("Failed to get historical metrics", error=str(e))
            return []
    
    def create_alert(self, alert_type: str, message: str, severity: str = "warning") -> None:
        """Create an alert."""
        try:
            alert = {
                'id': f"{alert_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat(),
                'acknowledged': False
            }
            
            # Store alert
            self.redis_client.setex(
                f"{self.alerts_key}:{alert['id']}",
                86400,  # Keep for 24 hours
                json.dumps(alert)
            )
            
            logger.warning("Alert created", alert=alert)
            
        except Exception as e:
            logger.error("Failed to create alert", error=str(e))
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        try:
            alert_keys = self.redis_client.keys(f"{self.alerts_key}:*")
            alerts = []
            
            for key in alert_keys:
                data = self.redis_client.get(key)
                if data:
                    try:
                        alert = json.loads(data)
                        if not alert.get('acknowledged', False):
                            alerts.append(alert)
                    except json.JSONDecodeError:
                        continue
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            return alerts
            
        except Exception as e:
            logger.error("Failed to get active alerts", error=str(e))
            return []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        try:
            key = f"{self.alerts_key}:{alert_id}"
            data = self.redis_client.get(key)
            
            if data:
                alert = json.loads(data)
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.utcnow().isoformat()
                
                self.redis_client.setex(key, 86400, json.dumps(alert))
                logger.info("Alert acknowledged", alert_id=alert_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to acknowledge alert", alert_id=alert_id, error=str(e))
            return False
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> None:
        """Check metrics against thresholds and create alerts if needed."""
        try:
            # Check queue size
            scheduler_metrics = metrics.get('scheduler', {})
            queue_size = scheduler_metrics.get('queue_size', 0)
            
            if queue_size > 10000:
                self.create_alert(
                    'high_queue_size',
                    f"URL queue size is high: {queue_size}",
                    'warning'
                )
            elif queue_size > 50000:
                self.create_alert(
                    'critical_queue_size',
                    f"URL queue size is critical: {queue_size}",
                    'critical'
                )
            
            # Check active crawlers
            registry_metrics = metrics.get('registry', {})
            active_crawlers = registry_metrics.get('active_crawlers', 0)
            
            if active_crawlers == 0:
                self.create_alert(
                    'no_active_crawlers',
                    "No active crawlers detected",
                    'critical'
                )
            
            # Check system metrics
            system_metrics = metrics.get('system', {})
            cpu_percent = system_metrics.get('cpu_percent', 0)
            memory_percent = system_metrics.get('memory_percent', 0)
            
            if cpu_percent > 90:
                self.create_alert(
                    'high_cpu_usage',
                    f"CPU usage is high: {cpu_percent}%",
                    'warning'
                )
            
            if memory_percent > 90:
                self.create_alert(
                    'high_memory_usage',
                    f"Memory usage is high: {memory_percent}%",
                    'warning'
                )
                
        except Exception as e:
            logger.error("Failed to check thresholds", error=str(e))
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        try:
            latest_metrics = self.collect_all_metrics()
            health_status = self.check_service_health()
            active_alerts = self.get_active_alerts()
            
            # Check thresholds
            self.check_thresholds(latest_metrics)
            
            return {
                'metrics': latest_metrics,
                'health': health_status,
                'alerts': active_alerts,
                'summary': {
                    'total_crawlers': latest_metrics.get('registry', {}).get('total_crawlers', 0),
                    'active_crawlers': latest_metrics.get('registry', {}).get('active_crawlers', 0),
                    'total_sites': latest_metrics.get('site_manager', {}).get('total_sites', 0),
                    'queue_size': latest_metrics.get('scheduler', {}).get('queue_size', 0),
                    'urls_in_progress': latest_metrics.get('scheduler', {}).get('in_progress_count', 0)
                }
            }
            
        except Exception as e:
            logger.error("Failed to get dashboard data", error=str(e))
            return {} 