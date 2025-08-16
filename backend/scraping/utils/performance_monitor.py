"""
Performance Monitoring Utilities
Comprehensive performance tracking and monitoring for web scraping operations
"""

import os
import time
import psutil
import asyncio
import threading
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
from contextlib import contextmanager, asynccontextmanager
from enum import Enum
import json

logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE MONITORING ENUMS AND CLASSES
# =============================================================================

class PerformanceLevel(str, Enum):
    EXCELLENT = "excellent"    # >90% efficiency
    GOOD = "good"             # 70-90% efficiency  
    AVERAGE = "average"       # 50-70% efficiency
    POOR = "poor"             # 30-50% efficiency
    CRITICAL = "critical"     # <30% efficiency

class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network" 
    DISK = "disk"
    BROWSER = "browser"

@dataclass
class ResourceSnapshot:
    """Single point-in-time resource measurement"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    disk_read_bytes: int
    disk_write_bytes: int
    process_count: int
    thread_count: int

@dataclass
class OperationMetrics:
    """Performance metrics for a single operation"""
    operation_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    
    # Resource usage during operation
    avg_cpu_percent: float
    max_cpu_percent: float
    avg_memory_mb: float
    max_memory_mb: float
    
    # Operation-specific metrics
    elements_processed: int = 0
    pages_processed: int = 0
    requests_made: int = 0
    errors_count: int = 0
    
    # Quality metrics
    throughput_per_second: float = 0.0
    efficiency_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations"""
    alert_id: str
    timestamp: datetime
    severity: str  # info, warning, critical
    resource_type: ResourceType
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

@dataclass
class PerformanceThresholds:
    """Performance monitoring thresholds"""
    # CPU thresholds (percentage)
    cpu_warning: float = 70.0
    cpu_critical: float = 85.0
    
    # Memory thresholds (percentage)
    memory_warning: float = 75.0
    memory_critical: float = 90.0
    
    # Response time thresholds (seconds)
    response_warning: float = 5.0
    response_critical: float = 10.0
    
    # Throughput thresholds (operations per minute)
    throughput_warning: float = 10.0
    throughput_critical: float = 5.0
    
    # Error rate thresholds (percentage)
    error_rate_warning: float = 5.0
    error_rate_critical: float = 15.0

