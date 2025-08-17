"""
Real-Time Monitoring Dashboard API Router
Provides API endpoints for the monitoring dashboard with WebSocket support
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Path, Depends
from fastapi import status
from pydantic import BaseModel, Field
from enum import Enum
import json
import asyncio

# Import monitoring services
from services.monitoring_service import (
    MonitoringService, MonitoringEvent, MonitoringEventType, 
    SystemHealthStatus, get_monitoring_service, initialize_monitoring_service
)
from utils.alerts_manager import (
    AlertsManager, Alert, AlertSeverity, AlertCategory, AlertStatus,
    get_alerts_manager, initialize_alerts_manager
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/monitoring", tags=["Monitoring Dashboard"])

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class MonitoringStatusResponse(BaseModel):
    """Monitoring system status response"""
    status: str
    uptime_hours: float
    active_connections: int
    events_processed: int
    alerts_active: int
    timestamp: datetime

class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_bytes_sent: float = 0
    network_bytes_recv: float = 0
    active_jobs: int = 0
    job_queue_length: int = 0

class AlertCreateRequest(BaseModel):
    """Request model for creating alerts"""
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description") 
    severity: AlertSeverity = Field(..., description="Alert severity")
    category: AlertCategory = Field(..., description="Alert category")
    source: str = Field(..., description="Alert source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Alert tags")

class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    title: str
    description: str
    severity: str
    category: str
    status: str
    source: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = {}
    tags: List[str] = []

class AlertActionRequest(BaseModel):
    """Request model for alert actions"""
    action_by: str = Field(..., description="Who is performing the action")
    comment: str = Field("", description="Optional comment")

class DashboardDataResponse(BaseModel):
    """Dashboard data response"""
    system_health: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]
    alert_statistics: Dict[str, Any]
    timestamp: datetime

class MetricHistoryResponse(BaseModel):
    """Metric history response"""
    metric_name: str
    data_points: List[Dict[str, Any]]
    period_hours: int
    timestamp: datetime

# =============================================================================
# SERVICE INITIALIZATION
# =============================================================================

# Global service instances
monitoring_service: Optional[MonitoringService] = None
alerts_manager: Optional[AlertsManager] = None

async def get_monitoring_service_instance():
    """Dependency to get monitoring service"""
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = get_monitoring_service()
    if monitoring_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring service not available"
        )
    return monitoring_service

async def get_alerts_manager_instance():
    """Dependency to get alerts manager"""
    global alerts_manager
    if alerts_manager is None:
        alerts_manager = get_alerts_manager()
    if alerts_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alerts manager not available"
        )
    return alerts_manager

# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring data streaming
    
    Provides real-time updates for:
    - System health status
    - Performance metrics
    - Alert notifications
    - Job status changes
    - System events
    """
    try:
        await websocket.accept()
        logger.info("WebSocket connection established")
        
        # Get monitoring service
        monitoring_service = get_monitoring_service()
        if not monitoring_service:
            await websocket.close(code=1011, reason="Monitoring service not available")
            return
        
        # Connect to monitoring service
        await monitoring_service.connect_websocket(websocket)
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client (if any)
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    
                    # Handle client requests
                    try:
                        message = json.loads(data)
                        await handle_websocket_message(websocket, message, monitoring_service)
                    except json.JSONDecodeError:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }))
                
                except asyncio.TimeoutError:
                    # No message received, continue to keep connection alive
                    continue
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
        finally:
            # Disconnect from monitoring service
            await monitoring_service.disconnect_websocket(websocket)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")

async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any], monitoring_service: MonitoringService):
    """Handle incoming WebSocket messages"""
    try:
        message_type = message.get("type")
        
        if message_type == "get_health":
            # Send current health status
            health = await monitoring_service.get_system_health()
            await websocket.send_text(json.dumps({
                "type": "system_health",
                "data": health.to_dict()
            }))
        
        elif message_type == "get_alerts":
            # Send current active alerts
            alerts_mgr = get_alerts_manager()
            if alerts_mgr:
                alerts = alerts_mgr.get_active_alerts()
                await websocket.send_text(json.dumps({
                    "type": "active_alerts",
                    "data": [alert.to_dict() for alert in alerts]
                }))
        
        elif message_type == "ping":
            # Respond to ping
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Internal server error"
        }))

# =============================================================================
# SYSTEM STATUS ENDPOINTS
# =============================================================================

