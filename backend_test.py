#!/usr/bin/env python3
"""
Comprehensive Backend Testing for AI-Enhanced Aptitude Questions API
Tests all AI services integration and endpoints + Anti-Detection & Rate Limiting System
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any
import os
import sys
from datetime import datetime

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIAptitudeAPITester:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = "https://scrapetest.preview.emergentagent.com/api"
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "performance_metrics": {}
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - PASSED ({response_time:.2f}s)")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def run_all_tests(self):
        """Run basic health check test"""
        logger.info("🚀 Starting AI Services Health Check...")
        start_time = time.time()
        
        # Test health endpoint
        try:
            start_time_test = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time_test
                data = await response.json()
                
                ai_services = data.get("ai_services", {})
                success = (
                    response.status == 200 and
                    data.get("status") == "healthy" and
                    ai_services.get("gemini") == "available" and
                    ai_services.get("groq") == "available" and
                    ai_services.get("huggingface") == "available"
                )
                
                details = f"MongoDB: {data.get('mongodb')}, AI Services: {ai_services}"
                self.log_test_result("Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Health Check", False, f"Exception: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 AI SERVICES TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 60)
        
        return self.test_results

class AntiDetectionSystemTester:
    """Tester for Anti-Detection & Rate Limiting System components"""
    
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "component_tests": {},
            "performance_metrics": {}
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - PASSED ({response_time:.2f}s)")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_imports(self):
        """Test that all scraping components can be imported"""
        logger.info("📦 Testing Anti-Detection System Imports...")
        
        try:
            # Test AntiDetectionManager import
            from scraping.utils.anti_detection import AntiDetectionManager, DetectionRiskLevel, create_anti_detection_manager
            self.log_test_result("AntiDetectionManager Import", True, "Successfully imported AntiDetectionManager and related classes")
        except Exception as e:
            self.log_test_result("AntiDetectionManager Import", False, f"Import error: {str(e)}")
        
        try:
            # Test Rate Limiter imports
            from scraping.utils.rate_limiter import RateLimiter, ExponentialBackoffLimiter, RateLimitConfig, BackoffStrategy, create_rate_limiter
            self.log_test_result("Rate Limiter Import", True, "Successfully imported rate limiter classes")
        except Exception as e:
            self.log_test_result("Rate Limiter Import", False, f"Import error: {str(e)}")
        
        try:
            # Test ProxyManager import
            from scraping.utils.proxy_manager import ProxyManager, ProxyConfig, ProxyType, create_proxy_manager
            self.log_test_result("ProxyManager Import", True, "Successfully imported proxy manager classes")
        except Exception as e:
            self.log_test_result("ProxyManager Import", False, f"Import error: {str(e)}")
        
        try:
            # Test EthicalCrawler import
            from scraping.utils.ethical_crawler import EthicalCrawler, EthicalCrawlConfig, create_ethical_crawler
            self.log_test_result("EthicalCrawler Import", True, "Successfully imported ethical crawler classes")
        except Exception as e:
            self.log_test_result("EthicalCrawler Import", False, f"Import error: {str(e)}")
    
    async def test_anti_detection_manager(self):
        """Test AntiDetectionManager functionality"""
        logger.info("🛡️ Testing AntiDetectionManager...")
        
        try:
            from scraping.utils.anti_detection import AntiDetectionManager, DetectionRiskLevel, create_anti_detection_manager
            
            # Test basic instantiation
            start_time = time.time()
            manager = AntiDetectionManager("test_source")
            response_time = time.time() - start_time
            
            success = manager is not None and manager.source_name == "test_source"
            self.log_test_result("AntiDetectionManager Instantiation", success, 
                               f"Manager created for source: {manager.source_name if manager else 'None'}", response_time)
            
            if not success:
                return
            
            # Test user agent rotation
            start_time = time.time()
            ua1 = manager.get_user_agent()
            ua2 = manager.get_user_agent(force_rotation=True)
            response_time = time.time() - start_time
            
            success = ua1 is not None and ua2 is not None and len(ua1) > 10
            self.log_test_result("User Agent Rotation", success, 
                               f"UA1 length: {len(ua1) if ua1 else 0}, UA2 length: {len(ua2) if ua2 else 0}", response_time)
            
            # Test request headers generation
            start_time = time.time()
            headers = manager.get_request_headers("https://example.com")
            response_time = time.time() - start_time
            
            required_headers = ["User-Agent", "Accept", "Accept-Language"]
            success = all(header in headers for header in required_headers)
            self.log_test_result("Request Headers Generation", success, 
                               f"Generated {len(headers)} headers, required headers present: {success}", response_time)
            
            # Test human delay simulation
            start_time = time.time()
            delay = manager.get_human_delay(2.0)
            response_time = time.time() - start_time
            
            success = isinstance(delay, float) and 0.5 <= delay <= 10.0
            self.log_test_result("Human Delay Simulation", success, 
                               f"Generated delay: {delay:.2f}s", response_time)
            
            # Test reading time simulation
            start_time = time.time()
            reading_time = manager.simulate_reading_time(1000)
            response_time = time.time() - start_time
            
            success = isinstance(reading_time, float) and 2.0 <= reading_time <= 60.0
            self.log_test_result("Reading Time Simulation", success, 
                               f"Reading time for 1000 chars: {reading_time:.2f}s", response_time)
            
            # Test detection risk analysis
            start_time = time.time()
            risk_level = manager.analyze_response(200, {}, "normal content", 1.0)
            response_time = time.time() - start_time
            
            success = risk_level == DetectionRiskLevel.LOW
            self.log_test_result("Detection Risk Analysis", success, 
                               f"Risk level for normal response: {risk_level.value}", response_time)
            
            # Test request tracking
            start_time = time.time()
            manager.track_request("https://example.com/test")
            stats = manager.get_request_statistics()
            response_time = time.time() - start_time
            
            success = stats.get("total_requests", 0) > 0
            self.log_test_result("Request Tracking", success, 
                               f"Tracked requests: {stats.get('total_requests', 0)}", response_time)
            
            # Test factory function
            start_time = time.time()
            factory_manager = create_anti_detection_manager("indiabix")
            response_time = time.time() - start_time
            
            success = factory_manager is not None and factory_manager.source_name == "indiabix"
            self.log_test_result("Factory Function", success, 
                               f"Factory created manager for: {factory_manager.source_name if factory_manager else 'None'}", response_time)
            
        except Exception as e:
            self.log_test_result("AntiDetectionManager Test", False, f"Exception: {str(e)}")
    
    async def test_rate_limiters(self):
        """Test Rate Limiter functionality"""
        logger.info("🚦 Testing Rate Limiters...")
        
        try:
            from scraping.utils.rate_limiter import RateLimiter, ExponentialBackoffLimiter, RateLimitConfig, BackoffStrategy, create_rate_limiter
            
            # Test basic RateLimiter
            start_time = time.time()
            config = RateLimitConfig(requests_per_second=2.0, base_delay=0.5)
            limiter = RateLimiter(config)
            response_time = time.time() - start_time
            
            success = limiter is not None and limiter.config.requests_per_second == 2.0
            self.log_test_result("Basic RateLimiter Creation", success, 
                               f"RPS: {limiter.config.requests_per_second if limiter else 'None'}", response_time)
            
            if not success:
                return
            
            # Test rate limiting acquire (should be fast for first request)
            start_time = time.time()
            delay = await limiter.acquire()
            response_time = time.time() - start_time
            
            success = isinstance(delay, float) and delay >= 0
            self.log_test_result("Rate Limiter Acquire", success, 
                               f"First request delay: {delay:.3f}s", response_time)
            
            # Test request recording
            start_time = time.time()
            limiter.record_request(True, 1.0, 200)
            stats = limiter.get_statistics()
            response_time = time.time() - start_time
            
            success = stats.get("total_requests", 0) > 0
            self.log_test_result("Request Recording", success, 
                               f"Total requests: {stats.get('total_requests', 0)}", response_time)
            
            # Test ExponentialBackoffLimiter
            start_time = time.time()
            backoff_config = RateLimitConfig(
                requests_per_second=1.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                base_delay=1.0,
                max_delay=10.0
            )
            backoff_limiter = ExponentialBackoffLimiter(backoff_config)
            response_time = time.time() - start_time
            
            success = backoff_limiter is not None and backoff_limiter.backoff_level == 0
            self.log_test_result("ExponentialBackoffLimiter Creation", success, 
                               f"Initial backoff level: {backoff_limiter.backoff_level if backoff_limiter else 'None'}", response_time)
            
            # Test backoff behavior with failures
            start_time = time.time()
            for i in range(3):  # Trigger backoff with failures
                backoff_limiter.record_request(False, 1.0, 429)  # Too Many Requests
            response_time = time.time() - start_time
            
            success = backoff_limiter.backoff_level > 0
            self.log_test_result("Backoff Trigger", success, 
                               f"Backoff level after failures: {backoff_limiter.backoff_level}", response_time)
            
            # Test different backoff strategies
            strategies_tested = []
            for strategy in [BackoffStrategy.LINEAR, BackoffStrategy.FIBONACCI, BackoffStrategy.EXPONENTIAL]:
                try:
                    start_time = time.time()
                    strategy_config = RateLimitConfig(backoff_strategy=strategy, base_delay=0.1, max_delay=1.0)
                    strategy_limiter = ExponentialBackoffLimiter(strategy_config)
                    response_time = time.time() - start_time
                    
                    success = strategy_limiter is not None
                    strategies_tested.append(strategy.value)
                    self.log_test_result(f"Backoff Strategy {strategy.value}", success, 
                                       f"Strategy limiter created", response_time)
                except Exception as e:
                    self.log_test_result(f"Backoff Strategy {strategy.value}", False, f"Error: {str(e)}")
            
            # Test factory function
            start_time = time.time()
            factory_limiter = create_rate_limiter("exponential", {"base_delay": 1.0})
            response_time = time.time() - start_time
            
            success = factory_limiter is not None
            self.log_test_result("Rate Limiter Factory", success, 
                               f"Factory created limiter: {type(factory_limiter).__name__ if factory_limiter else 'None'}", response_time)
            
        except Exception as e:
            self.log_test_result("Rate Limiter Test", False, f"Exception: {str(e)}")
    
    async def test_proxy_manager(self):
        """Test ProxyManager functionality (without actual proxies)"""
        logger.info("🔄 Testing ProxyManager...")
        
        try:
            from scraping.utils.proxy_manager import ProxyManager, ProxyConfig, ProxyType, create_proxy_manager
            
            # Test basic ProxyManager creation
            start_time = time.time()
            manager = ProxyManager()
            response_time = time.time() - start_time
            
            success = manager is not None and len(manager.proxies) == 0
            self.log_test_result("ProxyManager Creation", success, 
                               f"Manager created with {len(manager.proxies)} proxies", response_time)
            
            if not success:
                return
            
            # Test adding proxies
            start_time = time.time()
            proxy_id = manager.add_proxy("127.0.0.1", 8080, ProxyType.HTTP)
            response_time = time.time() - start_time
            
            success = proxy_id is not None and len(manager.proxies) == 1
            self.log_test_result("Add Proxy", success, 
                               f"Added proxy with ID: {proxy_id}, total proxies: {len(manager.proxies)}", response_time)
            
            # Test proxy configuration
            start_time = time.time()
            proxy = manager.proxies.get(proxy_id)
            response_time = time.time() - start_time
            
            success = proxy is not None and proxy.host == "127.0.0.1" and proxy.port == 8080
            self.log_test_result("Proxy Configuration", success, 
                               f"Proxy host: {proxy.host if proxy else 'None'}, port: {proxy.port if proxy else 'None'}", response_time)
            
            # Test adding multiple proxies
            start_time = time.time()
            proxy_list = [
                {"host": "127.0.0.2", "port": 3128, "proxy_type": ProxyType.HTTP},
                {"host": "127.0.0.3", "port": 1080, "proxy_type": ProxyType.SOCKS5}
            ]
            added_count = manager.add_proxy_list(proxy_list)
            response_time = time.time() - start_time
            
            success = added_count == 2 and len(manager.proxies) == 3
            self.log_test_result("Add Proxy List", success, 
                               f"Added {added_count} proxies, total: {len(manager.proxies)}", response_time)
            
            # Test rotation strategies
            strategies = ["round_robin", "random", "performance"]
            for strategy in strategies:
                start_time = time.time()
                manager.set_rotation_strategy(strategy)
                response_time = time.time() - start_time
                
                success = manager.rotation_strategy == strategy
                self.log_test_result(f"Rotation Strategy {strategy}", success, 
                                   f"Strategy set to: {manager.rotation_strategy}", response_time)
            
            # Test proxy statistics
            start_time = time.time()
            stats = manager.get_proxy_statistics()
            response_time = time.time() - start_time
            
            success = isinstance(stats, dict) and stats.get("total_proxies", 0) > 0
            self.log_test_result("Proxy Statistics", success, 
                               f"Stats: {stats.get('total_proxies', 0)} total, {stats.get('active_proxies', 0)} active", response_time)
            
            # Test proxy failure reporting
            start_time = time.time()
            manager.report_proxy_failure(proxy_id, {"error": "test_error"})
            updated_proxy = manager.proxies.get(proxy_id)
            response_time = time.time() - start_time
            
            success = updated_proxy and updated_proxy.failure_count > 0
            self.log_test_result("Proxy Failure Reporting", success, 
                               f"Failure count: {updated_proxy.failure_count if updated_proxy else 'None'}", response_time)
            
            # Test factory function
            start_time = time.time()
            factory_manager = create_proxy_manager({"rotation_strategy": "random"})
            response_time = time.time() - start_time
            
            success = factory_manager is not None
            self.log_test_result("ProxyManager Factory", success, 
                               f"Factory created manager with strategy: {factory_manager.rotation_strategy if factory_manager else 'None'}", response_time)
            
        except Exception as e:
            self.log_test_result("ProxyManager Test", False, f"Exception: {str(e)}")
    
    async def test_ethical_crawler(self):
        """Test EthicalCrawler integration"""
        logger.info("🌐 Testing EthicalCrawler...")
        
        try:
            from scraping.utils.ethical_crawler import EthicalCrawler, EthicalCrawlConfig, create_ethical_crawler
            
            # Test basic crawler creation
            start_time = time.time()
            config = EthicalCrawlConfig(
                respect_robots_txt=False,  # Disable for testing
                enable_proxy_rotation=False,  # Disable for testing
                default_delay=0.1,  # Fast for testing
                max_concurrent_requests=1
            )
            crawler = EthicalCrawler("test_crawler", config)
            response_time = time.time() - start_time
            
            success = crawler is not None and crawler.source_name == "test_crawler"
            self.log_test_result("EthicalCrawler Creation", success, 
                               f"Crawler created for: {crawler.source_name if crawler else 'None'}", response_time)
            
            if not success:
                return
            
            # Test component initialization
            start_time = time.time()
            has_anti_detection = hasattr(crawler, 'anti_detection') and crawler.anti_detection is not None
            has_rate_limiter = hasattr(crawler, 'rate_limiter') and crawler.rate_limiter is not None
            has_robots_manager = hasattr(crawler, 'robots_manager')
            response_time = time.time() - start_time
            
            success = has_anti_detection and has_rate_limiter
            self.log_test_result("Component Integration", success, 
                               f"Anti-detection: {has_anti_detection}, Rate limiter: {has_rate_limiter}, Robots: {has_robots_manager}", response_time)
            
            # Test configuration updates
            start_time = time.time()
            crawler.update_config({"default_delay": 0.2, "max_concurrent_requests": 2})
            response_time = time.time() - start_time
            
            success = crawler.config.default_delay == 0.2 and crawler.config.max_concurrent_requests == 2
            self.log_test_result("Configuration Update", success, 
                               f"Updated delay: {crawler.config.default_delay}, concurrent: {crawler.config.max_concurrent_requests}", response_time)
            
            # Test statistics
            start_time = time.time()
            stats = crawler.get_crawl_statistics()
            response_time = time.time() - start_time
            
            success = isinstance(stats, dict) and "crawler_name" in stats
            self.log_test_result("Crawl Statistics", success, 
                               f"Stats keys: {list(stats.keys()) if isinstance(stats, dict) else 'Not dict'}", response_time)
            
            # Test factory function
            start_time = time.time()
            factory_crawler = create_ethical_crawler("factory_test", {
                "respect_robots_txt": False,
                "default_delay": 0.1
            })
            response_time = time.time() - start_time
            
            success = factory_crawler is not None and factory_crawler.source_name == "factory_test"
            self.log_test_result("EthicalCrawler Factory", success, 
                               f"Factory crawler: {factory_crawler.source_name if factory_crawler else 'None'}", response_time)
            
            # Test cleanup
            start_time = time.time()
            await crawler.cleanup()
            response_time = time.time() - start_time
            
            success = True  # If no exception, cleanup succeeded
            self.log_test_result("Crawler Cleanup", success, 
                               f"Cleanup completed", response_time)
            
        except Exception as e:
            self.log_test_result("EthicalCrawler Test", False, f"Exception: {str(e)}")
    
    async def test_configuration_integration(self):
        """Test configuration and factory functions"""
        logger.info("⚙️ Testing Configuration Integration...")
        
        try:
            # Test all factory functions work together
            from scraping.utils.anti_detection import create_anti_detection_manager
            from scraping.utils.rate_limiter import create_rate_limiter
            from scraping.utils.proxy_manager import create_proxy_manager
            from scraping.utils.ethical_crawler import create_ethical_crawler
            
            start_time = time.time()
            
            # Create components using factory functions
            anti_detection = create_anti_detection_manager("test_source", {
                "user_agent_rotation_frequency": 10,
                "session_duration": {"min": 60, "max": 300}
            })
            
            rate_limiter = create_rate_limiter("exponential", {
                "base_delay": 1.0,
                "max_delay": 30.0
            })
            
            proxy_manager = create_proxy_manager({
                "rotation_strategy": "performance",
                "test_interval_minutes": 5
            })
            
            crawler = create_ethical_crawler("integration_test", {
                "respect_robots_txt": False,
                "enable_proxy_rotation": False,
                "default_delay": 0.5
            })
            
            response_time = time.time() - start_time
            
            success = all([
                anti_detection is not None,
                rate_limiter is not None,
                proxy_manager is not None,
                crawler is not None
            ])
            
            self.log_test_result("Factory Integration", success, 
                               f"All components created successfully", response_time)
            
            # Test configuration consistency
            start_time = time.time()
            
            # Update configurations
            anti_detection.update_config({"user_agent_rotation_frequency": 25})
            proxy_manager.update_config({"rotation_strategy": "random"})
            crawler.update_config({"default_delay": 1.0})
            
            response_time = time.time() - start_time
            
            config_success = (
                anti_detection.user_agent_rotation_frequency == 25 and
                proxy_manager.rotation_strategy == "random" and
                crawler.config.default_delay == 1.0
            )
            
            self.log_test_result("Configuration Updates", config_success, 
                               f"All configurations updated successfully", response_time)
            
        except Exception as e:
            self.log_test_result("Configuration Integration", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all anti-detection system tests"""
        logger.info("🚀 Starting Anti-Detection & Rate Limiting System Testing...")
        start_time = time.time()
        
        # Run all test suites
        await self.test_imports()
        await self.test_anti_detection_manager()
        await self.test_rate_limiters()
        await self.test_proxy_manager()
        await self.test_ethical_crawler()
        await self.test_configuration_integration()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 ANTI-DETECTION SYSTEM TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 60)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results
        
    def log_test_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - PASSED ({response_time:.2f}s)")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_health_endpoints(self):
        """Test basic health and status endpoints"""
        logger.info("🔍 Testing Health & Status Endpoints...")
        
        # Test root endpoint
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/") as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    "AI-Enhanced Aptitude Questions API" in data.get("message", "") and
                    "features" in data and
                    len(data["features"]) >= 4
                )
                
                details = f"Status: {response.status}, Features: {len(data.get('features', []))}"
                self.log_test_result("Root Endpoint", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Root Endpoint", False, f"Exception: {str(e)}")
        
        # Test health endpoint
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                ai_services = data.get("ai_services", {})
                success = (
                    response.status == 200 and
                    data.get("status") == "healthy" and
                    ai_services.get("gemini") == "available" and
                    ai_services.get("groq") == "available" and
                    ai_services.get("huggingface") == "available"
                )
                
                details = f"MongoDB: {data.get('mongodb')}, AI Services: {ai_services}"
                self.log_test_result("Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Health Check", False, f"Exception: {str(e)}")
    
    async def test_ai_question_generation(self):
        """Test AI question generation endpoints"""
        logger.info("🤖 Testing AI Question Generation...")
        
        # Test generate-ai endpoint
        try:
            start_time = time.time()
            payload = {
                "category": "quantitative",
                "difficulty": "placement_ready", 
                "topic": "percentages",
                "company_pattern": "TCS"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-ai",
                params=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "question_text" in data and
                        "options" in data and
                        len(data["options"]) == 4 and
                        "correct_answer" in data and
                        "ai_metrics" in data and
                        data["ai_metrics"]["quality_score"] > 0
                    )
                    details = f"Generated question with quality score: {data.get('ai_metrics', {}).get('quality_score', 0)}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Question Generation", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("AI Question Generation", False, f"Exception: {str(e)}")
        
        # Test create-enhanced endpoint
        try:
            start_time = time.time()
            payload = {
                "question_text": "If 20% of a number is 40, what is 50% of the same number?",
                "options": ["A) 80", "B) 100", "C) 120", "D) 160"],
                "correct_answer": "B) 100",
                "category": "quantitative",
                "difficulty": "placement_ready",
                "source": "manual"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/create-enhanced",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        data["question_text"] == payload["question_text"] and
                        "ai_metrics" in data and
                        "metadata" in data and
                        data["ai_metrics"]["quality_score"] > 0
                    )
                    details = f"Enhanced question created with quality: {data.get('ai_metrics', {}).get('quality_score', 0)}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Create Enhanced Question", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Create Enhanced Question", False, f"Exception: {str(e)}")
    
    async def test_instant_feedback_system(self):
        """Test ultra-fast Groq-powered feedback system"""
        logger.info("⚡ Testing Instant Feedback System...")
        
        try:
            start_time = time.time()
            payload = {
                "question_id": "test-question-123",
                "question_text": "What is 25% of 200?",
                "user_answer": "50",
                "correct_answer": "50"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/instant-feedback",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "is_correct" in data and
                        "feedback" in data and
                        "response_time_ms" in data and
                        response_time < 2.0  # Should be ultra-fast
                    )
                    details = f"Feedback in {response_time:.3f}s, Correct: {data.get('is_correct')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Instant Feedback", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Instant Feedback", False, f"Exception: {str(e)}")
    
    async def test_ai_analysis_features(self):
        """Test AI analysis features (hints, difficulty assessment, duplicates)"""
        logger.info("🧠 Testing AI Analysis Features...")
        
        # Test generate-hint
        try:
            start_time = time.time()
            payload = {
                "question_text": "A train travels 120 km in 2 hours. What is its speed?",
                "user_progress": "I know distance and time but stuck on formula"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-hint",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "hint" in data and
                        len(data["hint"]) > 10 and
                        response_time < 2.0
                    )
                    details = f"Hint generated in {response_time:.3f}s"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Generate Hint", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Generate Hint", False, f"Exception: {str(e)}")
        
        # Test assess-difficulty
        try:
            start_time = time.time()
            payload = {
                "question_text": "Find the compound interest on Rs. 10000 at 10% per annum for 2 years compounded annually",
                "options": ["A) Rs. 2000", "B) Rs. 2100", "C) Rs. 2200", "D) Rs. 2300"]
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/assess-difficulty",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "difficulty_score" in data and
                        "difficulty_level" in data and
                        1 <= data["difficulty_score"] <= 10
                    )
                    details = f"Difficulty: {data.get('difficulty_level')} (Score: {data.get('difficulty_score')})"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Assess Difficulty", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Assess Difficulty", False, f"Exception: {str(e)}")
        
        # Test detect-duplicates
        try:
            start_time = time.time()
            payload = {
                "question_text": "What is 10% of 100?",
                "similarity_threshold": 0.85
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/detect-duplicates",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "is_duplicate" in data and
                        "similarity_scores" in data
                    )
                    details = f"Duplicate check completed, Is duplicate: {data.get('is_duplicate')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Detect Duplicates", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Detect Duplicates", False, f"Exception: {str(e)}")
    
    async def test_smart_features(self):
        """Test smart features like personalized questions and quality stats"""
        logger.info("🎯 Testing Smart Features...")
        
        # Test generate-personalized
        try:
            start_time = time.time()
            payload = {
                "user_id": "test-user-123",
                "weak_areas": ["percentages", "profit_loss"],
                "target_companies": ["TCS", "Infosys"],
                "count": 3
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-personalized",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, list) and
                        len(data) > 0 and
                        all("question_text" in q for q in data)
                    )
                    details = f"Generated {len(data)} personalized questions"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Generate Personalized Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Generate Personalized Questions", False, f"Exception: {str(e)}")
        
        # Test quality-stats
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/quality-stats") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "total_questions" in data and
                        "avg_quality_score" in data and
                        isinstance(data["total_questions"], int)
                    )
                    details = f"Total questions: {data.get('total_questions')}, Avg quality: {data.get('avg_quality_score', 0):.1f}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Quality Stats", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Quality Stats", False, f"Exception: {str(e)}")
    
    async def test_database_operations(self):
        """Test database operations with AI-enhanced models"""
        logger.info("💾 Testing Database Operations...")
        
        # Test filtered questions
        try:
            start_time = time.time()
            params = {
                "category": "quantitative",
                "difficulty": "placement_ready",
                "min_quality_score": 70.0,
                "limit": 5
            }
            
            async with self.session.get(
                f"{self.base_url}/questions/filtered",
                params=params
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "questions" in data and
                        "total_count" in data and
                        "batch_quality_score" in data and
                        isinstance(data["questions"], list)
                    )
                    details = f"Found {len(data.get('questions', []))} questions, Quality: {data.get('batch_quality_score', 0):.1f}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Filtered Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Filtered Questions", False, f"Exception: {str(e)}")
        
        # Test company-specific questions
        try:
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/questions/company-specific/TCS",
                params={"count": 3}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, list) and
                        len(data) >= 0  # May be empty if no TCS questions exist yet
                    )
                    details = f"Found {len(data)} TCS-specific questions"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Company-Specific Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Company-Specific Questions", False, f"Exception: {str(e)}")
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for AI services"""
        logger.info("⏱️ Testing Performance Benchmarks...")
        
        # Test multiple instant feedback calls for performance
        feedback_times = []
        for i in range(3):
            try:
                start_time = time.time()
                payload = {
                    "question_id": f"perf-test-{i}",
                    "question_text": f"What is {10 + i * 5}% of 100?",
                    "user_answer": str(10 + i * 5),
                    "correct_answer": str(10 + i * 5)
                }
                
                async with self.session.post(
                    f"{self.base_url}/questions/instant-feedback",
                    json=payload
                ) as response:
                    response_time = time.time() - start_time
                    feedback_times.append(response_time)
                    
            except Exception as e:
                logger.error(f"Performance test {i} failed: {str(e)}")
        
        if feedback_times:
            avg_time = sum(feedback_times) / len(feedback_times)
            max_time = max(feedback_times)
            success = avg_time < 2.0 and max_time < 3.0
            details = f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s"
            self.log_test_result("Performance Benchmark", success, details, avg_time)
            
            self.test_results["performance_metrics"] = {
                "avg_feedback_time": avg_time,
                "max_feedback_time": max_time,
                "feedback_samples": len(feedback_times)
            }
    
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting Comprehensive AI-Enhanced Backend Testing...")
        start_time = time.time()
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_ai_question_generation()
        await self.test_instant_feedback_system()
        await self.test_ai_analysis_features()
        await self.test_smart_features()
        await self.test_database_operations()
        await self.test_performance_benchmarks()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        
        if self.test_results["performance_metrics"]:
            logger.info(f"Avg Feedback Time: {self.test_results['performance_metrics']['avg_feedback_time']:.3f}s")
        
        logger.info("=" * 60)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results

class ScrapingExtractorsTester:
    """Tester for TASK 6-8 - Content Extractors & Main Scraping Coordinator"""
    
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "component_tests": {}
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - PASSED ({response_time:.2f}s)")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_scraping_module_imports(self):
        """Test scraping module imports and organization"""
        logger.info("📦 Testing Scraping Module Imports...")
        
        try:
            # Test main scraping module import
            start_time = time.time()
            import scraping
            response_time = time.time() - start_time
            
            success = hasattr(scraping, '__version__') and scraping.__version__ == "1.0.0"
            self.log_test_result("Scraping Module Import", success, 
                               f"Module imported with version: {getattr(scraping, '__version__', 'None')}", response_time)
        except Exception as e:
            self.log_test_result("Scraping Module Import", False, f"Import error: {str(e)}")
        
        # Test core engine imports
        try:
            start_time = time.time()
            from scraping import (
                ScrapingEngine, ScrapingEngineConfig, JobProgress, ScrapingStats,
                create_scraping_engine, create_quick_scraping_job, 
                get_scraping_engine, shutdown_scraping_engine
            )
            response_time = time.time() - start_time
            self.log_test_result("Core Engine Imports", True, "Successfully imported all core engine classes", response_time)
        except Exception as e:
            self.log_test_result("Core Engine Imports", False, f"Import error: {str(e)}")
        
        # Test extractor imports
        try:
            start_time = time.time()
            from scraping import (
                BaseContentExtractor, ExtractionResult, BatchExtractionResult,
                IndiaBixExtractor, create_indiabix_extractor,
                GeeksforGeeksExtractor, create_geeksforgeeks_extractor
            )
            response_time = time.time() - start_time
            self.log_test_result("Extractor Imports", True, "Successfully imported all extractor classes", response_time)
        except Exception as e:
            self.log_test_result("Extractor Imports", False, f"Import error: {str(e)}")
        
        # Test utility imports
        try:
            start_time = time.time()
            from scraping import (
                ContentValidator, create_indiabix_validator, create_geeksforgeeks_validator,
                PerformanceMonitor, create_performance_monitor
            )
            response_time = time.time() - start_time
            self.log_test_result("Utility Imports", True, "Successfully imported utility classes", response_time)
        except Exception as e:
            self.log_test_result("Utility Imports", False, f"Import error: {str(e)}")
    
    async def test_base_extractor_framework(self):
        """Test BaseContentExtractor framework"""
        logger.info("🏗️ Testing Base Extractor Framework...")
        
        try:
            from scraping.extractors.base_extractor import (
                BaseContentExtractor, ExtractionResult, BatchExtractionResult,
                PageExtractionContext, create_extraction_context, merge_batch_results
            )
            
            # Test ExtractionResult creation
            start_time = time.time()
            extraction_result = ExtractionResult(
                success=True,
                question_data=None,
                extraction_time=1.5,
                source_url="https://test.com"
            )
            response_time = time.time() - start_time
            
            success = (extraction_result.success == True and 
                      extraction_result.extraction_time == 1.5 and
                      extraction_result.source_url == "https://test.com")
            self.log_test_result("ExtractionResult Creation", success, 
                               f"Result created with success: {extraction_result.success}", response_time)
            
            # Test BatchExtractionResult creation
            start_time = time.time()
            batch_result = BatchExtractionResult(
                total_processed=10,
                successful_extractions=8,
                failed_extractions=2,
                extraction_results=[extraction_result],
                batch_start_time=datetime.now(),
                batch_end_time=datetime.now(),
                total_batch_time=5.0,
                errors=["Test error"],
                metadata={"test": "data"}
            )
            response_time = time.time() - start_time
            
            success = (batch_result.total_processed == 10 and
                      batch_result.successful_extractions == 8 and
                      len(batch_result.extraction_results) == 1)
            self.log_test_result("BatchExtractionResult Creation", success, 
                               f"Batch result: {batch_result.successful_extractions}/{batch_result.total_processed} successful", response_time)
            
            # Test PageExtractionContext creation
            start_time = time.time()
            context = PageExtractionContext(
                page_url="https://test.com/page1",
                page_number=1,
                category="quantitative",
                subcategory="percentages",
                expected_questions=20,
                selectors={"question": "div.question"},
                extraction_config={}
            )
            response_time = time.time() - start_time
            
            success = (context.page_number == 1 and 
                      context.category == "quantitative" and
                      context.expected_questions == 20)
            self.log_test_result("PageExtractionContext Creation", success, 
                               f"Context created for page {context.page_number}, category: {context.category}", response_time)
            
            # Test merge_batch_results utility
            start_time = time.time()
            batch1 = BatchExtractionResult(
                total_processed=5, successful_extractions=4, failed_extractions=1,
                extraction_results=[], batch_start_time=datetime.now(),
                batch_end_time=datetime.now(), total_batch_time=2.0,
                errors=[], metadata={}
            )
            batch2 = BatchExtractionResult(
                total_processed=3, successful_extractions=2, failed_extractions=1,
                extraction_results=[], batch_start_time=datetime.now(),
                batch_end_time=datetime.now(), total_batch_time=1.5,
                errors=[], metadata={}
            )
            
            merged = merge_batch_results([batch1, batch2])
            response_time = time.time() - start_time
            
            success = (merged.total_processed == 8 and 
                      merged.successful_extractions == 6 and
                      merged.failed_extractions == 2)
            self.log_test_result("Merge Batch Results", success, 
                               f"Merged: {merged.successful_extractions}/{merged.total_processed} successful", response_time)
            
        except Exception as e:
            self.log_test_result("Base Extractor Framework", False, f"Framework test error: {str(e)}")
    
    async def test_indiabix_extractor(self):
        """Test IndiaBix Content Extractor"""
        logger.info("🇮🇳 Testing IndiaBix Extractor...")
        
        try:
            from scraping.extractors.indiabix_extractor import IndiaBixExtractor, create_indiabix_extractor
            from config.scraping_config import INDIABIX_CONFIG
            
            # Test factory function
            start_time = time.time()
            extractor = create_indiabix_extractor()
            response_time = time.time() - start_time
            
            success = (extractor is not None and 
                      extractor.source_name == "indiabix" and
                      hasattr(extractor, 'indiabix_patterns'))
            self.log_test_result("IndiaBix Extractor Factory", success, 
                               f"Extractor created for source: {extractor.source_name if extractor else 'None'}", response_time)
            
            if not success:
                return
            
            # Test extractor configuration
            start_time = time.time()
            has_patterns = hasattr(extractor, 'indiabix_patterns') and len(extractor.indiabix_patterns) > 0
            has_format_rules = hasattr(extractor, 'format_rules') and len(extractor.format_rules) > 0
            has_validator = extractor.validator is not None
            has_performance_monitor = extractor.performance_monitor is not None
            response_time = time.time() - start_time
            
            success = has_patterns and has_format_rules and has_validator and has_performance_monitor
            self.log_test_result("IndiaBix Extractor Configuration", success, 
                               f"Patterns: {has_patterns}, Rules: {has_format_rules}, Validator: {has_validator}, Monitor: {has_performance_monitor}", response_time)
            
            # Test text cleaning methods
            start_time = time.time()
            test_text = "Q. 1. What is 25% of 200?   "
            cleaned = extractor.clean_text(test_text)
            response_time = time.time() - start_time
            
            success = cleaned == "Q. 1. What is 25% of 200?" and len(cleaned) < len(test_text)
            self.log_test_result("IndiaBix Text Cleaning", success, 
                               f"Original: '{test_text}' -> Cleaned: '{cleaned}'", response_time)
            
            # Test IndiaBix-specific pattern matching
            start_time = time.time()
            option_text = "A) 50"
            cleaned_option = extractor.indiabix_patterns["option_prefix"].sub("", option_text).strip()
            response_time = time.time() - start_time
            
            success = cleaned_option == "50"
            self.log_test_result("IndiaBix Pattern Matching", success, 
                               f"Option '{option_text}' -> '{cleaned_option}'", response_time)
            
            # Test extraction statistics
            start_time = time.time()
            stats = extractor.get_extraction_statistics()
            response_time = time.time() - start_time
            
            success = (isinstance(stats, dict) and 
                      "total_processed" in stats and
                      "success_rate" in stats and
                      stats["total_processed"] == 0)
            self.log_test_result("IndiaBix Statistics", success, 
                               f"Stats keys: {list(stats.keys()) if isinstance(stats, dict) else 'Not dict'}", response_time)
            
        except Exception as e:
            self.log_test_result("IndiaBix Extractor", False, f"Extractor test error: {str(e)}")
    
    async def test_geeksforgeeks_extractor(self):
        """Test GeeksforGeeks Content Extractor"""
        logger.info("🤓 Testing GeeksforGeeks Extractor...")
        
        try:
            from scraping.extractors.geeksforgeeks_extractor import GeeksforGeeksExtractor, create_geeksforgeeks_extractor
            from config.scraping_config import GEEKSFORGEEKS_CONFIG
            
            # Test factory function
            start_time = time.time()
            extractor = create_geeksforgeeks_extractor()
            response_time = time.time() - start_time
            
            success = (extractor is not None and 
                      extractor.source_name == "geeksforgeeks" and
                      hasattr(extractor, 'gfg_patterns'))
            self.log_test_result("GeeksforGeeks Extractor Factory", success, 
                               f"Extractor created for source: {extractor.source_name if extractor else 'None'}", response_time)
            
            if not success:
                return
            
            # Test GeeksforGeeks-specific configuration
            start_time = time.time()
            has_gfg_patterns = hasattr(extractor, 'gfg_patterns') and len(extractor.gfg_patterns) > 0
            has_gfg_formats = hasattr(extractor, 'gfg_formats') and len(extractor.gfg_formats) > 0
            has_dynamic_selectors = hasattr(extractor, 'dynamic_selectors') and len(extractor.dynamic_selectors) > 0
            response_time = time.time() - start_time
            
            success = has_gfg_patterns and has_gfg_formats and has_dynamic_selectors
            self.log_test_result("GeeksforGeeks Extractor Configuration", success, 
                               f"GFG Patterns: {has_gfg_patterns}, Formats: {has_gfg_formats}, Dynamic: {has_dynamic_selectors}", response_time)
            
            # Test code pattern matching
            start_time = time.time()
            code_text = "```python\nprint('Hello World')\n```"
            code_matches = extractor.gfg_patterns["code_block"].findall(code_text)
            response_time = time.time() - start_time
            
            success = len(code_matches) > 0 and "print('Hello World')" in code_matches[0]
            self.log_test_result("GeeksforGeeks Code Pattern", success, 
                               f"Found {len(code_matches)} code blocks", response_time)
            
            # Test complexity pattern matching
            start_time = time.time()
            complexity_text = "Time Complexity: O(n log n)"
            complexity_matches = extractor.gfg_patterns["complexity_pattern"].findall(complexity_text)
            response_time = time.time() - start_time
            
            success = len(complexity_matches) > 0
            self.log_test_result("GeeksforGeeks Complexity Pattern", success, 
                               f"Found {len(complexity_matches)} complexity patterns", response_time)
            
            # Test format detection capabilities
            start_time = time.time()
            format_types = list(extractor.gfg_formats.keys())
            response_time = time.time() - start_time
            
            expected_formats = ["multiple_choice", "coding_problem", "theory_question", "practice_problem"]
            success = all(fmt in format_types for fmt in expected_formats)
            self.log_test_result("GeeksforGeeks Format Detection", success, 
                               f"Supported formats: {format_types}", response_time)
            
        except Exception as e:
            self.log_test_result("GeeksforGeeks Extractor", False, f"Extractor test error: {str(e)}")
    
    async def test_scraping_engine(self):
        """Test Main Scraping Coordinator (ScrapingEngine)"""
        logger.info("🚀 Testing Scraping Engine...")
        
        try:
            from scraping.scraper_engine import (
                ScrapingEngine, ScrapingEngineConfig, JobProgress, ScrapingStats,
                create_scraping_engine, get_scraping_engine
            )
            
            # Test engine configuration
            start_time = time.time()
            config = ScrapingEngineConfig(
                max_concurrent_jobs=2,
                max_retries_per_job=2,
                job_timeout_minutes=30,
                enable_performance_monitoring=True
            )
            response_time = time.time() - start_time
            
            success = (config.max_concurrent_jobs == 2 and 
                      config.max_retries_per_job == 2 and
                      config.enable_performance_monitoring == True)
            self.log_test_result("Scraping Engine Config", success, 
                               f"Config: {config.max_concurrent_jobs} jobs, {config.max_retries_per_job} retries", response_time)
            
            # Test engine creation
            start_time = time.time()
            engine = create_scraping_engine(config)
            response_time = time.time() - start_time
            
            success = (engine is not None and 
                      engine.config.max_concurrent_jobs == 2 and
                      hasattr(engine, 'job_queue') and
                      hasattr(engine, 'extractors'))
            self.log_test_result("Scraping Engine Creation", success, 
                               f"Engine created with {len(engine.extractors)} extractors", response_time)
            
            if not success:
                return
            
            # Test engine components initialization
            start_time = time.time()
            has_extractors = len(engine.extractors) > 0
            has_validators = len(engine.content_validators) > 0
            has_performance_monitor = engine.performance_monitor is not None
            has_anti_detection = engine.anti_detection is not None
            response_time = time.time() - start_time
            
            success = has_extractors and has_validators and has_performance_monitor and has_anti_detection
            self.log_test_result("Engine Components", success, 
                               f"Extractors: {len(engine.extractors)}, Validators: {len(engine.content_validators)}, Monitor: {has_performance_monitor}, Anti-detection: {has_anti_detection}", response_time)
            
            # Test engine statistics
            start_time = time.time()
            stats = engine.get_engine_statistics()
            response_time = time.time() - start_time
            
            success = (isinstance(stats, dict) and 
                      "engine_status" in stats and
                      "active_jobs" in stats and
                      "statistics" in stats)
            self.log_test_result("Engine Statistics", success, 
                               f"Stats keys: {list(stats.keys()) if isinstance(stats, dict) else 'Not dict'}", response_time)
            
            # Test health check
            start_time = time.time()
            health = engine.health_check()
            response_time = time.time() - start_time
            
            success = (isinstance(health, dict) and 
                      "status" in health and
                      "health_score" in health and
                      health.get("extractors_available", 0) > 0)
            self.log_test_result("Engine Health Check", success, 
                               f"Health status: {health.get('status', 'unknown')}, Score: {health.get('health_score', 0):.2f}", response_time)
            
            # Test global engine access
            start_time = time.time()
            global_engine = get_scraping_engine()
            response_time = time.time() - start_time
            
            success = global_engine is not None and hasattr(global_engine, 'extractors')
            self.log_test_result("Global Engine Access", success, 
                               f"Global engine available with {len(global_engine.extractors) if global_engine else 0} extractors", response_time)
            
        except Exception as e:
            self.log_test_result("Scraping Engine", False, f"Engine test error: {str(e)}")
    
    async def test_factory_functions(self):
        """Test factory functions and convenience methods"""
        logger.info("🏭 Testing Factory Functions...")
        
        try:
            # Test create_quick_scraping_job
            start_time = time.time()
            from scraping.scraper_engine import create_quick_scraping_job
            
            job_config = create_quick_scraping_job(
                source_type="indiabix",
                category="quantitative",
                subcategory="percentages",
                max_questions=50
            )
            response_time = time.time() - start_time
            
            success = (job_config is not None and 
                      job_config.max_questions == 50 and
                      job_config.target.category == "quantitative")
            self.log_test_result("Quick Job Creation", success, 
                               f"Job config created for {job_config.target.category if job_config else 'None'}/{job_config.target.subcategory if job_config else 'None'}", response_time)
            
        except Exception as e:
            # This might fail if config targets are not available, which is acceptable
            self.log_test_result("Quick Job Creation", False, f"Job creation error (may be expected): {str(e)}")
        
        try:
            # Test extractor factory functions
            start_time = time.time()
            from scraping import create_indiabix_extractor, create_geeksforgeeks_extractor
            
            indiabix_extractor = create_indiabix_extractor()
            gfg_extractor = create_geeksforgeeks_extractor()
            response_time = time.time() - start_time
            
            success = (indiabix_extractor is not None and 
                      gfg_extractor is not None and
                      indiabix_extractor.source_name == "indiabix" and
                      gfg_extractor.source_name == "geeksforgeeks")
            self.log_test_result("Extractor Factories", success, 
                               f"Created extractors: {indiabix_extractor.source_name if indiabix_extractor else 'None'}, {gfg_extractor.source_name if gfg_extractor else 'None'}", response_time)
            
        except Exception as e:
            self.log_test_result("Extractor Factories", False, f"Factory function error: {str(e)}")
    
    async def test_integration_compatibility(self):
        """Test integration with existing infrastructure"""
        logger.info("🔗 Testing Integration Compatibility...")
        
        try:
            # Test integration with anti-detection system
            start_time = time.time()
            from scraping.utils.anti_detection import create_anti_detection_manager
            from scraping.extractors.indiabix_extractor import create_indiabix_extractor
            
            anti_detection = create_anti_detection_manager("indiabix")
            extractor = create_indiabix_extractor()
            response_time = time.time() - start_time
            
            success = (anti_detection is not None and 
                      extractor is not None and
                      extractor.performance_monitor is not None)
            self.log_test_result("Anti-Detection Integration", success, 
                               f"Anti-detection: {anti_detection.source_name if anti_detection else 'None'}, Extractor monitor: {extractor.performance_monitor is not None if extractor else False}", response_time)
            
        except Exception as e:
            self.log_test_result("Anti-Detection Integration", False, f"Integration error: {str(e)}")
        
        try:
            # Test integration with content validation
            start_time = time.time()
            from scraping.utils.content_validator import create_indiabix_validator, create_geeksforgeeks_validator
            
            indiabix_validator = create_indiabix_validator()
            gfg_validator = create_geeksforgeeks_validator()
            response_time = time.time() - start_time
            
            success = (indiabix_validator is not None and 
                      gfg_validator is not None and
                      indiabix_validator.source_name == "indiabix" and
                      gfg_validator.source_name == "geeksforgeeks")
            self.log_test_result("Content Validation Integration", success, 
                               f"Validators: {indiabix_validator.source_name if indiabix_validator else 'None'}, {gfg_validator.source_name if gfg_validator else 'None'}", response_time)
            
        except Exception as e:
            self.log_test_result("Content Validation Integration", False, f"Validation integration error: {str(e)}")
        
        try:
            # Test integration with performance monitoring
            start_time = time.time()
            from scraping.utils.performance_monitor import create_performance_monitor, create_extraction_monitor
            
            perf_monitor = create_performance_monitor()
            extraction_monitor = create_extraction_monitor()
            response_time = time.time() - start_time
            
            success = (perf_monitor is not None and 
                      extraction_monitor is not None and
                      hasattr(perf_monitor, 'monitor_operation') and
                      hasattr(extraction_monitor, 'monitor_operation'))
            self.log_test_result("Performance Monitoring Integration", success, 
                               f"Monitors created: {perf_monitor is not None}, {extraction_monitor is not None}", response_time)
            
        except Exception as e:
            self.log_test_result("Performance Monitoring Integration", False, f"Performance integration error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all scraping extractor tests"""
        logger.info("🚀 Starting Scraping Extractors & Coordinator Testing...")
        start_time = time.time()
        
        # Run all test suites
        await self.test_scraping_module_imports()
        await self.test_base_extractor_framework()
        await self.test_indiabix_extractor()
        await self.test_geeksforgeeks_extractor()
        await self.test_scraping_engine()
        await self.test_factory_functions()
        await self.test_integration_compatibility()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 SCRAPING EXTRACTORS & COORDINATOR TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 60)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results
    
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class ScrapingEnginesTester:
    """Tester for TASK 4 & 5 - Selenium, Playwright, Content Validation, and Performance Monitoring"""
    
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "component_tests": {}
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - PASSED ({response_time:.2f}s)")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_selenium_driver_imports(self):
        """Test Selenium driver imports and basic functionality"""
        logger.info("🚗 Testing Selenium Driver Imports...")
        
        try:
            # Test SeleniumDriver import
            start_time = time.time()
            from scraping.drivers.selenium_driver import (
                SeleniumDriver, SeleniumConfig, PageLoadResult, 
                ElementExtractionResult, create_selenium_driver,
                create_indiabix_selenium_driver, create_geeksforgeeks_selenium_driver
            )
            response_time = time.time() - start_time
            self.log_test_result("SeleniumDriver Import", True, "Successfully imported all Selenium classes", response_time)
        except Exception as e:
            self.log_test_result("SeleniumDriver Import", False, f"Import error: {str(e)}")
            return
        
        # Test SeleniumConfig creation
        try:
            start_time = time.time()
            config = SeleniumConfig(
                browser="chrome",
                headless=True,
                page_load_timeout=30,
                enable_anti_detection=True
            )
            response_time = time.time() - start_time
            
            success = (config.browser == "chrome" and 
                      config.headless == True and 
                      config.page_load_timeout == 30)
            self.log_test_result("SeleniumConfig Creation", success, 
                               f"Config created with browser: {config.browser}, headless: {config.headless}", response_time)
        except Exception as e:
            self.log_test_result("SeleniumConfig Creation", False, f"Config creation error: {str(e)}")
        
        # Test SeleniumDriver instantiation (without actual browser)
        try:
            start_time = time.time()
            driver = SeleniumDriver("test_source", config)
            response_time = time.time() - start_time
            
            success = (driver.source_name == "test_source" and 
                      driver.config.browser == "chrome" and
                      not driver.is_initialized)
            self.log_test_result("SeleniumDriver Instantiation", success, 
                               f"Driver created for source: {driver.source_name}, initialized: {driver.is_initialized}", response_time)
        except Exception as e:
            self.log_test_result("SeleniumDriver Instantiation", False, f"Driver instantiation error: {str(e)}")
        
        # Test factory functions
        try:
            start_time = time.time()
            factory_driver = create_selenium_driver("factory_test", browser="chrome", headless=True)
            indiabix_driver = create_indiabix_selenium_driver()
            geeks_driver = create_geeksforgeeks_selenium_driver()
            response_time = time.time() - start_time
            
            success = (factory_driver.source_name == "factory_test" and
                      indiabix_driver.source_name == "indiabix" and
                      geeks_driver.source_name == "geeksforgeeks")
            self.log_test_result("Selenium Factory Functions", success, 
                               f"Created drivers: {factory_driver.source_name}, {indiabix_driver.source_name}, {geeks_driver.source_name}", response_time)
        except Exception as e:
            self.log_test_result("Selenium Factory Functions", False, f"Factory function error: {str(e)}")
    
    async def test_playwright_driver_imports(self):
        """Test Playwright driver imports and basic functionality"""
        logger.info("🎭 Testing Playwright Driver Imports...")
        
        try:
            # Test PlaywrightDriver import
            start_time = time.time()
            from scraping.drivers.playwright_driver import (
                PlaywrightDriver, PlaywrightConfig, NavigationResult,
                JavaScriptExecutionResult, DynamicContentResult,
                create_playwright_driver, create_indiabix_playwright_driver,
                create_geeksforgeeks_playwright_driver
            )
            response_time = time.time() - start_time
            self.log_test_result("PlaywrightDriver Import", True, "Successfully imported all Playwright classes", response_time)
        except Exception as e:
            self.log_test_result("PlaywrightDriver Import", False, f"Import error: {str(e)}")
            return
        
        # Test PlaywrightConfig creation
        try:
            start_time = time.time()
            config = PlaywrightConfig(
                browser_type="chromium",
                headless=True,
                enable_javascript=True,
                enable_anti_detection=True,
                stealth_mode=True
            )
            response_time = time.time() - start_time
            
            success = (config.browser_type == "chromium" and 
                      config.headless == True and 
                      config.enable_javascript == True and
                      config.stealth_mode == True)
            self.log_test_result("PlaywrightConfig Creation", success, 
                               f"Config created with browser: {config.browser_type}, stealth: {config.stealth_mode}", response_time)
        except Exception as e:
            self.log_test_result("PlaywrightConfig Creation", False, f"Config creation error: {str(e)}")
        
        # Test PlaywrightDriver instantiation (without actual browser)
        try:
            start_time = time.time()
            driver = PlaywrightDriver("test_source", config)
            response_time = time.time() - start_time
            
            success = (driver.source_name == "test_source" and 
                      driver.config.browser_type == "chromium" and
                      not driver.is_initialized)
            self.log_test_result("PlaywrightDriver Instantiation", success, 
                               f"Driver created for source: {driver.source_name}, initialized: {driver.is_initialized}", response_time)
        except Exception as e:
            self.log_test_result("PlaywrightDriver Instantiation", False, f"Driver instantiation error: {str(e)}")
        
        # Test factory functions
        try:
            start_time = time.time()
            factory_driver = create_playwright_driver("factory_test", browser_type="chromium")
            indiabix_driver = create_indiabix_playwright_driver()
            geeks_driver = create_geeksforgeeks_playwright_driver()
            response_time = time.time() - start_time
            
            success = (factory_driver.source_name == "factory_test" and
                      indiabix_driver.source_name == "indiabix" and
                      geeks_driver.source_name == "geeksforgeeks")
            self.log_test_result("Playwright Factory Functions", success, 
                               f"Created drivers: {factory_driver.source_name}, {indiabix_driver.source_name}, {geeks_driver.source_name}", response_time)
        except Exception as e:
            self.log_test_result("Playwright Factory Functions", False, f"Factory function error: {str(e)}")
    
    async def test_content_validator(self):
        """Test Content Validation utilities"""
        logger.info("🔍 Testing Content Validator...")
        
        try:
            # Test ContentValidator import
            start_time = time.time()
            from scraping.utils.content_validator import (
                ContentValidator, ContentQualityScore, ValidationRule,
                ContentType, ValidationSeverity, QualityGate,
                create_indiabix_validator, create_geeksforgeeks_validator,
                validate_extracted_question
            )
            response_time = time.time() - start_time
            self.log_test_result("ContentValidator Import", True, "Successfully imported all content validation classes", response_time)
        except Exception as e:
            self.log_test_result("ContentValidator Import", False, f"Import error: {str(e)}")
            return
        
        # Test ContentValidator instantiation
        try:
            start_time = time.time()
            validator = ContentValidator("test_source")
            response_time = time.time() - start_time
            
            success = (validator.source_name == "test_source" and
                      len(validator.validation_rules) > 0 and
                      validator.quality_thresholds is not None)
            self.log_test_result("ContentValidator Instantiation", success, 
                               f"Validator created for: {validator.source_name}, rules: {len(validator.validation_rules)}", response_time)
        except Exception as e:
            self.log_test_result("ContentValidator Instantiation", False, f"Validator instantiation error: {str(e)}")
        
        # Test content validation with sample data
        try:
            start_time = time.time()
            sample_content = {
                "question_text": "What is 25% of 200?",
                "options": ["A) 40", "B) 50", "C) 60", "D) 70"],
                "correct_answer": "B) 50",
                "explanation": "25% of 200 = (25/100) × 200 = 50"
            }
            
            quality_score = validator.validate_content(sample_content)
            response_time = time.time() - start_time
            
            success = (isinstance(quality_score, ContentQualityScore) and
                      quality_score.overall_score > 0 and
                      quality_score.quality_gate in [QualityGate.APPROVE, QualityGate.REVIEW, QualityGate.REJECT])
            self.log_test_result("Content Validation", success, 
                               f"Quality score: {quality_score.overall_score:.1f}, Gate: {quality_score.quality_gate.value}", response_time)
        except Exception as e:
            self.log_test_result("Content Validation", False, f"Content validation error: {str(e)}")
        
        # Test specialized validators
        try:
            start_time = time.time()
            indiabix_validator = create_indiabix_validator()
            geeks_validator = create_geeksforgeeks_validator()
            response_time = time.time() - start_time
            
            success = (indiabix_validator.source_name == "indiabix" and
                      geeks_validator.source_name == "geeksforgeeks")
            self.log_test_result("Specialized Validators", success, 
                               f"Created validators: {indiabix_validator.source_name}, {geeks_validator.source_name}", response_time)
        except Exception as e:
            self.log_test_result("Specialized Validators", False, f"Specialized validator error: {str(e)}")
        
        # Test validation rule system
        try:
            start_time = time.time()
            custom_rule = ValidationRule(
                name="test_rule",
                description="Test validation rule",
                content_types=[ContentType.QUESTION_TEXT],
                severity=ValidationSeverity.WARNING
            )
            
            custom_validator = ContentValidator("custom_test", [custom_rule])
            response_time = time.time() - start_time
            
            success = (len(custom_validator.validation_rules) > len(validator.validation_rules) and
                      any(rule.name == "test_rule" for rule in custom_validator.validation_rules))
            self.log_test_result("Custom Validation Rules", success, 
                               f"Custom validator has {len(custom_validator.validation_rules)} rules", response_time)
        except Exception as e:
            self.log_test_result("Custom Validation Rules", False, f"Custom rule error: {str(e)}")
    
    async def test_performance_monitor(self):
        """Test Performance Monitoring utilities"""
        logger.info("📊 Testing Performance Monitor...")
        
        try:
            # Test PerformanceMonitor import
            start_time = time.time()
            from scraping.utils.performance_monitor import (
                PerformanceMonitor, PerformanceThresholds, OperationMetrics,
                PerformanceAlert, ResourceSnapshot, PerformanceLevel,
                create_scraping_performance_monitor, create_high_volume_monitor,
                PerformanceAnalyzer, get_global_monitor
            )
            response_time = time.time() - start_time
            self.log_test_result("PerformanceMonitor Import", True, "Successfully imported all performance monitoring classes", response_time)
        except Exception as e:
            self.log_test_result("PerformanceMonitor Import", False, f"Import error: {str(e)}")
            return
        
        # Test PerformanceMonitor instantiation
        try:
            start_time = time.time()
            monitor = PerformanceMonitor("test_monitor")
            response_time = time.time() - start_time
            
            success = (monitor.monitor_name == "test_monitor" and
                      monitor.thresholds is not None and
                      not monitor.is_monitoring)
            self.log_test_result("PerformanceMonitor Instantiation", success, 
                               f"Monitor created: {monitor.monitor_name}, monitoring: {monitor.is_monitoring}", response_time)
        except Exception as e:
            self.log_test_result("PerformanceMonitor Instantiation", False, f"Monitor instantiation error: {str(e)}")
        
        # Test resource snapshot collection
        try:
            start_time = time.time()
            snapshot = monitor._get_resource_snapshot()
            response_time = time.time() - start_time
            
            success = (isinstance(snapshot, ResourceSnapshot) and
                      snapshot.cpu_percent >= 0 and
                      snapshot.memory_mb >= 0)
            self.log_test_result("Resource Snapshot", success, 
                               f"CPU: {snapshot.cpu_percent:.1f}%, Memory: {snapshot.memory_mb:.1f}MB", response_time)
        except Exception as e:
            self.log_test_result("Resource Snapshot", False, f"Resource snapshot error: {str(e)}")
        
        # Test operation monitoring context manager
        try:
            start_time = time.time()
            with monitor.monitor_operation("test_operation", elements_processed=10) as op_id:
                time.sleep(0.1)  # Simulate work
                success_op = True
            response_time = time.time() - start_time
            
            success = (len(monitor.operation_metrics) > 0 and
                      monitor.operation_metrics[-1].operation_name == "test_operation" and
                      monitor.operation_metrics[-1].success == True)
            self.log_test_result("Operation Monitoring", success, 
                               f"Monitored operation: {monitor.operation_metrics[-1].operation_name if monitor.operation_metrics else 'None'}", response_time)
        except Exception as e:
            self.log_test_result("Operation Monitoring", False, f"Operation monitoring error: {str(e)}")
        
        # Test performance summary
        try:
            start_time = time.time()
            summary = monitor.get_performance_summary()
            response_time = time.time() - start_time
            
            success = (isinstance(summary, dict) and
                      "monitor_name" in summary and
                      "resource_statistics" in summary and
                      "operation_statistics" in summary)
            self.log_test_result("Performance Summary", success, 
                               f"Summary keys: {list(summary.keys())[:5]}", response_time)
        except Exception as e:
            self.log_test_result("Performance Summary", False, f"Performance summary error: {str(e)}")
        
        # Test factory functions
        try:
            start_time = time.time()
            scraping_monitor = create_scraping_performance_monitor("scraping_test")
            high_volume_monitor = create_high_volume_monitor("volume_test")
            response_time = time.time() - start_time
            
            success = (scraping_monitor.monitor_name == "scraping_test_scraper" and
                      high_volume_monitor.monitor_name == "volume_test_high_volume")
            self.log_test_result("Performance Monitor Factories", success, 
                               f"Created monitors: {scraping_monitor.monitor_name}, {high_volume_monitor.monitor_name}", response_time)
        except Exception as e:
            self.log_test_result("Performance Monitor Factories", False, f"Factory function error: {str(e)}")
        
        # Test PerformanceAnalyzer
        try:
            start_time = time.time()
            bottlenecks = PerformanceAnalyzer.identify_bottlenecks(monitor)
            response_time = time.time() - start_time
            
            success = isinstance(bottlenecks, list)
            self.log_test_result("Performance Analysis", success, 
                               f"Identified {len(bottlenecks)} bottlenecks", response_time)
        except Exception as e:
            self.log_test_result("Performance Analysis", False, f"Performance analysis error: {str(e)}")
        
        # Cleanup
        try:
            monitor.cleanup()
            scraping_monitor.cleanup()
            high_volume_monitor.cleanup()
        except:
            pass
    
    async def test_integration_compatibility(self):
        """Test integration between scraping components"""
        logger.info("🔗 Testing Integration Compatibility...")
        
        try:
            # Test that all components can be imported together
            start_time = time.time()
            from scraping.drivers.selenium_driver import SeleniumDriver, SeleniumConfig
            from scraping.drivers.playwright_driver import PlaywrightDriver, PlaywrightConfig
            from scraping.utils.content_validator import ContentValidator
            from scraping.utils.performance_monitor import PerformanceMonitor
            from scraping.utils.anti_detection import AntiDetectionManager
            from scraping.utils.rate_limiter import ExponentialBackoffLimiter
            response_time = time.time() - start_time
            
            self.log_test_result("Component Integration Import", True, "All scraping components imported successfully", response_time)
        except Exception as e:
            self.log_test_result("Component Integration Import", False, f"Integration import error: {str(e)}")
            return
        
        # Test component compatibility
        try:
            start_time = time.time()
            
            # Create components
            selenium_config = SeleniumConfig(enable_anti_detection=True)
            selenium_driver = SeleniumDriver("integration_test", selenium_config)
            
            playwright_config = PlaywrightConfig(enable_anti_detection=True)
            playwright_driver = PlaywrightDriver("integration_test", playwright_config)
            
            validator = ContentValidator("integration_test")
            monitor = PerformanceMonitor("integration_test")
            
            response_time = time.time() - start_time
            
            success = all([
                selenium_driver.source_name == "integration_test",
                playwright_driver.source_name == "integration_test", 
                validator.source_name == "integration_test",
                monitor.monitor_name == "integration_test"
            ])
            
            self.log_test_result("Component Compatibility", success, 
                               "All components created with consistent configuration", response_time)
        except Exception as e:
            self.log_test_result("Component Compatibility", False, f"Component compatibility error: {str(e)}")
        
        # Test anti-detection integration
        try:
            start_time = time.time()
            
            # Verify anti-detection is properly integrated
            selenium_has_anti_detection = hasattr(selenium_driver, 'anti_detection') and selenium_driver.anti_detection is not None
            playwright_has_anti_detection = hasattr(playwright_driver, 'anti_detection') and playwright_driver.anti_detection is not None
            
            response_time = time.time() - start_time
            
            success = selenium_has_anti_detection and playwright_has_anti_detection
            self.log_test_result("Anti-Detection Integration", success, 
                               f"Selenium anti-detection: {selenium_has_anti_detection}, Playwright: {playwright_has_anti_detection}", response_time)
        except Exception as e:
            self.log_test_result("Anti-Detection Integration", False, f"Anti-detection integration error: {str(e)}")
        
        # Test rate limiting integration
        try:
            start_time = time.time()
            
            # Verify rate limiting is properly integrated
            selenium_has_rate_limiter = hasattr(selenium_driver, 'rate_limiter') and selenium_driver.rate_limiter is not None
            playwright_has_rate_limiter = hasattr(playwright_driver, 'rate_limiter') and playwright_driver.rate_limiter is not None
            
            response_time = time.time() - start_time
            
            success = selenium_has_rate_limiter and playwright_has_rate_limiter
            self.log_test_result("Rate Limiting Integration", success, 
                               f"Selenium rate limiter: {selenium_has_rate_limiter}, Playwright: {playwright_has_rate_limiter}", response_time)
        except Exception as e:
            self.log_test_result("Rate Limiting Integration", False, f"Rate limiting integration error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all scraping engines tests"""
        logger.info("🚀 Starting TASK 4 & 5 - Scraping Engines Testing...")
        start_time = time.time()
        
        # Run all test suites
        await self.test_selenium_driver_imports()
        await self.test_playwright_driver_imports()
        await self.test_content_validator()
        await self.test_performance_monitor()
        await self.test_integration_compatibility()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 SCRAPING ENGINES TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 60)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results

