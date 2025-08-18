"""
Error Tracking and Monitoring System
Comprehensive error handling, tracking, and alerting for production deployment
"""

import logging
import traceback
import sys
import threading
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path
import hashlib
import os

from config.production_config import get_production_config
from utils.production_logging import get_security_logger


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    APPLICATION = "application"
    DATABASE = "database"
    AI_SERVICE = "ai_service"
    SCRAPING = "scraping"
    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    NETWORK = "network"
    VALIDATION = "validation"
    SYSTEM = "system"


@dataclass
class ErrorEvent:
    """Represents a single error event"""
    id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    traceback_info: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    fingerprint: Optional[str] = None
    count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    resolved: bool = False
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp
        if self.fingerprint is None:
            self.fingerprint = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint for error grouping"""
        content = f"{self.exception_type}:{self.message}:{self.category}"
        return hashlib.md5(content.encode()).hexdigest()


class ErrorAggregator:
    """Aggregates and groups similar errors"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: Dict[str, ErrorEvent] = {}
        self.recent_events: deque = deque(maxlen=max_events)
        self.lock = threading.Lock()
        self.severity_counts = defaultdict(int)
        self.category_counts = defaultdict(int)
    
    def add_error(self, error_event: ErrorEvent) -> str:
        """Add error event and return its fingerprint"""
        with self.lock:
            fingerprint = error_event.fingerprint
            
            if fingerprint in self.events:
                # Update existing error
                existing = self.events[fingerprint]
                existing.count += 1
                existing.last_seen = error_event.timestamp
                # Update context with new information
                existing.context.update(error_event.context)
            else:
                # Add new error
                self.events[fingerprint] = error_event
                
                # Maintain max events limit
                if len(self.events) > self.max_events:
                    # Remove oldest errors (simple cleanup)
                    oldest_key = min(self.events.keys(), 
                                   key=lambda k: self.events[k].first_seen)
                    del self.events[oldest_key]
            
            # Update counts
            self.severity_counts[error_event.severity] += 1
            self.category_counts[error_event.category] += 1
            
            # Add to recent events
            self.recent_events.append(error_event)
            
            return fingerprint
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self.lock:
            total_errors = len(self.events)
            total_occurrences = sum(event.count for event in self.events.values())
            
            # Recent errors (last hour)
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_errors = [
                event for event in self.recent_events
                if event.timestamp >= one_hour_ago
            ]
            
            return {
                "total_unique_errors": total_errors,
                "total_occurrences": total_occurrences,
                "recent_errors_1h": len(recent_errors),
                "severity_breakdown": dict(self.severity_counts),
                "category_breakdown": dict(self.category_counts),
                "error_rate_1h": len(recent_errors) / 60 if recent_errors else 0,  # errors per minute
            }
    
    def get_top_errors(self, limit: int = 10) -> List[ErrorEvent]:
        """Get top errors by occurrence count"""
        with self.lock:
            return sorted(
                self.events.values(),
                key=lambda e: e.count,
                reverse=True
            )[:limit]
    
    def get_critical_errors(self) -> List[ErrorEvent]:
        """Get all critical errors"""
        with self.lock:
            return [
                event for event in self.events.values()
                if event.severity == ErrorSeverity.CRITICAL and not event.resolved
            ]


