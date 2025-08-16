"""
Playwright-Based Web Scraping Driver
Advanced Playwright implementation for JavaScript-heavy dynamic content with performance monitoring
"""

import os
import asyncio
import time
import random
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, 
    TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError,
    Route, Request, Response
)
from playwright._impl._api_types import Error as PlaywrightAPIError

from ..utils.anti_detection import AntiDetectionManager, DetectionRiskLevel
from ..utils.rate_limiter import AdaptiveRateLimiter
from ...models.scraping_models import (
    ContentExtractionMethod, ScrapingPerformanceLog,
    AntiDetectionLog, RawExtractedQuestion
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class PlaywrightConfig:
    """Configuration for Playwright driver"""
    
    # Browser Configuration
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    viewport: Dict[str, int] = None  # {"width": 1920, "height": 1080}
    
    # Performance Settings
    enable_javascript: bool = True
    enable_images: bool = False
    enable_css: bool = True
    enable_fonts: bool = False
    
    # Timeouts (in milliseconds)
    navigation_timeout: int = 30000
    default_timeout: int = 20000
    wait_for_selector_timeout: int = 15000
    
    # Anti-Detection
    enable_anti_detection: bool = True
    user_agent_rotation: bool = True
    stealth_mode: bool = True
    
    # JavaScript Execution
    enable_custom_js: bool = True
    js_execution_timeout: int = 10000
    
    # Network Monitoring
    enable_network_monitoring: bool = True
    intercept_requests: bool = True
    block_resources: List[str] = None  # ['image', 'media', 'font']
    
    # Screenshots & Debugging
    screenshots_enabled: bool = True
    screenshot_on_error: bool = True
    screenshot_dir: str = "/tmp/playwright_screenshots"
    full_page_screenshots: bool = False
    
    # Performance Monitoring
    enable_performance_monitoring: bool = True
    track_resource_usage: bool = True
    performance_metrics_interval: int = 1000  # milliseconds
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 2.0
    exponential_backoff: bool = True
    
    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1920, "height": 1080}
        if self.block_resources is None:
            self.block_resources = ['image', 'media', 'font'] if not self.enable_images else ['media']

@dataclass
class NavigationResult:
    """Result of page navigation operation"""
    success: bool
    url: str
    final_url: str
    load_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    network_requests: int = 0
    blocked_requests: int = 0
    javascript_errors: List[str] = None
    
    def __post_init__(self):
        if self.javascript_errors is None:
            self.javascript_errors = []

@dataclass
class JavaScriptExecutionResult:
    """Result of JavaScript execution"""
    success: bool
    result: Any = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    console_logs: List[str] = None
    
    def __post_init__(self):
        if self.console_logs is None:
            self.console_logs = []

@dataclass
class DynamicContentResult:
    """Result of dynamic content extraction"""
    success: bool
    content: Dict[str, Any]
    extraction_method: str
    wait_time: float = 0.0
    elements_found: int = 0
    error_message: Optional[str] = None

# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for a page operation"""
    timestamp: datetime
    memory_usage_mb: float
    cpu_usage_percent: float
    network_requests: int
    dom_content_loaded_time: Optional[float]
    load_event_time: Optional[float]
    first_contentful_paint: Optional[float]
    largest_contentful_paint: Optional[float]
    javascript_heap_size: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# =============================================================================
# PLAYWRIGHT DRIVER CLASS
# =============================================================================

