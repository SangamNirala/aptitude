#!/usr/bin/env python3
"""
Critical Driver/Extractor Integration Test
Focus: Test the specific issues mentioned in the review request
- Driver creation for IndiaBix (SeleniumDriver) and GeeksforGeeks (PlaywrightDriver)
- Extractor integration verification
- Question collection count assessment
- Case-insensitive source name matching
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
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend
load_dotenv('/app/backend/.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DriverExtractorTester:
    """Critical tester for driver/extractor integration issues"""
    
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://driver-extractor-fix.preview.emergentagent.com/api"
        except:
            self.base_url = "https://driver-extractor-fix.preview.emergentagent.com/api"
        
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "question_collection": {
                "indiabix_questions": 0,
                "geeksforgeeks_questions": 0,
                "total_questions": 0
            }
        }
        self.created_job_ids = []
    
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
    
    async def test_basic_api_endpoints(self):
        """Test basic API endpoints to ensure system is responsive"""
        logger.info("🔧 Testing Basic API Endpoints...")
        
        # Test health check
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = "status" in data
                    details = f"Status: {data.get('status')}, Services: {len(data.get('services', {}))}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("API Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("API Health Check", False, f"Exception: {str(e)}")
        
        # Test sources list
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list) and len(data) >= 2
                    
                    # Check for IndiaBix and GeeksforGeeks
                    source_names = [source.get('name', '').lower() for source in data]
                    has_indiabix = any('indiabix' in name for name in source_names)
                    has_geeksforgeeks = any('geeks' in name for name in source_names)
                    
                    details = f"Found {len(data)} sources, IndiaBix: {has_indiabix}, GeeksforGeeks: {has_geeksforgeeks}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Sources List", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Sources List", False, f"Exception: {str(e)}")
    
    async def test_driver_creation_verification(self):
        """Test driver creation for both sources"""
        logger.info("🚗 Testing Driver Creation Verification...")
        
        # Create test jobs to trigger driver creation
        indiabix_job_id = await self.create_test_job("IndiaBix", "IndiaBix_Driver_Test", 5)
        geeksforgeeks_job_id = await self.create_test_job("GeeksforGeeks", "GeeksforGeeks_Driver_Test", 5)
        
        # Start both jobs to trigger driver initialization
        if indiabix_job_id:
            await self.start_job(indiabix_job_id, "IndiaBix")
        
        if geeksforgeeks_job_id:
            await self.start_job(geeksforgeeks_job_id, "GeeksforGeeks")
        
        return indiabix_job_id, geeksforgeeks_job_id
    
    async def create_test_job(self, source_name: str, job_name: str, max_questions: int) -> str:
        """Create a test job for the specified source"""
        try:
            start_time = time.time()
            payload = {
                "job_name": job_name,
                "source_names": [source_name],
                "max_questions_per_source": max_questions,
                "target_categories": ["quantitative", "logical"] if source_name == "IndiaBix" else ["programming", "algorithms"],
                "priority_level": 1,
                "enable_ai_processing": False,  # Disable to focus on scraping
                "enable_duplicate_detection": False
            }
            
            async with self.session.post(f"{self.base_url}/scraping/jobs", json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 201:
                    data = await response.json()
                    job_id = data.get("job_id")
                    if job_id:
                        self.created_job_ids.append(job_id)
                    success = job_id is not None
                    details = f"Job ID: {job_id}, Status: {data.get('status')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result(f"Create {source_name} Job", success, details, response_time)
                return job_id if success else None
                
        except Exception as e:
            self.log_test_result(f"Create {source_name} Job", False, f"Exception: {str(e)}")
            return None
    
    async def start_job(self, job_id: str, source_name: str):
        """Start a job and check for driver initialization"""
        try:
            start_time = time.time()
            async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = data.get("status") in ["started", "running"]
                    details = f"Job started, Status: {data.get('status')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result(f"Start {source_name} Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result(f"Start {source_name} Job", False, f"Exception: {str(e)}")
    
    async def monitor_job_execution(self, job_ids: List[str], monitoring_duration: int = 180):
        """Monitor job execution for driver/extractor issues"""
        logger.info(f"🔍 Monitoring Job Execution for {monitoring_duration} seconds...")
        
        check_interval = 30
        checks = monitoring_duration // check_interval
        
        for check_num in range(checks):
            logger.info(f"📊 Check {check_num + 1}/{checks} - {(check_num + 1) * check_interval}s elapsed")
            
            for job_id in job_ids:
                if not job_id:
                    continue
                    
                try:
                    async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                        if response.status == 200:
                            data = await response.json()
                            status = data.get("status", "unknown")
                            questions_extracted = data.get("questions_extracted", 0)
                            error_message = data.get("error_message", "") or data.get("last_error", "")
                            
                            logger.info(f"📊 Job {job_id[:8]}: Status={status}, Questions={questions_extracted}")
                            
                            # Check for specific driver/extractor errors
                            critical_errors = [
                                "Failed to initialize driver or extractor",
                                "create_selenium_driver() missing 1 required positional argument",
                                "NoneType' object has no attribute 'execute_job'",
                                "asdict() should be called on dataclass instances"
                            ]
                            
                            has_critical_error = any(error in str(error_message) for error in critical_errors)
                            
                            if has_critical_error:
                                logger.error(f"🚨 CRITICAL ERROR in Job {job_id[:8]}: {error_message}")
                                self.log_test_result(f"Job {job_id[:8]} Execution", False, f"Critical error: {error_message}")
                            elif status == "completed":
                                logger.info(f"✅ Job {job_id[:8]} completed successfully")
                                self.log_test_result(f"Job {job_id[:8]} Execution", True, f"Completed with {questions_extracted} questions")
                                
                                # Update question collection count
                                if "IndiaBix" in str(data.get("config", {})):
                                    self.test_results["question_collection"]["indiabix_questions"] += questions_extracted
                                elif "GeeksforGeeks" in str(data.get("config", {})):
                                    self.test_results["question_collection"]["geeksforgeeks_questions"] += questions_extracted
                                
                                self.test_results["question_collection"]["total_questions"] += questions_extracted
                            elif status == "failed":
                                logger.error(f"❌ Job {job_id[:8]} failed: {error_message}")
                                self.log_test_result(f"Job {job_id[:8]} Execution", False, f"Job failed: {error_message}")
                            elif error_message:
                                logger.warning(f"⚠️ Job {job_id[:8]} has error: {error_message}")
                        else:
                            logger.error(f"❌ Failed to get status for job {job_id[:8]}: {response.status}")
                            
                except Exception as e:
                    logger.error(f"❌ Exception monitoring job {job_id[:8]}: {e}")
            
            # Wait before next check (except on last iteration)
            if check_num < checks - 1:
                await asyncio.sleep(check_interval)
    
    async def test_case_insensitive_matching(self):
        """Test case-insensitive source name matching"""
        logger.info("🔤 Testing Case-Insensitive Source Name Matching...")
        
        # Test different case variations
        test_cases = [
            ("indiabix", "IndiaBix"),
            ("INDIABIX", "IndiaBix"),
            ("IndiaBix", "IndiaBix"),
            ("geeksforgeeks", "GeeksforGeeks"),
            ("GEEKSFORGEEKS", "GeeksforGeeks"),
            ("GeeksforGeeks", "GeeksforGeeks")
        ]
        
        for input_name, expected_name in test_cases:
            try:
                job_id = await self.create_test_job(input_name, f"Case_Test_{input_name}", 2)
                success = job_id is not None
                details = f"Input: {input_name}, Expected: {expected_name}, Job Created: {success}"
                self.log_test_result(f"Case Matching: {input_name}", success, details)
                
                if job_id:
                    self.created_job_ids.append(job_id)
                    
            except Exception as e:
                self.log_test_result(f"Case Matching: {input_name}", False, f"Exception: {str(e)}")
    
    async def run_critical_tests(self):
        """Run all critical driver/extractor tests"""
        logger.info("🚀 Starting Critical Driver/Extractor Integration Tests...")
        logger.info("🎯 Focus: Verify fixes for driver creation and question collection")
        start_time = time.time()
        
        # Test 1: Basic API functionality
        await self.test_basic_api_endpoints()
        
        # Test 2: Case-insensitive matching
        await self.test_case_insensitive_matching()
        
        # Test 3: Driver creation verification
        indiabix_job_id, geeksforgeeks_job_id = await self.test_driver_creation_verification()
        
        # Test 4: Monitor job execution for 3 minutes
        job_ids = [job_id for job_id in [indiabix_job_id, geeksforgeeks_job_id] if job_id]
        if job_ids:
            await self.monitor_job_execution(job_ids, monitoring_duration=180)
        
        total_time = time.time() - start_time
        
        # Generate final report
        self.generate_final_report(total_time)
    
    def generate_final_report(self, total_time: float):
        """Generate comprehensive final report"""
        logger.info("=" * 80)
        logger.info("🎯 CRITICAL DRIVER/EXTRACTOR INTEGRATION TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 40)
        logger.info("📊 QUESTION COLLECTION RESULTS:")
        collection = self.test_results["question_collection"]
        logger.info(f"IndiaBix Questions: {collection['indiabix_questions']}")
        logger.info(f"GeeksforGeeks Questions: {collection['geeksforgeeks_questions']}")
        logger.info(f"TOTAL QUESTIONS COLLECTED: {collection['total_questions']}")
        logger.info("=" * 40)
        
        # Critical findings
        logger.info("🔍 CRITICAL FINDINGS:")
        if collection['total_questions'] > 0:
            logger.info("✅ SUCCESS: Question collection is working!")
            logger.info(f"🎉 The web scraper collected {collection['total_questions']} questions after fixes")
        else:
            logger.info("❌ FAILURE: No questions were collected")
            logger.info("🔍 Driver/extractor integration issues remain")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        logger.info("=" * 80)

async def main():
    """Main test execution function"""
    logger.info("🚀 CRITICAL DRIVER/EXTRACTOR INTEGRATION TESTING")
    logger.info("🎯 Testing fixes for 'Failed to initialize driver or extractor' error")
    logger.info("🔍 Focus: IndiaBix (SeleniumDriver) and GeeksforGeeks (PlaywrightDriver)")
    
    async with DriverExtractorTester() as tester:
        await tester.run_critical_tests()

if __name__ == "__main__":
    asyncio.run(main())