#!/usr/bin/env python3
"""
Focused Scraping System Backend Testing
Specifically testing the execute_job method fix and API parameter validation fixes as requested in review
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

class FocusedScrapingTester:
    """Focused tester for execute_job method fix and API parameter validation"""
    
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://aptiscraper.preview.emergentagent.com/api"
        except:
            self.base_url = "https://aptiscraper.preview.emergentagent.com/api"
        
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "critical_findings": []
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
    
    def log_critical_finding(self, finding: str):
        """Log critical finding"""
        self.test_results["critical_findings"].append(finding)
        logger.warning(f"🚨 CRITICAL: {finding}")
    
    async def test_execute_job_method_fix(self):
        """Test 1: Verify the execute_job method fix - no more 'NoneType' object has no attribute 'execute_job' errors"""
        logger.info("🔧 Testing execute_job Method Fix...")
        
        # Create a test job first
        job_id = None
        try:
            start_time = time.time()
            payload = {
                "job_name": "ExecuteJobMethodTest",
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
                    success = True
                    details = f"Job created successfully: {job_id}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Job creation failed: Status {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Create Test Job for execute_job Fix", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Create Test Job for execute_job Fix", False, f"Exception: {str(e)}")
        
        # Now try to start the job and monitor for execute_job errors
        if job_id:
            try:
                start_time = time.time()
                async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        success = True
                        details = f"Job start successful: Status {data.get('status')}"
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Job start failed: Status {response.status}, Error: {error_text[:200]}"
                        
                        # Check for the specific execute_job error
                        if "'NoneType' object has no attribute 'execute_job'" in error_text:
                            self.log_critical_finding("execute_job method fix NOT working - still getting NoneType error")
                    
                    self.log_test_result("Start Job - execute_job Method Test", success, details, response_time)
                    
            except Exception as e:
                error_msg = str(e)
                if "'NoneType' object has no attribute 'execute_job'" in error_msg:
                    self.log_critical_finding("execute_job method fix NOT working - exception contains NoneType error")
                self.log_test_result("Start Job - execute_job Method Test", False, f"Exception: {error_msg}")
            
            # Monitor the job for a few seconds to check for execution errors
            await asyncio.sleep(10)  # Wait 10 seconds for job to start executing
            
            try:
                start_time = time.time()
                async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        error_message = data.get("error_message", "")
                        last_error = data.get("last_error", "")
                        status = data.get("status", "unknown")
                        
                        # Check for the specific execute_job error in job status
                        execute_job_error_found = False
                        if "'NoneType' object has no attribute 'execute_job'" in str(error_message) + str(last_error):
                            execute_job_error_found = True
                            self.log_critical_finding("execute_job method fix NOT working - error found in job status")
                        
                        if execute_job_error_found:
                            success = False
                            details = f"execute_job error found: {error_message or last_error}"
                        else:
                            success = True
                            details = f"No execute_job errors found. Status: {status}, Error: {error_message or 'None'}"
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Failed to get job status: {response.status}, Error: {error_text[:200]}"
                    
                    self.log_test_result("Monitor Job for execute_job Errors", success, details, response_time)
                    
            except Exception as e:
                self.log_test_result("Monitor Job for execute_job Errors", False, f"Exception: {str(e)}")
    
    async def test_api_parameter_validation_fixes(self):
        """Test 2: Test job creation and job start operations to see if API parameter validation issues are resolved"""
        logger.info("🔍 Testing API Parameter Validation Fixes...")
        
        # Test various parameter combinations that were previously failing
        test_cases = [
            {
                "name": "Standard Parameters",
                "payload": {
                    "job_name": "StandardParamTest",
                    "source_names": ["IndiaBix"],
                    "max_questions_per_source": 20,
                    "target_categories": ["quantitative", "logical"],
                    "priority_level": 1,
                    "enable_ai_processing": True,
                    "enable_duplicate_detection": True
                }
            },
            {
                "name": "GeeksforGeeks Source",
                "payload": {
                    "job_name": "GeeksforGeeksParamTest",
                    "source_names": ["GeeksforGeeks"],
                    "max_questions_per_source": 15,
                    "target_categories": ["programming", "algorithms"],
                    "priority_level": 2,
                    "enable_ai_processing": False,
                    "enable_duplicate_detection": True
                }
            },
            {
                "name": "Multiple Sources",
                "payload": {
                    "job_name": "MultiSourceParamTest",
                    "source_names": ["IndiaBix", "GeeksforGeeks"],
                    "max_questions_per_source": 10,
                    "target_categories": ["quantitative", "programming"],
                    "priority_level": 1,
                    "enable_ai_processing": True,
                    "enable_duplicate_detection": False
                }
            }
        ]
        
        for test_case in test_cases:
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}/scraping/jobs",
                    json=test_case["payload"]
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 201:
                        data = await response.json()
                        job_id = data.get("job_id")
                        if job_id:
                            self.created_job_ids.append(job_id)
                        success = True
                        details = f"Job created successfully: {job_id}"
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Status {response.status}, Error: {error_text[:200]}"
                        
                        # Check for specific parameter validation errors
                        if "validation" in error_text.lower() or "field required" in error_text.lower():
                            self.log_critical_finding(f"API parameter validation issue in {test_case['name']}: {error_text[:100]}")
                    
                    self.log_test_result(f"Create Job - {test_case['name']}", success, details, response_time)
                    
            except Exception as e:
                self.log_test_result(f"Create Job - {test_case['name']}", False, f"Exception: {str(e)}")
    
    async def test_job_start_operations(self):
        """Test 3: Try to start scraping jobs and see if they can actually begin execution"""
        logger.info("🚀 Testing Job Start Operations...")
        
        if not self.created_job_ids:
            logger.warning("No jobs created to test start operations")
            return
        
        for i, job_id in enumerate(self.created_job_ids[:3]):  # Test first 3 jobs
            try:
                start_time = time.time()
                async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "unknown")
                        
                        if status in ["running", "started"]:
                            success = True
                            details = f"Job started successfully: Status {status}"
                        else:
                            success = False
                            details = f"Job start returned success but status is {status}"
                            self.log_critical_finding(f"Job {job_id[:8]} start operation returned 200 but status is {status}")
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Status {response.status}, Error: {error_text[:200]}"
                        
                        # Check for specific start operation errors
                        if "execute_job" in error_text or "NoneType" in error_text:
                            self.log_critical_finding(f"Job start operation has execute_job related error: {error_text[:100]}")
                    
                    self.log_test_result(f"Start Job {i+1} ({job_id[:8]})", success, details, response_time)
                    
            except Exception as e:
                error_msg = str(e)
                if "execute_job" in error_msg or "NoneType" in error_msg:
                    self.log_critical_finding(f"Job start operation exception has execute_job error: {error_msg[:100]}")
                self.log_test_result(f"Start Job {i+1} ({job_id[:8]})", False, f"Exception: {error_msg}")
    
    async def test_question_collection_capability(self):
        """Test 4: Check if jobs can collect any questions from the configured sources"""
        logger.info("📊 Testing Question Collection Capability...")
        
        if not self.created_job_ids:
            logger.warning("No jobs created to test question collection")
            return
        
        # Wait for jobs to have time to collect questions
        logger.info("⏳ Waiting 60 seconds for jobs to collect questions...")
        await asyncio.sleep(60)
        
        total_questions_collected = 0
        
        for i, job_id in enumerate(self.created_job_ids):
            try:
                start_time = time.time()
                async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        statistics = data.get("statistics", {})
                        progress = data.get("progress", {})
                        
                        questions_extracted = (
                            statistics.get("questions_extracted", 0) or 
                            data.get("questions_extracted", 0) or
                            progress.get("questions_extracted", 0)
                        )
                        
                        total_questions_collected += questions_extracted
                        
                        status = data.get("status", "unknown")
                        error_message = data.get("error_message", "")
                        
                        if questions_extracted > 0:
                            success = True
                            details = f"Questions collected: {questions_extracted}, Status: {status}"
                        else:
                            success = False
                            details = f"No questions collected. Status: {status}, Error: {error_message or 'None'}"
                            
                            # Check for specific collection blocking errors
                            if error_message:
                                if "dataclass" in error_message.lower() or "attribute" in error_message.lower():
                                    self.log_critical_finding(f"Question collection blocked by dataclass/attribute error: {error_message[:100]}")
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Failed to get job status: Status {response.status}, Error: {error_text[:200]}"
                    
                    self.log_test_result(f"Question Collection Job {i+1} ({job_id[:8]})", success, details, response_time)
                    
            except Exception as e:
                self.log_test_result(f"Question Collection Job {i+1} ({job_id[:8]})", False, f"Exception: {str(e)}")
        
        # Overall collection assessment
        if total_questions_collected > 0:
            self.log_test_result("Overall Question Collection", True, f"Total questions collected: {total_questions_collected}")
        else:
            self.log_test_result("Overall Question Collection", False, "No questions collected from any source")
            self.log_critical_finding("System unable to collect any questions from configured sources")
    
    async def test_remaining_blockers(self):
        """Test 5: Report any remaining issues that prevent actual question collection"""
        logger.info("🔍 Testing for Remaining Blockers...")
        
        # Test system health
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status", "unknown")
                    services = data.get("services", {})
                    
                    if status == "healthy":
                        success = True
                        details = f"System healthy with {len(services)} services"
                    else:
                        success = False
                        details = f"System status: {status}, Services: {len(services)}"
                        
                        # Check for specific service issues
                        for service_name, service_status in services.items():
                            if service_status.get("status") != "healthy":
                                self.log_critical_finding(f"Service {service_name} is not healthy: {service_status}")
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Health check failed: Status {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("System Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("System Health Check", False, f"Exception: {str(e)}")
        
        # Test source availability
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) >= 2:
                        success = True
                        details = f"Found {len(data)} sources available"
                    else:
                        success = False
                        details = f"Insufficient sources: {len(data) if isinstance(data, list) else 'Invalid response'}"
                        self.log_critical_finding("Insufficient scraping sources configured")
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Source listing failed: Status {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Source Availability Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Source Availability Check", False, f"Exception: {str(e)}")
    
    async def run_focused_tests(self):
        """Run all focused tests for the review request"""
        logger.info("🎯 Starting Focused Scraping System Backend Testing")
        logger.info("📋 Review Focus: execute_job method fix and API parameter validation fixes")
        start_time = time.time()
        
        # Run focused tests in order
        await self.test_execute_job_method_fix()
        await self.test_api_parameter_validation_fixes()
        await self.test_job_start_operations()
        await self.test_question_collection_capability()
        await self.test_remaining_blockers()
        
        total_time = time.time() - start_time
        
        # Generate focused summary
        logger.info("=" * 80)
        logger.info("🎯 FOCUSED SCRAPING SYSTEM TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 40)
        logger.info("📊 REVIEW REQUEST ASSESSMENT:")
        logger.info(f"Jobs Created: {len(self.created_job_ids)}")
        logger.info(f"Critical Findings: {len(self.test_results['critical_findings'])}")
        logger.info("=" * 40)
        
        # Show critical findings
        if self.test_results["critical_findings"]:
            logger.info("🚨 CRITICAL FINDINGS:")
            for finding in self.test_results["critical_findings"]:
                logger.info(f"  - {finding}")
        else:
            logger.info("✅ NO CRITICAL ISSUES FOUND")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        logger.info("=" * 80)
        
        return self.test_results


async def main():
    """Main test execution function"""
    logger.info("🚀 FOCUSED SCRAPING ENGINE TESTING - REVIEW REQUEST")
    logger.info("🎯 Testing: execute_job method fix and API parameter validation fixes")
    
    async with FocusedScrapingTester() as tester:
        results = await tester.run_focused_tests()
    
    # Final assessment
    logger.info("\n" + "=" * 80)
    logger.info("🎯 REVIEW REQUEST ASSESSMENT SUMMARY")
    logger.info("=" * 80)
    
    critical_findings = results["critical_findings"]
    success_rate = (results["passed_tests"] / max(results["total_tests"], 1)) * 100
    
    logger.info(f"Overall Success Rate: {success_rate:.1f}%")
    logger.info(f"Critical Issues Found: {len(critical_findings)}")
    
    # Specific review request assessments
    logger.info("\n📋 REVIEW REQUEST ITEMS:")
    logger.info("1. execute_job method fix verification: " + ("✅ VERIFIED" if not any("execute_job" in f for f in critical_findings) else "❌ ISSUES FOUND"))
    logger.info("2. API parameter validation fixes: " + ("✅ VERIFIED" if not any("parameter validation" in f for f in critical_findings) else "❌ ISSUES FOUND"))
    logger.info("3. Job start operations: " + ("✅ WORKING" if success_rate > 70 else "❌ ISSUES FOUND"))
    logger.info("4. Question collection capability: " + ("✅ WORKING" if not any("collection" in f for f in critical_findings) else "❌ BLOCKED"))
    
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())