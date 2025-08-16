#!/usr/bin/env python3
"""
Anti-Detection & Rate Limiting System Testing
Tests all newly implemented scraping components
"""

import asyncio
import time
import logging
import sys
import json
from typing import Dict, List, Any
from datetime import datetime

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AntiDetectionSystemTester:
    """Tester for Anti-Detection & Rate Limiting System components"""
    
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
            try:
                stats = manager.get_request_statistics()
                response_time = time.time() - start_time
                
                success = isinstance(stats, dict) and stats.get("total_requests", 0) > 0
                self.log_test_result("Request Tracking", success, 
                                   f"Tracked requests: {stats.get('total_requests', 0)}", response_time)
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test_result("Request Tracking", False, f"Stats error: {str(e)}", response_time)
            
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
            try:
                stats = manager.get_proxy_statistics()
                response_time = time.time() - start_time
                
                success = isinstance(stats, dict) and stats.get("total_proxies", 0) > 0
                self.log_test_result("Proxy Statistics", success, 
                                   f"Stats: {stats.get('total_proxies', 0)} total, {stats.get('active_proxies', 0)} active", response_time)
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test_result("Proxy Statistics", False, f"Stats error: {str(e)}", response_time)
            
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

async def main():
    """Main test execution"""
    logger.info("🛡️ TESTING ANTI-DETECTION & RATE LIMITING SYSTEM")
    logger.info("=" * 80)
    
    tester = AntiDetectionSystemTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open('/app/test_results_anti_detection.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("📊 Anti-detection test results saved to test_results_anti_detection.json")
    
    # Return exit code based on results
    if results["failed_tests"] > 0:
        logger.error("Some tests failed!")
        return 1
    else:
        logger.info("All tests passed! 🎉")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)