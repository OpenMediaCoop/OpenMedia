"""
Utility functions for the distributed crawler system.
"""

import os
import logging
import structlog
import yaml
import validators
import tldextract
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Dict, Any, Optional
import socket
import platform


def setup_logging(level: str = "INFO", service_name: str = "crawler") -> None:
    """Setup structured logging for the service."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper()),
    )
    
    # Add service context
    logger = structlog.get_logger(service_name)
    return logger


def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or environment variables."""
    
    config = {}
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(f)
            else:
                # Assume JSON for other extensions
                import json
                config = json.load(f)
    
    # Override with environment variables
    env_config = {
        'kafka': {
            'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
            'topic_prefix': os.getenv('KAFKA_TOPIC_PREFIX', 'crawler'),
        },
        'redis': {
            'host': os.getenv('REDIS_HOST', 'redis'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD'),
        },
        'postgres': {
            'host': os.getenv('POSTGRES_HOST', 'pgvector'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'scrapper'),
            'username': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        },
        'crawler': {
            'user_agent': os.getenv('CRAWLER_USER_AGENT', 'OpenMedia-Crawler/1.0'),
            'default_delay': float(os.getenv('CRAWLER_DEFAULT_DELAY', '1.0')),
            'max_retries': int(os.getenv('CRAWLER_MAX_RETRIES', '3')),
            'timeout': int(os.getenv('CRAWLER_TIMEOUT', '30')),
        },
        'service': {
            'host': os.getenv('SERVICE_HOST', '0.0.0.0'),
            'port': int(os.getenv('SERVICE_PORT', '8000')),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
        }
    }
    
    # Merge configurations (env overrides file)
    def merge_dicts(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    return merge_dicts(config, env_config)


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    return validators.url(url) is True


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """Normalize URL by removing fragments and query parameters."""
    
    # Convert relative URLs to absolute
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Parse URL
    parsed = urlparse(url)
    
    # Remove fragment and normalize
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path,
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))
    
    return normalized


def get_host_info() -> Dict[str, str]:
    """Get information about the current host."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'architecture': platform.architecture()[0],
    }


def calculate_crawl_delay(site_config: Dict[str, Any], default_delay: float = 1.0) -> float:
    """Calculate appropriate crawl delay based on site configuration and politeness."""
    
    base_delay = site_config.get('crawl_delay', default_delay)
    rate_limit = site_config.get('rate_limit', 60)  # requests per minute
    
    # Calculate minimum delay based on rate limit
    min_delay = 60.0 / rate_limit if rate_limit > 0 else base_delay
    
    # Return the maximum of configured delay and rate-limit-based delay
    return max(base_delay, min_delay)


def is_allowed_domain(url: str, allowed_domains: list) -> bool:
    """Check if URL domain is in the allowed domains list."""
    domain = extract_domain(url)
    return any(allowed in domain or domain in allowed for allowed in allowed_domains)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    return sanitized[:255]


def create_user_agent(service_name: str = "OpenMedia-Crawler", version: str = "1.0") -> str:
    """Create a proper user agent string."""
    return f"{service_name}/{version} (+https://github.com/openmedia/crawler)"


def parse_robots_txt(robots_content: str, user_agent: str = "*") -> Dict[str, Any]:
    """Parse robots.txt content and extract rules."""
    
    rules = {
        'allowed': [],
        'disallowed': [],
        'crawl_delay': None,
        'sitemap': []
    }
    
    current_user_agent = None
    applies_to_us = False
    
    for line in robots_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if line.lower().startswith('user-agent:'):
            current_user_agent = line.split(':', 1)[1].strip()
            applies_to_us = (current_user_agent == '*' or 
                           user_agent.lower() in current_user_agent.lower())
        
        elif applies_to_us:
            if line.lower().startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    rules['disallowed'].append(path)
            
            elif line.lower().startswith('allow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    rules['allowed'].append(path)
            
            elif line.lower().startswith('crawl-delay:'):
                try:
                    delay = float(line.split(':', 1)[1].strip())
                    rules['crawl_delay'] = delay
                except ValueError:
                    pass
        
        elif line.lower().startswith('sitemap:'):
            sitemap_url = line.split(':', 1)[1].strip()
            rules['sitemap'].append(sitemap_url)
    
    return rules


def is_robots_allowed(url: str, robots_rules: Dict[str, Any]) -> bool:
    """Check if URL is allowed according to robots.txt rules."""
    
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Check explicit allows first
    for allowed_path in robots_rules.get('allowed', []):
        if path.startswith(allowed_path):
            return True
    
    # Check disallows
    for disallowed_path in robots_rules.get('disallowed', []):
        if path.startswith(disallowed_path):
            return False
    
    # Default is allowed
    return True 