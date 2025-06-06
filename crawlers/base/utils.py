"""
Essential utility functions for the News Monitor.
"""

import os
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Dict, Any, Optional

def get_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    
    return {
        'kafka': {
            'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'enabled': os.getenv('KAFKA_ENABLED', 'true').lower() == 'true',
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
        },
        'monitor': {
            'interval': int(os.getenv('MONITOR_INTERVAL', '60')),
            'request_delay': float(os.getenv('REQUEST_DELAY', '1.0')),
        }
    }


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """Normalize URL by removing fragments and making it absolute."""
    
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