@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    service: MonitoringService = Depends(get_monitoring_service_instance)
):
    """
    Get current monitoring system status
    
    Returns overall status of the monitoring system including uptime,
    active connections, processed events, and active alerts.
    """
    try:
        logger.info("Getting monitoring system status")
        
        alerts_mgr = get_alerts_manager()
        
        # Calculate uptime
        uptime_hours = (datetime.utcnow() - service.start_time).total_seconds() / 3600
        
        return MonitoringStatusResponse(
            status="healthy" if service.is_running else "stopped",
            uptime_hours=uptime_hours,
            active_connections=len(service.streamer.active_connections),
            events_processed=len(service.event_history),
            alerts_active=len(alerts_mgr.active_alerts) if alerts_mgr else 0,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve monitoring status: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    service: MonitoringService = Depends(get_monitoring_service_instance)
):
    """
    Get comprehensive system health status
    
    Returns detailed health information including system resources,
    service status, and performance indicators.
    """
    try:
        logger.info("Getting system health status")
        
        health = await service.get_system_health()
        return health.to_dict()
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system health: {str(e)}"
        )

@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    service: MonitoringService = Depends(get_monitoring_service_instance)
):
    """
    Get current performance metrics
    
    Returns current system performance metrics including CPU, memory,
    disk usage, and job statistics.
    """
    try:
        logger.info("Getting performance metrics")
        
        # Get system health for resource metrics
        health = await service.get_system_health()
        
        return PerformanceMetricsResponse(
            timestamp=datetime.utcnow(),
            cpu_usage=health.cpu_usage,
            memory_usage=health.memory_usage,
            disk_usage=health.disk_usage,
            network_bytes_sent=0,  # Would be populated from metrics
            network_bytes_recv=0,
            active_jobs=health.active_jobs,
            job_queue_length=0  # Would be populated from job manager
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

# =============================================================================
# ALERT MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    category: Optional[AlertCategory] = Query(None, description="Filter by category"),
    status_filter: Optional[AlertStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    alerts_mgr: AlertsManager = Depends(get_alerts_manager_instance)
):
    """
    List alerts with optional filtering
    
    Returns a list of alerts with optional filtering by severity, category, or status.
    """
    try:
        logger.info(f"Listing alerts (severity={severity}, category={category}, status={status_filter})")
        
        # Get alerts based on status filter
        if status_filter == AlertStatus.ACTIVE:
            alerts = alerts_mgr.get_active_alerts(severity, category)
        else:
            # For now, only support active alerts
            # In a full implementation, you'd query historical data
            alerts = alerts_mgr.get_active_alerts(severity, category)
            
            if status_filter:
                alerts = [a for a in alerts if a.status == status_filter]
        
        alerts = alerts[:limit]
        
        return [AlertResponse(**alert.to_dict()) for alert in alerts]
        
    except Exception as e:
        logger.error(f"Error listing alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )

@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    request: AlertCreateRequest,
    alerts_mgr: AlertsManager = Depends(get_alerts_manager_instance)
):
    """
    Create a new alert
    
    Creates a new alert with the specified parameters and triggers
    notifications based on configured rules.
    """
    try:
        logger.info(f"Creating alert: {request.title}")
        
        alert = await alerts_mgr.create_alert(
            title=request.title,
            description=request.description,
            severity=request.severity,
            category=request.category,
            source=request.source,
            metadata=request.metadata,
            tags=request.tags
        )
        
        return AlertResponse(**alert.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )

@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert ID"),
    request: AlertActionRequest = None,
    alerts_mgr: AlertsManager = Depends(get_alerts_manager_instance)
):
    """
    Acknowledge an alert
    
    Marks an alert as acknowledged, indicating that someone is aware of
    and working on the issue.
    """
    try:
        logger.info(f"Acknowledging alert {alert_id}")
        
        action_by = request.action_by if request else "api_user"
        
        success = await alerts_mgr.acknowledge_alert(alert_id, action_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found or cannot be acknowledged"
            )
        
        # Get updated alert
        alert = alerts_mgr.active_alerts.get(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found after acknowledgment"
            )
        
        return AlertResponse(**alert.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )

@router.put("/alerts/{alert_id}/resolve", response_model=Dict[str, str])
async def resolve_alert(
    alert_id: str = Path(..., description="Alert ID"),
    request: AlertActionRequest = None,
    alerts_mgr: AlertsManager = Depends(get_alerts_manager_instance)
):
    """
    Resolve an alert
    
    Marks an alert as resolved, indicating that the underlying issue
    has been fixed.
    """
    try:
        logger.info(f"Resolving alert {alert_id}")
        
        action_by = request.action_by if request else "api_user"
        
        success = await alerts_mgr.resolve_alert(alert_id, action_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found or cannot be resolved"
            )
        
        return {"message": f"Alert {alert_id} resolved successfully", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}"
        )

