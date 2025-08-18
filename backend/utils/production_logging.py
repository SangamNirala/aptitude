"""
Production Logging System
Advanced structured logging with JSON format, log rotation, and performance monitoring
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from contextlib import contextmanager
import traceback
import threading
import time
from functools import wraps

from config.production_config import get_production_config


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self):
        super().__init__()
        
    def format(self, record):
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        extra_fields = {
            key: value for key, value in record.__dict__.items()
            if key not in log_entry and not key.startswith('_') and key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            ]
        }
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class PerformanceLogger:
    """Logger for performance metrics and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        self._metrics = {}
        self._lock = threading.Lock()
    
    def log_request(self, method: str, endpoint: str, status_code: int, 
                   duration_ms: float, user_id: Optional[str] = None):
        """Log API request performance"""
        self.logger.info(
            "API Request",
            extra={
                "event_type": "api_request",
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
            }
        )
        
        # Update metrics
        with self._lock:
            key = f"{method}:{endpoint}"
            if key not in self._metrics:
                self._metrics[key] = {"count": 0, "total_duration": 0, "error_count": 0}
            
            self._metrics[key]["count"] += 1
            self._metrics[key]["total_duration"] += duration_ms
            
            if status_code >= 400:
                self._metrics[key]["error_count"] += 1
    
    def log_scraping_performance(self, source: str, questions_extracted: int, 
                               duration_seconds: float, success: bool):
        """Log scraping performance metrics"""
        self.logger.info(
            "Scraping Performance",
            extra={
                "event_type": "scraping_performance",
                "source": source,
                "questions_extracted": questions_extracted,
                "duration_seconds": duration_seconds,
                "success": success,
                "extraction_rate": questions_extracted / duration_seconds if duration_seconds > 0 else 0
            }
        )
    
    def log_ai_processing(self, service: str, operation: str, duration_ms: float, 
                         success: bool, error_message: Optional[str] = None):
        """Log AI service performance"""
        self.logger.info(
            "AI Processing",
            extra={
                "event_type": "ai_processing",
                "service": service,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "error_message": error_message
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self._lock:
            metrics = {}
            for key, data in self._metrics.items():
                metrics[key] = {
                    "count": data["count"],
                    "average_duration_ms": data["total_duration"] / data["count"] if data["count"] > 0 else 0,
                    "error_rate": data["error_count"] / data["count"] if data["count"] > 0 else 0,
                    "total_errors": data["error_count"]
                }
            return metrics


class SecurityLogger:
    """Logger for security events and audit trails"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str, 
                          user_agent: Optional[str] = None):
        """Log authentication events"""
        self.logger.info(
            "Authentication Event",
            extra={
                "event_type": "authentication",
                "user_id": user_id,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "security_level": "HIGH" if not success else "INFO"
            }
        )
    
    def log_rate_limit_violation(self, ip_address: str, endpoint: str, current_rate: int):
        """Log rate limiting violations"""
        self.logger.warning(
            "Rate Limit Violation",
            extra={
                "event_type": "rate_limit_violation",
                "ip_address": ip_address,
                "endpoint": endpoint,
                "current_rate": current_rate,
                "security_level": "HIGH"
            }
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any], 
                               severity: str = "MEDIUM"):
        """Log suspicious security activities"""
        self.logger.warning(
            "Suspicious Activity",
            extra={
                "event_type": "suspicious_activity",
                "activity_type": activity_type,
                "details": details,
                "security_level": severity
            }
        )


class ProductionLoggerSetup:
    """Setup and configure production logging system"""
    
    def __init__(self):
        self.config = get_production_config()
        self.performance_logger = PerformanceLogger()
        self.security_logger = SecurityLogger()
        self._setup_complete = False
    
    def setup_logging(self):
        """Configure production logging system"""
        if self._setup_complete:
            return
        
        # Create log directory
        log_dir = Path(self.config.logging.log_directory)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.logging.level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Setup formatters
        if self.config.logging.format_type == "json":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Application log file with rotation
        app_log_file = log_dir / "application.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.logging.backup_count
        )
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)
        
        # Performance log file
        if self.config.logging.enable_performance_logs:
            perf_log_file = log_dir / "performance.log"
            perf_handler = logging.handlers.RotatingFileHandler(
                perf_log_file,
                maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.logging.backup_count
            )
            perf_handler.setFormatter(formatter)
            
            perf_logger = logging.getLogger('performance')
            perf_logger.addHandler(perf_handler)
            perf_logger.setLevel(logging.INFO)
            perf_logger.propagate = False
        
        # Security log file
        if self.config.logging.enable_security_logs:
            security_log_file = log_dir / "security.log"
            security_handler = logging.handlers.RotatingFileHandler(
                security_log_file,
                maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.logging.backup_count
            )
            security_handler.setFormatter(formatter)
            
            security_logger = logging.getLogger('security')
            security_logger.addHandler(security_handler)
            security_logger.setLevel(logging.INFO)
            security_logger.propagate = False
        
        # Error log file
        error_log_file = log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.logging.backup_count
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        self._setup_complete = True
        logging.info("✅ Production logging system initialized")


# Decorators for automatic logging
def log_performance(operation_name: str = None):
    """Decorator to automatically log function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger = logging.getLogger('performance')
                logger.info(
                    f"Operation completed: {operation}",
                    extra={
                        "event_type": "operation_performance",
                        "operation": operation,
                        "duration_ms": duration_ms,
                        "success": True
                    }
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger = logging.getLogger('performance')
                logger.error(
                    f"Operation failed: {operation}",
                    extra={
                        "event_type": "operation_performance",
                        "operation": operation,
                        "duration_ms": duration_ms,
                        "success": False,
                        "error_message": str(e)
                    }
                )
                
                raise
        
        return wrapper
    return decorator


@contextmanager
def log_operation(operation_name: str, logger: Optional[logging.Logger] = None):
    """Context manager for logging operations with timing"""
    if logger is None:
        logger = logging.getLogger()
    
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}")
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Operation completed: {operation_name}",
            extra={
                "event_type": "operation_completed",
                "operation": operation_name,
                "duration_ms": duration_ms,
                "success": True
            }
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Operation failed: {operation_name}",
            extra={
                "event_type": "operation_failed",
                "operation": operation_name,
                "duration_ms": duration_ms,
                "success": False,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise


# Global logger setup instance
production_logger = ProductionLoggerSetup()


def setup_production_logging():
    """Initialize production logging system"""
    production_logger.setup_logging()


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance"""
    return production_logger.performance_logger


def get_security_logger() -> SecurityLogger:
    """Get security logger instance"""
    return production_logger.security_logger