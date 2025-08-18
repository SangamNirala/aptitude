#!/usr/bin/env python3
"""
Critical Scraping Engine Test - Focus on Review Request Issues
Tests the specific fixes mentioned in the review request:
1. Execute_job Fix Verification
2. Driver Creation Fix (source_name argument)
3. Question Collection Testing
4. Results Reporting
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CriticalScrapingTester:
    """Critical tester focused on review request issues"""
    
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://quizdata.preview.emergentagent.com/api"
        except:
            self.base_url = "https://quizdata.preview.emergentagent.com/api"
        
        self.session = None
        self.test_results = {
            "execute_job_fix": {"verified": False, "details": ""},
            "driver_creation_fix": {"verified": False, "details": ""},
            "question_collection": {"total_questions": 0, "indiabix": 0, "geeksforgeeks": 0},
            "job_execution_status": {"jobs_created": 0, "jobs_started": 0, "jobs_running": 0},
            "critical_errors": []
        }
        self.created_job_ids = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_execute_job_fix(self):
        """Test if the execute_job method fix is working"""
        logger.info("🔍 Testing Execute_job Method Fix...")
        
        try:
            # Create a test job
            payload = {
                "job_name": "Execute_Job_Fix_Test",
                "source_names": ["IndiaBix"],
                "max_questions_per_source": 10,
                "target_categories": ["quantitative"],
                "priority_level": 1,
                "enable_ai_processing": False,
                "enable_duplicate_detection": False
            }
            
            async with self.session.post(f"{self.base_url}/scraping/jobs", json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    job_id = data.get("job_id")
                    self.created_job_ids.append(job_id)
                    self.test_results["job_execution_status"]["jobs_created"] += 1
                    
                    # Start the job
                    async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as start_response:
                        if start_response.status == 200:
                            self.test_results["job_execution_status"]["jobs_started"] += 1
                            
                            # Wait a bit and check for execute_job errors
                            await asyncio.sleep(10)
                            
                            # Check job status for execute_job errors
                            async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    error_message = status_data.get("error_message", "") or status_data.get("last_error", "")
                                    
                                    # Check for the specific execute_job error
                                    if "'NoneType' object has no attribute 'execute_job'" in str(error_message):
                                        self.test_results["execute_job_fix"]["verified"] = False
                                        self.test_results["execute_job_fix"]["details"] = f"❌ EXECUTE_JOB ERROR STILL PRESENT: {error_message}"
                                        self.test_results["critical_errors"].append("execute_job method not properly initialized")
                                        logger.error(f"❌ Execute_job error still present: {error_message}")
                                    else:
                                        self.test_results["execute_job_fix"]["verified"] = True
                                        self.test_results["execute_job_fix"]["details"] = f"✅ No execute_job errors detected. Status: {status_data.get('status')}"
                                        logger.info(f"✅ Execute_job fix verified - no NoneType errors")
                                        
                                        if status_data.get("status") == "running":
                                            self.test_results["job_execution_status"]["jobs_running"] += 1
                                else:
                                    self.test_results["execute_job_fix"]["details"] = f"Could not check job status: {status_response.status}"
                        else:
                            self.test_results["execute_job_fix"]["details"] = f"Could not start job: {start_response.status}"
                else:
                    self.test_results["execute_job_fix"]["details"] = f"Could not create job: {response.status}"
                    
        except Exception as e:
            self.test_results["execute_job_fix"]["details"] = f"Exception during test: {str(e)}"
            logger.error(f"Exception testing execute_job fix: {e}")
    
    async def test_driver_creation_fix(self):
        """Test if the driver creation source_name argument fix is working"""
        logger.info("🔍 Testing Driver Creation Fix...")
        
        try:
            # Create jobs for both sources to test driver creation
            sources_to_test = ["IndiaBix", "GeeksforGeeks"]
            
            for source in sources_to_test:
                payload = {
                    "job_name": f"Driver_Creation_Test_{source}",
                    "source_names": [source],
                    "max_questions_per_source": 5,
                    "target_categories": ["quantitative"] if source == "IndiaBix" else ["programming"],
                    "priority_level": 1,
                    "enable_ai_processing": False,
                    "enable_duplicate_detection": False
                }
                
                async with self.session.post(f"{self.base_url}/scraping/jobs", json=payload) as response:
                    if response.status == 201:
                        data = await response.json()
                        job_id = data.get("job_id")
                        self.created_job_ids.append(job_id)
                        
                        # Start the job
                        async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as start_response:
                            if start_response.status == 200:
                                # Wait and check for driver creation errors
                                await asyncio.sleep(15)
                                
                                async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as status_response:
                                    if status_response.status == 200:
                                        status_data = await status_response.json()
                                        error_message = status_data.get("error_message", "") or status_data.get("last_error", "")
                                        
                                        # Check for driver creation errors
                                        driver_errors = [
                                            "create_selenium_driver() missing 1 required positional argument: 'source_name'",
                                            "create_playwright_driver() missing 1 required positional argument: 'source_name'",
                                            "missing source_name argument"
                                        ]
                                        
                                        has_driver_error = any(error in str(error_message) for error in driver_errors)
                                        
                                        if has_driver_error:
                                            self.test_results["driver_creation_fix"]["verified"] = False
                                            self.test_results["driver_creation_fix"]["details"] = f"❌ DRIVER CREATION ERROR for {source}: {error_message}"
                                            self.test_results["critical_errors"].append(f"Driver creation error for {source}")
                                            logger.error(f"❌ Driver creation error for {source}: {error_message}")
                                        else:
                                            if not self.test_results["driver_creation_fix"]["verified"]:
                                                self.test_results["driver_creation_fix"]["verified"] = True
                                            
                                            current_details = self.test_results["driver_creation_fix"]["details"]
                                            self.test_results["driver_creation_fix"]["details"] = f"{current_details} ✅ {source}: No driver errors"
                                            logger.info(f"✅ Driver creation fix verified for {source}")
                                            
        except Exception as e:
            self.test_results["driver_creation_fix"]["details"] = f"Exception during test: {str(e)}"
            logger.error(f"Exception testing driver creation fix: {e}")
    
    async def test_question_collection(self):
        """Test actual question collection from both sources"""
        logger.info("🔍 Testing Question Collection...")
        
        try:
            # Create high-volume jobs for question collection
            sources_config = {
                "IndiaBix": {
                    "max_questions": 500,
                    "categories": ["quantitative", "logical", "verbal"]
                },
                "GeeksforGeeks": {
                    "max_questions": 500,
                    "categories": ["programming", "algorithms", "data-structures"]
                }
            }
            
            collection_jobs = []
            
            for source, config in sources_config.items():
                payload = {
                    "job_name": f"Question_Collection_{source}",
                    "source_names": [source],
                    "max_questions_per_source": config["max_questions"],
                    "target_categories": config["categories"],
                    "priority_level": 1,
                    "enable_ai_processing": True,
                    "enable_duplicate_detection": True
                }
                
                async with self.session.post(f"{self.base_url}/scraping/jobs", json=payload) as response:
                    if response.status == 201:
                        data = await response.json()
                        job_id = data.get("job_id")
                        self.created_job_ids.append(job_id)
                        collection_jobs.append((job_id, source))
                        
                        # Start the job
                        async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as start_response:
                            if start_response.status == 200:
                                logger.info(f"✅ Started collection job for {source}: {job_id}")
                            else:
                                logger.error(f"❌ Failed to start collection job for {source}")
            
            # Monitor collection progress for 10 minutes (as requested in review)
            logger.info("📊 Monitoring question collection for 10 minutes...")
            monitoring_duration = 600  # 10 minutes
            check_interval = 30  # Check every 30 seconds
            checks = monitoring_duration // check_interval
            
            for check in range(checks):
                logger.info(f"📈 Collection check {check + 1}/{checks} ({(check + 1) * check_interval}s elapsed)")
                
                total_questions = 0
                source_questions = {"IndiaBix": 0, "GeeksforGeeks": 0}
                
                for job_id, source in collection_jobs:
                    try:
                        async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                            if response.status == 200:
                                data = await response.json()
                                questions_extracted = data.get("questions_extracted", 0) or data.get("total_questions_extracted", 0)
                                status = data.get("status", "unknown")
                                
                                source_questions[source] = questions_extracted
                                total_questions += questions_extracted
                                
                                logger.info(f"  {source}: {questions_extracted} questions, status: {status}")
                                
                                # Check for errors
                                error_message = data.get("error_message", "") or data.get("last_error", "")
                                if error_message and "error" in error_message.lower():
                                    logger.warning(f"  {source} error: {error_message}")
                                    
                    except Exception as e:
                        logger.warning(f"Error checking {source} job {job_id}: {e}")
                
                # Update results
                self.test_results["question_collection"]["total_questions"] = total_questions
                self.test_results["question_collection"]["indiabix"] = source_questions["IndiaBix"]
                self.test_results["question_collection"]["geeksforgeeks"] = source_questions["GeeksforGeeks"]
                
                logger.info(f"📊 Total questions collected so far: {total_questions}")
                logger.info(f"   IndiaBix: {source_questions['IndiaBix']}, GeeksforGeeks: {source_questions['GeeksforGeeks']}")
                
                # If we've collected a good amount, we can report success early
                if total_questions >= 100:
                    logger.info(f"🎉 Good progress! {total_questions} questions collected")
                
                if check < checks - 1:  # Don't sleep on last check
                    await asyncio.sleep(check_interval)
            
            # Final collection report
            final_total = self.test_results["question_collection"]["total_questions"]
            logger.info(f"🎯 Final question collection results:")
            logger.info(f"   Total: {final_total}")
            logger.info(f"   IndiaBix: {self.test_results['question_collection']['indiabix']}")
            logger.info(f"   GeeksforGeeks: {self.test_results['question_collection']['geeksforgeeks']}")
            
        except Exception as e:
            logger.error(f"Exception during question collection test: {e}")
    
    async def test_source_id_to_name_resolution(self):
        """Test if source ID to source name resolution is working"""
        logger.info("🔍 Testing Source ID to Name Resolution...")
        
        try:
            # Check if sources are properly configured
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                if response.status == 200:
                    sources = await response.json()
                    logger.info(f"📋 Found {len(sources)} configured sources")
                    
                    for source in sources:
                        source_name = source.get("name", "unknown")
                        source_id = source.get("id", "unknown")
                        logger.info(f"   {source_name} (ID: {source_id})")
                        
                        # Test individual source details
                        async with self.session.get(f"{self.base_url}/scraping/sources/{source_name.lower()}") as detail_response:
                            if detail_response.status == 200:
                                logger.info(f"   ✅ {source_name} details accessible")
                            else:
                                logger.warning(f"   ❌ {source_name} details not accessible: {detail_response.status}")
                else:
                    logger.error(f"❌ Could not list sources: {response.status}")
                    
        except Exception as e:
            logger.error(f"Exception testing source resolution: {e}")
    
    async def run_critical_tests(self):
        """Run all critical tests"""
        logger.info("🚀 Starting Critical Scraping Engine Tests")
        logger.info("🎯 Focus: Execute_job fix, Driver creation fix, Question collection")
        
        start_time = time.time()
        
        # Test 1: Execute_job method fix
        await self.test_execute_job_fix()
        
        # Test 2: Driver creation fix
        await self.test_driver_creation_fix()
        
        # Test 3: Source ID to name resolution
        await self.test_source_id_to_name_resolution()
        
        # Test 4: Question collection (main goal)
        await self.test_question_collection()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        logger.info("=" * 80)
        logger.info("🎯 CRITICAL SCRAPING ENGINE TEST RESULTS")
        logger.info("=" * 80)
        
        # Execute_job fix results
        execute_fix = self.test_results["execute_job_fix"]
        logger.info(f"1. Execute_job Fix: {'✅ VERIFIED' if execute_fix['verified'] else '❌ FAILED'}")
        logger.info(f"   Details: {execute_fix['details']}")
        
        # Driver creation fix results
        driver_fix = self.test_results["driver_creation_fix"]
        logger.info(f"2. Driver Creation Fix: {'✅ VERIFIED' if driver_fix['verified'] else '❌ FAILED'}")
        logger.info(f"   Details: {driver_fix['details']}")
        
        # Question collection results
        collection = self.test_results["question_collection"]
        logger.info(f"3. Question Collection Results:")
        logger.info(f"   Total Questions Collected: {collection['total_questions']}")
        logger.info(f"   IndiaBix: {collection['indiabix']}")
        logger.info(f"   GeeksforGeeks: {collection['geeksforgeeks']}")
        
        # Job execution status
        job_status = self.test_results["job_execution_status"]
        logger.info(f"4. Job Execution Status:")
        logger.info(f"   Jobs Created: {job_status['jobs_created']}")
        logger.info(f"   Jobs Started: {job_status['jobs_started']}")
        logger.info(f"   Jobs Running: {job_status['jobs_running']}")
        
        # Critical errors
        if self.test_results["critical_errors"]:
            logger.info(f"5. Critical Errors Found:")
            for error in self.test_results["critical_errors"]:
                logger.info(f"   ❌ {error}")
        else:
            logger.info(f"5. Critical Errors: ✅ None detected")
        
        logger.info(f"Total Test Time: {total_time:.2f}s")
        logger.info("=" * 80)
        
        # Assessment based on review request goals
        logger.info("🎯 REVIEW REQUEST ASSESSMENT:")
        
        if execute_fix['verified']:
            logger.info("✅ Execute_job 'NoneType' error: FIXED")
        else:
            logger.info("❌ Execute_job 'NoneType' error: STILL PRESENT")
        
        if driver_fix['verified']:
            logger.info("✅ Driver creation 'source_name argument' error: FIXED")
        else:
            logger.info("❌ Driver creation 'source_name argument' error: STILL PRESENT")
        
        total_questions = collection['total_questions']
        if total_questions >= 1000:
            logger.info(f"🎉 Question collection goal: EXCEEDED ({total_questions} questions)")
        elif total_questions >= 500:
            logger.info(f"⚠️ Question collection goal: PARTIAL SUCCESS ({total_questions} questions)")
        elif total_questions >= 100:
            logger.info(f"⚠️ Question collection goal: GOOD PROGRESS ({total_questions} questions)")
        else:
            logger.info(f"❌ Question collection goal: INSUFFICIENT ({total_questions} questions)")
        
        return self.test_results

async def main():
    """Main test execution"""
    logger.info("🚀 CRITICAL QUESTION COLLECTION TEST")
    logger.info("🎯 Testing fixes and question collection capability")
    
    async with CriticalScrapingTester() as tester:
        results = await tester.run_critical_tests()
    
    return results

if __name__ == "__main__":
    asyncio.run(main())