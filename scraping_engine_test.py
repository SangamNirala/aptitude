#!/usr/bin/env python3
"""
Focused Testing for Main Scraping Coordinator (ScrapingEngine) - Task 8
Tests ScrapingEngine initialization, core components, dependencies, and integration
"""

import asyncio
import time
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingEngineTester:
    """Focused tester for Main Scraping Coordinator (ScrapingEngine) - Task 8"""
    
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
    
    async def test_dependency_verification(self):
        """Test that all newly added dependencies are working"""
        logger.info("📦 Testing Dependency Verification...")
        
        # Test newly added dependencies from requirements.txt
        dependencies_to_test = [
            ("multidict", "multidict"),
            ("attrs", "attrs"),
            ("yarl", "yarl"),
            ("propcache", "propcache"),
            ("aiohappyeyeballs", "aiohappyeyeballs"),
            ("aiosignal", "aiosignal"),
            ("frozenlist", "frozenlist"),
            ("greenlet", "greenlet")
        ]
        
        for dep_name, import_name in dependencies_to_test:
            try:
                start_time = time.time()
                __import__(import_name)
                response_time = time.time() - start_time
                self.log_test_result(f"Dependency {dep_name}", True, 
                                   f"Successfully imported {import_name}", response_time)
            except ImportError as e:
                self.log_test_result(f"Dependency {dep_name}", False, 
                                   f"Import error: {str(e)}")
            except Exception as e:
                self.log_test_result(f"Dependency {dep_name}", False, 
                                   f"Unexpected error: {str(e)}")
    
    async def test_scraping_engine_imports(self):
        """Test ScrapingEngine and related imports"""
        logger.info("🔧 Testing ScrapingEngine Imports...")
        
        try:
            start_time = time.time()
            from scraping.scraper_engine import (
                ScrapingEngine, ScrapingEngineConfig, JobProgress, ScrapingStats,
                create_scraping_engine, create_quick_scraping_job,
                get_scraping_engine, shutdown_scraping_engine
            )
            response_time = time.time() - start_time
            self.log_test_result("ScrapingEngine Imports", True, 
                               "Successfully imported all ScrapingEngine classes and functions", response_time)
        except Exception as e:
            self.log_test_result("ScrapingEngine Imports", False, f"Import error: {str(e)}")
            return False
        
        return True
    
    async def test_scraping_engine_initialization(self):
        """Test ScrapingEngine initialization without errors"""
        logger.info("🚀 Testing ScrapingEngine Initialization...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine, ScrapingEngineConfig
            
            # Test basic initialization
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            success = engine is not None
            self.log_test_result("Basic ScrapingEngine Initialization", success, 
                               f"Engine created successfully", response_time)
            
            if not success:
                return False
            
            # Test initialization with custom config
            start_time = time.time()
            config = ScrapingEngineConfig(
                max_concurrent_jobs=2,
                max_retries_per_job=2,
                job_timeout_minutes=30,
                enable_performance_monitoring=True,
                enable_anti_detection=True
            )
            engine_with_config = ScrapingEngine(config)
            response_time = time.time() - start_time
            
            success = (engine_with_config is not None and 
                      engine_with_config.config.max_concurrent_jobs == 2)
            self.log_test_result("ScrapingEngine with Custom Config", success, 
                               f"Engine created with custom config: max_jobs={engine_with_config.config.max_concurrent_jobs}", response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("ScrapingEngine Initialization", False, f"Initialization error: {str(e)}")
            return False
    
    async def test_anti_detection_manager_integration(self):
        """Test AntiDetectionManager integration with source_name parameter"""
        logger.info("🛡️ Testing AntiDetectionManager Integration...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine
            
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            # Check if AntiDetectionManager is properly initialized
            has_anti_detection = hasattr(engine, 'anti_detection') and engine.anti_detection is not None
            
            if has_anti_detection:
                # Check if source_name is properly set
                source_name_correct = engine.anti_detection.source_name == "scraping_engine"
                success = has_anti_detection and source_name_correct
                details = f"AntiDetectionManager initialized with source_name: {engine.anti_detection.source_name}"
            else:
                success = False
                details = "AntiDetectionManager not initialized"
            
            self.log_test_result("AntiDetectionManager Integration", success, details, response_time)
            
            # Test AntiDetectionManager functionality
            if has_anti_detection:
                start_time = time.time()
                user_agent = engine.anti_detection.get_user_agent()
                headers = engine.anti_detection.get_request_headers("https://example.com")
                response_time = time.time() - start_time
                
                success = user_agent is not None and len(headers) > 0
                self.log_test_result("AntiDetectionManager Functionality", success, 
                                   f"Generated user agent and {len(headers)} headers", response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("AntiDetectionManager Integration", False, f"Integration error: {str(e)}")
            return False
    
    async def test_performance_monitoring_system(self):
        """Test Performance monitoring system integration"""
        logger.info("📊 Testing Performance Monitoring System...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine
            
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            # Check if PerformanceMonitor is properly initialized
            has_performance_monitor = hasattr(engine, 'performance_monitor') and engine.performance_monitor is not None
            
            success = has_performance_monitor
            details = f"PerformanceMonitor initialized: {has_performance_monitor}"
            self.log_test_result("Performance Monitor Integration", success, details, response_time)
            
            # Test PerformanceMonitor functionality
            if has_performance_monitor:
                start_time = time.time()
                stats = engine.performance_monitor.get_performance_summary()
                response_time = time.time() - start_time
                
                success = isinstance(stats, dict)
                self.log_test_result("Performance Monitor Functionality", success, 
                                   f"Retrieved performance stats: {type(stats)}", response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("Performance Monitoring System", False, f"Performance monitor error: {str(e)}")
            return False
    
    async def test_statistics_tracking(self):
        """Test Statistics tracking (ScrapingStats)"""
        logger.info("📈 Testing Statistics Tracking...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine, ScrapingStats
            
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            # Check if ScrapingStats is properly initialized
            has_stats = hasattr(engine, 'stats') and engine.stats is not None
            
            success = has_stats and isinstance(engine.stats, ScrapingStats)
            details = f"ScrapingStats initialized: {has_stats}, type: {type(engine.stats)}"
            self.log_test_result("Statistics Tracking Integration", success, details, response_time)
            
            # Test ScrapingStats functionality
            if has_stats:
                start_time = time.time()
                initial_jobs = engine.stats.total_jobs_completed
                initial_questions = engine.stats.total_questions_extracted
                response_time = time.time() - start_time
                
                success = (isinstance(initial_jobs, int) and 
                          isinstance(initial_questions, int) and
                          initial_jobs >= 0 and initial_questions >= 0)
                self.log_test_result("Statistics Tracking Functionality", success, 
                                   f"Jobs: {initial_jobs}, Questions: {initial_questions}", response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("Statistics Tracking", False, f"Statistics error: {str(e)}")
            return False
    
    async def test_engine_configuration_and_health(self):
        """Test Engine configuration and health checks"""
        logger.info("⚙️ Testing Engine Configuration and Health Checks...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine
            
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            # Test engine configuration
            has_config = hasattr(engine, 'config') and engine.config is not None
            success = has_config
            details = f"Engine configuration available: {has_config}"
            self.log_test_result("Engine Configuration", success, details, response_time)
            
            # Test health check functionality
            start_time = time.time()
            health_status = engine.health_check()
            response_time = time.time() - start_time
            
            success = (isinstance(health_status, dict) and 
                      "status" in health_status and
                      "health_score" in health_status)
            details = f"Health check returned: {health_status.get('status', 'unknown')}, score: {health_status.get('health_score', 0)}"
            self.log_test_result("Engine Health Check", success, details, response_time)
            
            # Test engine statistics
            start_time = time.time()
            engine_stats = engine.get_engine_statistics()
            response_time = time.time() - start_time
            
            success = (isinstance(engine_stats, dict) and 
                      "engine_status" in engine_stats and
                      "statistics" in engine_stats)
            details = f"Engine stats available with keys: {list(engine_stats.keys()) if isinstance(engine_stats, dict) else 'None'}"
            self.log_test_result("Engine Statistics", success, details, response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("Engine Configuration and Health", False, f"Configuration error: {str(e)}")
            return False
    
    async def test_factory_functions(self):
        """Test factory functions for creating ScrapingEngine instances"""
        logger.info("🏭 Testing Factory Functions...")
        
        try:
            from scraping.scraper_engine import create_scraping_engine, get_scraping_engine, ScrapingEngineConfig
            
            # Test create_scraping_engine factory function
            start_time = time.time()
            engine1 = create_scraping_engine()
            response_time = time.time() - start_time
            
            success = engine1 is not None
            self.log_test_result("create_scraping_engine Factory", success, 
                               f"Factory function created engine: {engine1 is not None}", response_time)
            
            # Test create_scraping_engine with custom config
            start_time = time.time()
            custom_config = ScrapingEngineConfig(max_concurrent_jobs=1, job_timeout_minutes=15)
            engine2 = create_scraping_engine(custom_config)
            response_time = time.time() - start_time
            
            success = (engine2 is not None and 
                      engine2.config.max_concurrent_jobs == 1 and
                      engine2.config.job_timeout_minutes == 15)
            self.log_test_result("create_scraping_engine with Config", success, 
                               f"Custom config applied: jobs={engine2.config.max_concurrent_jobs}, timeout={engine2.config.job_timeout_minutes}", response_time)
            
            # Test get_scraping_engine singleton function
            start_time = time.time()
            singleton_engine1 = get_scraping_engine()
            singleton_engine2 = get_scraping_engine()
            response_time = time.time() - start_time
            
            success = (singleton_engine1 is not None and 
                      singleton_engine2 is not None and
                      singleton_engine1 is singleton_engine2)  # Should be same instance
            self.log_test_result("get_scraping_engine Singleton", success, 
                               f"Singleton pattern working: {singleton_engine1 is singleton_engine2}", response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("Factory Functions", False, f"Factory function error: {str(e)}")
            return False
    
    async def test_integration_with_existing_infrastructure(self):
        """Test integration with existing scraping infrastructure"""
        logger.info("🔗 Testing Integration with Existing Infrastructure...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine
            
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            # Test extractors integration
            has_extractors = hasattr(engine, 'extractors') and len(engine.extractors) > 0
            success = has_extractors
            details = f"Extractors initialized: {len(engine.extractors) if has_extractors else 0}"
            self.log_test_result("Extractors Integration", success, details, response_time)
            
            # Test content validators integration
            start_time = time.time()
            has_validators = hasattr(engine, 'content_validators') and len(engine.content_validators) > 0
            response_time = time.time() - start_time
            
            success = has_validators
            details = f"Content validators initialized: {len(engine.content_validators) if has_validators else 0}"
            self.log_test_result("Content Validators Integration", success, details, response_time)
            
            # Test job management components
            start_time = time.time()
            has_job_queue = hasattr(engine, 'job_queue') and engine.job_queue is not None
            has_active_jobs = hasattr(engine, 'active_jobs') and isinstance(engine.active_jobs, dict)
            has_job_progress = hasattr(engine, 'job_progress') and isinstance(engine.job_progress, dict)
            response_time = time.time() - start_time
            
            success = has_job_queue and has_active_jobs and has_job_progress
            details = f"Job management: queue={has_job_queue}, active_jobs={has_active_jobs}, progress={has_job_progress}"
            self.log_test_result("Job Management Integration", success, details, response_time)
            
            return True
            
        except Exception as e:
            self.log_test_result("Integration with Existing Infrastructure", False, f"Integration error: {str(e)}")
            return False
    
    async def test_core_components_operational(self):
        """Test that all core engine components are operational"""
        logger.info("🔧 Testing Core Components Operational Status...")
        
        try:
            from scraping.scraper_engine import ScrapingEngine
            
            start_time = time.time()
            engine = ScrapingEngine()
            response_time = time.time() - start_time
            
            # Test all core components are present and operational
            components_status = {
                "job_queue": hasattr(engine, 'job_queue') and engine.job_queue is not None,
                "active_jobs": hasattr(engine, 'active_jobs') and isinstance(engine.active_jobs, dict),
                "completed_jobs": hasattr(engine, 'completed_jobs') and isinstance(engine.completed_jobs, dict),
                "job_progress": hasattr(engine, 'job_progress') and isinstance(engine.job_progress, dict),
                "extractors": hasattr(engine, 'extractors') and isinstance(engine.extractors, dict),
                "performance_monitor": hasattr(engine, 'performance_monitor') and engine.performance_monitor is not None,
                "anti_detection": hasattr(engine, 'anti_detection') and engine.anti_detection is not None,
                "content_validators": hasattr(engine, 'content_validators') and isinstance(engine.content_validators, dict),
                "stats": hasattr(engine, 'stats') and engine.stats is not None,
                "job_lock": hasattr(engine, 'job_lock') and engine.job_lock is not None
            }
            
            operational_count = sum(components_status.values())
            total_components = len(components_status)
            
            success = operational_count == total_components
            details = f"Operational components: {operational_count}/{total_components} - {components_status}"
            self.log_test_result("Core Components Operational", success, details, response_time)
            
            # Test component initialization details
            if engine.anti_detection:
                start_time = time.time()
                anti_detection_working = engine.anti_detection.source_name == "scraping_engine"
                response_time = time.time() - start_time
                
                self.log_test_result("AntiDetectionManager Source Name", anti_detection_working, 
                                   f"Source name: {engine.anti_detection.source_name}", response_time)
            
            return success
            
        except Exception as e:
            self.log_test_result("Core Components Operational", False, f"Components error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all ScrapingEngine tests"""
        logger.info("🚀 Starting Main Scraping Coordinator (ScrapingEngine) Testing...")
        start_time = time.time()
        
        # Run all test suites in order
        await self.test_dependency_verification()
        
        # Only proceed with engine tests if imports work
        if await self.test_scraping_engine_imports():
            await self.test_scraping_engine_initialization()
            await self.test_anti_detection_manager_integration()
            await self.test_performance_monitoring_system()
            await self.test_statistics_tracking()
            await self.test_engine_configuration_and_health()
            await self.test_factory_functions()
            await self.test_integration_with_existing_infrastructure()
            await self.test_core_components_operational()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 70)
        logger.info("🎯 MAIN SCRAPING COORDINATOR (ScrapingEngine) TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 70)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        else:
            logger.info("🎉 ALL TESTS PASSED!")
        
        logger.info("=" * 70)
        
        return self.test_results

async def main():
    """Main test execution function"""
    tester = ScrapingEngineTester()
    results = await tester.run_all_tests()
    
    # Return exit code based on test results
    if results["failed_tests"] == 0:
        logger.info("✅ All ScrapingEngine tests passed successfully!")
        return 0
    else:
        logger.error(f"❌ {results['failed_tests']} tests failed!")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)