"""
Selenium-Based Web Scraping Driver
Advanced Selenium WebDriver implementation with comprehensive error handling and anti-detection
"""

import os
import time
import random
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException, TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementClickInterceptedException,
    ElementNotInteractableException, InvalidSessionIdException
)

from ..utils.anti_detection import AntiDetectionManager, DetectionRiskLevel
from ..utils.rate_limiter import RateLimiter, ExponentialBackoffLimiter
from models.scraping_models import (
    ContentExtractionMethod, ScrapingPerformanceLog,
    AntiDetectionLog, RawExtractedQuestion
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class SeleniumConfig:
    """Configuration for Selenium driver"""
    
    # Browser Configuration
    browser: str = "chrome"  # chrome, firefox
    headless: bool = True
    window_size: Tuple[int, int] = (1920, 1080)
    
    # Timeouts
    page_load_timeout: int = 30
    implicit_wait: int = 10
    explicit_wait_timeout: int = 20
    
    # Performance
    enable_images: bool = False
    enable_css: bool = True
    enable_javascript: bool = True
    
    # Anti-Detection
    enable_anti_detection: bool = True
    user_agent_rotation: bool = True
    viewport_randomization: bool = True
    
    # Screenshots & Debugging
    screenshots_enabled: bool = True
    screenshot_on_error: bool = True
    screenshot_dir: str = "/tmp/selenium_screenshots"
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 2.0
    
    # Custom Chrome/Firefox Options
    custom_chrome_options: List[str] = None
    custom_firefox_options: List[str] = None

@dataclass
class PageLoadResult:
    """Result of page loading operation"""
    success: bool
    url: str
    load_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    page_source_length: int = 0

@dataclass
class ElementExtractionResult:
    """Result of element extraction"""
    success: bool
    element_type: str
    selector: str
    content: Optional[str] = None
    attributes: Dict[str, str] = None
    error_message: Optional[str] = None
    extraction_time: float = 0.0

# =============================================================================
# SELENIUM DRIVER CLASS
# =============================================================================

class SeleniumDriver:
    """
    Advanced Selenium WebDriver with comprehensive error handling and anti-detection
    """
    
    def __init__(self, source_name: str, config: SeleniumConfig = None, 
                 anti_detection_config: Dict[str, Any] = None):
        """
        Initialize Selenium driver with configuration
        
        Args:
            source_name: Name of the scraping source
            config: Selenium configuration
            anti_detection_config: Anti-detection configuration
        """
        self.source_name = source_name
        self.config = config or SeleniumConfig()
        
        # Driver state
        self.driver: Optional[webdriver.Chrome | webdriver.Firefox] = None
        self.is_initialized = False
        self.session_start_time = None
        
        # Anti-detection integration
        self.anti_detection = AntiDetectionManager(
            source_name, 
            anti_detection_config or {}
        ) if self.config.enable_anti_detection else None
        
        # Rate limiting
        from ..utils.rate_limiter import RateLimitConfig
        rate_config = RateLimitConfig(base_delay=1.0, max_delay=10.0)
        self.rate_limiter = ExponentialBackoffLimiter(rate_config)
        
        # Performance tracking
        self.performance_logs: List[ScrapingPerformanceLog] = []
        self.page_load_times: List[float] = []
        self.extraction_times: List[float] = []
        
        # Screenshot management
        self._ensure_screenshot_directory()
        
        logger.info(f"🚗 SeleniumDriver initialized for {source_name}")
    
    def _ensure_screenshot_directory(self):
        """Ensure screenshot directory exists"""
        try:
            os.makedirs(self.config.screenshot_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create screenshot directory: {e}")
            self.config.screenshots_enabled = False
    
    def _create_chrome_options(self) -> ChromeOptions:
        """Create Chrome options with anti-detection measures"""
        options = ChromeOptions()
        
        # Basic options
        if self.config.headless:
            options.add_argument("--headless")
        
        # Window size
        options.add_argument(f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}")
        
        # Performance optimizations
        if not self.config.enable_images:
            options.add_argument("--disable-images")
        
        # Anti-detection measures
        if self.config.enable_anti_detection:
            # Disable automation indicators
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Additional stealth options
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # User agent
            if self.anti_detection and self.config.user_agent_rotation:
                user_agent = self.anti_detection.get_user_agent()
                options.add_argument(f"--user-agent={user_agent}")
        
        # Set chromium binary location if available
        if os.path.exists("/usr/bin/chromium"):
            options.binary_location = "/usr/bin/chromium"
        
        # Custom options
        if self.config.custom_chrome_options:
            for option in self.config.custom_chrome_options:
                options.add_argument(option)
        
        return options
    
    def _create_firefox_options(self) -> FirefoxOptions:
        """Create Firefox options with anti-detection measures"""
        options = FirefoxOptions()
        
        # Basic options
        if self.config.headless:
            options.add_argument("--headless")
        
        # Performance optimizations
        if not self.config.enable_images:
            options.set_preference("permissions.default.image", 2)
        
        # Anti-detection measures
        if self.config.enable_anti_detection:
            # User agent
            if self.anti_detection and self.config.user_agent_rotation:
                user_agent = self.anti_detection.get_user_agent()
                options.set_preference("general.useragent.override", user_agent)
            
            # Disable automation indicators
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference('useAutomationExtension', False)
        
        # Custom options
        if self.config.custom_firefox_options:
            for option in self.config.custom_firefox_options:
                options.add_argument(option)
        
        return options
    
    def initialize_driver(self) -> bool:
        """
        Initialize the Selenium WebDriver
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Initializing {self.config.browser} driver...")
            
            if self.config.browser.lower() == "chrome":
                options = self._create_chrome_options()
                # Use ChromeDriver service with correct path
                if os.path.exists("/usr/bin/chromedriver"):
                    service = ChromeService("/usr/bin/chromedriver")
                    self.driver = webdriver.Chrome(service=service, options=options)
                else:
                    self.driver = webdriver.Chrome(options=options)
            elif self.config.browser.lower() == "firefox":
                options = self._create_firefox_options()
                self.driver = webdriver.Firefox(options=options)
            else:
                raise ValueError(f"Unsupported browser: {self.config.browser}")
            
            # Set timeouts
            self.driver.implicitly_wait(self.config.implicit_wait)
            self.driver.set_page_load_timeout(self.config.page_load_timeout)
            
            # Execute anti-detection scripts
            if self.config.enable_anti_detection and self.driver:
                self._execute_anti_detection_scripts()
            
            self.is_initialized = True
            self.session_start_time = datetime.utcnow()
            
            logger.info(f"✅ {self.config.browser} driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize driver: {e}")
            self.cleanup()
            return False
    
    def _execute_anti_detection_scripts(self):
        """Execute JavaScript to reduce detection fingerprints"""
        if not self.driver:
            return
            
        try:
            # Remove webdriver property
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Randomize screen properties if enabled
            if self.config.viewport_randomization:
                width, height = self.config.window_size
                # Add small random variations
                width += random.randint(-50, 50)
                height += random.randint(-30, 30)
                self.driver.set_window_size(width, height)
                
        except Exception as e:
            logger.warning(f"Failed to execute anti-detection scripts: {e}")
    
    @contextmanager
    def rate_limited_request(self, url: str):
        """Context manager for rate-limited requests"""
        # Apply rate limiting
        delay = self.rate_limiter.get_delay()
        if delay > 0:
            logger.debug(f"⏰ Rate limiting: waiting {delay:.2f}s before request to {url}")
            time.sleep(delay)
        
        # Apply anti-detection measures
        if self.anti_detection:
            self.anti_detection.before_request(url)
        
        start_time = time.time()
        
        try:
            yield
            
            # Record successful request
            request_time = time.time() - start_time
            self.rate_limiter.record_success()
            
            if self.anti_detection:
                self.anti_detection.after_request(url, success=True, response_time=request_time)
                
        except Exception as e:
            # Record failed request
            request_time = time.time() - start_time
            self.rate_limiter.record_failure()
            
            if self.anti_detection:
                self.anti_detection.after_request(url, success=False, response_time=request_time, error=str(e))
            
            raise
    
    def navigate_to_page(self, url: str, wait_for_element: str = None) -> PageLoadResult:
        """
        Navigate to a page with comprehensive error handling
        
        Args:
            url: Target URL
            wait_for_element: CSS selector to wait for after page load
            
        Returns:
            PageLoadResult: Result of the navigation
        """
        if not self.is_initialized:
            if not self.initialize_driver():
                return PageLoadResult(
                    success=False,
                    url=url,
                    load_time=0.0,
                    error_message="Failed to initialize driver"
                )
        
        start_time = time.time()
        result = PageLoadResult(success=False, url=url, load_time=0.0)
        
        try:
            with self.rate_limited_request(url):
                logger.info(f"🌐 Navigating to: {url}")
                
                # Navigate to page
                self.driver.get(url)
                
                # Wait for specific element if provided
                if wait_for_element:
                    wait = WebDriverWait(self.driver, self.config.explicit_wait_timeout)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element)))
                
                # Additional wait for JavaScript to finish
                if self.config.enable_javascript:
                    self._wait_for_page_ready()
                
                load_time = time.time() - start_time
                self.page_load_times.append(load_time)
                
                # Get page source length for validation
                page_source_length = len(self.driver.page_source)
                
                result = PageLoadResult(
                    success=True,
                    url=url,
                    load_time=load_time,
                    page_source_length=page_source_length
                )
                
                logger.info(f"✅ Page loaded successfully in {load_time:.2f}s")
                
        except TimeoutException as e:
            load_time = time.time() - start_time
            error_msg = f"Page load timeout after {load_time:.2f}s: {e}"
            logger.error(error_msg)
            
            result.error_message = error_msg
            result.load_time = load_time
            
            # Take screenshot on error
            if self.config.screenshot_on_error:
                result.screenshot_path = self.take_screenshot(f"timeout_error_{int(time.time())}")
                
        except WebDriverException as e:
            load_time = time.time() - start_time
            error_msg = f"WebDriver error: {e}"
            logger.error(error_msg)
            
            result.error_message = error_msg
            result.load_time = load_time
            
            if self.config.screenshot_on_error:
                result.screenshot_path = self.take_screenshot(f"webdriver_error_{int(time.time())}")
        
        # Log performance
        self._log_performance("page_navigation", load_time, result.success, result.error_message)
        
        return result
    
    def _wait_for_page_ready(self):
        """Wait for page to be fully loaded (JavaScript ready)"""
        try:
            wait = WebDriverWait(self.driver, self.config.explicit_wait_timeout)
            wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("Page ready state timeout - continuing anyway")
    
    def extract_elements(self, selectors: Dict[str, str], 
                        optional_selectors: List[str] = None) -> Dict[str, ElementExtractionResult]:
        """
        Extract multiple elements using CSS selectors
        
        Args:
            selectors: Dictionary of {field_name: css_selector}
            optional_selectors: List of selector names that are optional
            
        Returns:
            Dict of {field_name: ElementExtractionResult}
        """
        results = {}
        optional_selectors = optional_selectors or []
        
        for field_name, css_selector in selectors.items():
            start_time = time.time()
            is_optional = field_name in optional_selectors
            
            try:
                logger.debug(f"🔍 Extracting {field_name} using selector: {css_selector}")
                
                # Find element with retry logic
                element = self._find_element_with_retry(css_selector, is_optional)
                
                extraction_time = time.time() - start_time
                
                if element:
                    # Extract content and attributes
                    content = self._extract_element_content(element)
                    attributes = self._extract_element_attributes(element)
                    
                    results[field_name] = ElementExtractionResult(
                        success=True,
                        element_type=element.tag_name,
                        selector=css_selector,
                        content=content,
                        attributes=attributes,
                        extraction_time=extraction_time
                    )
                    
                    logger.debug(f"✅ Extracted {field_name}: {len(content)} characters")
                    
                else:
                    # Element not found
                    error_msg = f"Element not found: {css_selector}"
                    if not is_optional:
                        logger.warning(f"⚠️ Required element missing: {field_name}")
                    
                    results[field_name] = ElementExtractionResult(
                        success=False,
                        element_type="unknown",
                        selector=css_selector,
                        error_message=error_msg,
                        extraction_time=extraction_time
                    )
                
            except Exception as e:
                extraction_time = time.time() - start_time
                error_msg = f"Extraction error for {field_name}: {e}"
                logger.error(error_msg)
                
                results[field_name] = ElementExtractionResult(
                    success=False,
                    element_type="unknown",
                    selector=css_selector,
                    error_message=error_msg,
                    extraction_time=extraction_time
                )
            
            # Track extraction time
            self.extraction_times.append(extraction_time)
        
        return results
    
    def _find_element_with_retry(self, css_selector: str, is_optional: bool = False):
        """Find element with retry logic"""
        max_attempts = self.config.max_retries + 1
        
        for attempt in range(max_attempts):
            try:
                # Use explicit wait for element
                wait = WebDriverWait(self.driver, self.config.explicit_wait_timeout // max_attempts)
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
                return element
                
            except TimeoutException:
                if attempt < max_attempts - 1:  # Not the last attempt
                    logger.debug(f"🔄 Retry {attempt + 1}/{max_attempts} for selector: {css_selector}")
                    time.sleep(self.config.retry_delay)
                    continue
                elif not is_optional:
                    logger.warning(f"⚠️ Element not found after {max_attempts} attempts: {css_selector}")
                
                return None
            
            except StaleElementReferenceException:
                if attempt < max_attempts - 1:
                    logger.debug(f"🔄 Stale element, retrying: {css_selector}")
                    time.sleep(self.config.retry_delay)
                    continue
                return None
    
    def _extract_element_content(self, element) -> str:
        """Extract content from element with fallback methods"""
        try:
            # Try different content extraction methods
            content_methods = [
                lambda e: e.get_attribute('textContent'),
                lambda e: e.get_attribute('innerText'),
                lambda e: e.text,
                lambda e: e.get_attribute('innerHTML')
            ]
            
            for method in content_methods:
                try:
                    content = method(element)
                    if content and content.strip():
                        return content.strip()
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to extract element content: {e}")
            return ""
    
    def _extract_element_attributes(self, element) -> Dict[str, str]:
        """Extract useful attributes from element"""
        try:
            attributes = {}
            
            # Common useful attributes
            attr_names = ['href', 'src', 'alt', 'title', 'class', 'id', 'data-*']
            
            for attr in attr_names:
                if attr == 'data-*':
                    # Extract all data attributes
                    try:
                        data_attrs = self.driver.execute_script(
                            "return Array.from(arguments[0].attributes).filter(attr => attr.name.startsWith('data-')).reduce((obj, attr) => { obj[attr.name] = attr.value; return obj; }, {});",
                            element
                        )
                        attributes.update(data_attrs)
                    except:
                        pass
                else:
                    value = element.get_attribute(attr)
                    if value:
                        attributes[attr] = value
            
            return attributes
            
        except Exception as e:
            logger.warning(f"Failed to extract element attributes: {e}")
            return {}
    
    def extract_list_items(self, container_selector: str, item_selector: str, 
                          item_fields: Dict[str, str], max_items: int = None) -> List[Dict[str, Any]]:
        """
        Extract multiple items from a list/container
        
        Args:
            container_selector: CSS selector for container element
            item_selector: CSS selector for individual items within container
            item_fields: Dict of {field_name: css_selector_relative_to_item}
            max_items: Maximum number of items to extract
            
        Returns:
            List of extracted items
        """
        results = []
        
        try:
            # Find container
            container = self._find_element_with_retry(container_selector)
            if not container:
                logger.error(f"Container not found: {container_selector}")
                return results
            
            # Find items within container
            items = container.find_elements(By.CSS_SELECTOR, item_selector)
            
            if max_items:
                items = items[:max_items]
            
            logger.info(f"📋 Found {len(items)} items to extract")
            
            for i, item in enumerate(items):
                item_data = {"index": i}
                
                # Extract fields from each item
                for field_name, field_selector in item_fields.items():
                    try:
                        field_element = item.find_element(By.CSS_SELECTOR, field_selector)
                        content = self._extract_element_content(field_element)
                        item_data[field_name] = content
                        
                    except NoSuchElementException:
                        logger.debug(f"Field {field_name} not found in item {i}")
                        item_data[field_name] = None
                    except Exception as e:
                        logger.warning(f"Error extracting {field_name} from item {i}: {e}")
                        item_data[field_name] = None
                
                results.append(item_data)
            
            logger.info(f"✅ Successfully extracted {len(results)} items")
            
        except Exception as e:
            logger.error(f"❌ Error in list extraction: {e}")
        
        return results
    
    def take_screenshot(self, filename_prefix: str = "screenshot") -> Optional[str]:
        """
        Take a screenshot for debugging
        
        Args:
            filename_prefix: Prefix for the screenshot filename
            
        Returns:
            Path to the screenshot file, or None if failed
        """
        if not self.config.screenshots_enabled or not self.driver:
            return None
        
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(self.config.screenshot_dir, filename)
            
            self.driver.save_screenshot(filepath)
            
            logger.info(f"📸 Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Failed to take screenshot: {e}")
            return None
    
    def execute_javascript(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of the JavaScript execution
        """
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"❌ JavaScript execution failed: {e}")
            return None
    
    def scroll_to_element(self, element_or_selector: Union[str, Any]) -> bool:
        """
        Scroll to an element on the page
        
        Args:
            element_or_selector: Element object or CSS selector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(element_or_selector, str):
                element = self._find_element_with_retry(element_or_selector)
            else:
                element = element_or_selector
            
            if element:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)  # Brief pause for scroll to complete
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to scroll to element: {e}")
        
        return False
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior patterns"""
        if not self.anti_detection:
            return
        
        try:
            # Random mouse movements
            actions = ActionChains(self.driver)
            
            # Move to random positions
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.1, 0.5))
            
            # Occasional scroll
            if random.random() < 0.3:
                self.driver.execute_script("window.scrollBy(0, arguments[0]);", random.randint(100, 300))
            
            actions.perform()
            
            # Random pause
            time.sleep(random.uniform(0.5, 2.0))
            
        except Exception as e:
            logger.debug(f"Human behavior simulation failed: {e}")
    
    def _log_performance(self, operation: str, duration: float, success: bool, error_message: str = None):
        """Log performance metrics"""
        log_entry = ScrapingPerformanceLog(
            job_id="current_session",  # Would be set by job manager
            operation=operation,
            duration_seconds=duration,
            success=success,
            error_message=error_message
        )
        
        self.performance_logs.append(log_entry)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "total_page_loads": len(self.page_load_times),
            "avg_page_load_time": sum(self.page_load_times) / len(self.page_load_times) if self.page_load_times else 0,
            "max_page_load_time": max(self.page_load_times) if self.page_load_times else 0,
            "total_extractions": len(self.extraction_times),
            "avg_extraction_time": sum(self.extraction_times) / len(self.extraction_times) if self.extraction_times else 0,
            "total_performance_logs": len(self.performance_logs),
            "session_duration_seconds": (datetime.utcnow() - self.session_start_time).total_seconds() if self.session_start_time else 0
        }
    
    def cleanup(self):
        """Clean up resources and close driver"""
        try:
            if self.driver:
                logger.info("🧹 Cleaning up Selenium driver...")
                self.driver.quit()
                self.driver = None
                
            self.is_initialized = False
            
            # Log final performance stats
            stats = self.get_performance_stats()
            logger.info(f"📊 Final performance stats: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        if not self.initialize_driver():
            raise RuntimeError("Failed to initialize Selenium driver")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_selenium_driver(source_name: str, browser: str = "chrome", 
                          headless: bool = True, anti_detection_config: Dict[str, Any] = None, **kwargs) -> SeleniumDriver:
    """
    Factory function to create a configured Selenium driver
    
    Args:
        source_name: Name of the scraping source
        browser: Browser to use (chrome/firefox)
        headless: Whether to run in headless mode
        anti_detection_config: Anti-detection configuration
        **kwargs: Additional configuration options
        
    Returns:
        Configured SeleniumDriver instance
    """
    config = SeleniumConfig(
        browser=browser,
        headless=headless,
        **kwargs
    )
    
    return SeleniumDriver(source_name, config, anti_detection_config)

def create_indiabix_selenium_driver(**kwargs) -> SeleniumDriver:
    """Create Selenium driver optimized for IndiaBix"""
    return create_selenium_driver(
        source_name="indiabix",
        browser="chrome",
        headless=True,
        page_load_timeout=30,
        implicit_wait=10,
        enable_images=False,
        **kwargs
    )

def create_geeksforgeeks_selenium_driver(**kwargs) -> SeleniumDriver:
    """Create Selenium driver optimized for GeeksforGeeks"""
    return create_selenium_driver(
        source_name="geeksforgeeks",
        browser="chrome",
        headless=True,
        page_load_timeout=35,
        implicit_wait=12,
        enable_images=False,
        enable_javascript=True,
        **kwargs
    )