class PlaywrightDriver:
    """
    Advanced Playwright WebDriver for dynamic content scraping with performance monitoring
    """
    
    def __init__(self, source_name: str, config: PlaywrightConfig = None,
                 anti_detection_config: Dict[str, Any] = None):
        """
        Initialize Playwright driver
        
        Args:
            source_name: Name of the scraping source
            config: Playwright configuration
            anti_detection_config: Anti-detection configuration
        """
        self.source_name = source_name
        self.config = config or PlaywrightConfig()
        
        # Playwright components
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # State management
        self.is_initialized = False
        self.session_start_time = None
        
        # Anti-detection integration
        self.anti_detection = AntiDetectionManager(
            source_name,
            anti_detection_config or {}
        ) if self.config.enable_anti_detection else None
        
        # Rate limiting
        self.rate_limiter = AdaptiveRateLimiter(
            base_delay=1.0,
            max_delay=15.0,
            adaptation_factor=0.1
        )
        
        # Performance tracking
        self.performance_logs: List[ScrapingPerformanceLog] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        self.navigation_times: List[float] = []
        self.extraction_times: List[float] = []
        
        # Network monitoring
        self.network_requests: List[Dict[str, Any]] = []
        self.blocked_requests: int = 0
        
        # JavaScript monitoring
        self.javascript_errors: List[str] = []
        self.console_logs: List[str] = []
        
        # Screenshot management
        self._ensure_screenshot_directory()
        
        logger.info(f"🎭 PlaywrightDriver initialized for {source_name}")
    
    def _ensure_screenshot_directory(self):
        """Ensure screenshot directory exists"""
        try:
            os.makedirs(self.config.screenshot_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create screenshot directory: {e}")
            self.config.screenshots_enabled = False
    
    async def initialize_driver(self) -> bool:
        """
        Initialize Playwright browser and context
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Initializing Playwright {self.config.browser_type} browser...")
            
            # Launch Playwright
            self.playwright = await async_playwright().start()
            
            # Get browser
            if self.config.browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif self.config.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.config.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                raise ValueError(f"Unsupported browser type: {self.config.browser_type}")
            
            # Browser launch options
            launch_options = {
                "headless": self.config.headless,
                "args": self._get_browser_args()
            }
            
            self.browser = await browser_launcher.launch(**launch_options)
            
            # Create context with anti-detection measures
            context_options = await self._create_context_options()
            self.context = await self.browser.new_context(**context_options)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Configure page
            await self._configure_page()
            
            self.is_initialized = True
            self.session_start_time = datetime.utcnow()
            
            logger.info(f"✅ Playwright {self.config.browser_type} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Playwright driver: {e}")
            await self.cleanup()
            return False
    
    def _get_browser_args(self) -> List[str]:
        """Get browser launch arguments"""
        args = []
        
        if self.config.browser_type == "chromium":
            args.extend([
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-features=VizDisplayCompositor",
            ])
            
            if self.config.enable_anti_detection:
                args.extend([
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=TranslateUI",
                    "--no-first-run",
                ])
        
        return args
    
    async def _create_context_options(self) -> Dict[str, Any]:
        """Create browser context options with anti-detection measures"""
        options = {
            "viewport": self.config.viewport,
            "ignore_https_errors": True,
            "java_script_enabled": self.config.enable_javascript,
        }
        
        # Anti-detection measures
        if self.config.enable_anti_detection:
            if self.anti_detection and self.config.user_agent_rotation:
                user_agent = self.anti_detection.get_user_agent()
                options["user_agent"] = user_agent
            
            # Additional headers for stealth
            if self.config.stealth_mode:
                options["extra_http_headers"] = {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
        
        return options
    
    async def _configure_page(self):
        """Configure page settings and event handlers"""
        # Set timeouts
        self.page.set_default_navigation_timeout(self.config.navigation_timeout)
        self.page.set_default_timeout(self.config.default_timeout)
        
        # Network monitoring
        if self.config.enable_network_monitoring:
            await self._setup_network_monitoring()
        
        # JavaScript error handling
        self.page.on("pageerror", self._handle_page_error)
        self.page.on("console", self._handle_console_message)
        
        # Performance monitoring
        if self.config.enable_performance_monitoring:
            await self._setup_performance_monitoring()
        
        # Anti-detection JavaScript
        if self.config.enable_anti_detection and self.config.stealth_mode:
            await self._inject_stealth_scripts()
    
    async def _setup_network_monitoring(self):
        """Setup network request monitoring and blocking"""
        async def handle_route(route: Route, request: Request):
            # Track request
            request_data = {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.network_requests.append(request_data)
            
            # Block unwanted resources
            if (self.config.intercept_requests and 
                request.resource_type in self.config.block_resources):
                self.blocked_requests += 1
                await route.abort()
            else:
                await route.continue_()
        
        # Intercept all requests
        await self.page.route("**/*", handle_route)
    
    def _handle_page_error(self, error):
        """Handle JavaScript page errors"""
        error_msg = str(error)
        self.javascript_errors.append(error_msg)
        logger.warning(f"🚨 JavaScript error: {error_msg}")
    
    def _handle_console_message(self, message):
        """Handle console messages"""
        if message.type in ["error", "warning"]:
            log_msg = f"{message.type.upper()}: {message.text}"
            self.console_logs.append(log_msg)
            if message.type == "error":
                logger.debug(f"Console error: {message.text}")
    
    async def _setup_performance_monitoring(self):
        """Setup performance metrics collection"""
        try:
            # Enable performance metrics collection
            await self.page.add_init_script("""
                window.performanceMetrics = {
                    startTime: performance.now(),
                    metrics: []
                };
                
                // Collect performance metrics periodically
                setInterval(() => {
                    const memory = performance.memory;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    
                    window.performanceMetrics.metrics.push({
                        timestamp: Date.now(),
                        memoryUsed: memory ? memory.usedJSHeapSize : null,
                        memoryTotal: memory ? memory.totalJSHeapSize : null,
                        domContentLoaded: navigation ? navigation.domContentLoadedEventEnd : null,
                        loadComplete: navigation ? navigation.loadEventEnd : null
                    });
                }, """ + str(self.config.performance_metrics_interval) + """);
            """)
        except Exception as e:
            logger.warning(f"Failed to setup performance monitoring: {e}")
    
    async def _inject_stealth_scripts(self):
        """Inject stealth JavaScript to avoid detection"""
        stealth_script = """
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // Mock chrome runtime
            if (!window.chrome) {
                window.chrome = {};
            }
            if (!window.chrome.runtime) {
                window.chrome.runtime = {
                    onConnect: undefined,
                    onMessage: undefined
                };
            }
        """
        
        try:
            await self.page.add_init_script(stealth_script)
        except Exception as e:
            logger.warning(f"Failed to inject stealth scripts: {e}")
    
    @asynccontextmanager
    async def rate_limited_request(self, url: str):
        """Async context manager for rate-limited requests"""
        # Apply rate limiting
        delay = self.rate_limiter.get_delay()
        if delay > 0:
            logger.debug(f"⏰ Rate limiting: waiting {delay:.2f}s before request to {url}")
            await asyncio.sleep(delay)
        
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
    
    async def navigate_to_page(self, url: str, wait_for: str = None, 
                             wait_for_function: str = None) -> NavigationResult:
        """
        Navigate to a page with advanced waiting and error handling
        
        Args:
            url: Target URL
            wait_for: CSS selector or 'networkidle' to wait for
            wait_for_function: JavaScript function to wait for (returns true when ready)
            
        Returns:
            NavigationResult with navigation details
        """
        if not self.is_initialized:
            if not await self.initialize_driver():
                return NavigationResult(
                    success=False,
                    url=url,
                    final_url=url,
                    load_time=0.0,
                    error_message="Failed to initialize driver"
                )
        
        start_time = time.time()
        result = NavigationResult(success=False, url=url, final_url=url, load_time=0.0)
        
        try:
            async with self.rate_limited_request(url):
                logger.info(f"🌐 Navigating to: {url}")
                
                # Reset monitoring data
                self.javascript_errors.clear()
                initial_requests = len(self.network_requests)
                
                # Navigate to page
                response = await self.page.goto(url, wait_until="domcontentloaded")
                
                result.status_code = response.status if response else None
                result.final_url = self.page.url
                
                # Wait for specific conditions
                if wait_for == "networkidle":
                    await self.page.wait_for_load_state("networkidle")
                elif wait_for:
                    await self.page.wait_for_selector(wait_for, timeout=self.config.wait_for_selector_timeout)
                
                if wait_for_function:
                    await self.page.wait_for_function(wait_for_function, timeout=self.config.js_execution_timeout)
                
                # Additional wait for dynamic content
                await self._wait_for_dynamic_content()
                
                load_time = time.time() - start_time
                self.navigation_times.append(load_time)
                
                result.success = True
                result.load_time = load_time
                result.network_requests = len(self.network_requests) - initial_requests
                result.blocked_requests = self.blocked_requests
                result.javascript_errors = list(self.javascript_errors)
                
                logger.info(f"✅ Page loaded successfully in {load_time:.2f}s")
                
        except PlaywrightTimeoutError as e:
            load_time = time.time() - start_time
            error_msg = f"Navigation timeout after {load_time:.2f}s: {e}"
            logger.error(error_msg)
            
            result.error_message = error_msg
            result.load_time = load_time
            
            if self.config.screenshot_on_error:
                result.screenshot_path = await self.take_screenshot(f"timeout_error_{int(time.time())}")
                
        except PlaywrightError as e:
            load_time = time.time() - start_time
            error_msg = f"Playwright error: {e}"
            logger.error(error_msg)
            
            result.error_message = error_msg
            result.load_time = load_time
            
            if self.config.screenshot_on_error:
                result.screenshot_path = await self.take_screenshot(f"playwright_error_{int(time.time())}")
        
        # Log performance
        await self._log_performance("page_navigation", load_time, result.success, result.error_message)
        
        return result
    
    async def _wait_for_dynamic_content(self):
        """Wait for dynamic content to fully load"""
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=5000)
            
            # Wait for any pending JavaScript
            await self.page.wait_for_function(
                "document.readyState === 'complete'",
                timeout=3000
            )
            
            # Additional small delay for animations/transitions
            await asyncio.sleep(0.5)
            
        except PlaywrightTimeoutError:
            logger.debug("Dynamic content wait timeout - continuing anyway")
    
    async def extract_elements(self, selectors: Dict[str, str],
                             optional_selectors: List[str] = None,
                             wait_for_elements: bool = True) -> Dict[str, Any]:
        """
        Extract multiple elements using CSS selectors with advanced waiting
        
        Args:
            selectors: Dictionary of {field_name: css_selector}
            optional_selectors: List of selector names that are optional
            wait_for_elements: Whether to wait for elements to appear
            
        Returns:
            Dict of extracted content
        """
        results = {}
        optional_selectors = optional_selectors or []
        
        for field_name, css_selector in selectors.items():
            start_time = time.time()
            is_optional = field_name in optional_selectors
            
            try:
                logger.debug(f"🔍 Extracting {field_name} using selector: {css_selector}")
                
                # Find element with advanced waiting
                element = await self._find_element_with_retry(css_selector, is_optional, wait_for_elements)
                
                extraction_time = time.time() - start_time
                
                if element:
                    # Extract content
                    content = await self._extract_element_content(element)
                    attributes = await self._extract_element_attributes(element)
                    
                    results[field_name] = {
                        "content": content,
                        "attributes": attributes,
                        "extraction_time": extraction_time,
                        "success": True
                    }
                    
                    logger.debug(f"✅ Extracted {field_name}: {len(content) if content else 0} characters")
                    
                else:
                    error_msg = f"Element not found: {css_selector}"
                    if not is_optional:
                        logger.warning(f"⚠️ Required element missing: {field_name}")
                    
                    results[field_name] = {
                        "content": None,
                        "attributes": {},
                        "extraction_time": extraction_time,
                        "success": False,
                        "error": error_msg
                    }
                
            except Exception as e:
                extraction_time = time.time() - start_time
                error_msg = f"Extraction error for {field_name}: {e}"
                logger.error(error_msg)
                
                results[field_name] = {
                    "content": None,
                    "attributes": {},
                    "extraction_time": extraction_time,
                    "success": False,
                    "error": error_msg
                }
            
            # Track extraction time
            self.extraction_times.append(extraction_time)
        
        return results
    
    async def _find_element_with_retry(self, css_selector: str, is_optional: bool = False,
                                     wait_for_element: bool = True):
        """Find element with retry logic and intelligent waiting"""
        max_attempts = self.config.max_retries + 1
        
        for attempt in range(max_attempts):
            try:
                if wait_for_element:
                    # Wait for element to appear
                    await self.page.wait_for_selector(
                        css_selector,
                        timeout=self.config.wait_for_selector_timeout // max_attempts
                    )
                
                # Get element
                element = await self.page.query_selector(css_selector)
                if element:
                    return element
                
            except PlaywrightTimeoutError:
                if attempt < max_attempts - 1:  # Not the last attempt
                    logger.debug(f"🔄 Retry {attempt + 1}/{max_attempts} for selector: {css_selector}")
                    delay = self.config.retry_delay
                    if self.config.exponential_backoff:
                        delay *= (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                elif not is_optional:
                    logger.warning(f"⚠️ Element not found after {max_attempts} attempts: {css_selector}")
                
                return None
            
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.debug(f"🔄 Error finding element, retrying: {css_selector} - {e}")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                return None
        
        return None
    
    async def _extract_element_content(self, element) -> Optional[str]:
        """Extract content from element with multiple fallback methods"""
        try:
            # Try different content extraction methods
            content_methods = [
                "textContent",
                "innerText", 
                "innerHTML"
            ]
            
            for method in content_methods:
                try:
                    content = await element.get_attribute(method)
                    if content and content.strip():
                        return content.strip()
                except:
                    continue
            
            # Fallback to evaluate
            try:
                content = await element.evaluate("element => element.textContent || element.innerText || element.innerHTML")
                if content and str(content).strip():
                    return str(content).strip()
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract element content: {e}")
            return None
    
    async def _extract_element_attributes(self, element) -> Dict[str, str]:
        """Extract useful attributes from element"""
        try:
            attributes = {}
            
            # Get all attributes
            all_attrs = await element.evaluate("""
                element => {
                    const attrs = {};
                    for (let attr of element.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            
            if all_attrs:
                attributes.update(all_attrs)
            
            return attributes
            
        except Exception as e:
            logger.warning(f"Failed to extract element attributes: {e}")
            return {}
    
    async def execute_javascript(self, script: str, *args, 
                               timeout: int = None) -> JavaScriptExecutionResult:
        """
        Execute JavaScript in the browser with monitoring
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            timeout: Execution timeout in milliseconds
            
        Returns:
            JavaScriptExecutionResult with execution details
        """
        start_time = time.time()
        timeout = timeout or self.config.js_execution_timeout
        
        try:
            logger.debug(f"🔧 Executing JavaScript: {script[:100]}...")
            
            # Clear previous console logs
            initial_console_count = len(self.console_logs)
            
            # Execute script
            if args:
                result = await self.page.evaluate(script, *args, timeout=timeout)
            else:
                result = await self.page.evaluate(script, timeout=timeout)
            
            execution_time = time.time() - start_time
            
            # Get new console logs
            new_console_logs = self.console_logs[initial_console_count:]
            
            logger.debug(f"✅ JavaScript executed successfully in {execution_time:.3f}s")
            
            return JavaScriptExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                console_logs=new_console_logs
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"JavaScript execution failed: {e}"
            logger.error(error_msg)
            
            return JavaScriptExecutionResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    async def extract_dynamic_content(self, config: Dict[str, Any]) -> DynamicContentResult:
        """
        Extract content that requires JavaScript interaction or waiting
        
        Args:
            config: Configuration with extraction parameters
                - method: 'scroll_and_extract', 'click_and_extract', 'wait_and_extract'
                - selectors: Dict of selectors to extract
                - actions: List of actions to perform
                - wait_conditions: Conditions to wait for
                
        Returns:
            DynamicContentResult with extracted content
        """
        start_time = time.time()
        method = config.get("method", "wait_and_extract")
        
        try:
            logger.info(f"🔄 Extracting dynamic content using method: {method}")
            
            # Perform method-specific actions
            if method == "scroll_and_extract":
                await self._scroll_and_extract(config)
            elif method == "click_and_extract":
                await self._click_and_extract(config)
            elif method == "wait_and_extract":
                await self._wait_and_extract(config)
            else:
                raise ValueError(f"Unsupported extraction method: {method}")
            
            # Extract content after actions
            selectors = config.get("selectors", {})
            content = await self.extract_elements(selectors)
            
            wait_time = time.time() - start_time
            elements_found = len([v for v in content.values() if v.get("success", False)])
            
            return DynamicContentResult(
                success=True,
                content=content,
                extraction_method=method,
                wait_time=wait_time,
                elements_found=elements_found
            )
            
        except Exception as e:
            wait_time = time.time() - start_time
            error_msg = f"Dynamic content extraction failed: {e}"
            logger.error(error_msg)
            
            return DynamicContentResult(
                success=False,
                content={},
                extraction_method=method,
                wait_time=wait_time,
                error_message=error_msg
            )
    
    async def _scroll_and_extract(self, config: Dict[str, Any]):
        """Scroll to load content dynamically"""
        scroll_config = config.get("scroll", {})
        scroll_distance = scroll_config.get("distance", 1000)
        scroll_count = scroll_config.get("count", 5)
        scroll_delay = scroll_config.get("delay", 1.0)
        
        for i in range(scroll_count):
            await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(scroll_delay)
            
            # Check if new content loaded
            wait_selector = scroll_config.get("wait_for_new_content")
            if wait_selector:
                try:
                    await self.page.wait_for_selector(wait_selector, timeout=2000)
                except PlaywrightTimeoutError:
                    pass
    
    async def _click_and_extract(self, config: Dict[str, Any]):
        """Click elements to load content dynamically"""
        click_config = config.get("click", {})
        click_selectors = click_config.get("selectors", [])
        click_delay = click_config.get("delay", 1.0)
        
        for selector in click_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.click()
                    await asyncio.sleep(click_delay)
                    
                    # Wait for content to load
                    wait_selector = click_config.get("wait_after_click")
                    if wait_selector:
                        await self.page.wait_for_selector(wait_selector, timeout=5000)
                        
            except Exception as e:
                logger.warning(f"Failed to click element {selector}: {e}")
    
    async def _wait_and_extract(self, config: Dict[str, Any]):
        """Wait for conditions before extracting"""
        wait_config = config.get("wait", {})
        
        # Wait for selectors
        wait_selectors = wait_config.get("selectors", [])
        for selector in wait_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout waiting for selector: {selector}")
        
        # Wait for functions
        wait_functions = wait_config.get("functions", [])
        for func in wait_functions:
            try:
                await self.page.wait_for_function(func, timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout waiting for function: {func}")
        
        # Additional delay
        extra_delay = wait_config.get("extra_delay", 0)
        if extra_delay > 0:
            await asyncio.sleep(extra_delay)
    
    async def take_screenshot(self, filename_prefix: str = "screenshot") -> Optional[str]:
        """
        Take a screenshot for debugging
        
        Args:
            filename_prefix: Prefix for the screenshot filename
            
        Returns:
            Path to the screenshot file, or None if failed
        """
        if not self.config.screenshots_enabled or not self.page:
            return None
        
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(self.config.screenshot_dir, filename)
            
            await self.page.screenshot(
                path=filepath,
                full_page=self.config.full_page_screenshots
            )
            
            logger.info(f"📸 Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Failed to take screenshot: {e}")
            return None
    
    async def simulate_human_behavior(self):
        """Simulate human-like behavior patterns"""
        if not self.anti_detection or not self.page:
            return
        
        try:
            # Random mouse movements
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Occasional scroll
            if random.random() < 0.3:
                scroll_distance = random.randint(100, 300)
                await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            
            # Random pause
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
        except Exception as e:
            logger.debug(f"Human behavior simulation failed: {e}")
    
    async def _log_performance(self, operation: str, duration: float, 
                             success: bool, error_message: str = None):
        """Log performance metrics"""
        # Collect current performance metrics
        try:
            performance_data = await self.page.evaluate("""
                () => {
                    const memory = performance.memory;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        memoryUsed: memory ? memory.usedJSHeapSize : null,
                        memoryTotal: memory ? memory.totalJSHeapSize : null,
                        domContentLoaded: navigation ? navigation.domContentLoadedEventEnd : null,
                        loadComplete: navigation ? navigation.loadEventEnd : null
                    };
                }
            """)
            
            if performance_data:
                metrics = PerformanceMetrics(
                    timestamp=datetime.utcnow(),
                    memory_usage_mb=performance_data.get('memoryUsed', 0) / (1024 * 1024),
                    cpu_usage_percent=0.0,  # Would need system-level monitoring
                    network_requests=len(self.network_requests),
                    dom_content_loaded_time=performance_data.get('domContentLoaded'),
                    load_event_time=performance_data.get('loadComplete'),
                    first_contentful_paint=None,  # Would need additional setup
                    largest_contentful_paint=None,
                    javascript_heap_size=performance_data.get('memoryUsed')
                )
                
                self.performance_metrics.append(metrics)
                
        except Exception as e:
            logger.debug(f"Failed to collect performance metrics: {e}")
        
        # Standard performance log
        log_entry = ScrapingPerformanceLog(
            job_id="current_session",
            operation=operation,
            duration_seconds=duration,
            success=success,
            error_message=error_message
        )
        
        self.performance_logs.append(log_entry)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = {
            "total_navigations": len(self.navigation_times),
            "avg_navigation_time": sum(self.navigation_times) / len(self.navigation_times) if self.navigation_times else 0,
            "max_navigation_time": max(self.navigation_times) if self.navigation_times else 0,
            "total_extractions": len(self.extraction_times),
            "avg_extraction_time": sum(self.extraction_times) / len(self.extraction_times) if self.extraction_times else 0,
            "total_network_requests": len(self.network_requests),
            "blocked_requests": self.blocked_requests,
            "javascript_errors": len(self.javascript_errors),
            "console_logs": len(self.console_logs),
            "performance_metrics_count": len(self.performance_metrics),
            "session_duration_seconds": (datetime.utcnow() - self.session_start_time).total_seconds() if self.session_start_time else 0
        }
        
        # Add memory usage statistics if available
        if self.performance_metrics:
            memory_usages = [m.memory_usage_mb for m in self.performance_metrics if m.memory_usage_mb > 0]
            if memory_usages:
                stats.update({
                    "avg_memory_usage_mb": sum(memory_usages) / len(memory_usages),
                    "max_memory_usage_mb": max(memory_usages),
                    "min_memory_usage_mb": min(memory_usages)
                })
        
        return stats
    
    async def cleanup(self):
        """Clean up resources and close browser"""
        try:
            logger.info("🧹 Cleaning up Playwright resources...")
            
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.is_initialized = False
            
            # Log final performance stats
            stats = self.get_performance_stats()
            logger.info(f"📊 Final performance stats: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not await self.initialize_driver():
            raise RuntimeError("Failed to initialize Playwright driver")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_playwright_driver(source_name: str, browser_type: str = "chromium",
                           headless: bool = True, **kwargs) -> PlaywrightDriver:
    """
    Factory function to create a configured Playwright driver
    
    Args:
        source_name: Name of the scraping source
        browser_type: Browser type (chromium/firefox/webkit)
        headless: Whether to run in headless mode
        **kwargs: Additional configuration options
        
    Returns:
        Configured PlaywrightDriver instance
    """
    config = PlaywrightConfig(
        browser_type=browser_type,
        headless=headless,
        **kwargs
    )
    
    return PlaywrightDriver(source_name, config)

def create_indiabix_playwright_driver(**kwargs) -> PlaywrightDriver:
    """Create Playwright driver optimized for IndiaBix"""
    return create_playwright_driver(
        source_name="indiabix",
        browser_type="chromium",
        headless=True,
        enable_images=False,
        enable_javascript=True,
        stealth_mode=True,
        **kwargs
    )

def create_geeksforgeeks_playwright_driver(**kwargs) -> PlaywrightDriver:
    """Create Playwright driver optimized for GeeksforGeeks (JavaScript-heavy)"""
    return create_playwright_driver(
        source_name="geeksforgeeks",
        browser_type="chromium",
        headless=True,
        enable_images=False,
        enable_javascript=True,
        enable_performance_monitoring=True,
        stealth_mode=True,
        navigation_timeout=45000,
        **kwargs
    )