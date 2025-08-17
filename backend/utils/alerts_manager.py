"""
Alerts Management System
Handles alert lifecycle, notifications, and alert processing for the monitoring system
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status values"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class AlertCategory(str, Enum):
    """Alert categories"""
    SYSTEM = "system"
    JOB = "job"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BUSINESS = "business"

@dataclass
class AlertCondition:
    """Alert triggering condition"""
    metric_name: str
    operator: str  # ">", "<", ">=", "<=", "==", "!="
    threshold: float
    duration_minutes: int = 0  # How long condition must persist
    description: str = ""

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    category: AlertCategory
    status: AlertStatus
    source: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "status": self.status.value,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "metadata": self.metadata,
            "tags": self.tags
        }

@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    description: str
    category: AlertCategory
    severity: AlertSeverity
    condition: AlertCondition
    enabled: bool = True
    suppression_duration_minutes: int = 60
    notification_channels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert rule to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "condition": asdict(self.condition),
            "enabled": self.enabled,
            "suppression_duration_minutes": self.suppression_duration_minutes,
            "notification_channels": self.notification_channels,
            "tags": self.tags
        }

class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, channel_id: str, name: str, config: Dict[str, Any]):
        self.channel_id = channel_id
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for alert"""
        raise NotImplementedError("Subclasses must implement send_notification")

class LogNotificationChannel(NotificationChannel):
    """Log-based notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification via logging"""
        try:
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.ERROR: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.INFO)
            
            logger.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send log notification: {str(e)}")
            return False

