#!/usr/bin/env python3
"""
Focused Web Scraping Test - Testing the specific issues mentioned in the review request
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingTestRunner:
    """Test runner focused on the specific scraping issues"""
    
    def __init__(self):
        # Get backend URL from frontend env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://aptitude-extract.preview.emergentagent.com/api"
        except:
            self.base_url = "https://aptitude-extract.preview.emergentagent.com/api"
        
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {test_name} - {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_selenium_driver_initialization(self):
        """Test 1: Test if Selenium WebDriver can initialize properly with current Chrome setup"""
        logger.info("🔧 TEST 1: Selenium WebDriver Initialization")
        
        try:
            # Add backend to path
            sys.path.append('/app/backend')
            
            # Test direct driver creation
            from scraping.drivers.selenium_driver import create_indiabix_selenium_driver
            
            # Test with proper anti_detection_config
            anti_detection_config = {
                "source_name": "IndiaBix",
                "enable_user_agent_rotation": True,
                "enable_behavior_simulation": True,
                "detection_risk_threshold": 0.7
            }
            
            logger.info("Creating IndiaBix Selenium driver...")
            driver = create_indiabix_selenium_driver(anti_detection_config=anti_detection_config)
            
            if driver:
                logger.info("Driver created successfully, testing initialization...")
                if driver.initialize_driver():
                    logger.info("Driver initialized successfully!")
                    driver.cleanup()
                    self.log_result("Selenium Driver Initialization", True, "Driver created and initialized successfully")
                    return True
                else:
                    self.log_result("Selenium Driver Initialization", False, "Driver created but initialization failed")
                    return False
            else:
                self.log_result("Selenium Driver Initialization", False, "Driver creation returned None")
                return False
                
        except Exception as e:
            self.log_result("Selenium Driver Initialization", False, f"Exception: {str(e)}")
            return False
    
    async def test_website_accessibility(self):
        """Test 2: Test if the scraping engine can access IndiaBix and GeeksforGeeks websites"""
        logger.info("🌐 TEST 2: Website Accessibility")
        
        test_urls = [
            ("IndiaBix", "https://www.indiabix.com/aptitude/arithmetic-aptitude"),
            ("GeeksforGeeks", "https://www.geeksforgeeks.org/practice/data-structures/arrays")
        ]
        
        results = []
        
        for site_name, url in test_urls:
            try:
                logger.info(f"Testing accessibility to {site_name}: {url}")
                
                # Test with aiohttp first (basic connectivity)
                async with self.session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 1000:  # Basic content check
                            logger.info(f"✅ {site_name} accessible via HTTP (status: {response.status}, content: {len(content)} chars)")
                            results.append(True)
                        else:
                            logger.warning(f"⚠️ {site_name} accessible but content seems limited ({len(content)} chars)")
                            results.append(False)
                    else:
                        logger.error(f"❌ {site_name} returned status {response.status}")
                        results.append(False)
                        
            except Exception as e:
                logger.error(f"❌ Error accessing {site_name}: {str(e)}")
                results.append(False)
        
        success = all(results)
        details = f"IndiaBix: {'✅' if results[0] else '❌'}, GeeksforGeeks: {'✅' if results[1] else '❌'}"
        self.log_result("Website Accessibility", success, details)
        return success
    
    async def test_css_selectors(self):
        """Test 3: Test if CSS selectors in scraping configuration can find question elements"""
        logger.info("🎯 TEST 3: CSS Selectors Validation")
        
        try:
            sys.path.append('/app/backend')
            from config.scraping_config import INDIABIX_CONFIG, GEEKSFORGEEKS_CONFIG
            
            # Test IndiaBix selectors
            indiabix_selectors = INDIABIX_CONFIG.selectors
            logger.info(f"IndiaBix selectors configured: {len(indiabix_selectors)} selectors")
            
            key_selectors = ["question_text", "question_options", "correct_answer"]
            indiabix_has_key_selectors = all(selector in indiabix_selectors for selector in key_selectors)
            
            # Test GeeksforGeeks selectors
            geeksforgeeks_selectors = GEEKSFORGEEKS_CONFIG.selectors
            logger.info(f"GeeksforGeeks selectors configured: {len(geeksforgeeks_selectors)} selectors")
            
            geeksforgeeks_has_key_selectors = all(selector in geeksforgeeks_selectors for selector in key_selectors)
            
            success = indiabix_has_key_selectors and geeksforgeeks_has_key_selectors
            details = f"IndiaBix key selectors: {'✅' if indiabix_has_key_selectors else '❌'}, GeeksforGeeks key selectors: {'✅' if geeksforgeeks_has_key_selectors else '❌'}"
            
            # Log specific selectors for debugging
            logger.info(f"IndiaBix question_text selector: {indiabix_selectors.get('question_text')}")
            logger.info(f"GeeksforGeeks question_text selector: {geeksforgeeks_selectors.get('question_text')}")
            
            self.log_result("CSS Selectors Configuration", success, details)
            return success
            
        except Exception as e:
            self.log_result("CSS Selectors Configuration", False, f"Exception: {str(e)}")
            return False
    
    async def test_scraping_api_endpoints(self):
        """Test 4: Test scraping API endpoints functionality"""
        logger.info("🔌 TEST 4: Scraping API Endpoints")
        
        tests = []
        
        # Test health endpoint
        try:
            async with self.session.get(f"{self.base_url}/scraping/health") as response:
                if response.status == 200:
                    data = await response.json()
                    health_ok = data.get("status") == "healthy"
                    tests.append(("Health Check", health_ok, f"Status: {data.get('status')}"))
                else:
                    tests.append(("Health Check", False, f"HTTP {response.status}"))
        except Exception as e:
            tests.append(("Health Check", False, f"Exception: {str(e)}"))
        
        # Test sources list
        try:
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                if response.status == 200:
                    data = await response.json()
                    sources_ok = isinstance(data, list) and len(data) >= 2
                    source_names = [s.get('name', '') for s in data] if isinstance(data, list) else []
                    tests.append(("Sources List", sources_ok, f"Found {len(data) if isinstance(data, list) else 0} sources: {source_names}"))
                else:
                    tests.append(("Sources List", False, f"HTTP {response.status}"))
        except Exception as e:
            tests.append(("Sources List", False, f"Exception: {str(e)}"))
        
        # Test queue status
        try:
            async with self.session.get(f"{self.base_url}/scraping/queue-status") as response:
                if response.status == 200:
                    data = await response.json()
                    queue_ok = "total_queued" in data and "active_jobs" in data
                    tests.append(("Queue Status", queue_ok, f"Queued: {data.get('total_queued', 'N/A')}, Active: {data.get('active_jobs', 'N/A')}"))
                else:
                    tests.append(("Queue Status", False, f"HTTP {response.status}"))
        except Exception as e:
            tests.append(("Queue Status", False, f"Exception: {str(e)}"))
        
        success = all(test[1] for test in tests)
        details = "; ".join([f"{test[0]}: {'✅' if test[1] else '❌'} ({test[2]})" for test in tests])
        self.log_result("Scraping API Endpoints", success, details)
        return success
    
    async def test_job_creation_and_execution(self):
        """Test 5: Test the complete scraping pipeline from driver creation to question extraction"""
        logger.info("🚀 TEST 5: Complete Scraping Pipeline")
        
        # Create a small test job
        job_payload = {
            "job_name": "Pipeline_Test_Job",
            "source_names": ["IndiaBix"],
            "max_questions_per_source": 5,  # Small test
            "target_categories": ["quantitative"],
            "priority_level": 1,
            "enable_ai_processing": False,
            "enable_duplicate_detection": False
        }
        
        job_id = None
        
        try:
            # Create job
            logger.info("Creating test scraping job...")
            async with self.session.post(f"{self.base_url}/scraping/jobs", json=job_payload) as response:
                if response.status == 201:
                    data = await response.json()
                    job_id = data.get("job_id")
                    logger.info(f"Job created successfully: {job_id}")
                else:
                    error_text = await response.text()
                    self.log_result("Job Creation", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # Start job
            if job_id:
                logger.info(f"Starting job {job_id}...")
                async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as response:
                    if response.status == 200:
                        logger.info("Job started successfully")
                    else:
                        error_text = await response.text()
                        logger.warning(f"Job start returned {response.status}: {error_text}")
                
                # Monitor job for 60 seconds
                logger.info("Monitoring job execution for 60 seconds...")
                questions_extracted = 0
                final_status = "unknown"
                error_message = None
                
                for i in range(4):  # Check every 15 seconds for 60 seconds
                    await asyncio.sleep(15)
                    
                    try:
                        async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                            if response.status == 200:
                                data = await response.json()
                                status = data.get("status", "unknown")
                                questions = data.get("questions_extracted", 0)
                                error_msg = data.get("error_message") or data.get("last_error")
                                
                                logger.info(f"Check {i+1}: Status={status}, Questions={questions}")
                                
                                if questions > questions_extracted:
                                    questions_extracted = questions
                                
                                final_status = status
                                if error_msg:
                                    error_message = error_msg
                                
                                if status in ["completed", "failed"]:
                                    break
                    except Exception as e:
                        logger.error(f"Error monitoring job: {e}")
                
                # Evaluate results
                success = questions_extracted > 0
                details = f"Status: {final_status}, Questions extracted: {questions_extracted}"
                if error_message:
                    details += f", Error: {error_message}"
                
                self.log_result("Complete Scraping Pipeline", success, details)
                return success
            
        except Exception as e:
            self.log_result("Complete Scraping Pipeline", False, f"Exception: {str(e)}")
            return False
        
        return False
    
    async def run_all_tests(self):
        """Run all focused tests"""
        logger.info("🚀 Starting Focused Web Scraping Tests")
        logger.info("=" * 80)
        
        test_functions = [
            self.test_selenium_driver_initialization,
            self.test_website_accessibility,
            self.test_css_selectors,
            self.test_scraping_api_endpoints,
            self.test_job_creation_and_execution
        ]
        
        results = []
        for test_func in test_functions:
            try:
                result = await test_func()
                results.append(result)
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with exception: {e}")
                results.append(False)
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        # Summary
        logger.info("=" * 80)
        logger.info("🎯 FOCUSED TEST SUMMARY")
        logger.info("=" * 80)
        
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        logger.info(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        logger.info("")
        
        for i, result in enumerate(self.test_results):
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
        
        logger.info("=" * 80)
        
        # Final assessment
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Web scraping system is working correctly!")
        elif passed >= total * 0.8:
            logger.info("⚠️ MOSTLY WORKING - Some issues found but core functionality intact")
        else:
            logger.info("❌ SIGNIFICANT ISSUES - Web scraping system needs attention")
        
        return results

async def main():
    """Main test execution"""
    async with ScrapingTestRunner() as tester:
        results = await tester.run_all_tests()
        
        # Return exit code based on results
        if all(results):
            return 0
        else:
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)