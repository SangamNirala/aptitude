#!/usr/bin/env python3
"""
CRITICAL EXECUTE_JOB METHOD FIX VERIFICATION TEST
Testing the specific fix for 'NoneType' object has no attribute 'execute_job' error
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

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecuteJobFixTester:
    """Focused tester for the execute_job method fix"""
    
    def __init__(self):
        # Get backend URL from environment
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
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "execute_job_fix_verified": False,
            "critical_errors_found": []
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
    
    async def test_scraping_engine_execute_job_method(self):
        """Test that the ScrapingEngine has the execute_job method"""
        logger.info("🔍 Testing ScrapingEngine execute_job method existence...")
        
        try:
            # Import and test the scraping engine directly
            from scraping.scraper_engine import ScrapingEngine, get_scraping_engine
            from models.scraping_models import ScrapingJob, ScrapingJobConfig, ScrapingJobStatus
            
            # Get scraping engine instance
            engine = get_scraping_engine()
            
            # Check if execute_job method exists
            has_execute_job = hasattr(engine, 'execute_job')
            is_callable = callable(getattr(engine, 'execute_job', None))
            
            if has_execute_job and is_callable:
                self.log_test_result("ScrapingEngine execute_job Method Exists", True, 
                                   "execute_job method found and is callable")
                return True
            else:
                self.log_test_result("ScrapingEngine execute_job Method Exists", False, 
                                   f"execute_job method missing or not callable. has_method={has_execute_job}, is_callable={is_callable}")
                return False
                
        except Exception as e:
            self.log_test_result("ScrapingEngine execute_job Method Exists", False, f"Exception: {str(e)}")
            return False
    
    async def test_job_creation_with_execute_job_integration(self):
        """Test job creation and verify execute_job integration"""
        logger.info("🚀 Testing Job Creation with execute_job Integration...")
        
        try:
            start_time = time.time()
            payload = {
                "job_name": "ExecuteJob_Fix_Test",
                "source_names": ["IndiaBix"],
                "max_questions_per_source": 10,
                "target_categories": ["quantitative"],
                "priority_level": 1,
                "enable_ai_processing": False,
                "enable_duplicate_detection": False
            }
            
            async with self.session.post(
                f"{self.base_url}/scraping/jobs",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 201:
                    data = await response.json()
                    job_id = data.get("job_id")
                    if job_id:
                        self.created_job_ids.append(job_id)
                    
                    success = (
                        "job_id" in data and
                        "status" in data and
                        data["status"] == "pending"
                    )
                    details = f"Job ID: {job_id}, Status: {data.get('status')}"
                    self.log_test_result("Job Creation with execute_job Integration", success, details, response_time)
                    return job_id if success else None
                else:
                    error_text = await response.text()
                    self.log_test_result("Job Creation with execute_job Integration", False, 
                                       f"Status: {response.status}, Error: {error_text[:200]}", response_time)
                    return None
                    
        except Exception as e:
            self.log_test_result("Job Creation with execute_job Integration", False, f"Exception: {str(e)}")
            return None
    
    async def test_job_start_with_execute_job_call(self, job_id: str):
        """Test job start operation that should call execute_job"""
        logger.info(f"▶️ Testing Job Start with execute_job Call for job {job_id}...")
        
        try:
            start_time = time.time()
            # Create proper request body for job start
            request_body = {
                "priority": "high",
                "custom_config": None
            }
            
            async with self.session.put(
                f"{self.base_url}/scraping/jobs/{job_id}/start",
                json=request_body
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "action" in data and
                        data["action"] == "start" and
                        data.get("status") in ["started", "already_running"]
                    )
                    details = f"Action: {data.get('action')}, Status: {data.get('status')}, Message: {data.get('message')}"
                    self.log_test_result("Job Start with execute_job Call", success, details, response_time)
                    return success
                else:
                    error_text = await response.text()
                    self.log_test_result("Job Start with execute_job Call", False, 
                                       f"Status: {response.status}, Error: {error_text[:200]}", response_time)
                    return False
                    
        except Exception as e:
            self.log_test_result("Job Start with execute_job Call", False, f"Exception: {str(e)}")
            return False
    
    async def test_job_execution_monitoring(self, job_id: str):
        """Monitor job execution for execute_job related errors"""
        logger.info(f"📊 Monitoring Job Execution for execute_job Errors...")
        
        execute_job_errors_found = []
        
        for check_num in range(3):  # Check 3 times over 60 seconds
            try:
                start_time = time.time()
                async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for specific execute_job related errors
                        status = data.get("status", "unknown")
                        error_message = data.get("last_error", "") or data.get("error_message", "")
                        
                        # Look for the specific error that was supposed to be fixed
                        execute_job_error_patterns = [
                            "'NoneType' object has no attribute 'execute_job'",
                            "has no attribute 'execute_job'",
                            "execute_job method not found",
                            "execute_job is not defined"
                        ]
                        
                        has_execute_job_error = any(pattern in str(error_message).lower() for pattern in execute_job_error_patterns)
                        
                        if has_execute_job_error:
                            execute_job_errors_found.append(f"Check {check_num+1}: {error_message}")
                            self.test_results["critical_errors_found"].append(error_message)
                        
                        details = f"Check {check_num+1}: Status: {status}, Error: {error_message[:100] if error_message else 'None'}"
                        
                        # Success if no execute_job errors found
                        success = not has_execute_job_error
                        self.log_test_result(f"Job Execution Monitor Check {check_num+1}", success, details, response_time)
                        
                    else:
                        error_text = await response.text()
                        self.log_test_result(f"Job Execution Monitor Check {check_num+1}", False, 
                                           f"Status: {response.status}, Error: {error_text[:200]}", response_time)
                        
            except Exception as e:
                self.log_test_result(f"Job Execution Monitor Check {check_num+1}", False, f"Exception: {str(e)}")
            
            # Wait 20 seconds between checks
            if check_num < 2:
                logger.info(f"⏳ Waiting 20 seconds before next check...")
                await asyncio.sleep(20)
        
        # Overall assessment
        if not execute_job_errors_found:
            self.test_results["execute_job_fix_verified"] = True
            self.log_test_result("Execute Job Fix Verification", True, 
                               "No 'execute_job' related errors found during job execution monitoring")
        else:
            self.log_test_result("Execute Job Fix Verification", False, 
                               f"Execute job errors found: {'; '.join(execute_job_errors_found)}")
    
    async def test_background_job_manager_integration(self):
        """Test BackgroundJobManager integration with ScrapingEngine.execute_job"""
        logger.info("🔗 Testing BackgroundJobManager Integration with execute_job...")
        
        try:
            # Import required modules
            from services.job_manager_service import BackgroundJobManager, create_job_manager
            from scraping.scraper_engine import get_scraping_engine
            from models.scraping_models import ScrapingJob, ScrapingJobConfig, ScrapingJobStatus
            
            # Create job manager and scraping engine
            job_manager = create_job_manager(max_concurrent_jobs=1)
            scraping_engine = get_scraping_engine()
            
            # Verify the integration function exists
            async def test_execute_scraping_job(job: ScrapingJob):
                """Test job execution function that should call scraping_engine.execute_job"""
                return await scraping_engine.execute_job(job)
            
            # Test that the function can be called without errors
            try:
                # Create a minimal test job
                test_job = ScrapingJob(
                    id="test_integration_job",
                    config=ScrapingJobConfig(
                        job_name="Integration Test",
                        source_ids=["IndiaBix"],
                        max_questions_per_source=1
                    ),
                    status=ScrapingJobStatus.PENDING
                )
                
                # This should not raise an AttributeError about execute_job
                # We're not actually executing it, just verifying the method exists
                has_method = hasattr(scraping_engine, 'execute_job')
                is_async = asyncio.iscoroutinefunction(scraping_engine.execute_job) if has_method else False
                
                success = has_method and is_async
                details = f"execute_job method exists: {has_method}, is async: {is_async}"
                
                self.log_test_result("BackgroundJobManager Integration", success, details)
                return success
                
            except AttributeError as e:
                if "execute_job" in str(e):
                    self.log_test_result("BackgroundJobManager Integration", False, 
                                       f"CRITICAL: execute_job method missing - {str(e)}")
                    self.test_results["critical_errors_found"].append(str(e))
                    return False
                else:
                    raise
                    
        except Exception as e:
            self.log_test_result("BackgroundJobManager Integration", False, f"Exception: {str(e)}")
            return False
    
    async def run_execute_job_fix_tests(self):
        """Run all execute_job fix verification tests"""
        logger.info("🚀 STARTING EXECUTE_JOB METHOD FIX VERIFICATION TESTS")
        logger.info("🎯 Focus: Verify 'NoneType' object has no attribute 'execute_job' error is fixed")
        start_time = time.time()
        
        # Test 1: Verify execute_job method exists
        await self.test_scraping_engine_execute_job_method()
        
        # Test 2: Test BackgroundJobManager integration
        await self.test_background_job_manager_integration()
        
        # Test 3: Create a job to test the integration
        job_id = await self.test_job_creation_with_execute_job_integration()
        
        # Test 4: Start the job (this should call execute_job)
        if job_id:
            job_started = await self.test_job_start_with_execute_job_call(job_id)
            
            # Test 5: Monitor for execute_job errors
            if job_started:
                await self.test_job_execution_monitoring(job_id)
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 80)
        logger.info("🎯 EXECUTE_JOB METHOD FIX VERIFICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 40)
        
        # Critical assessment
        if self.test_results["execute_job_fix_verified"]:
            logger.info("✅ EXECUTE_JOB FIX VERIFIED: No 'execute_job' related errors found")
        else:
            logger.info("❌ EXECUTE_JOB FIX NOT VERIFIED: Issues still present")
        
        if self.test_results["critical_errors_found"]:
            logger.info("🚨 CRITICAL ERRORS FOUND:")
            for error in self.test_results["critical_errors_found"]:
                logger.info(f"  - {error}")
        else:
            logger.info("✅ NO CRITICAL EXECUTE_JOB ERRORS FOUND")
        
        logger.info("=" * 80)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results


async def main():
    """Main test execution function"""
    logger.info("🚀 CRITICAL EXECUTE_JOB METHOD FIX VERIFICATION")
    logger.info("🎯 Testing the fix for 'NoneType' object has no attribute 'execute_job' error")
    
    async with ExecuteJobFixTester() as tester:
        results = await tester.run_execute_job_fix_tests()
    
    # Final assessment
    logger.info("\n" + "=" * 80)
    logger.info("🎯 FINAL ASSESSMENT")
    logger.info("=" * 80)
    
    if results["execute_job_fix_verified"] and not results["critical_errors_found"]:
        logger.info("🎉 SUCCESS: execute_job method fix is working correctly!")
        logger.info("✅ BackgroundJobManager can successfully call scraping_engine.execute_job()")
        logger.info("✅ No 'NoneType' object has no attribute 'execute_job' errors detected")
    else:
        logger.info("⚠️ ISSUES DETECTED: execute_job method fix needs attention")
        if results["critical_errors_found"]:
            logger.info("❌ Critical errors still present in the system")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())