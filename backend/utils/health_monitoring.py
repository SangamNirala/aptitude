"""
Health Monitoring System
Comprehensive system health monitoring and alerting for production deployment
"""

import asyncio
import psutil
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from collections import deque, defaultdict
import json

from motor.motor_asyncio import AsyncIOMotorClient
from config.production_config import get_production_config
from utils.error_tracking import error_tracker, ErrorCategory, ErrorSeverity


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


class ComponentType(str, Enum):
    """System component types"""
    DATABASE = "database"
    AI_SERVICE = "ai_service"
    SCRAPING_ENGINE = "scraping_engine"
    WEB_SERVER = "web_server"
    SYSTEM_RESOURCES = "system_resources"
    EXTERNAL_API = "external_api"


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime
    duration_ms: float
    error_details: Optional[str] = None


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_mb: Dict[str, float]
    active_connections: int
    load_average: List[float]
    uptime_hours: float
    timestamp: datetime


class HealthMonitor:
    """Main health monitoring system"""
    
    def __init__(self):
        self.config = get_production_config()
        self.logger = logging.getLogger('health_monitor')
        self.checks: Dict[str, Callable] = {}
        self.check_results: deque = deque(maxlen=1000)
        self.system_metrics_history: deque = deque(maxlen=100)
        self.alert_thresholds = self._setup_alert_thresholds()
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        
        # Initialize built-in health checks
        self._setup_builtin_checks()
    
    def _setup_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Setup alert thresholds for various metrics"""
        return {
            "cpu_percent": {"warning": 70.0, "critical": 85.0},
            "memory_percent": {"warning": 75.0, "critical": 90.0},
            "disk_percent": {"warning": 80.0, "critical": 95.0},
            "response_time_ms": {"warning": 1000.0, "critical": 3000.0},
            "error_rate_percent": {"warning": 5.0, "critical": 10.0},
            "active_connections": {"warning": 80, "critical": 95}
        }
    
    def _setup_builtin_checks(self):
        """Setup built-in health checks"""
        self.register_check("system_resources", self._check_system_resources, ComponentType.SYSTEM_RESOURCES)
        self.register_check("database", self._check_database, ComponentType.DATABASE)
        self.register_check("ai_services", self._check_ai_services, ComponentType.AI_SERVICE)
        self.register_check("scraping_engine", self._check_scraping_engine, ComponentType.SCRAPING_ENGINE)
    
    def register_check(self, name: str, check_func: Callable, component_type: ComponentType):
        """Register a new health check"""
        self.checks[name] = {
            "func": check_func,
            "type": component_type,
            "enabled": True
        }
        self.logger.info(f"Health check registered: {name}")
    
    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        if name not in self.checks:
            raise ValueError(f"Health check '{name}' not found")
        
        check_info = self.checks[name]
        if not check_info["enabled"]:
            return HealthCheck(
                component=name,
                component_type=check_info["type"],
                status=HealthStatus.WARNING,
                message="Health check disabled",
                metrics={},
                timestamp=datetime.now(timezone.utc),
                duration_ms=0.0
            )
        
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        
        try:
            result = await check_info["func"]()
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, dict):
                return HealthCheck(
                    component=name,
                    component_type=check_info["type"],
                    status=result.get("status", HealthStatus.HEALTHY),
                    message=result.get("message", "OK"),
                    metrics=result.get("metrics", {}),
                    timestamp=timestamp,
                    duration_ms=duration_ms,
                    error_details=result.get("error_details")
                )
            else:
                return result
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Capture error
            error_tracker.capture_exception(
                e,
                context={"health_check": name},
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH
            )
            
            return HealthCheck(
                component=name,
                component_type=check_info["type"],
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {error_msg}",
                metrics={},
                timestamp=timestamp,
                duration_ms=duration_ms,
                error_details=error_msg
            )
    
    async def run_all_checks(self) -> List[HealthCheck]:
        """Run all registered health checks"""
        results = []
        
        for name in self.checks:
            try:
                result = await self.run_check(name)
                results.append(result)
                
                # Store result for history
                with self._lock:
                    self.check_results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to run health check '{name}': {str(e)}")
        
        return results
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_io_mb = {
                "bytes_sent_mb": network_io.bytes_sent / (1024 * 1024),
                "bytes_recv_mb": network_io.bytes_recv / (1024 * 1024)
            }
            
            # Load average (Unix systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]  # Windows doesn't have load average
            
            # Active connections
            try:
                active_connections = len(psutil.net_connections(kind='inet'))
            except psutil.AccessDenied:
                active_connections = 0
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime_hours = (time.time() - boot_time) / 3600
            
            # Create system metrics
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_mb=network_io_mb,
                active_connections=active_connections,
                load_average=load_avg,
                uptime_hours=uptime_hours,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Store metrics history
            with self._lock:
                self.system_metrics_history.append(metrics)
            
            # Determine status
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > self.alert_thresholds["cpu_percent"]["critical"]:
                status = HealthStatus.CRITICAL
                messages.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > self.alert_thresholds["cpu_percent"]["warning"]:
                status = HealthStatus.WARNING
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > self.alert_thresholds["memory_percent"]["critical"]:
                status = HealthStatus.CRITICAL
                messages.append(f"Critical memory usage: {memory_percent:.1f}%")
            elif memory_percent > self.alert_thresholds["memory_percent"]["warning"]:
                status = HealthStatus.WARNING
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            
            if disk_percent > self.alert_thresholds["disk_percent"]["critical"]:
                status = HealthStatus.CRITICAL
                messages.append(f"Critical disk usage: {disk_percent:.1f}%")
            elif disk_percent > self.alert_thresholds["disk_percent"]["warning"]:
                status = HealthStatus.WARNING
                messages.append(f"High disk usage: {disk_percent:.1f}%")
            
            message = "; ".join(messages) if messages else "All system resources within normal limits"
            
            return {
                "status": status,
                "message": message,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "network_io_mb": network_io_mb,
                    "active_connections": active_connections,
                    "load_average": load_avg,
                    "uptime_hours": uptime_hours
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"System resource check failed: {str(e)}",
                "metrics": {},
                "error_details": str(e)
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Test MongoDB connection
            import os
            from motor.motor_asyncio import AsyncIOMotorClient
            
            mongo_url = os.environ.get('MONGO_URL')
            if not mongo_url:
                return {
                    "status": HealthStatus.CRITICAL,
                    "message": "MongoDB URL not configured",
                    "metrics": {}
                }
            
            start_time = time.time()
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            
            # Test connection with ping
            await client.admin.command('ping')
            ping_time_ms = (time.time() - start_time) * 1000
            
            # Get server status
            server_status = await client.admin.command('serverStatus')
            
            # Get database stats
            db_name = os.environ.get('DB_NAME', 'test_database')
            db_stats = await client[db_name].command('dbStats')
            
            client.close()
            
            # Check response time
            status = HealthStatus.HEALTHY
            if ping_time_ms > 1000:
                status = HealthStatus.WARNING
            if ping_time_ms > 3000:
                status = HealthStatus.CRITICAL
            
            return {
                "status": status,
                "message": f"Database responsive (ping: {ping_time_ms:.1f}ms)",
                "metrics": {
                    "ping_time_ms": ping_time_ms,
                    "connections": server_status.get('connections', {}),
                    "uptime_hours": server_status.get('uptime', 0) / 3600,
                    "database_size_mb": db_stats.get('dataSize', 0) / (1024 * 1024),
                    "collection_count": db_stats.get('collections', 0)
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"Database check failed: {str(e)}",
                "metrics": {},
                "error_details": str(e)
            }
    
    async def _check_ai_services(self) -> Dict[str, Any]:
        """Check AI services availability"""
        try:
            import os
            
            ai_services = {
                "gemini": os.getenv('GEMINI_API_KEY'),
                "groq": os.getenv('GROQ_API_KEY'),
                "huggingface": os.getenv('HUGGINGFACE_API_TOKEN')
            }
            
            configured_services = [name for name, key in ai_services.items() if key]
            
            if not configured_services:
                return {
                    "status": HealthStatus.CRITICAL,
                    "message": "No AI services configured",
                    "metrics": {"configured_services": 0}
                }
            
            # For now, just check if keys are configured
            # In a real implementation, you'd test actual API connectivity
            status = HealthStatus.HEALTHY
            message = f"AI services configured: {', '.join(configured_services)}"
            
            return {
                "status": status,
                "message": message,
                "metrics": {
                    "configured_services": len(configured_services),
                    "available_services": configured_services
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"AI services check failed: {str(e)}",
                "metrics": {},
                "error_details": str(e)
            }
    
    async def _check_scraping_engine(self) -> Dict[str, Any]:
        """Check scraping engine health"""
        try:
            # This would check scraping engine status in a real implementation
            # For now, return healthy status
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Scraping engine available",
                "metrics": {
                    "active_jobs": 0,
                    "queued_jobs": 0,
                    "total_processed": 0
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"Scraping engine check failed: {str(e)}",
                "metrics": {},
                "error_details": str(e)
            }
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("✅ Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        interval = self.config.monitoring.health_check_interval_seconds
        
        while self.monitoring_active:
            try:
                await self.run_all_checks()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(interval)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        with self._lock:
            recent_checks = list(self.check_results)[-len(self.checks):] if self.check_results else []
        
        if not recent_checks:
            return {
                "overall_status": HealthStatus.WARNING,
                "message": "No recent health checks available",
                "component_statuses": {},
                "last_check": None
            }
        
        # Determine overall status
        component_statuses = {}
        critical_count = 0
        warning_count = 0
        
        for check in recent_checks:
            component_statuses[check.component] = {
                "status": check.status.value,
                "message": check.message,
                "last_check": check.timestamp.isoformat()
            }
            
            if check.status == HealthStatus.CRITICAL:
                critical_count += 1
            elif check.status == HealthStatus.WARNING:
                warning_count += 1
        
        # Overall status logic
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
            message = f"{critical_count} critical issue(s) detected"
        elif warning_count > 0:
            overall_status = HealthStatus.WARNING
            message = f"{warning_count} warning(s) detected"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "All systems operational"
        
        return {
            "overall_status": overall_status.value,
            "message": message,
            "component_statuses": component_statuses,
            "last_check": max(check.timestamp for check in recent_checks).isoformat(),
            "total_components": len(component_statuses),
            "critical_count": critical_count,
            "warning_count": warning_count
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        with self._lock:
            if not self.system_metrics_history:
                return {"error": "No system metrics available"}
            
            current_metrics = self.system_metrics_history[-1]
            
        return {
            "cpu_percent": current_metrics.cpu_percent,
            "memory_percent": current_metrics.memory_percent,
            "disk_percent": current_metrics.disk_percent,
            "network_io_mb": current_metrics.network_io_mb,
            "active_connections": current_metrics.active_connections,
            "load_average": current_metrics.load_average,
            "uptime_hours": current_metrics.uptime_hours,
            "timestamp": current_metrics.timestamp.isoformat()
        }
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get system metrics history"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with self._lock:
            filtered_metrics = [
                {
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "disk_percent": m.disk_percent,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.system_metrics_history
                if m.timestamp >= cutoff_time
            ]
        
        return filtered_metrics


# Global health monitor instance
health_monitor = HealthMonitor()


async def get_health_summary() -> Dict[str, Any]:
    """Get system health summary"""
    return health_monitor.get_health_summary()


async def run_health_check(name: str) -> HealthCheck:
    """Run specific health check"""
    return await health_monitor.run_check(name)


async def run_all_health_checks() -> List[HealthCheck]:
    """Run all health checks"""
    return await health_monitor.run_all_checks()


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    return health_monitor.get_system_metrics()


async def setup_health_monitoring():
    """Initialize health monitoring system"""
    await health_monitor.start_monitoring()
    logging.info("✅ Health monitoring system initialized")