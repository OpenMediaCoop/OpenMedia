"""
FastAPI application for the Monitoring Service.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from prometheus_client import CONTENT_TYPE_LATEST

from base.utils import setup_logging, get_config
from .models import MonitoringService


# Setup logging
logger = setup_logging(service_name="monitoring")

# Initialize FastAPI app
app = FastAPI(
    title="Monitoring Service",
    description="Collects metrics and health status from all crawler components",
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

# Initialize monitoring service
config = get_config()
monitoring = MonitoringService(config)


# Pydantic models for API
class AlertRequest(BaseModel):
    alert_type: str
    message: str
    severity: str = "warning"


class AlertResponse(BaseModel):
    id: str
    type: str
    message: str
    severity: str
    timestamp: datetime
    acknowledged: bool


class HealthResponse(BaseModel):
    timestamp: datetime
    overall_status: str
    services: Dict[str, Dict[str, Any]]


class DashboardResponse(BaseModel):
    metrics: Dict[str, Any]
    health: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    summary: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("Starting Monitoring Service", config=config.get('service', {}))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Monitoring Service")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics/collect")
async def collect_metrics():
    """Manually trigger metrics collection."""
    try:
        metrics = monitoring.collect_all_metrics()
        return {"status": "success", "metrics": metrics}
        
    except Exception as e:
        logger.error("Failed to collect metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/historical")
async def get_historical_metrics(hours: int = 24):
    """Get historical metrics."""
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        metrics = monitoring.get_historical_metrics(hours)
        return {"metrics": metrics, "hours": hours}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get historical metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/services", response_model=HealthResponse)
async def check_services_health():
    """Check health of all services."""
    try:
        health_status = monitoring.check_service_health()
        return HealthResponse(**health_status)
        
    except Exception as e:
        logger.error("Failed to check services health", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """Get all active alerts."""
    try:
        alerts = monitoring.get_active_alerts()
        return [AlertResponse(**alert) for alert in alerts]
        
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts")
async def create_alert(request: AlertRequest):
    """Create a new alert."""
    try:
        monitoring.create_alert(
            alert_type=request.alert_type,
            message=request.message,
            severity=request.severity
        )
        
        return {"status": "success", "message": "Alert created"}
        
    except Exception as e:
        logger.error("Failed to create alert", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    try:
        success = monitoring.acknowledge_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "success", "message": "Alert acknowledged"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to acknowledge alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data():
    """Get comprehensive dashboard data."""
    try:
        dashboard_data = monitoring.get_dashboard_data()
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus metrics."""
    try:
        metrics = monitoring.get_prometheus_metrics()
        return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        logger.error("Failed to get Prometheus metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/metrics/auto-collect")
async def start_auto_collection(background_tasks: BackgroundTasks, interval_minutes: int = 5):
    """Start automatic metrics collection."""
    try:
        if interval_minutes < 1 or interval_minutes > 60:
            raise HTTPException(status_code=400, detail="Interval must be between 1 and 60 minutes")
        
        # This would typically be handled by a scheduler like Celery
        # For now, we'll just trigger a single collection
        background_tasks.add_task(monitoring.collect_all_metrics)
        
        return {
            "status": "success",
            "message": f"Auto-collection started with {interval_minutes} minute interval"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start auto collection", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/summary")
async def get_summary_stats():
    """Get summary statistics."""
    try:
        dashboard_data = monitoring.get_dashboard_data()
        summary = dashboard_data.get('summary', {})
        
        return {
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get summary stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_overall_status():
    """Get overall system status."""
    try:
        health_status = monitoring.check_service_health()
        active_alerts = monitoring.get_active_alerts()
        
        # Count alerts by severity
        alert_counts = {"critical": 0, "warning": 0, "info": 0}
        for alert in active_alerts:
            severity = alert.get('severity', 'info')
            alert_counts[severity] = alert_counts.get(severity, 0) + 1
        
        return {
            "overall_status": health_status.get('overall_status', 'unknown'),
            "services_status": health_status.get('services', {}),
            "active_alerts_count": len(active_alerts),
            "alerts_by_severity": alert_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get overall status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Background task to periodically collect metrics
@app.on_event("startup")
async def setup_periodic_tasks():
    """Setup periodic tasks."""
    # In a production environment, you would use Celery or similar
    # for periodic tasks. For now, this is just a placeholder.
    logger.info("Periodic tasks setup completed")


if __name__ == "__main__":
    import uvicorn
    
    service_config = config.get('service', {})
    uvicorn.run(
        app,
        host=service_config.get('host', '0.0.0.0'),
        port=service_config.get('port', 8083),
        log_level="info"
    ) 