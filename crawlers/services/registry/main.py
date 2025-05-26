"""
FastAPI application for the Crawler Registry Service.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from base.interfaces import CrawlerInfo, CrawlerStatus
from base.utils import setup_logging, get_config, get_host_info
from .models import CrawlerRegistryService


# Setup logging
logger = setup_logging(service_name="crawler-registry")

# Initialize FastAPI app
app = FastAPI(
    title="Crawler Registry Service",
    description="Manages crawler instances and their assignments",
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

# Initialize registry service
config = get_config()
registry_service = CrawlerRegistryService(config)


# Pydantic models for API
class CrawlerRegistrationRequest(BaseModel):
    instance_type: str
    crawler_id: Optional[str] = None
    host_info: Optional[Dict[str, str]] = None
    version: str = "1.0.0"


class CrawlerRegistrationResponse(BaseModel):
    crawler_id: str
    status: str
    message: str


class HeartbeatRequest(BaseModel):
    metrics: Dict[str, Any]


class SiteAssignmentRequest(BaseModel):
    site_ids: List[str]


class CrawlerInfoResponse(BaseModel):
    crawler_id: str
    instance_type: str
    status: str
    assigned_sites: List[str]
    last_heartbeat: datetime
    performance_metrics: Dict[str, Any]
    host_info: Dict[str, str]
    version: str


class RegistryStatsResponse(BaseModel):
    total_crawlers: int
    active_crawlers: int
    inactive_crawlers: int
    total_assignments: int
    crawler_types: Dict[str, int]
    heartbeat_timeout: int


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("Starting Crawler Registry Service", config=config.get('service', {}))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Crawler Registry Service")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "crawler-registry",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/crawlers/register", response_model=CrawlerRegistrationResponse)
async def register_crawler(request: CrawlerRegistrationRequest):
    """Register a new crawler instance."""
    try:
        # Create crawler info
        crawler_info = CrawlerInfo(
            crawler_id=request.crawler_id,
            instance_type=request.instance_type,
            status=CrawlerStatus.IDLE,
            host_info=request.host_info or get_host_info(),
            version=request.version
        )
        
        # Register crawler
        crawler_id = registry_service.register_crawler(crawler_info)
        
        return CrawlerRegistrationResponse(
            crawler_id=crawler_id,
            status="success",
            message="Crawler registered successfully"
        )
        
    except Exception as e:
        logger.error("Failed to register crawler", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawlers/{crawler_id}/heartbeat")
async def send_heartbeat(crawler_id: str, request: HeartbeatRequest):
    """Send heartbeat for a crawler."""
    try:
        success = registry_service.heartbeat(crawler_id, request.metrics)
        
        if not success:
            raise HTTPException(status_code=404, detail="Crawler not found")
        
        return {"status": "success", "message": "Heartbeat received"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process heartbeat", crawler_id=crawler_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawlers/{crawler_id}/assign")
async def assign_sites(crawler_id: str, request: SiteAssignmentRequest):
    """Assign sites to a crawler."""
    try:
        success = registry_service.assign_sites(crawler_id, request.site_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="Crawler not found")
        
        return {
            "status": "success",
            "message": f"Assigned {len(request.site_ids)} sites to crawler"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to assign sites", crawler_id=crawler_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawlers/{crawler_id}/unassign")
async def unassign_sites(crawler_id: str, request: SiteAssignmentRequest):
    """Unassign sites from a crawler."""
    try:
        success = registry_service.unassign_sites(crawler_id, request.site_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="Crawler not found")
        
        return {
            "status": "success",
            "message": f"Unassigned {len(request.site_ids)} sites from crawler"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to unassign sites", crawler_id=crawler_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crawlers", response_model=List[CrawlerInfoResponse])
async def list_crawlers(active_only: bool = True):
    """List all crawlers."""
    try:
        if active_only:
            crawlers = registry_service.get_active_crawlers()
        else:
            # For now, we only support active crawlers
            # Could be extended to include inactive ones
            crawlers = registry_service.get_active_crawlers()
        
        return [
            CrawlerInfoResponse(
                crawler_id=crawler.crawler_id,
                instance_type=crawler.instance_type,
                status=crawler.status.value,
                assigned_sites=crawler.assigned_sites,
                last_heartbeat=crawler.last_heartbeat,
                performance_metrics=crawler.performance_metrics,
                host_info=crawler.host_info,
                version=crawler.version
            )
            for crawler in crawlers
        ]
        
    except Exception as e:
        logger.error("Failed to list crawlers", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crawlers/{crawler_id}", response_model=CrawlerInfoResponse)
async def get_crawler(crawler_id: str):
    """Get information about a specific crawler."""
    try:
        crawler = registry_service.get_crawler_info(crawler_id)
        
        if not crawler:
            raise HTTPException(status_code=404, detail="Crawler not found")
        
        return CrawlerInfoResponse(
            crawler_id=crawler.crawler_id,
            instance_type=crawler.instance_type,
            status=crawler.status.value,
            assigned_sites=crawler.assigned_sites,
            last_heartbeat=crawler.last_heartbeat,
            performance_metrics=crawler.performance_metrics,
            host_info=crawler.host_info,
            version=crawler.version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get crawler info", crawler_id=crawler_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/crawlers/{crawler_id}")
async def unregister_crawler(crawler_id: str):
    """Unregister a crawler."""
    try:
        success = registry_service.unregister_crawler(crawler_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Crawler not found")
        
        return {"status": "success", "message": "Crawler unregistered"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to unregister crawler", crawler_id=crawler_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=RegistryStatsResponse)
async def get_stats():
    """Get registry statistics."""
    try:
        stats = registry_service.get_registry_stats()
        return RegistryStatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup")
async def cleanup_inactive_crawlers(background_tasks: BackgroundTasks):
    """Cleanup inactive crawlers."""
    try:
        background_tasks.add_task(registry_service.cleanup_inactive_crawlers)
        return {"status": "success", "message": "Cleanup task scheduled"}
        
    except Exception as e:
        logger.error("Failed to schedule cleanup", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    service_config = config.get('service', {})
    uvicorn.run(
        app,
        host=service_config.get('host', '0.0.0.0'),
        port=service_config.get('port', 8080),
        log_level="info"
    ) 