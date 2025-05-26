"""
FastAPI application for the URL Scheduler Service.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from base.interfaces import CrawlRequest
from base.utils import setup_logging, get_config
from .models import URLSchedulerService


# Setup logging
logger = setup_logging(service_name="url-scheduler")

# Initialize FastAPI app
app = FastAPI(
    title="URL Scheduler Service",
    description="Manages URL frontier and scheduling",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scheduler service
config = get_config()
scheduler = URLSchedulerService(config)


# Pydantic models for API
class URLRequest(BaseModel):
    url: str
    priority: int = 1
    metadata: Dict[str, Any] = {}


class URLBatchRequest(BaseModel):
    urls: List[str]
    priority: int = 1


class CrawlRequestResponse(BaseModel):
    url: str
    priority: int
    metadata: Dict[str, Any]
    retry_count: int
    max_retries: int
    crawl_delay: float
    site_id: Optional[str]
    created_at: datetime


class URLStatusRequest(BaseModel):
    url: str
    success: bool
    error_message: Optional[str] = None


class SchedulerStatsResponse(BaseModel):
    queue_size: int
    in_progress_count: int
    failed_count: int
    priority_distribution: Dict[str, int]
    operational_stats: Dict[str, int]
    dedup_window_hours: float


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("Starting URL Scheduler Service", config=config.get('service', {}))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down URL Scheduler Service")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "url-scheduler",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/urls")
async def add_url(request: URLRequest):
    """Add a single URL to the frontier."""
    try:
        success = scheduler.add_url(
            url=request.url,
            priority=request.priority,
            metadata=request.metadata
        )
        
        if not success:
            return {"status": "skipped", "message": "URL already visited or queued"}
        
        return {"status": "success", "message": "URL added to queue"}
        
    except Exception as e:
        logger.error("Failed to add URL", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/urls/batch")
async def add_urls_batch(request: URLBatchRequest):
    """Add multiple URLs to the frontier."""
    try:
        added_count = scheduler.add_urls(
            urls=request.urls,
            priority=request.priority
        )
        
        return {
            "status": "success",
            "message": f"Added {added_count} out of {len(request.urls)} URLs",
            "added_count": added_count,
            "total_count": len(request.urls)
        }
        
    except Exception as e:
        logger.error("Failed to add URLs batch", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/urls/next/{crawler_id}", response_model=Optional[CrawlRequestResponse])
async def get_next_url(crawler_id: str):
    """Get next URL for crawling."""
    try:
        request = scheduler.get_next_url(crawler_id)
        
        if not request:
            return None
        
        return CrawlRequestResponse(
            url=request.url,
            priority=request.priority,
            metadata=request.metadata,
            retry_count=request.retry_count,
            max_retries=request.max_retries,
            crawl_delay=request.crawl_delay,
            site_id=request.site_id,
            created_at=request.created_at
        )
        
    except Exception as e:
        logger.error("Failed to get next URL", crawler_id=crawler_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/urls/complete")
async def mark_url_completed(request: URLStatusRequest):
    """Mark URL as completed."""
    try:
        if request.success:
            success = scheduler.mark_completed(request.url, True)
        else:
            success = scheduler.mark_failed(request.url, request.error_message or "Unknown error")
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update URL status")
        
        return {"status": "success", "message": "URL status updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark URL completed", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/urls/failed")
async def mark_url_failed(url: str, error_message: str):
    """Mark URL as failed."""
    try:
        success = scheduler.mark_failed(url, error_message)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to mark URL as failed")
        
        return {"status": "success", "message": "URL marked as failed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark URL as failed", url=url, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/urls/visited/{url:path}")
async def check_url_visited(url: str):
    """Check if URL has been visited."""
    try:
        visited = scheduler.is_visited(url)
        return {"url": url, "visited": visited}
        
    except Exception as e:
        logger.error("Failed to check if URL is visited", url=url, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/size")
async def get_queue_size(priority: Optional[int] = None):
    """Get current queue size."""
    try:
        size = scheduler.get_queue_size(priority)
        return {"queue_size": size, "priority": priority}
        
    except Exception as e:
        logger.error("Failed to get queue size", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=SchedulerStatsResponse)
async def get_stats():
    """Get scheduler statistics."""
    try:
        stats = scheduler.get_stats()
        return SchedulerStatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup")
async def cleanup_expired(background_tasks: BackgroundTasks):
    """Cleanup expired URLs."""
    try:
        background_tasks.add_task(scheduler.cleanup_expired)
        return {"status": "success", "message": "Cleanup task scheduled"}
        
    except Exception as e:
        logger.error("Failed to schedule cleanup", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seed")
async def seed_urls(site_id: str, base_urls: List[str], priority: int = 1):
    """Seed the frontier with base URLs for a site."""
    try:
        # Add metadata to identify the site
        metadata = {"site_id": site_id, "is_seed": True}
        
        added_count = 0
        for url in base_urls:
            if scheduler.add_url(url, priority, metadata):
                added_count += 1
        
        return {
            "status": "success",
            "message": f"Seeded {added_count} URLs for site {site_id}",
            "site_id": site_id,
            "added_count": added_count,
            "total_count": len(base_urls)
        }
        
    except Exception as e:
        logger.error("Failed to seed URLs", site_id=site_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/peek")
async def peek_queue(limit: int = 10):
    """Peek at the top URLs in the queue without removing them."""
    try:
        # This is a debug endpoint to see what's in the queue
        items = scheduler.redis_client.zrevrange(
            scheduler.queue_key, 0, limit - 1, withscores=True
        )
        
        queue_items = []
        for item_json, score in items:
            try:
                import json
                item_data = json.loads(item_json)
                queue_items.append({
                    "url": item_data.get("url"),
                    "priority": item_data.get("priority"),
                    "score": score,
                    "retry_count": item_data.get("retry_count", 0),
                    "created_at": item_data.get("created_at")
                })
            except:
                continue
        
        return {
            "queue_items": queue_items,
            "total_queue_size": scheduler.get_queue_size()
        }
        
    except Exception as e:
        logger.error("Failed to peek queue", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    service_config = config.get('service', {})
    uvicorn.run(
        app,
        host=service_config.get('host', '0.0.0.0'),
        port=service_config.get('port', 8082),
        log_level="info"
    ) 