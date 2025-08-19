#!/usr/bin/env python3
"""
Focused Web Scraping System Test
Tests the core scraping functionality for collecting questions from IndiaBix and GeeksforGeeks
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingSystemTester:
    def __init__(self):
        self.base_url = "https://question-vault.preview.emergentagent.com/api"
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "scraping_stats": {
                "jobs_created": 0,
                "jobs_started": 0,
                "questions_collected": 0,
                "sources_available": []
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
            logger.info(f"✅ {test_name} - PASSED ({response_time:.2f}s) - {details}")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED - {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_scraping_health(self):
        """Test scraping system health"""
        logger.info("🏥 Testing Scraping System Health...")
        
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
                    details = f"HTTP {response.status}: {error_text[:200]}"
                
                self.log_test_result("Scraping Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Scraping Health Check", False, f"Exception: {str(e)}")
    
    async def test_available_sources(self):
        """Test available scraping sources"""
        logger.info("📋 Testing Available Sources...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list) and len(data) >= 2
                    
                    source_names = [source.get('name', '') for source in data]
                    self.test_results["scraping_stats"]["sources_available"] = source_names
                    
                    has_indiabix = any('IndiaBix' in name for name in source_names)
                    has_geeksforgeeks = any('GeeksforGeeks' in name for name in source_names)
                    
                    details = f"Found {len(data)} sources: {', '.join(source_names)}, IndiaBix: {has_indiabix}, GeeksforGeeks: {has_geeksforgeeks}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"HTTP {response.status}: {error_text[:200]}"
                
                self.log_test_result("Available Sources", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Available Sources", False, f"Exception: {str(e)}")
    
    async def test_create_scraping_job(self, source_name, max_questions=100):
        """Test creating a scraping job"""
        logger.info(f"🚀 Testing Job Creation for {source_name}...")
        
        try:
            start_time = time.time()
            payload = {
                "job_name": f"{source_name}_Test_Collection",
                "source_names": [source_name.lower()],
                "max_questions_per_source": max_questions,
                "target_categories": ["quantitative", "logical", "verbal", "programming"],
                "priority_level": 1,  # 1=highest priority
                "configuration": {
                    "enable_ai_processing": True,
                    "quality_threshold": 0.6,
                    "duplicate_detection": True
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/scraping/jobs",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 201:
                    data = await response.json()
                    success = "job_id" in data and "status" in data
                    job_id = data.get("job_id")
                    
                    if job_id:
                        self.created_job_ids.append(job_id)
                        self.test_results["scraping_stats"]["jobs_created"] += 1
                    
                    details = f"Job ID: {job_id}, Status: {data.get('status')}, Target: {max_questions} questions"
                    self.log_test_result(f"Create {source_name} Job", success, details, response_time)
                    return job_id
                else:
                    success = False
                    error_text = await response.text()
                    details = f"HTTP {response.status}: {error_text[:200]}"
                    self.log_test_result(f"Create {source_name} Job", success, details, response_time)
                    return None
                
        except Exception as e:
            self.log_test_result(f"Create {source_name} Job", False, f"Exception: {str(e)}")
            return None
    
    async def test_start_job(self, job_id, source_name):
        """Test starting a scraping job"""
        logger.info(f"▶️ Testing Job Start for {source_name}...")
        
        if not job_id:
            self.log_test_result(f"Start {source_name} Job", False, "No job ID available")
            return
        
        try:
            start_time = time.time()
            payload = {
                "priority": "normal",  # JobPriority enum value
                "custom_config": None
            }
            
            async with self.session.put(
                f"{self.base_url}/scraping/jobs/{job_id}/start",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = "status" in data and data["status"] in ["running", "started"]
                    
                    if success:
                        self.test_results["scraping_stats"]["jobs_started"] += 1
                    
                    details = f"Job started, Status: {data.get('status')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"HTTP {response.status}: {error_text[:200]}"
                
                self.log_test_result(f"Start {source_name} Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result(f"Start {source_name} Job", False, f"Exception: {str(e)}")
    
    async def test_monitor_job(self, job_id, source_name):
        """Test monitoring job progress"""
        logger.info(f"📊 Testing Job Monitoring for {source_name}...")
        
        if not job_id:
            self.log_test_result(f"Monitor {source_name} Job", False, "No job ID available")
            return
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = "job_id" in data and "status" in data
                    
                    progress = data.get("progress", {})
                    statistics = data.get("statistics", {})
                    questions_extracted = statistics.get("questions_extracted", 0)
                    
                    self.test_results["scraping_stats"]["questions_collected"] += questions_extracted
                    
                    details = f"Status: {data.get('status')}, Progress: {progress.get('percentage', 0):.1f}%, Questions: {questions_extracted}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"HTTP {response.status}: {error_text[:200]}"
                
                self.log_test_result(f"Monitor {source_name} Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result(f"Monitor {source_name} Job", False, f"Exception: {str(e)}")
    
    async def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        logger.info("📈 Testing Analytics Endpoints...")
        
        # Test source analytics
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/sources") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, (list, dict))
                    details = f"Analytics data available, Type: {type(data).__name__}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"HTTP {response.status}: {error_text[:200]}"
                
                self.log_test_result("Source Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Source Analytics", False, f"Exception: {str(e)}")
        
        # Test quality analytics
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/quality") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, dict)
                    
                    total_questions = data.get("total_questions", 0)
                    avg_quality = data.get("average_quality", 0)
                    
                    details = f"Total Questions: {total_questions}, Avg Quality: {avg_quality:.2f}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"HTTP {response.status}: {error_text[:200]}"
                
                self.log_test_result("Quality Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Quality Analytics", False, f"Exception: {str(e)}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive scraping system test"""
        logger.info("🚀 Starting Comprehensive Web Scraping System Test")
        logger.info("🎯 Goal: Test system capability to collect questions from IndiaBix and GeeksforGeeks")
        start_time = time.time()
        
        # Test basic system health
        await self.test_scraping_health()
        await self.test_available_sources()
        
        # Create and start jobs for both sources
        indiabix_job_id = await self.test_create_scraping_job("IndiaBix", 50)
        geeksforgeeks_job_id = await self.test_create_scraping_job("GeeksforGeeks", 50)
        
        # Start the jobs
        await self.test_start_job(indiabix_job_id, "IndiaBix")
        await self.test_start_job(geeksforgeeks_job_id, "GeeksforGeeks")
        
        # Wait for jobs to process
        logger.info("⏳ Waiting 60 seconds for jobs to process...")
        await asyncio.sleep(60)
        
        # Monitor job progress
        await self.test_monitor_job(indiabix_job_id, "IndiaBix")
        await self.test_monitor_job(geeksforgeeks_job_id, "GeeksforGeeks")
        
        # Test analytics
        await self.test_analytics_endpoints()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 80)
        logger.info("🎯 WEB SCRAPING SYSTEM TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 40)
        logger.info("📊 SCRAPING STATISTICS:")
        stats = self.test_results["scraping_stats"]
        logger.info(f"Sources Available: {', '.join(stats['sources_available'])}")
        logger.info(f"Jobs Created: {stats['jobs_created']}")
        logger.info(f"Jobs Started: {stats['jobs_started']}")
        logger.info(f"Questions Collected: {stats['questions_collected']}")
        logger.info("=" * 80)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results

async def main():
    """Main test execution"""
    async with ScrapingSystemTester() as tester:
        results = await tester.run_comprehensive_test()
    
    return results

if __name__ == "__main__":
    asyncio.run(main())