# =============================================================================
# PERFORMANCE MONITOR CLASS
# =============================================================================

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for scraping operations
    """
    
    def __init__(self, monitor_name: str = "scraping_monitor", 
                 collection_interval: float = 1.0,
                 max_history_size: int = 1000,
                 thresholds: PerformanceThresholds = None):
        """
        Initialize performance monitor
        
        Args:
            monitor_name: Name of the monitoring instance
            collection_interval: How often to collect metrics (seconds)
            max_history_size: Maximum number of snapshots to keep
            thresholds: Performance thresholds for alerting
        """
        self.monitor_name = monitor_name
        self.collection_interval = collection_interval
        self.max_history_size = max_history_size
        self.thresholds = thresholds or PerformanceThresholds()
        
        # Data storage
        self.resource_history: deque = deque(maxlen=max_history_size)
        self.operation_metrics: List[OperationMetrics] = []
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.performance_alerts: List[PerformanceAlert] = []
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.start_time = datetime.utcnow()
        
        # Process tracking
        self.process = psutil.Process()
        self.initial_resources = self._get_resource_snapshot()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        logger.info(f"📊 PerformanceMonitor initialized: {monitor_name}")
    
    def _get_resource_snapshot(self) -> ResourceSnapshot:
        """Get current system resource snapshot"""
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            network = psutil.net_io_counters()
            disk = psutil.disk_io_counters()
            
            # Process-specific metrics  
            process_memory = self.process.memory_info()
            process_threads = self.process.num_threads()
            
            return ResourceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=process_memory.rss / (1024 * 1024),
                network_bytes_sent=network.bytes_sent if network else 0,
                network_bytes_recv=network.bytes_recv if network else 0,
                disk_read_bytes=disk.read_bytes if disk else 0,
                disk_write_bytes=disk.write_bytes if disk else 0,
                process_count=len(psutil.pids()),
                thread_count=process_threads
            )
            
        except Exception as e:
            logger.warning(f"Failed to get resource snapshot: {e}")
            return ResourceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=0.0, memory_percent=0.0, memory_mb=0.0,
                network_bytes_sent=0, network_bytes_recv=0,
                disk_read_bytes=0, disk_write_bytes=0,
                process_count=0, thread_count=0
            )
    
    def start_monitoring(self):
        """Start continuous resource monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name=f"perf_monitor_{self.monitor_name}"
        )
        self.monitoring_thread.start()
        
        logger.info(f"🔄 Performance monitoring started for {self.monitor_name}")
    
    def stop_monitoring(self):
        """Stop continuous resource monitoring"""
        self.is_monitoring = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info(f"⏹️ Performance monitoring stopped for {self.monitor_name}")
    
    def _monitoring_loop(self):
        """Main monitoring loop (runs in separate thread)"""
        logger.debug(f"Starting monitoring loop with {self.collection_interval}s interval")
        
        while self.is_monitoring:
            try:
                # Collect resource snapshot
                snapshot = self._get_resource_snapshot()
                self.resource_history.append(snapshot)
                
                # Check for threshold violations
                self._check_thresholds(snapshot)
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.collection_interval)
    
    def _check_thresholds(self, snapshot: ResourceSnapshot):
        """Check current metrics against thresholds and generate alerts"""
        alerts_generated = []
        
        # CPU threshold check
        if snapshot.cpu_percent >= self.thresholds.cpu_critical:
            alert = self._create_alert(
                "cpu_critical", ResourceType.CPU, "cpu_percent",
                snapshot.cpu_percent, self.thresholds.cpu_critical,
                f"Critical CPU usage: {snapshot.cpu_percent:.1f}%",
                ["Consider reducing concurrent operations", "Check for CPU-intensive tasks"]
            )
            alerts_generated.append(alert)
            
        elif snapshot.cpu_percent >= self.thresholds.cpu_warning:
            alert = self._create_alert(
                "cpu_warning", ResourceType.CPU, "cpu_percent",
                snapshot.cpu_percent, self.thresholds.cpu_warning,
                f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                ["Monitor CPU usage trends", "Consider optimization"]
            )
            alerts_generated.append(alert)
        
        # Memory threshold check
        if snapshot.memory_percent >= self.thresholds.memory_critical:
            alert = self._create_alert(
                "memory_critical", ResourceType.MEMORY, "memory_percent",
                snapshot.memory_percent, self.thresholds.memory_critical,
                f"Critical memory usage: {snapshot.memory_percent:.1f}%",
                ["Free up memory immediately", "Restart operations if necessary"]
            )
            alerts_generated.append(alert)
            
        elif snapshot.memory_percent >= self.thresholds.memory_warning:
            alert = self._create_alert(
                "memory_warning", ResourceType.MEMORY, "memory_percent",
                snapshot.memory_percent, self.thresholds.memory_warning,
                f"High memory usage: {snapshot.memory_percent:.1f}%",
                ["Monitor memory trends", "Consider garbage collection"]
            )
            alerts_generated.append(alert)
        
        # Process alerts and trigger callbacks
        for alert in alerts_generated:
            self.performance_alerts.append(alert)
            self._trigger_alert_callbacks(alert)
    
    def _create_alert(self, alert_type: str, resource_type: ResourceType, 
                     metric_name: str, current_value: float, threshold_value: float,
                     message: str, suggestions: List[str]) -> PerformanceAlert:
        """Create a performance alert"""
        severity = "critical" if "critical" in alert_type else "warning"
        
        return PerformanceAlert(
            alert_id=f"{alert_type}_{int(time.time())}",
            timestamp=datetime.utcnow(),
            severity=severity,
            resource_type=resource_type,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            suggestions=suggestions
        )
    
    def _trigger_alert_callbacks(self, alert: PerformanceAlert):
        """Trigger registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    @contextmanager
    def monitor_operation(self, operation_name: str, **metadata):
        """
        Context manager to monitor a synchronous operation
        
        Args:
            operation_name: Name of the operation being monitored
            **metadata: Additional metadata for the operation
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        # Start monitoring
        start_time = datetime.utcnow()
        start_snapshot = self._get_resource_snapshot()
        
        self.active_operations[operation_id] = {
            "name": operation_name,
            "start_time": start_time,
            "start_snapshot": start_snapshot,
            "metadata": metadata,
            "snapshots": [start_snapshot]
        }
        
        logger.debug(f"🔍 Started monitoring operation: {operation_name}")
        
        try:
            yield operation_id
            success = True
            
        except Exception as e:
            success = False
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
            
        finally:
            # End monitoring
            end_time = datetime.utcnow()
            end_snapshot = self._get_resource_snapshot()
            
            operation_data = self.active_operations.pop(operation_id, {})
            
            # Calculate metrics
            metrics = self._calculate_operation_metrics(
                operation_name, start_time, end_time, success,
                operation_data.get("start_snapshot", start_snapshot),
                end_snapshot, operation_data.get("snapshots", []),
                metadata
            )
            
            self.operation_metrics.append(metrics)
            
            logger.debug(f"✅ Completed monitoring operation: {operation_name} "
                        f"(Duration: {metrics.duration_seconds:.2f}s, Success: {success})")
    
    @asynccontextmanager
    async def monitor_async_operation(self, operation_name: str, **metadata):
        """
        Async context manager to monitor an asynchronous operation
        
        Args:
            operation_name: Name of the operation being monitored
            **metadata: Additional metadata for the operation
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        # Start monitoring
        start_time = datetime.utcnow()
        start_snapshot = self._get_resource_snapshot()
        
        self.active_operations[operation_id] = {
            "name": operation_name,
            "start_time": start_time,
            "start_snapshot": start_snapshot,
            "metadata": metadata,
            "snapshots": [start_snapshot]
        }
        
        logger.debug(f"🔍 Started monitoring async operation: {operation_name}")
        
        # Start periodic snapshot collection for long-running operations
        snapshot_task = asyncio.create_task(
            self._collect_operation_snapshots(operation_id)
        )
        
        try:
            yield operation_id
            success = True
            
        except Exception as e:
            success = False
            logger.error(f"Async operation {operation_name} failed: {e}")
            raise
            
        finally:
            # Stop periodic collection
            snapshot_task.cancel()
            try:
                await snapshot_task
            except asyncio.CancelledError:
                pass
            
            # End monitoring
            end_time = datetime.utcnow()
            end_snapshot = self._get_resource_snapshot()
            
            operation_data = self.active_operations.pop(operation_id, {})
            
            # Calculate metrics
            metrics = self._calculate_operation_metrics(
                operation_name, start_time, end_time, success,
                operation_data.get("start_snapshot", start_snapshot),
                end_snapshot, operation_data.get("snapshots", []),
                metadata
            )
            
            self.operation_metrics.append(metrics)
            
            logger.debug(f"✅ Completed monitoring async operation: {operation_name} "
                        f"(Duration: {metrics.duration_seconds:.2f}s, Success: {success})")
    
    async def _collect_operation_snapshots(self, operation_id: str):
        """Collect periodic snapshots during long-running operations"""
        try:
            while operation_id in self.active_operations:
                await asyncio.sleep(self.collection_interval)
                
                if operation_id in self.active_operations:
                    snapshot = self._get_resource_snapshot()
                    self.active_operations[operation_id]["snapshots"].append(snapshot)
                    
        except asyncio.CancelledError:
            pass
    
    def _calculate_operation_metrics(self, operation_name: str, 
                                   start_time: datetime, end_time: datetime, 
                                   success: bool, start_snapshot: ResourceSnapshot,
                                   end_snapshot: ResourceSnapshot, 
                                   snapshots: List[ResourceSnapshot],
                                   metadata: Dict[str, Any]) -> OperationMetrics:
        """Calculate comprehensive metrics for an operation"""
        duration = (end_time - start_time).total_seconds()
        
        # Calculate resource usage statistics
        all_snapshots = [start_snapshot] + snapshots + [end_snapshot]
        
        if len(all_snapshots) > 1:
            cpu_values = [s.cpu_percent for s in all_snapshots]
            memory_values = [s.memory_mb for s in all_snapshots]
            
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
        else:
            avg_cpu = start_snapshot.cpu_percent
            max_cpu = start_snapshot.cpu_percent
            avg_memory = start_snapshot.memory_mb
            max_memory = start_snapshot.memory_mb
        
        # Extract metadata values
        elements_processed = metadata.get("elements_processed", 0)
        pages_processed = metadata.get("pages_processed", 0) 
        requests_made = metadata.get("requests_made", 0)
        errors_count = metadata.get("errors_count", 0)
        
        # Calculate throughput and efficiency
        total_operations = max(elements_processed, pages_processed, requests_made, 1)
        throughput_per_second = total_operations / duration if duration > 0 else 0
        
        # Simple efficiency score (higher throughput, lower resource usage = better)
        efficiency_score = self._calculate_efficiency_score(
            throughput_per_second, avg_cpu, avg_memory, errors_count, total_operations
        )
        
        return OperationMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            success=success,
            avg_cpu_percent=round(avg_cpu, 2),
            max_cpu_percent=round(max_cpu, 2),
            avg_memory_mb=round(avg_memory, 2),
            max_memory_mb=round(max_memory, 2),
            elements_processed=elements_processed,
            pages_processed=pages_processed,
            requests_made=requests_made,
            errors_count=errors_count,
            throughput_per_second=round(throughput_per_second, 2),
            efficiency_score=round(efficiency_score, 2)
        )
    
    def _calculate_efficiency_score(self, throughput: float, cpu_usage: float, 
                                  memory_usage: float, errors: int, 
                                  total_ops: int) -> float:
        """Calculate efficiency score (0-100)"""
        # Base score from throughput
        throughput_score = min(throughput * 10, 50)  # Max 50 points from throughput
        
        # Resource efficiency (less usage = higher score)
        resource_score = max(0, 30 - (cpu_usage + memory_usage) / 10)  # Max 30 points
        
        # Error penalty
        error_rate = errors / max(total_ops, 1)
        error_penalty = error_rate * 20  # Max 20 point penalty
        
        # Combine scores
        total_score = throughput_score + resource_score - error_penalty
        
        return max(0.0, min(100.0, total_score))
    
    def record_custom_metric(self, metric_name: str, value: Union[int, float], 
                           metadata: Dict[str, Any] = None):
        """Record a custom performance metric"""
        # Implementation could store custom metrics in a separate structure
        logger.debug(f"📏 Custom metric recorded: {metric_name} = {value}")
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function for performance alerts"""
        self.alert_callbacks.append(callback)
        logger.debug(f"Added alert callback: {callback.__name__}")
    
    def get_current_performance_level(self) -> PerformanceLevel:
        """Get current overall performance level"""
        if not self.resource_history:
            return PerformanceLevel.AVERAGE
        
        # Analyze recent performance (last 10 snapshots)
        recent_snapshots = list(self.resource_history)[-10:]
        
        avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
        avg_memory = sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots)
        
        # Calculate overall efficiency
        resource_efficiency = 100 - (avg_cpu + avg_memory) / 2
        
        if resource_efficiency >= 90:
            return PerformanceLevel.EXCELLENT
        elif resource_efficiency >= 70:
            return PerformanceLevel.GOOD
        elif resource_efficiency >= 50:
            return PerformanceLevel.AVERAGE
        elif resource_efficiency >= 30:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_time = datetime.utcnow()
        session_duration = (current_time - self.start_time).total_seconds()
        
        # Resource statistics
        if self.resource_history:
            recent_snapshots = list(self.resource_history)
            
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            memory_values = [s.memory_mb for s in recent_snapshots]
            
            resource_stats = {
                "avg_cpu_percent": round(sum(cpu_values) / len(cpu_values), 2),
                "max_cpu_percent": round(max(cpu_values), 2),
                "avg_memory_mb": round(sum(memory_values) / len(memory_values), 2),
                "max_memory_mb": round(max(memory_values), 2),
                "snapshots_collected": len(recent_snapshots)
            }
        else:
            resource_stats = {
                "avg_cpu_percent": 0.0,
                "max_cpu_percent": 0.0,
                "avg_memory_mb": 0.0,
                "max_memory_mb": 0.0,
                "snapshots_collected": 0
            }
        
        # Operation statistics
        if self.operation_metrics:
            successful_ops = [op for op in self.operation_metrics if op.success]
            failed_ops = [op for op in self.operation_metrics if not op.success]
            
            operation_stats = {
                "total_operations": len(self.operation_metrics),
                "successful_operations": len(successful_ops),
                "failed_operations": len(failed_ops),
                "success_rate": round(len(successful_ops) / len(self.operation_metrics) * 100, 2),
                "avg_duration": round(sum(op.duration_seconds for op in self.operation_metrics) / len(self.operation_metrics), 2),
                "avg_efficiency_score": round(sum(op.efficiency_score for op in self.operation_metrics) / len(self.operation_metrics), 2)
            }
        else:
            operation_stats = {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "avg_efficiency_score": 0.0
            }
        
        # Alert statistics
        alert_stats = {
            "total_alerts": len(self.performance_alerts),
            "critical_alerts": len([a for a in self.performance_alerts if a.severity == "critical"]),
            "warning_alerts": len([a for a in self.performance_alerts if a.severity == "warning"]),
        }
        
        return {
            "monitor_name": self.monitor_name,
            "session_duration_seconds": round(session_duration, 2),
            "current_performance_level": self.get_current_performance_level().value,
            "is_monitoring": self.is_monitoring,
            "resource_statistics": resource_stats,
            "operation_statistics": operation_stats,
            "alert_statistics": alert_stats,
            "thresholds": asdict(self.thresholds),
            "timestamp": current_time.isoformat()
        }
    
    def export_metrics(self, filepath: str, format: str = "json"):
        """Export performance metrics to file"""
        try:
            data = {
                "summary": self.get_performance_summary(),
                "resource_history": [asdict(snapshot) for snapshot in self.resource_history],
                "operation_metrics": [op.to_dict() for op in self.operation_metrics],
                "performance_alerts": [asdict(alert) for alert in self.performance_alerts]
            }
            
            if format.lower() == "json":
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"📁 Performance metrics exported to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Failed to export metrics: {e}")
    
    def cleanup(self):
        """Clean up monitoring resources"""
        self.stop_monitoring()
        
        # Clear data structures
        self.resource_history.clear()
        self.operation_metrics.clear()
        self.active_operations.clear()
        self.performance_alerts.clear()
        self.alert_callbacks.clear()
        
        logger.info(f"🧹 Performance monitor cleaned up: {self.monitor_name}")

# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

def create_scraping_performance_monitor(source_name: str = "scraping",
                                      **kwargs) -> PerformanceMonitor:
    """
    Create performance monitor optimized for scraping operations
    
    Args:
        source_name: Name of the scraping source
        **kwargs: Additional configuration options
        
    Returns:
        Configured PerformanceMonitor instance
    """
    # Scraping-optimized thresholds
    thresholds = PerformanceThresholds(
        cpu_warning=60.0,      # Lower CPU warning for scraping
        cpu_critical=80.0,
        memory_warning=70.0,   # Lower memory warning
        memory_critical=85.0,
        response_warning=3.0,  # Faster response expectations
        response_critical=8.0,
        throughput_warning=15.0,  # Higher throughput expectations
        throughput_critical=8.0
    )
    
    return PerformanceMonitor(
        monitor_name=f"{source_name}_scraper",
        collection_interval=0.5,  # More frequent collection
        thresholds=thresholds,
        **kwargs
    )

def create_high_volume_monitor(source_name: str = "high_volume",
                             **kwargs) -> PerformanceMonitor:
    """Create monitor optimized for high-volume operations"""
    thresholds = PerformanceThresholds(
        cpu_warning=75.0,
        cpu_critical=90.0,
        memory_warning=80.0,
        memory_critical=95.0,
        response_warning=2.0,
        response_critical=5.0,
        throughput_warning=30.0,
        throughput_critical=15.0
    )
    
    return PerformanceMonitor(
        monitor_name=f"{source_name}_high_volume",
        collection_interval=0.25,  # Very frequent collection
        max_history_size=2000,     # Larger history
        thresholds=thresholds,
        **kwargs
    )

