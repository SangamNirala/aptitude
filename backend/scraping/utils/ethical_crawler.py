"""
Ethical Crawler Utilities
Comprehensive ethical web crawling utilities combining anti-detection, rate limiting, and proxy management
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time
import random

from .anti_detection import AntiDetectionManager, DetectionRiskLevel
from .rate_limiter import ExponentialBackoffLimiter, RateLimitConfig
from .proxy_manager import ProxyManager, ProxyConfig

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class EthicalCrawlConfig:
    """Configuration for ethical crawling behavior"""
    
    # Basic crawl settings
    respect_robots_txt: bool = True
    user_agent_rotation: bool = True
    enable_rate_limiting: bool = True
    enable_proxy_rotation: bool = False
    
    # Rate limiting configuration
    default_delay: float = 2.0
    max_delay: float = 300.0
    requests_per_minute: int = 20
    requests_per_hour: int = 500
    
    # Session behavior
    max_session_duration: int = 1800  # 30 minutes
    session_break_duration: int = 600  # 10 minutes
    max_concurrent_requests: int = 3
    
    # Politeness settings
    respect_crawl_delay: bool = True
    minimum_crawl_delay: float = 1.0
    honor_retry_after: bool = True
    
    # Detection avoidance
    enable_human_simulation: bool = True
    reading_time_simulation: bool = True
    random_navigation_delay: bool = True
    
    # Error handling
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    timeout_seconds: float = 30.0

@dataclass
class CrawlRequest:
    """Request for ethical crawling"""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    priority: int = 1  # 1=highest, 5=lowest
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CrawlResponse:
    """Response from ethical crawling"""
    request: CrawlRequest
    status_code: int
    headers: Dict[str, str]
    content: str
    response_time: float
    success: bool
    error_message: Optional[str] = None
    used_proxy: Optional[str] = None
    detection_risk: Optional[DetectionRiskLevel] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

# =============================================================================
# ROBOTS.TXT MANAGER
# =============================================================================

class RobotsTxtManager:
    """Manager for robots.txt compliance"""
    
    def __init__(self):
        self.robots_cache: Dict[str, Tuple[RobotFileParser, datetime]] = {}
        self.cache_duration = timedelta(hours=24)  # Cache robots.txt for 24 hours
    
    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt"""
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            # Get robots.txt parser
            rp = await self._get_robots_parser(robots_url)
            if not rp:
                return True  # If robots.txt not accessible, assume allowed
            
            # Check if URL can be fetched
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking robots.txt for {url}: {str(e)}")
            return True  # Default to allowed on error
    
    async def get_crawl_delay(self, url: str, user_agent: str = "*") -> Optional[float]:
        """Get crawl delay from robots.txt"""
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = await self._get_robots_parser(robots_url)
            if not rp:
                return None
            
            return rp.crawl_delay(user_agent)
            
        except Exception as e:
            logger.debug(f"Error getting crawl delay for {url}: {str(e)}")
            return None
    
    async def _get_robots_parser(self, robots_url: str) -> Optional[RobotFileParser]:
        """Get cached or fetch robots.txt parser"""
        
        # Check cache first
        if robots_url in self.robots_cache:
            rp, cached_time = self.robots_cache[robots_url]
            if datetime.utcnow() - cached_time < self.cache_duration:
                return rp
        
        # Fetch robots.txt
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        
                        # Parse robots.txt
                        rp = RobotFileParser()
                        rp.set_url(robots_url)
                        rp.read_urllib(robots_content.splitlines())
                        
                        # Cache the parser
                        self.robots_cache[robots_url] = (rp, datetime.utcnow())
                        return rp
                    else:
                        return None
        
        except Exception as e:
            logger.debug(f"Failed to fetch robots.txt from {robots_url}: {str(e)}")
            return None

# =============================================================================
# ETHICAL CRAWLER
# =============================================================================

