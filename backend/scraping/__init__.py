"""
Scraping Module - AI-Enhanced Web Scraping & Data Collection System
Comprehensive scraping infrastructure for aptitude questions from multiple sources
"""

# Version and metadata
__version__ = "1.0.0"
__description__ = "Comprehensive web scraping infrastructure for educational content extraction"

# Core scraping engine
from .scraper_engine import (
    ScrapingEngine, ScrapingEngineConfig, JobProgress, ScrapingStats,
    create_scraping_engine, create_quick_scraping_job, 
    get_scraping_engine, shutdown_scraping_engine
)

# Drivers
from .drivers.selenium_driver import SeleniumDriver, SeleniumConfig, create_selenium_driver
from .drivers.playwright_driver import PlaywrightDriver, PlaywrightConfig, create_playwright_driver

# Extractors
from .extractors.base_extractor import (
    BaseContentExtractor, ExtractionResult, BatchExtractionResult, 
    PageExtractionContext, create_extraction_context, merge_batch_results
)
from .extractors.indiabix_extractor import IndiaBixExtractor, create_indiabix_extractor
from .extractors.geeksforgeeks_extractor import GeeksforGeeksExtractor, create_geeksforgeeks_extractor

# Utilities
from .utils.anti_detection import AntiDetectionManager, create_anti_detection_manager
from .utils.rate_limiter import (
    RateLimiter, ExponentialBackoffLimiter, AdaptiveRateLimiter,
    RateLimitConfig, create_rate_limiter, RateLimiterManager
)
from .utils.proxy_manager import ProxyManager, ProxyConfig, create_proxy_manager
from .utils.ethical_crawler import EthicalCrawler, EthicalCrawlConfig, create_ethical_crawler
from .utils.content_validator import (
    ContentValidator, ContentQualityScore, ValidationIssue, ValidationSeverity,
    create_indiabix_validator, create_geeksforgeeks_validator,
    validate_extracted_question, validate_with_quality_gate
)
from .utils.performance_monitor import (
    PerformanceMonitor, PerformanceThresholds, PerformanceAnalyzer,
    create_performance_monitor, create_extraction_monitor
)

__all__ = [
    # Core Engine
    'ScrapingEngine', 'ScrapingEngineConfig', 'JobProgress', 'ScrapingStats',
    'create_scraping_engine', 'create_quick_scraping_job',
    'get_scraping_engine', 'shutdown_scraping_engine',
    
    # Drivers
    'SeleniumDriver', 'SeleniumConfig', 'create_selenium_driver',
    'PlaywrightDriver', 'PlaywrightConfig', 'create_playwright_driver',
    
    # Extractors
    'BaseContentExtractor', 'ExtractionResult', 'BatchExtractionResult',
    'PageExtractionContext', 'create_extraction_context', 'merge_batch_results',
    'IndiaBixExtractor', 'create_indiabix_extractor',
    'GeeksforGeeksExtractor', 'create_geeksforgeeks_extractor',
    
    # Anti-Detection
    'AntiDetectionManager', 'create_anti_detection_manager',
    
    # Rate Limiting  
    'RateLimiter', 'ExponentialBackoffLimiter', 'AdaptiveRateLimiter',
    'RateLimitConfig', 'create_rate_limiter', 'RateLimiterManager',
    
    # Proxy Management
    'ProxyManager', 'ProxyConfig', 'create_proxy_manager',
    
    # Ethical Crawling
    'EthicalCrawler', 'EthicalCrawlConfig', 'create_ethical_crawler',
    
    # Content Validation
    'ContentValidator', 'ContentQualityScore', 'ValidationIssue', 'ValidationSeverity',
    'create_indiabix_validator', 'create_geeksforgeeks_validator',
    'validate_extracted_question', 'validate_with_quality_gate',
    
    # Performance Monitoring
    'PerformanceMonitor', 'PerformanceThresholds', 'PerformanceAnalyzer',
    'create_performance_monitor', 'create_extraction_monitor'
]