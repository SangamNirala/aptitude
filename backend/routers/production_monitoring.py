"""
Production Monitoring API Router
Comprehensive endpoints for production monitoring, health checks, and system status
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel, Field

from utils.health_monitoring import (
    health_monitor, get_health_summary, run_health_check, 
    run_all_health_checks, get_system_metrics
)
from utils.error_tracking import (
    error_tracker, get_error_dashboard_data, ErrorCategory, ErrorSeverity
)
from utils.production_logging import get_performance_logger, get_security_logger
from config.production_config import get_production_config, validate_production_readiness

router = APIRouter(prefix="/api/production", tags=["Production Monitoring"])

logger = logging.getLogger(__name__)
performance_logger = get_performance_logger()
security_logger = get_security_logger()


# Response Models
class HealthCheckResponse(BaseModel):
    component: str
    status: str
    message: str
    metrics: Dict[str, Any]
    timestamp: str
    duration_ms: float
    error_details: Optional[str] = None


class SystemHealthResponse(BaseModel):
    overall_status: str
    message: str
    component_statuses: Dict[str, Dict[str, Any]]
    last_check: str
    total_components: int
    critical_count: int
    warning_count: int


class SystemMetricsResponse(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_mb: Dict[str, float]
    active_connections: int
    load_average: List[float]
    uptime_hours: float
    timestamp: str


class ErrorStatsResponse(BaseModel):
    total_unique_errors: int
    total_occurrences: int
    recent_errors_1h: int
    severity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    error_rate_1h: float


class ProductionStatusResponse(BaseModel):
    environment: str
    app_name: str
    version: str
    deployment_ready: bool
    health_status: str
    system_metrics: SystemMetricsResponse
    error_stats: ErrorStatsResponse
    uptime_hours: float
    last_updated: str


# Health Check Endpoints
@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get overall system health status"""
    try:
        health_data = await get_health_summary()
        return SystemHealthResponse(**health_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/{component}", response_model=HealthCheckResponse)
async def get_component_health(component: str):
    """Get health status for specific component"""
    try:
        check_result = await run_health_check(component)
        return HealthCheckResponse(
            component=check_result.component,
            status=check_result.status.value,
            message=check_result.message,
            metrics=check_result.metrics,
            timestamp=check_result.timestamp.isoformat(),
            duration_ms=check_result.duration_ms,
            error_details=check_result.error_details
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Component health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Component health check failed")


@router.get("/health-checks/all")
async def run_all_health_checks_endpoint():
    """Run all health checks and return results"""
    try:
        results = await run_all_health_checks()
        return [
            {
                "component": result.component,
                "status": result.status.value,
                "message": result.message,
                "metrics": result.metrics,
                "timestamp": result.timestamp.isoformat(),
                "duration_ms": result.duration_ms,
                "error_details": result.error_details
            }
            for result in results
        ]
    except Exception as e:
        logger.error(f"All health checks failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health checks failed")


# System Metrics Endpoints
@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_current_system_metrics():
    """Get current system resource metrics"""
    try:
        metrics = get_system_metrics()
        if "error" in metrics:
            raise HTTPException(status_code=503, detail=metrics["error"])
        return SystemMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"System metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="System metrics unavailable")


@router.get("/metrics/history")
async def get_system_metrics_history(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of history to retrieve")
):
    """Get system metrics history"""
    try:
        history = health_monitor.get_metrics_history(hours=hours)
        return {
            "hours": hours,
            "data_points": len(history),
            "metrics": history
        }
    except Exception as e:
        logger.error(f"Metrics history retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics history unavailable")


# Error Tracking Endpoints
@router.get("/errors/dashboard")
async def get_error_dashboard():
    """Get comprehensive error dashboard data"""
    try:
        dashboard_data = get_error_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Error dashboard retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Error dashboard unavailable")


@router.get("/errors/stats", response_model=ErrorStatsResponse)
async def get_error_statistics():
    """Get error statistics and trends"""
    try:
        dashboard_data = get_error_dashboard_data()
        stats = dashboard_data["statistics"]
        return ErrorStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error statistics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Error statistics unavailable")


@router.post("/errors/capture")
async def capture_error_manually(
    message: str,
    category: ErrorCategory = ErrorCategory.APPLICATION,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None
):
    """Manually capture an error for testing/debugging"""
    try:
        fingerprint = error_tracker.capture_message(
            message=message,
            category=category,
            severity=severity,
            context=context or {}
        )
        return {
            "success": True,
            "fingerprint": fingerprint,
            "message": "Error captured successfully"
        }
    except Exception as e:
        logger.error(f"Manual error capture failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Error capture failed")


# Configuration and Status Endpoints
@router.get("/status", response_model=ProductionStatusResponse)
async def get_production_status():
    """Get comprehensive production system status"""
    try:
        config = get_production_config()
        health_data = await get_health_summary()
        metrics = get_system_metrics()
        error_data = get_error_dashboard_data()
        
        # Check deployment readiness
        deployment_ready = validate_production_readiness()
        
        if "error" in metrics:
            # Fallback metrics if system metrics unavailable
            metrics = {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
                "network_io_mb": {"bytes_sent_mb": 0.0, "bytes_recv_mb": 0.0},
                "active_connections": 0,
                "load_average": [0.0, 0.0, 0.0],
                "uptime_hours": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return ProductionStatusResponse(
            environment=config.environment.value,
            app_name=config.app_name,
            version=config.version,
            deployment_ready=deployment_ready,
            health_status=health_data["overall_status"],
            system_metrics=SystemMetricsResponse(**metrics),
            error_stats=ErrorStatsResponse(**error_data["statistics"]),
            uptime_hours=metrics.get("uptime_hours", 0.0),
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Production status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Production status unavailable")


@router.get("/config/validation")
async def validate_configuration():
    """Validate production configuration"""
    try:
        config = get_production_config()
        is_ready = validate_production_readiness()
        
        # Get detailed validation report (would implement in production_config.py)
        validation_report = {
            "valid": is_ready,
            "environment": config.environment.value,
            "checks": {
                "database_config": bool(config.database.mongo_url),
                "logging_config": config.logging.enable_structured_logs,
                "security_config": config.security.enable_rate_limiting,
                "monitoring_config": config.monitoring.enable_health_checks,
                "ai_services": bool(config.ai_service_timeout_seconds > 0)
            }
        }
        
        return {
            "production_ready": is_ready,
            "validation_report": validation_report,
            "configuration": {
                "app_name": config.app_name,
                "version": config.version,
                "environment": config.environment.value,
                "debug_mode": config.debug_mode
            }
        }
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Configuration validation failed")


# Performance Monitoring Endpoints
@router.get("/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics from performance logger"""
    try:
        metrics = performance_logger.get_metrics()
        return {
            "performance_metrics": metrics,
            "total_endpoints": len(metrics),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Performance metrics unavailable")


@router.post("/performance/test")
async def run_performance_test():
    """Run basic performance test"""
    try:
        import time
        import asyncio
        
        # Simple performance test
        start_time = time.time()
        
        # Test database connection
        health_result = await run_health_check("database")
        
        # Test system resources
        metrics = get_system_metrics()
        
        # Test error tracking
        error_data = get_error_dashboard_data()
        
        end_time = time.time()
        test_duration_ms = (end_time - start_time) * 1000
        
        performance_logger.log_request(
            method="POST",
            endpoint="/api/production/performance/test",
            status_code=200,
            duration_ms=test_duration_ms
        )
        
        return {
            "test_completed": True,
            "duration_ms": test_duration_ms,
            "components_tested": ["database", "system_metrics", "error_tracking"],
            "database_status": health_result.status.value,
            "system_responsive": "error" not in metrics,
            "error_tracking_active": len(error_data["statistics"]) > 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Performance test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance test failed: {str(e)}")


# Alerting Endpoints
@router.get("/alerts/recent")
async def get_recent_alerts(
    limit: int = Query(default=10, ge=1, le=100, description="Number of recent alerts")
):
    """Get recent alerts"""
    try:
        error_data = get_error_dashboard_data()
        recent_alerts = error_data.get("recent_alerts", [])
        
        return {
            "alerts": recent_alerts[-limit:],
            "total_alerts": len(recent_alerts),
            "limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Recent alerts retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Recent alerts unavailable")


@router.get("/logs/summary")
async def get_logs_summary():
    """Get logging system summary"""
    try:
        config = get_production_config()
        
        # Check if log files exist
        from pathlib import Path
        log_dir = Path(config.logging.log_directory)
        
        log_files = []
        if log_dir.exists():
            log_files = [
                {
                    "name": f.name,
                    "size_mb": f.stat().st_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in log_dir.glob("*.log")
            ]
        
        return {
            "logging_enabled": config.logging.enable_structured_logs,
            "log_level": config.logging.level,
            "log_directory": config.logging.log_directory,
            "log_files": log_files,
            "total_log_files": len(log_files),
            "total_size_mb": sum(lf["size_mb"] for lf in log_files)
        }
    except Exception as e:
        logger.error(f"Logs summary retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Logs summary unavailable")


# Initialize production monitoring services
async def initialize_production_monitoring():
    """Initialize production monitoring services"""
    try:
        # Setup health monitoring
        await health_monitor.start_monitoring()
        
        # Setup error tracking
        error_tracker.install_global_handler()
        
        logger.info("✅ Production monitoring services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Production monitoring initialization failed: {str(e)}")
        raise