class EthicalCrawler:
    """
    Comprehensive ethical web crawler combining all anti-detection measures
    """
    
    def __init__(self, source_name: str, config: EthicalCrawlConfig = None):
        self.source_name = source_name
        self.config = config or EthicalCrawlConfig()
        
        # Initialize components
        self._init_components()
        
        # Request queue and session management
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.active_requests = 0
        self.session_start_time = datetime.utcnow()
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.blocked_requests = 0
        
        logger.info(f"🌐 EthicalCrawler initialized for {source_name}")
    
    def _init_components(self):
        """Initialize all crawler components"""
        
        # Anti-detection manager
        self.anti_detection = AntiDetectionManager(
            self.source_name,
            {
                "user_agent_rotation_frequency": 50,
                "session_duration": {"min": 180, "max": self.config.max_session_duration},
                "human_behavior": {"reading_time_multiplier": 1.0}
            }
        )
        
        # Rate limiter
        rate_config = RateLimitConfig(
            requests_per_second=1.0 / self.config.default_delay,
            requests_per_minute=self.config.requests_per_minute,
            requests_per_hour=self.config.requests_per_hour,
            base_delay=self.config.default_delay,
            max_delay=self.config.max_delay
        )
        self.rate_limiter = ExponentialBackoffLimiter(rate_config)
        
        # Proxy manager (optional)
        if self.config.enable_proxy_rotation:
            self.proxy_manager = ProxyManager()
        else:
            self.proxy_manager = None
        
        # Robots.txt manager
        if self.config.respect_robots_txt:
            self.robots_manager = RobotsTxtManager()
        else:
            self.robots_manager = None
    
    # =============================================================================
    # MAIN CRAWLING METHODS
    # =============================================================================
    
    async def crawl_url(self, url: str, **kwargs) -> CrawlResponse:
        """Crawl a single URL with full ethical compliance"""
        
        request = CrawlRequest(url=url, **kwargs)
        return await self.crawl_request(request)
    
    async def crawl_request(self, request: CrawlRequest) -> CrawlResponse:
        """Crawl a single request with full ethical compliance"""
        
        start_time = time.time()
        
        try:
            # Pre-crawl checks
            if not await self._pre_crawl_checks(request):
                return self._create_blocked_response(request, "Pre-crawl checks failed")
            
            # Apply rate limiting
            await self._apply_rate_limiting(request)
            
            # Get proxy if enabled
            proxy = await self._get_proxy() if self.proxy_manager else None
            
            # Prepare request
            prepared_request = await self._prepare_request(request, proxy)
            
            # Execute request
            response = await self._execute_request(prepared_request, proxy)
            
            # Post-crawl processing
            await self._post_crawl_processing(request, response)
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"❌ Crawl error for {request.url}: {str(e)}")
            
            return CrawlResponse(
                request=request,
                status_code=0,
                headers={},
                content="",
                response_time=response_time,
                success=False,
                error_message=str(e)
            )
    
    async def crawl_batch(self, requests: List[CrawlRequest]) -> List[CrawlResponse]:
        """Crawl multiple requests with concurrency control"""
        
        logger.info(f"📦 Starting batch crawl: {len(requests)} requests")
        
        # Add requests to queue
        for request in requests:
            await self.request_queue.put(request)
        
        # Process requests with concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def process_request():
            async with semaphore:
                try:
                    request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                    return await self.crawl_request(request)
                except asyncio.TimeoutError:
                    return None
        
        # Create tasks
        tasks = [process_request() for _ in range(len(requests))]
        
        # Execute tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_responses = [
            result for result in results 
            if isinstance(result, CrawlResponse)
        ]
        
        logger.info(f"✅ Batch crawl complete: {len(valid_responses)} responses")
        return valid_responses
    
    # =============================================================================
    # PRE-CRAWL CHECKS
    # =============================================================================
    
    async def _pre_crawl_checks(self, request: CrawlRequest) -> bool:
        """Perform pre-crawl ethical checks"""
        
        # Check robots.txt compliance
        if self.robots_manager:
            user_agent = self.anti_detection.get_user_agent()
            
            if not await self.robots_manager.can_fetch(request.url, user_agent):
                logger.info(f"🚫 Blocked by robots.txt: {request.url}")
                self.blocked_requests += 1
                return False
        
        # Check session duration limits
        session_duration = (datetime.utcnow() - self.session_start_time).total_seconds()
        if session_duration > self.config.max_session_duration:
            logger.info(f"📴 Session duration limit reached, taking break...")
            await self._take_session_break()
        
        # Check detection risk level
        should_pause, pause_duration = self.anti_detection.should_pause_session()
        if should_pause:
            logger.info(f"⏸️ Pausing due to detection risk: {pause_duration:.1f}s")
            await asyncio.sleep(pause_duration)
            self.anti_detection.reset_session()
            self.session_start_time = datetime.utcnow()
        
        return True
    
    async def _take_session_break(self):
        """Take a break between crawling sessions"""
        
        break_duration = random.uniform(
            self.config.session_break_duration * 0.8,
            self.config.session_break_duration * 1.2
        )
        
        logger.info(f"☕ Taking session break: {break_duration:.1f} seconds")
        await asyncio.sleep(break_duration)
        
        # Reset session state
        self.session_start_time = datetime.utcnow()
        self.anti_detection.reset_session()
    
    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    
    async def _apply_rate_limiting(self, request: CrawlRequest):
        """Apply rate limiting with respect for crawl-delay"""
        
        # Check robots.txt crawl delay
        crawl_delay = None
        if self.robots_manager:
            user_agent = self.anti_detection.get_user_agent()
            crawl_delay = await self.robots_manager.get_crawl_delay(request.url, user_agent)
        
        # Use the more restrictive delay
        if crawl_delay and self.config.respect_crawl_delay:
            required_delay = max(crawl_delay, self.config.minimum_crawl_delay)
            
            # Override rate limiter if robots.txt specifies longer delay
            if required_delay > self.config.default_delay:
                await asyncio.sleep(required_delay)
                return
        
        # Apply standard rate limiting
        if self.config.enable_rate_limiting:
            await self.rate_limiter.acquire()
    
    # =============================================================================
    # PROXY MANAGEMENT
    # =============================================================================
    
    async def _get_proxy(self) -> Optional[ProxyConfig]:
        """Get next proxy for request"""
        
        if not self.proxy_manager:
            return None
        
        proxy = self.proxy_manager.get_next_proxy()
        if not proxy:
            logger.warning("⚠️ No available proxies, proceeding without proxy")
        
        return proxy
    
    # =============================================================================
    # REQUEST PREPARATION AND EXECUTION
    # =============================================================================
    
    async def _prepare_request(self, request: CrawlRequest, proxy: Optional[ProxyConfig] = None) -> Dict[str, Any]:
        """Prepare request with appropriate headers and settings"""
        
        # Get anti-detection headers
        headers = self.anti_detection.get_request_headers(request.url)
        
        # Merge with custom headers (custom headers take precedence)
        headers.update(request.headers)
        
        # Prepare request configuration
        prepared = {
            "method": request.method,
            "url": request.url,
            "headers": headers,
            "timeout": aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            "data": request.data
        }
        
        # Add proxy configuration if available
        if proxy:
            prepared["proxy"] = proxy.url
        
        return prepared
    
    async def _execute_request(self, prepared_request: Dict[str, Any], proxy: Optional[ProxyConfig] = None) -> CrawlResponse:
        """Execute the HTTP request"""
        
        start_time = time.time()
        
        # Track request
        self.anti_detection.track_request(prepared_request["url"], prepared_request["method"])
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(**prepared_request) as response:
                    content = await response.text()
                    response_time = time.time() - start_time
                    
                    # Analyze response for detection indicators
                    detection_risk = self.anti_detection.analyze_response(
                        response.status,
                        dict(response.headers),
                        content,
                        response_time
                    )
                    
                    # Create response object
                    crawl_response = CrawlResponse(
                        request=CrawlRequest(url=prepared_request["url"]),  # Simplified for response
                        status_code=response.status,
                        headers=dict(response.headers),
                        content=content,
                        response_time=response_time,
                        success=response.status < 400,
                        used_proxy=proxy.id if proxy else None,
                        detection_risk=detection_risk
                    )
                    
                    # Update statistics
                    self.total_requests += 1
                    if crawl_response.success:
                        self.successful_requests += 1
                    else:
                        self.failed_requests += 1
                    
                    return crawl_response
        
        except Exception as e:
            response_time = time.time() - start_time
            
            # Handle connection errors, timeouts, etc.
            crawl_response = CrawlResponse(
                request=CrawlRequest(url=prepared_request["url"]),
                status_code=0,
                headers={},
                content="",
                response_time=response_time,
                success=False,
                error_message=str(e),
                used_proxy=proxy.id if proxy else None
            )
            
            self.total_requests += 1
            self.failed_requests += 1
            
            return crawl_response
    
    # =============================================================================
    # POST-CRAWL PROCESSING
    # =============================================================================
    
    async def _post_crawl_processing(self, request: CrawlRequest, response: CrawlResponse):
        """Process response and update component states"""
        
        # Update rate limiter
        self.rate_limiter.record_request(
            response.success,
            response.response_time,
            response.status_code
        )
        
        # Update proxy manager if used
        if self.proxy_manager and response.used_proxy:
            if response.success:
                self.proxy_manager.report_proxy_success(response.used_proxy, response.response_time)
            else:
                self.proxy_manager.report_proxy_failure(response.used_proxy, {
                    "status_code": response.status_code,
                    "error": response.error_message,
                    "url": response.request.url
                })
        
        # Simulate human reading time if enabled
        if (self.config.reading_time_simulation and 
            response.success and 
            len(response.content) > 1000):
            
            reading_time = self.anti_detection.simulate_reading_time(len(response.content))
            logger.debug(f"📖 Simulating reading time: {reading_time:.1f}s")
            await asyncio.sleep(reading_time)
    
    def _create_blocked_response(self, request: CrawlRequest, reason: str) -> CrawlResponse:
        """Create response for blocked requests"""
        
        return CrawlResponse(
            request=request,
            status_code=403,
            headers={},
            content="",
            response_time=0.0,
            success=False,
            error_message=f"Blocked: {reason}"
        )
    
    # =============================================================================
    # STATISTICS AND MONITORING
    # =============================================================================
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """Get comprehensive crawling statistics"""
        
        session_duration = (datetime.utcnow() - self.session_start_time).total_seconds()
        
        stats = {
            "crawler_name": self.source_name,
            "session_duration_seconds": session_duration,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "blocked_requests": self.blocked_requests,
            "success_rate": self.successful_requests / max(1, self.total_requests),
            "requests_per_minute": (self.total_requests / max(1, session_duration / 60)),
        }
        
        # Add component statistics
        stats.update({
            "anti_detection": self.anti_detection.get_request_statistics(),
            "rate_limiter": self.rate_limiter.get_statistics()
        })
        
        if self.proxy_manager:
            stats["proxy_manager"] = self.proxy_manager.get_proxy_statistics()
        
        return stats
    
    # =============================================================================
    # CONFIGURATION AND LIFECYCLE
    # =============================================================================
    
    def update_config(self, config_updates: Dict[str, Any]):
        """Update crawler configuration"""
        
        # Update main config
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Update component configs
        if "anti_detection" in config_updates:
            self.anti_detection.update_config(config_updates["anti_detection"])
        
        if "proxy_manager" in config_updates and self.proxy_manager:
            self.proxy_manager.update_config(config_updates["proxy_manager"])
        
        logger.info(f"📝 Crawler configuration updated for {self.source_name}")
    
    async def cleanup(self):
        """Cleanup crawler resources"""
        
        logger.info(f"🧹 Cleaning up crawler for {self.source_name}")
        
        # Cleanup components
        await self.anti_detection.cleanup()
        
        if self.proxy_manager:
            # Stop any background tasks if needed
            pass
        
        # Log final statistics
        final_stats = self.get_crawl_statistics()
        logger.info(f"📊 Final crawler stats: {final_stats}")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_ethical_crawler(source_name: str, config_dict: Dict[str, Any] = None) -> EthicalCrawler:
    """Factory function to create ethical crawler"""
    
    # Convert dict to config object
    config = EthicalCrawlConfig()
    if config_dict:
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return EthicalCrawler(source_name, config)