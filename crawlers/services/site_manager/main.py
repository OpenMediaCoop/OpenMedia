"""
FastAPI application for the Site Manager Service.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog

from base.interfaces import SiteConfig
from base.utils import setup_logging, get_config
from .models import SiteManagerService


# Setup logging
logger = setup_logging(service_name="site-manager")

# Initialize FastAPI app
app = FastAPI(
    title="Site Manager Service",
    description="Handles site configurations and policies",
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

# Initialize site manager service
config = get_config()
site_manager = SiteManagerService(config)


# Pydantic models for API
class SiteConfigRequest(BaseModel):
    domain: str
    name: str
    base_urls: List[str]
    allowed_domains: List[str]
    crawl_delay: float = 1.0
    concurrent_requests: int = 1
    user_agent: str = "OpenMedia-Crawler/1.0"
    respect_robots_txt: bool = True
    custom_headers: Dict[str, str] = {}
    selectors: Dict[str, str] = {}
    rate_limit: int = 60
    priority: int = 1
    enabled: bool = True


class SiteConfigResponse(BaseModel):
    site_id: str
    domain: str
    name: str
    base_urls: List[str]
    allowed_domains: List[str]
    crawl_delay: float
    concurrent_requests: int
    user_agent: str
    respect_robots_txt: bool
    custom_headers: Dict[str, str]
    selectors: Dict[str, str]
    rate_limit: int
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class SiteRegistrationResponse(BaseModel):
    site_id: str
    status: str
    message: str


class SitesStatsResponse(BaseModel):
    total_sites: int
    enabled_sites: int
    disabled_sites: int
    priority_distribution: Dict[str, int]
    domain_distribution: Dict[str, int]
    operational_stats: Dict[str, int]


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("Starting Site Manager Service", config=config.get('service', {}))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Site Manager Service")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "site-manager",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/sites", response_model=SiteRegistrationResponse)
async def register_site(request: SiteConfigRequest):
    """Register a new site configuration."""
    try:
        # Create site config
        site_config = SiteConfig(
            domain=request.domain,
            name=request.name,
            base_urls=request.base_urls,
            allowed_domains=request.allowed_domains,
            crawl_delay=request.crawl_delay,
            concurrent_requests=request.concurrent_requests,
            user_agent=request.user_agent,
            respect_robots_txt=request.respect_robots_txt,
            custom_headers=request.custom_headers,
            selectors=request.selectors,
            rate_limit=request.rate_limit,
            priority=request.priority,
            enabled=request.enabled
        )
        
        # Register site
        site_id = site_manager.register_site(site_config)
        
        return SiteRegistrationResponse(
            site_id=site_id,
            status="success",
            message="Site registered successfully"
        )
        
    except ValueError as e:
        logger.warning("Invalid site configuration", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to register site", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sites/bulk", response_model=List[SiteRegistrationResponse])
async def register_sites_bulk(file: UploadFile = File(...)):
    """Register multiple sites from JSON file."""
    try:
        # Read and parse file
        content = await file.read()
        data = json.loads(content)
        
        results = []
        sites_data = data.get('sites', [])
        
        for site_data in sites_data:
            try:
                # Create site config
                site_config = SiteConfig(
                    domain=site_data['domain'],
                    name=site_data['name'],
                    base_urls=site_data['base_urls'],
                    allowed_domains=site_data['allowed_domains'],
                    crawl_delay=site_data.get('crawl_delay', 1.0),
                    concurrent_requests=site_data.get('concurrent_requests', 1),
                    user_agent=site_data.get('user_agent', 'OpenMedia-Crawler/1.0'),
                    respect_robots_txt=site_data.get('respect_robots_txt', True),
                    custom_headers=site_data.get('custom_headers', {}),
                    selectors=site_data.get('selectors', {}),
                    rate_limit=site_data.get('rate_limit', 60),
                    priority=site_data.get('priority', 1),
                    enabled=site_data.get('enabled', True)
                )
                
                # Register site
                site_id = site_manager.register_site(site_config)
                
                results.append(SiteRegistrationResponse(
                    site_id=site_id,
                    status="success",
                    message=f"Site {site_data['name']} registered successfully"
                ))
                
            except Exception as e:
                results.append(SiteRegistrationResponse(
                    site_id="",
                    status="error",
                    message=f"Failed to register {site_data.get('name', 'unknown')}: {str(e)}"
                ))
        
        return results
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error("Failed to process bulk registration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sites", response_model=List[SiteConfigResponse])
async def list_sites(enabled_only: bool = True):
    """List all registered sites."""
    try:
        sites = site_manager.list_sites(enabled_only=enabled_only)
        
        return [
            SiteConfigResponse(
                site_id=site.site_id,
                domain=site.domain,
                name=site.name,
                base_urls=site.base_urls,
                allowed_domains=site.allowed_domains,
                crawl_delay=site.crawl_delay,
                concurrent_requests=site.concurrent_requests,
                user_agent=site.user_agent,
                respect_robots_txt=site.respect_robots_txt,
                custom_headers=site.custom_headers,
                selectors=site.selectors,
                rate_limit=site.rate_limit,
                priority=site.priority,
                enabled=site.enabled,
                created_at=site.created_at,
                updated_at=site.updated_at
            )
            for site in sites
        ]
        
    except Exception as e:
        logger.error("Failed to list sites", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sites/{site_id}", response_model=SiteConfigResponse)
async def get_site(site_id: str):
    """Get site configuration by ID."""
    try:
        site = site_manager.get_site_config(site_id)
        
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return SiteConfigResponse(
            site_id=site.site_id,
            domain=site.domain,
            name=site.name,
            base_urls=site.base_urls,
            allowed_domains=site.allowed_domains,
            crawl_delay=site.crawl_delay,
            concurrent_requests=site.concurrent_requests,
            user_agent=site.user_agent,
            respect_robots_txt=site.respect_robots_txt,
            custom_headers=site.custom_headers,
            selectors=site.selectors,
            rate_limit=site.rate_limit,
            priority=site.priority,
            enabled=site.enabled,
            created_at=site.created_at,
            updated_at=site.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get site", site_id=site_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sites/domain/{domain}", response_model=SiteConfigResponse)
async def get_site_by_domain(domain: str):
    """Get site configuration by domain."""
    try:
        site = site_manager.get_site_by_domain(domain)
        
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return SiteConfigResponse(
            site_id=site.site_id,
            domain=site.domain,
            name=site.name,
            base_urls=site.base_urls,
            allowed_domains=site.allowed_domains,
            crawl_delay=site.crawl_delay,
            concurrent_requests=site.concurrent_requests,
            user_agent=site.user_agent,
            respect_robots_txt=site.respect_robots_txt,
            custom_headers=site.custom_headers,
            selectors=site.selectors,
            rate_limit=site.rate_limit,
            priority=site.priority,
            enabled=site.enabled,
            created_at=site.created_at,
            updated_at=site.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get site by domain", domain=domain, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/sites/{site_id}", response_model=SiteConfigResponse)
async def update_site(site_id: str, request: SiteConfigRequest):
    """Update site configuration."""
    try:
        # Create updated site config
        site_config = SiteConfig(
            domain=request.domain,
            name=request.name,
            base_urls=request.base_urls,
            allowed_domains=request.allowed_domains,
            crawl_delay=request.crawl_delay,
            concurrent_requests=request.concurrent_requests,
            user_agent=request.user_agent,
            respect_robots_txt=request.respect_robots_txt,
            custom_headers=request.custom_headers,
            selectors=request.selectors,
            rate_limit=request.rate_limit,
            priority=request.priority,
            enabled=request.enabled
        )
        
        # Update site
        success = site_manager.update_site(site_id, site_config)
        
        if not success:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Return updated site
        updated_site = site_manager.get_site_config(site_id)
        return SiteConfigResponse(
            site_id=updated_site.site_id,
            domain=updated_site.domain,
            name=updated_site.name,
            base_urls=updated_site.base_urls,
            allowed_domains=updated_site.allowed_domains,
            crawl_delay=updated_site.crawl_delay,
            concurrent_requests=updated_site.concurrent_requests,
            user_agent=updated_site.user_agent,
            respect_robots_txt=updated_site.respect_robots_txt,
            custom_headers=updated_site.custom_headers,
            selectors=updated_site.selectors,
            rate_limit=updated_site.rate_limit,
            priority=updated_site.priority,
            enabled=updated_site.enabled,
            created_at=updated_site.created_at,
            updated_at=updated_site.updated_at
        )
        
    except ValueError as e:
        logger.warning("Invalid site configuration", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update site", site_id=site_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sites/{site_id}/enable")
async def enable_site(site_id: str):
    """Enable a site."""
    try:
        success = site_manager.enable_site(site_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return {"status": "success", "message": "Site enabled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to enable site", site_id=site_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sites/{site_id}/disable")
async def disable_site(site_id: str):
    """Disable a site."""
    try:
        success = site_manager.disable_site(site_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return {"status": "success", "message": "Site disabled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to disable site", site_id=site_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sites/{site_id}")
async def delete_site(site_id: str):
    """Delete a site configuration."""
    try:
        success = site_manager.delete_site(site_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return {"status": "success", "message": "Site deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete site", site_id=site_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=SitesStatsResponse)
async def get_stats():
    """Get sites statistics."""
    try:
        stats = site_manager.get_sites_stats()
        return SitesStatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    service_config = config.get('service', {})
    uvicorn.run(
        app,
        host=service_config.get('host', '0.0.0.0'),
        port=service_config.get('port', 8081),
        log_level="info"
    ) 