# =============================================================================
# PERFORMANCE ANALYSIS UTILITIES  
# =============================================================================

class PerformanceAnalyzer:
    """Utility class for analyzing performance data"""
    
    @staticmethod
    def analyze_operation_trends(operations: List[OperationMetrics], 
                               operation_name: str = None) -> Dict[str, Any]:
        """Analyze performance trends for operations"""
        if operation_name:
            ops = [op for op in operations if op.operation_name == operation_name]
        else:
            ops = operations
        
        if not ops:
            return {"error": "No operations found"}
        
        # Sort by start time
        ops.sort(key=lambda x: x.start_time)
        
        # Calculate trends
        durations = [op.duration_seconds for op in ops]
        efficiency_scores = [op.efficiency_score for op in ops]
        success_rates = [1.0 if op.success else 0.0 for op in ops]
        
        return {
            "operation_count": len(ops),
            "duration_trend": PerformanceAnalyzer._calculate_trend(durations),
            "efficiency_trend": PerformanceAnalyzer._calculate_trend(efficiency_scores),
            "success_rate": sum(success_rates) / len(success_rates) * 100,
            "avg_duration": sum(durations) / len(durations),
            "avg_efficiency": sum(efficiency_scores) / len(efficiency_scores)
        }
    
    @staticmethod
    def _calculate_trend(values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if abs(slope) < 0.01:  # Threshold for "stable"
            return "stable"
        elif slope > 0:
            return "improving"
        else:
            return "declining"
    
    @staticmethod
    def identify_bottlenecks(monitor: PerformanceMonitor) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks from monitoring data"""
        bottlenecks = []
        
        # Analyze resource usage
        if monitor.resource_history:
            recent_snapshots = list(monitor.resource_history)[-50:]  # Last 50 snapshots
            
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_memory = sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots)
            
            if avg_cpu > 80:
                bottlenecks.append({
                    "type": "cpu_bottleneck",
                    "severity": "high" if avg_cpu > 90 else "medium",
                    "description": f"High CPU usage: {avg_cpu:.1f}% average",
                    "suggestions": [
                        "Reduce concurrent operations",
                        "Optimize CPU-intensive tasks",
                        "Consider scaling horizontally"
                    ]
                })
            
            if avg_memory > 85:
                bottlenecks.append({
                    "type": "memory_bottleneck", 
                    "severity": "high" if avg_memory > 95 else "medium",
                    "description": f"High memory usage: {avg_memory:.1f}% average",
                    "suggestions": [
                        "Implement memory cleanup",
                        "Reduce data caching",
                        "Check for memory leaks"
                    ]
                })
        
        # Analyze operation performance
        if monitor.operation_metrics:
            recent_ops = monitor.operation_metrics[-20:]  # Last 20 operations
            
            slow_ops = [op for op in recent_ops if op.duration_seconds > 10]
            if slow_ops:
                bottlenecks.append({
                    "type": "slow_operations",
                    "severity": "medium",
                    "description": f"{len(slow_ops)} slow operations detected (>10s)",
                    "suggestions": [
                        "Optimize operation algorithms",
                        "Implement caching",
                        "Review timeout settings"
                    ]
                })
            
            failed_ops = [op for op in recent_ops if not op.success]
            if len(failed_ops) > len(recent_ops) * 0.1:  # >10% failure rate
                bottlenecks.append({
                    "type": "high_failure_rate",
                    "severity": "high",
                    "description": f"High failure rate: {len(failed_ops)}/{len(recent_ops)} operations failed",
                    "suggestions": [
                        "Review error handling",
                        "Check network connectivity",
                        "Validate input data"
                    ]
                })
        
        return bottlenecks

# Global performance monitor instance for convenience
_global_monitor: Optional[PerformanceMonitor] = None

def get_global_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = create_scraping_performance_monitor("global")
        _global_monitor.start_monitoring()
    return _global_monitor

def cleanup_global_monitor():
    """Cleanup global performance monitor"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.cleanup()
        _global_monitor = None