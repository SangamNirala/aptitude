"""
Real-Time Monitoring Service
Provides comprehensive monitoring capabilities for the scraping system
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import weakref
from collections import defaultdict, deque
import threading
import time

logger = logging.getLogger(__name__)

class MonitoringEventType(str, Enum):
    """Types of monitoring events"""
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed" 
    JOB_FAILED = "job_failed"
    JOB_PROGRESS = "job_progress"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_UPDATE = "performance_update"
    SOURCE_STATUS = "source_status"
    RESOURCE_WARNING = "resource_warning"

class MetricType(str, Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class MonitoringEvent:
    """Monitoring event data structure"""
    event_id: str
    event_type: MonitoringEventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    severity: str = "info"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "source": self.source,
            "severity": self.severity
        }

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "unit": self.unit
        }

@dataclass
class SystemHealthStatus:
    """System health status"""
    overall_status: str
    services: Dict[str, str]
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_jobs: int
    failed_jobs_last_hour: int
    alerts_count: int
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "services": self.services,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "active_jobs": self.active_jobs,
            "failed_jobs_last_hour": self.failed_jobs_last_hour,
            "alerts_count": self.alerts_count,
            "timestamp": self.timestamp.isoformat()
        }

class RealTimeStreamer:
    """Real-time WebSocket streaming for monitoring data"""
    
    def __init__(self):
        self.active_connections: Set = set()
        self.connection_lock = threading.Lock()
        
    async def connect(self, websocket):
        """Add a WebSocket connection"""
        with self.connection_lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket):
        """Remove a WebSocket connection"""
        with self.connection_lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected = set()
        
        with self.connection_lock:
            connections_copy = self.active_connections.copy()
        
        for websocket in connections_copy:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {str(e)}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        if disconnected:
            with self.connection_lock:
                self.active_connections -= disconnected

class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.current_metrics: Dict[str, PerformanceMetric] = {}
        self.lock = threading.Lock()
        
    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric"""
        with self.lock:
            self.current_metrics[metric.name] = metric
            self.metrics_history[metric.name].append(metric)
            
    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """Get current value of a metric"""
        with self.lock:
            return self.current_metrics.get(name)
    
    def get_metric_history(self, name: str, limit: int = 100) -> List[PerformanceMetric]:
        """Get historical values of a metric"""
        with self.lock:
            history = list(self.metrics_history.get(name, []))
            return history[-limit:] if limit else history
    
    def get_all_current_metrics(self) -> Dict[str, PerformanceMetric]:
        """Get all current metrics"""
        with self.lock:
            return self.current_metrics.copy()
    
    def aggregate_metrics(self, name: str, period_minutes: int = 60) -> Dict[str, float]:
        """Aggregate metrics over a time period"""
        with self.lock:
            history = list(self.metrics_history.get(name, []))
            
        if not history:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=period_minutes)
        recent_metrics = [m for m in history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        values = [m.value for m in recent_metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else 0
        }

class MonitoringService:
    """
    Comprehensive Real-Time Monitoring Service
    
    Features:
    1. Real-time job status streaming via WebSocket
    2. Performance metrics aggregation
    3. System health monitoring
    4. Alert integration
    5. Historical data APIs
    """
    
    def __init__(self):
        """Initialize the monitoring service"""
        self.is_running = False
        self.streamer = RealTimeStreamer()
        self.metrics_collector = MetricsCollector()
        self.event_history: deque = deque(maxlen=10000)
        self.alerts_manager = None  # Will be set by dependency injection
        
        # Service references (weak references to avoid circular imports)
        self._job_manager_ref = None
        self._source_manager_ref = None
        
        # Monitoring tasks
        self._monitoring_tasks: List[asyncio.Task] = []
        
        # Performance tracking
        self.start_time = datetime.utcnow()
        self.last_health_check = datetime.utcnow()
        
        logger.info("MonitoringService initialized")
    
    def set_job_manager(self, job_manager):
        """Set job manager reference"""
        self._job_manager_ref = weakref.ref(job_manager) if job_manager else None
    
    def set_source_manager(self, source_manager):
        """Set source manager reference"""
        self._source_manager_ref = weakref.ref(source_manager) if source_manager else None
        
    def set_alerts_manager(self, alerts_manager):
        """Set alerts manager reference"""
        self.alerts_manager = alerts_manager
    
    async def start(self):
        """Start the monitoring service"""
        if self.is_running:
            logger.warning("MonitoringService is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        logger.info("Starting MonitoringService")
        
        # Start monitoring tasks
        self._monitoring_tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._performance_monitoring_loop()),
            asyncio.create_task(self._job_status_monitoring_loop()),
            asyncio.create_task(self._health_check_loop())
        ]
        
        logger.info("✅ MonitoringService started successfully")
    
    async def stop(self):
        """Stop the monitoring service"""
        if not self.is_running:
            return
        
        logger.info("Stopping MonitoringService")
        
        self.is_running = False
        
        # Cancel monitoring tasks
        for task in self._monitoring_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)
        
        logger.info("✅ MonitoringService stopped")
    
    async def emit_event(self, event: MonitoringEvent):
        """Emit a monitoring event"""
        try:
            # Add to history
            self.event_history.append(event)
            
            # Broadcast to WebSocket clients
            await self.streamer.broadcast({
                "type": "monitoring_event",
                "event": event.to_dict()
            })
            
            # Trigger alerts if needed
            if self.alerts_manager and event.severity in ["warning", "error", "critical"]:
                await self.alerts_manager.process_monitoring_event(event)
            
            logger.debug(f"Emitted monitoring event: {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"Error emitting monitoring event: {str(e)}")
    
    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = "", metric_type: MetricType = MetricType.GAUGE):
        """Record a performance metric"""
        try:
            metric = PerformanceMetric(
                name=name,
                type=metric_type,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                unit=unit
            )
            
            self.metrics_collector.add_metric(metric)
            
            # Broadcast metric update
            await self.streamer.broadcast({
                "type": "metric_update",
                "metric": metric.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Error recording metric {name}: {str(e)}")
    
    async def get_system_health(self) -> SystemHealthStatus:
        """Get current system health status"""
        try:
            # System resources
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Service status
            services = {}
            
            # Check job manager
            job_manager = self._job_manager_ref() if self._job_manager_ref else None
            if job_manager and hasattr(job_manager, 'is_running') and job_manager.is_running:
                services["job_manager"] = "healthy"
                active_jobs = len(getattr(job_manager, 'active_jobs', {}))
            else:
                services["job_manager"] = "down"
                active_jobs = 0
            
            # Check source manager
            source_manager = self._source_manager_ref() if self._source_manager_ref else None
            services["source_manager"] = "healthy" if source_manager else "down"
            
            # Check alerts manager
            services["alerts_manager"] = "healthy" if self.alerts_manager else "down"
            
            # Calculate failed jobs in last hour
            failed_jobs_last_hour = self._count_failed_jobs_last_hour()
            
            # Get alerts count
            alerts_count = len(self.alerts_manager.active_alerts) if self.alerts_manager else 0
            
            # Determine overall status
            overall_status = "healthy"
            if cpu_percent > 90 or memory.percent > 90:
                overall_status = "warning"
            if any(status == "down" for status in services.values()):
                overall_status = "degraded"
            if failed_jobs_last_hour > 10:
                overall_status = "critical"
            
            return SystemHealthStatus(
                overall_status=overall_status,
                services=services,
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                active_jobs=active_jobs,
                failed_jobs_last_hour=failed_jobs_last_hour,
                alerts_count=alerts_count,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return SystemHealthStatus(
                overall_status="error",
                services={"monitoring": "error"},
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                active_jobs=0,
                failed_jobs_last_hour=0,
                alerts_count=0,
                timestamp=datetime.utcnow()
            )
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        try:
            current_metrics = self.metrics_collector.get_all_current_metrics()
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
                "metrics": {}
            }
            
            for name, metric in current_metrics.items():
                summary["metrics"][name] = {
                    "current_value": metric.value,
                    "unit": metric.unit,
                    "last_updated": metric.timestamp.isoformat(),
                    "aggregation": self.metrics_collector.aggregate_metrics(name, 60)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            return {"error": str(e)}
    
    async def get_recent_events(self, limit: int = 100, event_type: Optional[MonitoringEventType] = None) -> List[Dict[str, Any]]:
        """Get recent monitoring events"""
        try:
            events = list(self.event_history)
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            events = events[-limit:] if limit else events
            
            return [event.to_dict() for event in events]
            
        except Exception as e:
            logger.error(f"Error getting recent events: {str(e)}")
            return []
    
    async def get_historical_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics data"""
        try:
            # Calculate number of data points (approximate)
            limit = hours * 60  # Assuming 1 metric per minute
            
            metrics = self.metrics_collector.get_metric_history(metric_name, limit)
            
            return [metric.to_dict() for metric in metrics]
            
        except Exception as e:
            logger.error(f"Error getting historical metrics for {metric_name}: {str(e)}")
            return []
    
    # WebSocket connection management
    
    async def connect_websocket(self, websocket):
        """Connect a WebSocket client"""
        await self.streamer.connect(websocket)
        
        # Send current system status
        health = await self.get_system_health()
        await websocket.send_text(json.dumps({
            "type": "system_health",
            "data": health.to_dict()
        }))
    
    async def disconnect_websocket(self, websocket):
        """Disconnect a WebSocket client"""
        await self.streamer.disconnect(websocket)
    
    # Private monitoring loops
    
    async def _system_monitoring_loop(self):
        """Monitor system resources"""
        logger.info("Starting system monitoring loop")
        
        while self.is_running:
            try:
                # CPU monitoring
                cpu_percent = psutil.cpu_percent(interval=1.0)
                await self.record_metric("system.cpu.usage", cpu_percent, unit="%")
                
                # Memory monitoring
                memory = psutil.virtual_memory()
                await self.record_metric("system.memory.usage", memory.percent, unit="%")
                await self.record_metric("system.memory.available", memory.available / (1024**3), unit="GB")
                
                # Disk monitoring
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                await self.record_metric("system.disk.usage", disk_percent, unit="%")
                await self.record_metric("system.disk.free", disk.free / (1024**3), unit="GB")
                
                # Network monitoring
                try:
                    network = psutil.net_io_counters()
                    await self.record_metric("system.network.bytes_sent", network.bytes_sent, unit="bytes", metric_type=MetricType.COUNTER)
                    await self.record_metric("system.network.bytes_recv", network.bytes_recv, unit="bytes", metric_type=MetricType.COUNTER)
                except:
                    pass  # Network stats might not be available
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Longer sleep on error
    
    async def _performance_monitoring_loop(self):
        """Monitor application performance"""
        logger.info("Starting performance monitoring loop")
        
        while self.is_running:
            try:
                # Job manager metrics
                job_manager = self._job_manager_ref() if self._job_manager_ref else None
                if job_manager and hasattr(job_manager, 'get_performance_metrics'):
                    try:
                        metrics = await job_manager.get_performance_metrics()
                        job_stats = metrics.get("job_statistics", {})
                        
                        await self.record_metric("jobs.active", len(getattr(job_manager, 'active_jobs', {})))
                        await self.record_metric("jobs.completed", job_stats.get("successful_jobs", 0), metric_type=MetricType.COUNTER)
                        await self.record_metric("jobs.failed", job_stats.get("failed_jobs", 0), metric_type=MetricType.COUNTER)
                        await self.record_metric("jobs.avg_execution_time", job_stats.get("avg_execution_time", 0), unit="seconds")
                        
                    except Exception as e:
                        logger.debug(f"Could not get job manager metrics: {str(e)}")
                
                # Record service uptime
                uptime_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
                await self.record_metric("monitoring.uptime", uptime_hours, unit="hours")
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {str(e)}")
                await asyncio.sleep(120)
    
    async def _job_status_monitoring_loop(self):
        """Monitor job status changes"""
        logger.info("Starting job status monitoring loop")
        
        last_jobs_check = {}
        
        while self.is_running:
            try:
                job_manager = self._job_manager_ref() if self._job_manager_ref else None
                if not job_manager:
                    await asyncio.sleep(30)
                    continue
                
                # Get current active jobs
                current_jobs = getattr(job_manager, 'active_jobs', {})
                
                # Check for new jobs
                for job_id, job in current_jobs.items():
                    if job_id not in last_jobs_check:
                        # New job started
                        await self.emit_event(MonitoringEvent(
                            event_id=f"job_start_{job_id}",
                            event_type=MonitoringEventType.JOB_STARTED,
                            timestamp=datetime.utcnow(),
                            data={
                                "job_id": job_id,
                                "job_type": "scraping",
                                "status": job.status.value if hasattr(job.status, 'value') else str(job.status)
                            },
                            source="job_monitor"
                        ))
                
                # Check for completed/failed jobs
                for job_id in last_jobs_check:
                    if job_id not in current_jobs:
                        # Job completed or failed
                        try:
                            if hasattr(job_manager, 'completed_jobs') and job_id in job_manager.completed_jobs:
                                await self.emit_event(MonitoringEvent(
                                    event_id=f"job_complete_{job_id}",
                                    event_type=MonitoringEventType.JOB_COMPLETED,
                                    timestamp=datetime.utcnow(),
                                    data={"job_id": job_id},
                                    source="job_monitor"
                                ))
                            elif hasattr(job_manager, 'failed_jobs') and job_id in job_manager.failed_jobs:
                                await self.emit_event(MonitoringEvent(
                                    event_id=f"job_failed_{job_id}",
                                    event_type=MonitoringEventType.JOB_FAILED,
                                    timestamp=datetime.utcnow(),
                                    data={"job_id": job_id},
                                    source="job_monitor",
                                    severity="error"
                                ))
                        except Exception as e:
                            logger.debug(f"Error checking job completion status: {str(e)}")
                
                last_jobs_check = current_jobs.copy()
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in job status monitoring loop: {str(e)}")
                await asyncio.sleep(30)
    
    async def _health_check_loop(self):
        """Regular health check and broadcasting"""
        logger.info("Starting health check loop")
        
        while self.is_running:
            try:
                # Get current health status
                health = await self.get_system_health()
                
                # Broadcast health update
                await self.streamer.broadcast({
                    "type": "health_update",
                    "data": health.to_dict()
                })
                
                self.last_health_check = datetime.utcnow()
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health check loop: {str(e)}")
                await asyncio.sleep(60)
    
    def _count_failed_jobs_last_hour(self) -> int:
        """Count failed jobs in the last hour"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            failed_count = 0
            
            for event in self.event_history:
                if (event.event_type == MonitoringEventType.JOB_FAILED and 
                    event.timestamp >= cutoff_time):
                    failed_count += 1
            
            return failed_count
            
        except Exception as e:
            logger.error(f"Error counting failed jobs: {str(e)}")
            return 0


# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None

def get_monitoring_service() -> Optional[MonitoringService]:
    """Get the global monitoring service instance"""
    return _monitoring_service

def create_monitoring_service() -> MonitoringService:
    """Factory function to create monitoring service"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service

async def initialize_monitoring_service(job_manager=None, source_manager=None, alerts_manager=None) -> MonitoringService:
    """Initialize monitoring service with dependencies"""
    monitoring_service = create_monitoring_service()
    
    if job_manager:
        monitoring_service.set_job_manager(job_manager)
    if source_manager:
        monitoring_service.set_source_manager(source_manager)
    if alerts_manager:
        monitoring_service.set_alerts_manager(alerts_manager)
    
    await monitoring_service.start()
    
    logger.info("✅ MonitoringService initialized and started")
    return monitoring_service

logger.info("✅ MonitoringService module loaded successfully")