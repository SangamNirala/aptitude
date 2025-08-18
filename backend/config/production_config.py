"""
Production Configuration Management
Handles environment-specific settings, validation, and optimization for production deployment
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
import json
from pathlib import Path


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):
    """Database configuration with production optimizations"""
    mongo_url: str
    db_name: str
    max_pool_size: int = Field(default=100, ge=10, le=500)
    min_pool_size: int = Field(default=10, ge=5, le=50)
    max_idle_time_ms: int = Field(default=30000, ge=10000, le=300000)
    connection_timeout_ms: int = Field(default=10000, ge=5000, le=30000)
    server_selection_timeout_ms: int = Field(default=10000, ge=5000, le=30000)
    
    @validator('max_pool_size')
    def validate_pool_size(cls, v, values):
        min_pool = values.get('min_pool_size', 10)
        if v <= min_pool:
            raise ValueError(f'max_pool_size ({v}) must be greater than min_pool_size ({min_pool})')
        return v


class LoggingConfig(BaseModel):
    """Structured logging configuration for production"""
    level: str = Field(default="INFO")
    format_type: str = Field(default="json")  # json or text
    max_file_size_mb: int = Field(default=100, ge=10, le=1000)
    backup_count: int = Field(default=5, ge=3, le=20)
    log_directory: str = Field(default="/var/log/ai-scraping")
    enable_structured_logs: bool = Field(default=True)
    enable_performance_logs: bool = Field(default=True)
    enable_security_logs: bool = Field(default=True)
    
    @validator('level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}. Must be one of {valid_levels}')
        return v.upper()


class SecurityConfig(BaseModel):
    """Security configuration for production deployment"""
    enable_cors_validation: bool = Field(default=True)
    allowed_origins: List[str] = Field(default=["https://*.emergentagent.com"])
    enable_rate_limiting: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=1000, ge=100, le=10000)
    enable_api_key_validation: bool = Field(default=True)
    session_timeout_minutes: int = Field(default=60, ge=15, le=480)
    max_request_size_mb: int = Field(default=10, ge=1, le=100)
    enable_request_logging: bool = Field(default=True)


class PerformanceConfig(BaseModel):
    """Performance optimization configuration"""
    enable_caching: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    max_concurrent_requests: int = Field(default=100, ge=10, le=1000)
    request_timeout_seconds: int = Field(default=30, ge=10, le=300)
    enable_compression: bool = Field(default=True)
    enable_connection_pooling: bool = Field(default=True)
    worker_processes: int = Field(default=4, ge=1, le=16)
    max_memory_mb: int = Field(default=2048, ge=512, le=8192)


class MonitoringConfig(BaseModel):
    """Monitoring and alerting configuration"""
    enable_health_checks: bool = Field(default=True)
    health_check_interval_seconds: int = Field(default=30, ge=10, le=300)
    enable_performance_monitoring: bool = Field(default=True)
    enable_error_tracking: bool = Field(default=True)
    alert_on_error_rate_percent: float = Field(default=5.0, ge=1.0, le=20.0)
    alert_on_response_time_ms: int = Field(default=5000, ge=1000, le=30000)
    metrics_retention_days: int = Field(default=30, ge=7, le=90)
    enable_real_time_alerts: bool = Field(default=True)


class ProductionConfig(BaseModel):
    """Complete production configuration"""
    environment: EnvironmentType = Field(default=EnvironmentType.PRODUCTION)
    app_name: str = Field(default="ai-enhanced-scraping-system")
    version: str = Field(default="2.0.0")
    debug_mode: bool = Field(default=False)
    
    # Component configurations
    database: DatabaseConfig
    logging: LoggingConfig
    security: SecurityConfig
    performance: PerformanceConfig
    monitoring: MonitoringConfig
    
    # AI Services configuration
    ai_service_timeout_seconds: int = Field(default=60, ge=10, le=300)
    ai_service_retry_attempts: int = Field(default=3, ge=1, le=10)
    ai_service_batch_size: int = Field(default=10, ge=1, le=100)
    
    # Scraping configuration
    max_concurrent_scraping_jobs: int = Field(default=5, ge=1, le=20)
    scraping_timeout_minutes: int = Field(default=60, ge=10, le=240)
    max_questions_per_job: int = Field(default=1000, ge=100, le=10000)
    
    @validator('environment')
    def validate_production_settings(cls, v, values):
        if v == EnvironmentType.PRODUCTION:
            # Ensure debug is disabled in production
            if values.get('debug_mode', False):
                raise ValueError("Debug mode must be disabled in production")
        return v


class ProductionConfigManager:
    """Manages production configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[ProductionConfig] = None
        self._logger = logging.getLogger(__name__)
    
    def _get_default_config_path(self) -> str:
        """Get default configuration path based on environment"""
        env = os.getenv('ENVIRONMENT', 'development')
        return f"/app/config/{env}.json"
    
    def load_config(self) -> ProductionConfig:
        """Load and validate production configuration"""
        try:
            # Load from environment variables first
            config_data = self._load_from_env()
            
            # Override with file-based config if exists
            if os.path.exists(self.config_path):
                file_config = self._load_from_file()
                config_data.update(file_config)
            
            # Validate and create configuration
            self.config = ProductionConfig(**config_data)
            self._logger.info(f"✅ Production configuration loaded successfully")
            return self.config
            
        except Exception as e:
            self._logger.error(f"❌ Failed to load production configuration: {str(e)}")
            raise
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            "environment": os.getenv('ENVIRONMENT', 'production'),
            "app_name": os.getenv('APP_NAME', 'ai-enhanced-scraping-system'),
            "version": os.getenv('APP_VERSION', '2.0.0'),
            "debug_mode": os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            
            "database": {
                "mongo_url": os.getenv('MONGO_URL'),
                "db_name": os.getenv('DB_NAME', 'production_database'),
                "max_pool_size": int(os.getenv('DB_MAX_POOL_SIZE', '100')),
                "min_pool_size": int(os.getenv('DB_MIN_POOL_SIZE', '10')),
                "max_idle_time_ms": int(os.getenv('DB_MAX_IDLE_TIME_MS', '30000')),
                "connection_timeout_ms": int(os.getenv('DB_CONNECTION_TIMEOUT_MS', '10000')),
                "server_selection_timeout_ms": int(os.getenv('DB_SERVER_SELECTION_TIMEOUT_MS', '10000')),
            },
            
            "logging": {
                "level": os.getenv('LOG_LEVEL', 'INFO'),
                "format_type": os.getenv('LOG_FORMAT', 'json'),
                "max_file_size_mb": int(os.getenv('LOG_MAX_FILE_SIZE_MB', '100')),
                "backup_count": int(os.getenv('LOG_BACKUP_COUNT', '5')),
                "log_directory": os.getenv('LOG_DIRECTORY', '/var/log/ai-scraping'),
                "enable_structured_logs": os.getenv('ENABLE_STRUCTURED_LOGS', 'true').lower() == 'true',
                "enable_performance_logs": os.getenv('ENABLE_PERFORMANCE_LOGS', 'true').lower() == 'true',
                "enable_security_logs": os.getenv('ENABLE_SECURITY_LOGS', 'true').lower() == 'true',
            },
            
            "security": {
                "enable_cors_validation": os.getenv('ENABLE_CORS_VALIDATION', 'true').lower() == 'true',
                "allowed_origins": os.getenv('CORS_ORIGINS', 'https://*.emergentagent.com').split(','),
                "enable_rate_limiting": os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
                "rate_limit_per_minute": int(os.getenv('RATE_LIMIT_PER_MINUTE', '1000')),
                "enable_api_key_validation": os.getenv('ENABLE_API_KEY_VALIDATION', 'true').lower() == 'true',
                "session_timeout_minutes": int(os.getenv('SESSION_TIMEOUT_MINUTES', '60')),
                "max_request_size_mb": int(os.getenv('MAX_REQUEST_SIZE_MB', '10')),
                "enable_request_logging": os.getenv('ENABLE_REQUEST_LOGGING', 'true').lower() == 'true',
            },
            
            "performance": {
                "enable_caching": os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
                "cache_ttl_seconds": int(os.getenv('CACHE_TTL_SECONDS', '3600')),
                "max_concurrent_requests": int(os.getenv('MAX_CONCURRENT_REQUESTS', '100')),
                "request_timeout_seconds": int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30')),
                "enable_compression": os.getenv('ENABLE_COMPRESSION', 'true').lower() == 'true',
                "enable_connection_pooling": os.getenv('ENABLE_CONNECTION_POOLING', 'true').lower() == 'true',
                "worker_processes": int(os.getenv('WORKER_PROCESSES', '4')),
                "max_memory_mb": int(os.getenv('MAX_MEMORY_MB', '2048')),
            },
            
            "monitoring": {
                "enable_health_checks": os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
                "health_check_interval_seconds": int(os.getenv('HEALTH_CHECK_INTERVAL_SECONDS', '30')),
                "enable_performance_monitoring": os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
                "enable_error_tracking": os.getenv('ENABLE_ERROR_TRACKING', 'true').lower() == 'true',
                "alert_on_error_rate_percent": float(os.getenv('ALERT_ON_ERROR_RATE_PERCENT', '5.0')),
                "alert_on_response_time_ms": int(os.getenv('ALERT_ON_RESPONSE_TIME_MS', '5000')),
                "metrics_retention_days": int(os.getenv('METRICS_RETENTION_DAYS', '30')),
                "enable_real_time_alerts": os.getenv('ENABLE_REAL_TIME_ALERTS', 'true').lower() == 'true',
            },
            
            # AI and Scraping configurations
            "ai_service_timeout_seconds": int(os.getenv('AI_SERVICE_TIMEOUT_SECONDS', '60')),
            "ai_service_retry_attempts": int(os.getenv('AI_SERVICE_RETRY_ATTEMPTS', '3')),
            "ai_service_batch_size": int(os.getenv('AI_SERVICE_BATCH_SIZE', '10')),
            "max_concurrent_scraping_jobs": int(os.getenv('MAX_CONCURRENT_SCRAPING_JOBS', '5')),
            "scraping_timeout_minutes": int(os.getenv('SCRAPING_TIMEOUT_MINUTES', '60')),
            "max_questions_per_job": int(os.getenv('MAX_QUESTIONS_PER_JOB', '1000')),
        }
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self._logger.warning(f"Could not load config file {self.config_path}: {str(e)}")
            return {}
    
    def save_config(self, config: ProductionConfig):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config.dict(), f, indent=2)
            self._logger.info(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            self._logger.error(f"❌ Failed to save configuration: {str(e)}")
            raise
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return validation report"""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        validation_report = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Validate database configuration
        if self.config.database.max_pool_size < 50:
            validation_report["warnings"].append("Database max_pool_size is low for production")
        
        # Validate security settings
        if not self.config.security.enable_rate_limiting:
            validation_report["warnings"].append("Rate limiting is disabled")
        
        # Validate performance settings
        if self.config.performance.max_concurrent_requests < 50:
            validation_report["recommendations"].append("Consider increasing max_concurrent_requests for production")
        
        # Validate monitoring
        if not self.config.monitoring.enable_error_tracking:
            validation_report["errors"].append("Error tracking should be enabled in production")
            validation_report["valid"] = False
        
        return validation_report
    
    def get_config(self) -> ProductionConfig:
        """Get current configuration"""
        if not self.config:
            return self.load_config()
        return self.config


# Global configuration manager instance
production_config_manager = ProductionConfigManager()


def get_production_config() -> ProductionConfig:
    """Get production configuration singleton"""
    return production_config_manager.get_config()


def validate_production_readiness() -> bool:
    """Validate if system is ready for production deployment"""
    try:
        config = get_production_config()
        validation_report = production_config_manager.validate_configuration()
        
        if not validation_report["valid"]:
            logging.error(f"❌ Production validation failed: {validation_report['errors']}")
            return False
        
        if validation_report["warnings"]:
            logging.warning(f"⚠️ Production warnings: {validation_report['warnings']}")
        
        logging.info("✅ System validated for production deployment")
        return True
        
    except Exception as e:
        logging.error(f"❌ Production validation error: {str(e)}")
        return False