class AlertManager:
    """Manages error-based alerting"""
    
    def __init__(self):
        self.config = get_production_config()
        self.alert_rules: List[Callable[[ErrorEvent], bool]] = []
        self.alert_handlers: List[Callable[[ErrorEvent, str], None]] = []
        self.alert_history: deque = deque(maxlen=1000)
        self.lock = threading.Lock()
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alerting rules"""
        # Critical errors always trigger alerts
        self.add_alert_rule(
            lambda error: error.severity == ErrorSeverity.CRITICAL,
            "Critical error detected"
        )
        
        # High frequency errors
        self.add_alert_rule(
            lambda error: error.count >= 10,
            "High frequency error detected"
        )
        
        # AI service failures
        self.add_alert_rule(
            lambda error: error.category == ErrorCategory.AI_SERVICE and error.count >= 3,
            "AI service failures detected"
        )
    
    def add_alert_rule(self, condition: Callable[[ErrorEvent], bool], message: str):
        """Add custom alert rule"""
        self.alert_rules.append((condition, message))
    
    def add_alert_handler(self, handler: Callable[[ErrorEvent, str], None]):
        """Add alert handler (e.g., email, webhook, etc.)"""
        self.alert_handlers.append(handler)
    
    def check_alerts(self, error_event: ErrorEvent):
        """Check if error triggers any alerts"""
        with self.lock:
            for condition, message in self.alert_rules:
                if condition(error_event):
                    self._trigger_alert(error_event, message)
    
    def _trigger_alert(self, error_event: ErrorEvent, alert_message: str):
        """Trigger alert for error event"""
        alert_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_id": error_event.id,
            "fingerprint": error_event.fingerprint,
            "severity": error_event.severity,
            "category": error_event.category,
            "message": alert_message,
            "error_message": error_event.message,
            "count": error_event.count,
            "context": error_event.context
        }
        
        # Log alert
        logger = logging.getLogger('alerts')
        logger.critical(
            f"ALERT: {alert_message}",
            extra={
                "event_type": "error_alert",
                "alert_data": alert_data
            }
        )
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(error_event, alert_message)
            except Exception as e:
                logging.error(f"Alert handler failed: {str(e)}")
        
        # Store in alert history
        self.alert_history.append(alert_data)


class ErrorTracker:
    """Main error tracking system"""
    
    def __init__(self):
        self.config = get_production_config()
        self.aggregator = ErrorAggregator()
        self.alert_manager = AlertManager()
        self.logger = logging.getLogger('error_tracker')
        self.security_logger = get_security_logger()
        self._original_excepthook = None
        
        # Setup default alert handlers
        self._setup_alert_handlers()
    
    def _setup_alert_handlers(self):
        """Setup default alert handlers"""
        # Log-based alert handler
        def log_alert_handler(error_event: ErrorEvent, message: str):
            self.logger.critical(
                f"PRODUCTION ALERT: {message}",
                extra={
                    "error_fingerprint": error_event.fingerprint,
                    "error_count": error_event.count,
                    "severity": error_event.severity,
                    "category": error_event.category
                }
            )
        
        self.alert_manager.add_alert_handler(log_alert_handler)
        
        # Security alert handler for authentication errors
        def security_alert_handler(error_event: ErrorEvent, message: str):
            if error_event.category == ErrorCategory.AUTHENTICATION:
                self.security_logger.log_suspicious_activity(
                    "authentication_error_spike",
                    {
                        "error_count": error_event.count,
                        "error_message": error_event.message,
                        "ip_address": error_event.ip_address,
                        "endpoint": error_event.endpoint
                    },
                    "HIGH"
                )
        
        self.alert_manager.add_alert_handler(security_alert_handler)
    
    def capture_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None,
                         category: ErrorCategory = ErrorCategory.APPLICATION,
                         severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                         user_id: Optional[str] = None,
                         ip_address: Optional[str] = None,
                         endpoint: Optional[str] = None,
                         method: Optional[str] = None,
                         request_id: Optional[str] = None) -> str:
        """Capture and track an exception"""
        
        # Determine severity based on exception type
        if isinstance(exception, (SystemExit, KeyboardInterrupt)):
            severity = ErrorSeverity.CRITICAL
        elif isinstance(exception, (MemoryError, OSError)):
            severity = ErrorSeverity.HIGH
        elif isinstance(exception, (ValueError, TypeError, AttributeError)):
            severity = ErrorSeverity.MEDIUM
        
        # Create error event
        error_event = ErrorEvent(
            id=f"error_{int(time.time())}_{threading.get_ident()}",
            timestamp=datetime.now(timezone.utc),
            severity=severity,
            category=category,
            message=str(exception),
            exception_type=exception.__class__.__name__,
            traceback_info=traceback.format_exc(),
            context=context or {},
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
            method=method,
            request_id=request_id
        )
        
        # Add to aggregator
        fingerprint = self.aggregator.add_error(error_event)
        
        # Check for alerts
        self.alert_manager.check_alerts(error_event)
        
        # Log the error
        self.logger.error(
            f"Exception captured: {exception}",
            extra={
                "error_id": error_event.id,
                "fingerprint": fingerprint,
                "severity": severity.value,
                "category": category.value,
                "context": context
            },
            exc_info=True
        )
        
        return fingerprint
    
    def capture_message(self, message: str, level: str = "error",
                       context: Optional[Dict[str, Any]] = None,
                       category: ErrorCategory = ErrorCategory.APPLICATION,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
        """Capture a custom error message"""
        
        # Create a custom exception for consistent handling
        class CapturedMessage(Exception):
            pass
        
        try:
            raise CapturedMessage(message)
        except CapturedMessage as e:
            return self.capture_exception(
                e, context=context, category=category, severity=severity
            )
    
    def get_error_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive error data for dashboard"""
        stats = self.aggregator.get_error_stats()
        top_errors = self.aggregator.get_top_errors(10)
        critical_errors = self.aggregator.get_critical_errors()
        
        return {
            "statistics": stats,
            "top_errors": [
                {
                    "fingerprint": error.fingerprint,
                    "message": error.message,
                    "count": error.count,
                    "severity": error.severity.value,
                    "category": error.category.value,
                    "first_seen": error.first_seen.isoformat(),
                    "last_seen": error.last_seen.isoformat()
                }
                for error in top_errors
            ],
            "critical_errors": [
                {
                    "fingerprint": error.fingerprint,
                    "message": error.message,
                    "count": error.count,
                    "first_seen": error.first_seen.isoformat(),
                    "last_seen": error.last_seen.isoformat(),
                    "context": error.context
                }
                for error in critical_errors
            ],
            "recent_alerts": list(self.alert_manager.alert_history)[-10:]
        }
    
    def install_global_handler(self):
        """Install global exception handler"""
        if self._original_excepthook is None:
            self._original_excepthook = sys.excepthook
            
            def error_tracker_excepthook(exc_type, exc_value, exc_traceback):
                if exc_type != KeyboardInterrupt:
                    self.capture_exception(
                        exc_value,
                        context={"global_exception": True},
                        severity=ErrorSeverity.CRITICAL
                    )
                
                # Call original handler
                self._original_excepthook(exc_type, exc_value, exc_traceback)
            
            sys.excepthook = error_tracker_excepthook
            self.logger.info("✅ Global exception handler installed")
    
    def uninstall_global_handler(self):
        """Uninstall global exception handler"""
        if self._original_excepthook is not None:
            sys.excepthook = self._original_excepthook
            self._original_excepthook = None
            self.logger.info("Global exception handler uninstalled")


# Global error tracker instance
error_tracker = ErrorTracker()


def capture_exception(exception: Exception, **kwargs) -> str:
    """Convenience function to capture exceptions"""
    return error_tracker.capture_exception(exception, **kwargs)


def capture_message(message: str, **kwargs) -> str:
    """Convenience function to capture messages"""
    return error_tracker.capture_message(message, **kwargs)


def get_error_dashboard_data() -> Dict[str, Any]:
    """Get error dashboard data"""
    return error_tracker.get_error_dashboard_data()


def setup_error_tracking():
    """Initialize error tracking system"""
    error_tracker.install_global_handler()
    logging.info("✅ Error tracking system initialized")


# Decorator for automatic exception capture
def track_errors(category: ErrorCategory = ErrorCategory.APPLICATION,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator to automatically track errors in functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracker.capture_exception(
                    e,
                    context={
                        "function": f"{func.__module__}.{func.__name__}",
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    category=category,
                    severity=severity
                )
                raise
        return wrapper
    return decorator