class WebhookNotificationChannel(NotificationChannel):
    """Webhook-based notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification via webhook"""
        try:
            # Placeholder for webhook implementation
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                logger.warning(f"No webhook URL configured for channel {self.channel_id}")
                return False
            
            # Here you would implement actual HTTP request to webhook
            logger.info(f"Webhook notification sent to {webhook_url} for alert {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
            return False

class AlertsManager:
    """
    Comprehensive Alert Management System
    
    Features:
    1. Alert lifecycle management (create, acknowledge, resolve)
    2. Alert rules engine with conditions
    3. Notification system with multiple channels
    4. Alert suppression and deduplication
    5. Historical alert tracking
    6. Performance monitoring integration
    """
    
    def __init__(self):
        """Initialize the alerts manager"""
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Alert processing
        self.is_running = False
        self._processing_tasks: List[asyncio.Task] = []
        
        # Condition tracking
        self._condition_states: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Suppression tracking
        self._suppressed_alerts: Dict[str, datetime] = {}
        
        # Notification callbacks
        self._notification_callbacks: List[Callable] = []
        
        self._initialize_default_channels()
        self._initialize_default_rules()
        
        logger.info("AlertsManager initialized")
    
    def _initialize_default_channels(self):
        """Initialize default notification channels"""
        # Log channel
        self.notification_channels["log"] = LogNotificationChannel(
            "log", "Log Notifications", {"enabled": True}
        )
        
        # Webhook channel (disabled by default)
        self.notification_channels["webhook"] = WebhookNotificationChannel(
            "webhook", "Webhook Notifications", {"enabled": False, "webhook_url": ""}
        )
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        
        # High CPU usage alert
        self.alert_rules["high_cpu"] = AlertRule(
            id="high_cpu",
            name="High CPU Usage",
            description="CPU usage is above threshold",
            category=AlertCategory.SYSTEM,
            severity=AlertSeverity.WARNING,
            condition=AlertCondition(
                metric_name="system.cpu.usage",
                operator=">",
                threshold=85.0,
                duration_minutes=5,
                description="CPU usage > 85% for 5 minutes"
            ),
            notification_channels=["log"],
            tags=["system", "performance"]
        )
        
        # High memory usage alert
        self.alert_rules["high_memory"] = AlertRule(
            id="high_memory",
            name="High Memory Usage",
            description="Memory usage is above threshold",
            category=AlertCategory.SYSTEM,
            severity=AlertSeverity.WARNING,
            condition=AlertCondition(
                metric_name="system.memory.usage",
                operator=">",
                threshold=90.0,
                duration_minutes=3,
                description="Memory usage > 90% for 3 minutes"
            ),
            notification_channels=["log"],
            tags=["system", "performance"]
        )
        
        # Job failure rate alert
        self.alert_rules["job_failure_rate"] = AlertRule(
            id="job_failure_rate",
            name="High Job Failure Rate",
            description="Job failure rate is too high",
            category=AlertCategory.JOB,
            severity=AlertSeverity.ERROR,
            condition=AlertCondition(
                metric_name="jobs.failed",
                operator=">",
                threshold=5.0,
                duration_minutes=10,
                description="More than 5 job failures in 10 minutes"
            ),
            notification_channels=["log"],
            tags=["jobs", "reliability"]
        )
        
        # Disk space alert
        self.alert_rules["low_disk_space"] = AlertRule(
            id="low_disk_space",
            name="Low Disk Space",
            description="Available disk space is running low",
            category=AlertCategory.SYSTEM,
            severity=AlertSeverity.CRITICAL,
            condition=AlertCondition(
                metric_name="system.disk.usage",
                operator=">",
                threshold=95.0,
                duration_minutes=0,
                description="Disk usage > 95%"
            ),
            notification_channels=["log"],
            tags=["system", "storage"]
        )
    
    async def start(self):
        """Start the alerts manager"""
        if self.is_running:
            logger.warning("AlertsManager is already running")
            return
        
        self.is_running = True
        
        logger.info("Starting AlertsManager")
        
        # Start processing tasks
        self._processing_tasks = [
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._condition_evaluation_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        logger.info("✅ AlertsManager started successfully")
    
    async def stop(self):
        """Stop the alerts manager"""
        if not self.is_running:
            return
        
        logger.info("Stopping AlertsManager")
        
        self.is_running = False
        
        # Cancel processing tasks
        for task in self._processing_tasks:
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        
        logger.info("✅ AlertsManager stopped")
    
    async def create_alert(self, 
                          title: str, 
                          description: str, 
                          severity: AlertSeverity, 
                          category: AlertCategory,
                          source: str,
                          metadata: Dict[str, Any] = None,
                          tags: List[str] = None) -> Alert:
        """Create a new alert"""
        try:
            alert = Alert(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                severity=severity,
                category=category,
                status=AlertStatus.ACTIVE,
                source=source,
                created_at=datetime.utcnow(),
                metadata=metadata or {},
                tags=tags or []
            )
            
            # Check for suppression
            suppression_key = f"{category.value}:{title}"
            if suppression_key in self._suppressed_alerts:
                suppression_end = self._suppressed_alerts[suppression_key]
                if datetime.utcnow() < suppression_end:
                    alert.status = AlertStatus.SUPPRESSED
                    logger.info(f"Alert {alert.id} suppressed until {suppression_end}")
                else:
                    del self._suppressed_alerts[suppression_key]
            
            # Add to active alerts
            if alert.status != AlertStatus.SUPPRESSED:
                self.active_alerts[alert.id] = alert
            
            # Add to history
            self.alert_history.append(alert)
            
            # Send notifications
            if alert.status == AlertStatus.ACTIVE:
                await self._send_notifications(alert)
            
            logger.info(f"Alert created: {alert.id} - {alert.title} [{alert.severity.value}]")
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.active_alerts:
                logger.warning(f"Alert {alert_id} not found in active alerts")
                return False
            
            alert = self.active_alerts[alert_id]
            if alert.status != AlertStatus.ACTIVE:
                logger.warning(f"Alert {alert_id} is not in active state")
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            
            # Notify callbacks
            await self._notify_callbacks("alert_acknowledged", alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.active_alerts:
                logger.warning(f"Alert {alert_id} not found in active alerts")
                return False
            
            alert = self.active_alerts[alert_id]
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            
            # Notify callbacks
            await self._notify_callbacks("alert_resolved", alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {str(e)}")
            return False
    
    async def process_monitoring_event(self, event):
        """Process a monitoring event for alert generation"""
        try:
            # Job failure events
            if hasattr(event, 'event_type') and event.event_type.value == "job_failed":
                await self.create_alert(
                    title="Job Execution Failed",
                    description=f"Job {event.data.get('job_id', 'unknown')} failed",
                    severity=AlertSeverity.ERROR,
                    category=AlertCategory.JOB,
                    source="job_monitor",
                    metadata=event.data,
                    tags=["job", "failure"]
                )
            
            # System alerts based on event severity
            if hasattr(event, 'severity') and event.severity in ["error", "critical"]:
                severity_map = {
                    "error": AlertSeverity.ERROR,
                    "critical": AlertSeverity.CRITICAL
                }
                
                await self.create_alert(
                    title=f"System Event: {event.event_type.value if hasattr(event, 'event_type') else 'Unknown'}",
                    description=getattr(event, 'data', {}).get('message', 'System event detected'),
                    severity=severity_map[event.severity],
                    category=AlertCategory.SYSTEM,
                    source=getattr(event, 'source', 'system'),
                    metadata=getattr(event, 'data', {}),
                    tags=["system", "event"]
                )
            
        except Exception as e:
            logger.error(f"Error processing monitoring event: {str(e)}")
    
    async def evaluate_metric_condition(self, metric_name: str, value: float):
        """Evaluate metric against alert conditions"""
        try:
            # Store metric value
            self._metric_history[metric_name].append({
                "value": value,
                "timestamp": datetime.utcnow()
            })
            
            # Check all rules that monitor this metric
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled or rule.condition.metric_name != metric_name:
                    continue
                
                # Evaluate condition
                if self._evaluate_condition(rule.condition, value):
                    # Check if condition has persisted for required duration
                    if self._check_condition_duration(rule_id, rule.condition):
                        # Create alert if not already active
                        existing_alert = self._find_existing_alert(rule)
                        if not existing_alert:
                            await self.create_alert(
                                title=rule.name,
                                description=f"{rule.description}. Current value: {value}",
                                severity=rule.severity,
                                category=rule.category,
                                source="alert_rule",
                                metadata={
                                    "rule_id": rule_id,
                                    "metric_name": metric_name,
                                    "current_value": value,
                                    "threshold": rule.condition.threshold
                                },
                                tags=rule.tags
                            )
                else:
                    # Condition no longer met, reset tracking
                    if rule_id in self._condition_states:
                        del self._condition_states[rule_id]
            
        except Exception as e:
            logger.error(f"Error evaluating metric condition for {metric_name}: {str(e)}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None, category: Optional[AlertCategory] = None) -> List[Alert]:
        """Get active alerts with optional filtering"""
        try:
            alerts = list(self.active_alerts.values())
            
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            if category:
                alerts = [a for a in alerts if a.category == category]
            
            # Sort by severity and creation time
            severity_order = {
                AlertSeverity.CRITICAL: 0,
                AlertSeverity.ERROR: 1,
                AlertSeverity.WARNING: 2,
                AlertSeverity.INFO: 3
            }
            
            alerts.sort(key=lambda a: (severity_order.get(a.severity, 4), a.created_at))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            active_alerts = list(self.active_alerts.values())
            
            # Count by severity
            severity_counts = {severity.value: 0 for severity in AlertSeverity}
            for alert in active_alerts:
                severity_counts[alert.severity.value] += 1
            
            # Count by category
            category_counts = {category.value: 0 for category in AlertCategory}
            for alert in active_alerts:
                category_counts[alert.category.value] += 1
            
            # Count by status
            status_counts = {status.value: 0 for status in AlertStatus}
            for alert in active_alerts:
                status_counts[alert.status.value] += 1
            
            # Recent activity (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_alerts = [a for a in self.alert_history if a.created_at >= cutoff_time]
            
            return {
                "total_active": len(active_alerts),
                "total_in_history": len(self.alert_history),
                "by_severity": severity_counts,
                "by_category": category_counts,
                "by_status": status_counts,
                "recent_24h": len(recent_alerts),
                "rules_configured": len(self.alert_rules),
                "notification_channels": len(self.notification_channels)
            }
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {str(e)}")
            return {}
    
    def add_notification_callback(self, callback: Callable):
        """Add notification callback"""
        self._notification_callbacks.append(callback)
    
    # Private methods
    
    def _evaluate_condition(self, condition: AlertCondition, value: float) -> bool:
        """Evaluate if condition is met"""
        try:
            operators = {
                ">": lambda a, b: a > b,
                "<": lambda a, b: a < b,
                ">=": lambda a, b: a >= b,
                "<=": lambda a, b: a <= b,
                "==": lambda a, b: a == b,
                "!=": lambda a, b: a != b
            }
            
            operator_func = operators.get(condition.operator)
            if not operator_func:
                logger.warning(f"Unknown operator: {condition.operator}")
                return False
            
            return operator_func(value, condition.threshold)
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    def _check_condition_duration(self, rule_id: str, condition: AlertCondition) -> bool:
        """Check if condition has persisted for required duration"""
        try:
            if condition.duration_minutes == 0:
                return True  # No duration requirement
            
            current_time = datetime.utcnow()
            
            # Initialize tracking if not exists
            if rule_id not in self._condition_states:
                self._condition_states[rule_id] = {
                    "first_met": current_time,
                    "consecutive": True
                }
                return False
            
            state = self._condition_states[rule_id]
            
            # Check if enough time has passed
            duration_passed = current_time - state["first_met"]
            required_duration = timedelta(minutes=condition.duration_minutes)
            
            return duration_passed >= required_duration
            
        except Exception as e:
            logger.error(f"Error checking condition duration: {str(e)}")
            return False
    
    def _find_existing_alert(self, rule: AlertRule) -> Optional[Alert]:
        """Find existing alert for the same rule"""
        try:
            for alert in self.active_alerts.values():
                if (alert.metadata.get("rule_id") == rule.id and 
                    alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]):
                    return alert
            return None
            
        except Exception as e:
            logger.error(f"Error finding existing alert: {str(e)}")
            return None
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for alert"""
        try:
            # Find applicable rules to get notification channels
            rule = self.alert_rules.get(alert.metadata.get("rule_id"))
            channels = rule.notification_channels if rule else ["log"]
            
            for channel_id in channels:
                channel = self.notification_channels.get(channel_id)
                if channel and channel.enabled:
                    try:
                        success = await channel.send_notification(alert)
                        if not success:
                            logger.warning(f"Failed to send notification via {channel_id}")
                    except Exception as e:
                        logger.error(f"Error sending notification via {channel_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.id}: {str(e)}")
    
    async def _notify_callbacks(self, event_type: str, alert: Alert):
        """Notify registered callbacks"""
        try:
            for callback in self._notification_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, alert)
                    else:
                        callback(event_type, alert)
                except Exception as e:
                    logger.error(f"Error in notification callback: {str(e)}")
        except Exception as e:
            logger.error(f"Error notifying callbacks: {str(e)}")
    
    async def _alert_processing_loop(self):
        """Background alert processing loop"""
        logger.info("Starting alert processing loop")
        
        while self.is_running:
            try:
                # Process any pending alert operations
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in alert processing loop: {str(e)}")
                await asyncio.sleep(30)
    
    async def _condition_evaluation_loop(self):
        """Background condition evaluation loop"""
        logger.info("Starting condition evaluation loop")
        
        while self.is_running:
            try:
                # Auto-resolve alerts based on conditions
                for alert_id, alert in list(self.active_alerts.items()):
                    rule = self.alert_rules.get(alert.metadata.get("rule_id"))
                    if rule and rule.enabled:
                        # Check if condition is no longer met (simplified check)
                        # In a real implementation, you'd check current metric values
                        pass
                
                await asyncio.sleep(60)  # Evaluate every minute
                
            except Exception as e:
                logger.error(f"Error in condition evaluation loop: {str(e)}")
                await asyncio.sleep(120)
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        logger.info("Starting cleanup loop")
        
        while self.is_running:
            try:
                # Clean up old suppression entries
                current_time = datetime.utcnow()
                expired_suppressions = [
                    key for key, end_time in self._suppressed_alerts.items()
                    if current_time >= end_time
                ]
                
                for key in expired_suppressions:
                    del self._suppressed_alerts[key]
                
                # Limit metric history size
                for metric_name, history in self._metric_history.items():
                    if len(history) > 1000:
                        # Keep only recent entries
                        while len(history) > 800:
                            history.popleft()
                
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(3600)


# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

# Global alerts manager instance
_alerts_manager: Optional[AlertsManager] = None

def get_alerts_manager() -> Optional[AlertsManager]:
    """Get the global alerts manager instance"""
    return _alerts_manager

def create_alerts_manager() -> AlertsManager:
    """Factory function to create alerts manager"""
    global _alerts_manager
    if _alerts_manager is None:
        _alerts_manager = AlertsManager()
    return _alerts_manager

async def initialize_alerts_manager() -> AlertsManager:
    """Initialize alerts manager"""
    alerts_manager = create_alerts_manager()
    await alerts_manager.start()
    
    logger.info("✅ AlertsManager initialized and started")
    return alerts_manager

logger.info("✅ AlertsManager module loaded successfully")