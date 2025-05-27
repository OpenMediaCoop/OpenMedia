"""
Setup and configuration for Logger
"""

import logging
import structlog

def setup_logging(level: str = "INFO", service_name: str = "news-monitor") -> None:
    """Setup simple structured logging."""
    
    # Configure structlog for simple, readable output
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer()
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

# Setup logging globally
setup_logging(service_name="news-monitor")
logger = structlog.get_logger("news-monitor")