async def main():
    """Main test execution function"""
    logger.info("🎯 STARTING COMPREHENSIVE BACKEND TESTING")
    logger.info("=" * 80)
    
    # Test scraping extractors and coordinator (TASK 6-8)
    logger.info("🔧 TESTING TASK 6-8: SCRAPING EXTRACTORS & COORDINATOR")
    logger.info("=" * 80)
    
    async with ScrapingExtractorsTester() as extractor_tester:
        extractor_results = await extractor_tester.run_all_tests()
    
    # Test existing AI services to ensure they still work
    logger.info("\n🤖 TESTING EXISTING AI SERVICES")
    logger.info("=" * 80)
    
    async with AIAptitudeAPITester() as ai_tester:
        ai_results = await ai_tester.run_all_tests()
    
    # Generate overall summary
    logger.info("\n" + "=" * 80)
    logger.info("🎯 OVERALL TESTING SUMMARY")
    logger.info("=" * 80)
    
    total_tests = extractor_results["total_tests"] + ai_results["total_tests"]
    total_passed = extractor_results["passed_tests"] + ai_results["passed_tests"]
    total_failed = extractor_results["failed_tests"] + ai_results["failed_tests"]
    
    logger.info(f"📊 SCRAPING EXTRACTORS & COORDINATOR:")
    logger.info(f"   Tests: {extractor_results['total_tests']}, Passed: {extractor_results['passed_tests']}, Failed: {extractor_results['failed_tests']}")
    logger.info(f"   Success Rate: {(extractor_results['passed_tests'] / max(extractor_results['total_tests'], 1)) * 100:.1f}%")
    
    logger.info(f"📊 AI SERVICES:")
    logger.info(f"   Tests: {ai_results['total_tests']}, Passed: {ai_results['passed_tests']}, Failed: {ai_results['failed_tests']}")
    logger.info(f"   Success Rate: {(ai_results['passed_tests'] / max(ai_results['total_tests'], 1)) * 100:.1f}%")
    
    logger.info(f"📊 OVERALL:")
    logger.info(f"   Total Tests: {total_tests}")
    logger.info(f"   ✅ Total Passed: {total_passed}")
    logger.info(f"   ❌ Total Failed: {total_failed}")
    logger.info(f"   🎯 Overall Success Rate: {(total_passed / max(total_tests, 1)) * 100:.1f}%")
    
    logger.info("=" * 80)
    logger.info("🏁 COMPREHENSIVE BACKEND TESTING COMPLETED")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())