@router.get("/alerts/statistics", response_model=Dict[str, Any])
async def get_alert_statistics(
    alerts_mgr: AlertsManager = Depends(get_alerts_manager_instance)
):
    """
    Get alert statistics
    
    Returns comprehensive statistics about alerts including counts by
    severity, category, and recent activity.
    """
    try:
        logger.info("Getting alert statistics")
        
        return alerts_mgr.get_alert_statistics()
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert statistics: {str(e)}"
        )

# =============================================================================
# EVENT AND METRICS ENDPOINTS
# =============================================================================

@router.get("/events", response_model=List[Dict[str, Any]])
async def get_recent_events(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    event_type: Optional[MonitoringEventType] = Query(None, description="Filter by event type"),
    service: MonitoringService = Depends(get_monitoring_service_instance)
):
    """
    Get recent monitoring events
    
    Returns a list of recent monitoring events with optional filtering by type.
    """
    try:
        logger.info(f"Getting recent events (limit={limit}, type={event_type})")
        
        events = await service.get_recent_events(limit, event_type)
        return events
        
    except Exception as e:
        logger.error(f"Error getting recent events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}"
        )

@router.get("/metrics/{metric_name}/history", response_model=MetricHistoryResponse)
async def get_metric_history(
    metric_name: str = Path(..., description="Metric name"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours of history"),
    service: MonitoringService = Depends(get_monitoring_service_instance)
):
    """
    Get historical data for a specific metric
    
    Returns time-series data for the specified metric over the requested time period.
    """
    try:
        logger.info(f"Getting metric history for {metric_name} ({hours} hours)")
        
        metrics = await service.get_historical_metrics(metric_name, hours)
        
        return MetricHistoryResponse(
            metric_name=metric_name,
            data_points=metrics,
            period_hours=hours,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting metric history for {metric_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metric history: {str(e)}"
        )

@router.get("/dashboard", response_model=DashboardDataResponse)
async def get_dashboard_data(
    service: MonitoringService = Depends(get_monitoring_service_instance)
):
    """
    Get comprehensive dashboard data
    
    Returns all data needed for the monitoring dashboard in a single request,
    including system health, performance metrics, alerts, and recent events.
    """
    try:
        logger.info("Getting dashboard data")
        
        # Get system health
        health = await service.get_system_health()
        
        # Get performance metrics
        performance = await service.get_performance_summary()
        
        # Get active alerts
        alerts_mgr = get_alerts_manager()
        alerts = []
        alert_stats = {}
        if alerts_mgr:
            active_alerts = alerts_mgr.get_active_alerts()
            alerts = [alert.to_dict() for alert in active_alerts]
            alert_stats = alerts_mgr.get_alert_statistics()
        
        # Get recent events
        events = await service.get_recent_events(50)
        
        return DashboardDataResponse(
            system_health=health.to_dict(),
            performance_metrics=performance,
            active_alerts=alerts,
            recent_events=events,
            alert_statistics=alert_stats,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

# =============================================================================
# SERVICE INITIALIZATION
# =============================================================================

async def initialize_monitoring_services():
    """Initialize monitoring services"""
    global monitoring_service, alerts_manager
    
    try:
        logger.info("Initializing monitoring services")
        
        # Initialize alerts manager first
        alerts_manager = await initialize_alerts_manager()
        
        # Try to get references to other services (job_manager, source_manager)
        job_manager = None
        source_manager = None
        
        try:
            from routers.scraping_management import job_manager as jm
            job_manager = jm
        except Exception as e:
            logger.warning(f"Could not get job manager reference: {str(e)}")
        
        try:
            from routers.scraping_management import source_manager as sm  
            source_manager = sm
        except Exception as e:
            logger.warning(f"Could not get source manager reference: {str(e)}")
        
        # Initialize monitoring service
        monitoring_service = await initialize_monitoring_service(
            job_manager=job_manager,
            source_manager=source_manager, 
            alerts_manager=alerts_manager
        )
        
        logger.info("✅ Monitoring services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize monitoring services: {str(e)}")
        raise

# =============================================================================
# STARTUP EVENT HANDLER
# =============================================================================

@router.on_event("startup") 
async def startup_monitoring_dashboard():
    """Initialize monitoring dashboard services on startup"""
    try:
        await initialize_monitoring_services()
    except Exception as e:
        logger.error(f"Failed to initialize monitoring dashboard services: {str(e)}")

logger.info("✅ Monitoring Dashboard API endpoints loaded successfully")