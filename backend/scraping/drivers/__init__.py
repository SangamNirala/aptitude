"""
Scraping Drivers Package
Advanced web scraping drivers for static and dynamic content extraction
"""

from .selenium_driver import (
    SeleniumDriver, 
    SeleniumConfig, 
    PageLoadResult, 
    ElementExtractionResult,
    create_selenium_driver,
    create_indiabix_selenium_driver,
    create_geeksforgeeks_selenium_driver
)

from .playwright_driver import (
    PlaywrightDriver,
    PlaywrightConfig,
    NavigationResult,
    JavaScriptExecutionResult,
    DynamicContentResult,
    PerformanceMetrics,
    create_playwright_driver,
    create_indiabix_playwright_driver,
    create_geeksforgeeks_playwright_driver
)

__all__ = [
    # Selenium Driver
    'SeleniumDriver',
    'SeleniumConfig', 
    'PageLoadResult',
    'ElementExtractionResult',
    'create_selenium_driver',
    'create_indiabix_selenium_driver',
    'create_geeksforgeeks_selenium_driver',
    
    # Playwright Driver
    'PlaywrightDriver',
    'PlaywrightConfig',
    'NavigationResult',
    'JavaScriptExecutionResult',
    'DynamicContentResult',
    'PerformanceMetrics',
    'create_playwright_driver',
    'create_indiabix_playwright_driver',
    'create_geeksforgeeks_playwright_driver'
]