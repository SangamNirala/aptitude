"""
Scraping Utilities Package
Utilities for web scraping operations including anti-detection, rate limiting, proxy management,
content validation, and performance monitoring
"""

from .anti_detection import AntiDetectionManager, DetectionRiskLevel, UserAgentProfile
from .rate_limiter import RateLimiter, ExponentialBackoffLimiter, AdaptiveRateLimiter
from .proxy_manager import ProxyManager, ProxyConfig, ProxyType, ProxyStatus
from .ethical_crawler import EthicalCrawler, CrawlingSession, CrawlingBehaviorConfig
from .content_validator import (
    ContentValidator, ContentQualityScore, ValidationIssue, ValidationSeverity,
    create_indiabix_validator, create_geeksforgeeks_validator, validate_extracted_question
)
from .performance_monitor import (
    PerformanceMonitor, PerformanceAlert, PerformanceThresholds, OperationMetrics,
    PerformanceLevel, ResourceSnapshot, PerformanceAnalyzer,
    create_scraping_performance_monitor, create_high_volume_monitor, 
    get_global_monitor, cleanup_global_monitor
)

__all__ = [
    # Anti-Detection
    'AntiDetectionManager',
    'DetectionRiskLevel', 
    'UserAgentProfile',
    
    # Rate Limiting
    'RateLimiter',
    'ExponentialBackoffLimiter',
    'AdaptiveRateLimiter',
    
    # Proxy Management
    'ProxyManager',
    'ProxyConfig',
    'ProxyType',
    'ProxyStatus',
    
    # Ethical Crawling
    'EthicalCrawler',
    'CrawlingSession',
    'CrawlingBehaviorConfig',
    
    # Content Validation
    'ContentValidator',
    'ContentQualityScore', 
    'ValidationIssue',
    'ValidationSeverity',
    'create_indiabix_validator',
    'create_geeksforgeeks_validator',
    'validate_extracted_question',
    
    # Performance Monitoring
    'PerformanceMonitor',
    'PerformanceAlert',
    'PerformanceThresholds',
    'OperationMetrics',
    'PerformanceLevel',
    'ResourceSnapshot',
    'PerformanceAnalyzer',
    'create_scraping_performance_monitor',
    'create_high_volume_monitor',
    'get_global_monitor',
    'cleanup_global_monitor'
]