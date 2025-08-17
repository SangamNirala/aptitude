#!/usr/bin/env python3
"""
Comprehensive Scraping Tester for Tasks 14-15
Tests all 19 endpoints as specified in the review request
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

class ComprehensiveScrapingTester:
    """Comprehensive tester for TASK 14-15 - All Scraping Management and Analytics API Endpoints"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "task_14_results": {},
            "task_15_results": {},
            "created_job_id": None
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
    
    # TASK 14 - Scraping Management API Endpoints (11 endpoints)
    
    async def test_create_scraping_job(self):
        """Test POST /api/scraping/jobs/create with case-insensitive source lookup"""
        logger.info("➕ Testing Create Scraping Job (Case-insensitive)...")
        
        # Test with different case variations
        test_cases = [
            {"source": "IndiaBix", "description": "Test with proper case"},
            {"source": "indiabix", "description": "Test with lowercase"},
            {"source": "INDIABIX", "description": "Test with uppercase"}
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                start_time = time.time()
                payload = {
                    "job_name": f"Test Job {i+1}",
                    "description": test_case["description"],
                    "source_names": [test_case["source"]],
                    "max_questions_per_source": 5,
                    "quality_threshold": 70.0,
                    "enable_ai_processing": True,
                    "enable_duplicate_detection": True,
                    "priority_level": 2
                }
                
                async with self.session.post(
                    f"{self.base_url}/scraping/jobs",
                    json=payload
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 201:
                        data = await response.json()
                        success = (
                            "job_id" in data and
                            "status" in data and
                            data.get("status") in ["created", "pending"]
                        )
                        details = f"Job created with ID: {data.get('job_id', 'unknown')}, Status: {data.get('status')}"
                        
                        # Store first successful job_id for later tests
                        if success and not self.test_results["created_job_id"]:
                            self.test_results["created_job_id"] = data.get("job_id")
                            
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Status: {response.status}, Error: {error_text[:200]}"
                    
                    self.log_test_result(f"Create Job ({test_case['source']})", success, details, response_time)
                    
            except Exception as e:
                self.log_test_result(f"Create Job ({test_case['source']})", False, f"Exception: {str(e)}")
    
    async def test_list_scraping_jobs(self):
        """Test GET /api/scraping/jobs"""
        logger.info("📋 Testing List Scraping Jobs...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/jobs") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list)
                    details = f"Retrieved {len(data)} jobs"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("List Scraping Jobs", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("List Scraping Jobs", False, f"Exception: {str(e)}")
    
    async def test_get_job_details(self):
        """Test GET /api/scraping/jobs/{job_id}"""
        logger.info("🔍 Testing Get Job Details...")
        
        job_id = self.test_results["created_job_id"]
        if not job_id:
            self.log_test_result("Get Job Details", False, "No job ID available for testing")
            return
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "job_id" in data and
                        "status" in data and
                        data["job_id"] == job_id
                    )
                    details = f"Job details retrieved, Status: {data.get('status', 'unknown')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Get Job Details", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Get Job Details", False, f"Exception: {str(e)}")
    
    async def test_start_job(self):
        """Test POST /api/scraping/jobs/{job_id}/start"""
        logger.info("▶️ Testing Start Job...")
        
        job_id = self.test_results["created_job_id"]
        if not job_id:
            self.log_test_result("Start Job", False, "No job ID available for testing")
            return
        
        try:
            start_time = time.time()
            async with self.session.post(f"{self.base_url}/scraping/jobs/{job_id}/start") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data and
                        data.get("status") in ["started", "running", "queued"]
                    )
                    details = f"Job start response: {data.get('status', 'unknown')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Start Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Start Job", False, f"Exception: {str(e)}")
    
    async def test_stop_job(self):
        """Test POST /api/scraping/jobs/{job_id}/stop"""
        logger.info("⏹️ Testing Stop Job...")
        
        job_id = self.test_results["created_job_id"]
        if not job_id:
            self.log_test_result("Stop Job", False, "No job ID available for testing")
            return
        
        try:
            start_time = time.time()
            async with self.session.post(f"{self.base_url}/scraping/jobs/{job_id}/stop") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data and
                        data.get("status") in ["stopped", "stopping", "cancelled"]
                    )
                    details = f"Job stop response: {data.get('status', 'unknown')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Stop Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Stop Job", False, f"Exception: {str(e)}")
    
    async def test_pause_job(self):
        """Test POST /api/scraping/jobs/{job_id}/pause"""
        logger.info("⏸️ Testing Pause Job...")
        
        job_id = self.test_results["created_job_id"]
        if not job_id:
            self.log_test_result("Pause Job", False, "No job ID available for testing")
            return
        
        try:
            start_time = time.time()
            async with self.session.post(f"{self.base_url}/scraping/jobs/{job_id}/pause") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data and
                        data.get("status") in ["paused", "pausing"]
                    )
                    details = f"Job pause response: {data.get('status', 'unknown')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Pause Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Pause Job", False, f"Exception: {str(e)}")
    
    async def test_delete_job(self):
        """Test DELETE /api/scraping/jobs/{job_id}"""
        logger.info("🗑️ Testing Delete Job...")
        
        job_id = self.test_results["created_job_id"]
        if not job_id:
            self.log_test_result("Delete Job", False, "No job ID available for testing")
            return
        
        try:
            start_time = time.time()
            async with self.session.delete(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "message" in data and
                        "deleted" in data.get("message", "").lower()
                    )
                    details = f"Job deletion response: {data.get('message', 'unknown')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Delete Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Delete Job", False, f"Exception: {str(e)}")
    
    async def test_list_sources(self):
        """Test GET /api/scraping/sources"""
        logger.info("📚 Testing List Sources...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, list) and
                        len(data) > 0
                    )
                    
                    # Check for expected sources
                    source_names = [source.get("name", "").lower() for source in data]
                    has_indiabix = any("indiabix" in name for name in source_names)
                    has_geeksforgeeks = any("geeks" in name for name in source_names)
                    
                    details = f"Found {len(data)} sources. IndiaBix: {has_indiabix}, GeeksforGeeks: {has_geeksforgeeks}"
                    
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("List Sources", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("List Sources", False, f"Exception: {str(e)}")
    
    async def test_get_source_details(self):
        """Test GET /api/scraping/sources/{source_id}"""
        logger.info("🔍 Testing Get Source Details...")
        
        # First get sources to find a valid source_id
        try:
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                if response.status == 200:
                    sources = await response.json()
                    if sources and len(sources) > 0:
                        source_id = sources[0].get("id") or sources[0].get("name", "indiabix")
                    else:
                        source_id = "indiabix"  # fallback
                else:
                    source_id = "indiabix"  # fallback
        except:
            source_id = "indiabix"  # fallback
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/sources/{source_id}") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "name" in data or "id" in data
                    )
                    details = f"Source details retrieved for: {source_id}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Get Source Details", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Get Source Details", False, f"Exception: {str(e)}")
    
    async def test_queue_status(self):
        """Test GET /api/scraping/queue"""
        logger.info("⏳ Testing Queue Status...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/queue-status") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "total_queued" in data or "queued_jobs" in data or
                        "active_jobs" in data or "queue_size" in data
                    )
                    details = f"Queue status retrieved with keys: {list(data.keys())}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Queue Status", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Queue Status", False, f"Exception: {str(e)}")
    
    async def test_system_status_and_health(self):
        """Test GET /api/scraping/system/status and GET /api/health"""
        logger.info("🖥️ Testing System Status and Health...")
        
        # Test system status
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/system-status") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data or "system_status" in data
                    )
                    details = f"System status: {data.get('status', data.get('system_status', 'unknown'))}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("System Status", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("System Status", False, f"Exception: {str(e)}")
        
        # Test health endpoint
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data and
                        data.get("status") == "healthy"
                    )
                    details = f"Health status: {data.get('status', 'unknown')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Health Check", False, f"Exception: {str(e)}")
    
    # TASK 15 - Analytics & Monitoring API Endpoints (8 endpoints)
    
    async def test_performance_analytics(self):
        """Test GET /api/scraping/analytics/performance"""
        logger.info("📊 Testing Performance Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/performance") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Performance analytics retrieved with {len(data)} metrics"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Performance Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Performance Analytics", False, f"Exception: {str(e)}")
    
    async def test_source_analytics(self):
        """Test GET /api/scraping/analytics/source"""
        logger.info("📈 Testing Source Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/source") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Source analytics retrieved with {len(data)} sources"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Source Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Source Analytics", False, f"Exception: {str(e)}")
    
    async def test_quality_analytics(self):
        """Test GET /api/scraping/analytics/quality"""
        logger.info("🎯 Testing Quality Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/quality") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Quality analytics retrieved with {len(data)} metrics"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Quality Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Quality Analytics", False, f"Exception: {str(e)}")
    
    async def test_jobs_analytics(self):
        """Test GET /api/scraping/analytics/jobs"""
        logger.info("💼 Testing Jobs Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/jobs") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Jobs analytics retrieved with {len(data)} metrics"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Jobs Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Jobs Analytics", False, f"Exception: {str(e)}")
    
    async def test_system_health_analytics(self):
        """Test GET /api/scraping/analytics/system-health"""
        logger.info("🏥 Testing System Health Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/system-health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"System health analytics retrieved with {len(data)} metrics"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("System Health Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("System Health Analytics", False, f"Exception: {str(e)}")
    
    async def test_trends_analytics(self):
        """Test GET /api/scraping/analytics/trends"""
        logger.info("📈 Testing Trends Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/trends") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Trends analytics retrieved with {len(data)} metrics"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Trends Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Trends Analytics", False, f"Exception: {str(e)}")
    
    async def test_realtime_analytics(self):
        """Test GET /api/scraping/analytics/realtime"""
        logger.info("⚡ Testing Realtime Analytics...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/realtime") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Realtime analytics retrieved with {len(data)} metrics"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Realtime Analytics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Realtime Analytics", False, f"Exception: {str(e)}")
    
    async def test_analytics_report(self):
        """Test POST /api/scraping/analytics/report"""
        logger.info("📋 Testing Analytics Report...")
        
        try:
            start_time = time.time()
            payload = {
                "report_type": "comprehensive",
                "time_range": {
                    "start_time": "2024-01-01T00:00:00Z",
                    "end_time": "2024-12-31T23:59:59Z"
                },
                "include_sections": ["performance", "quality", "sources", "jobs"],
                "format": "json"
            }
            
            async with self.session.post(
                f"{self.base_url}/scraping/analytics/report",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, dict) and
                        len(data) > 0
                    )
                    details = f"Analytics report generated with {len(data)} sections"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Analytics Report", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Analytics Report", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all comprehensive scraping tests for Tasks 14-15"""
        logger.info("🚀 Starting Comprehensive Scraping Tests (Tasks 14-15)...")
        start_time = time.time()
        
        # TASK 14 - Scraping Management API Endpoints (11 tests)
        logger.info("=" * 60)
        logger.info("🎯 TASK 14 - SCRAPING MANAGEMENT API ENDPOINTS")
        logger.info("=" * 60)
        
        await self.test_create_scraping_job()  # 1) POST /api/scraping/jobs/create
        await self.test_list_scraping_jobs()   # 2) GET /api/scraping/jobs
        await self.test_get_job_details()      # 3) GET /api/scraping/jobs/{job_id}
        await self.test_start_job()            # 4) POST /api/scraping/jobs/{job_id}/start
        await self.test_stop_job()             # 5) POST /api/scraping/jobs/{job_id}/stop
        await self.test_pause_job()            # 6) POST /api/scraping/jobs/{job_id}/pause
        await self.test_delete_job()           # 7) DELETE /api/scraping/jobs/{job_id}
        await self.test_list_sources()         # 8) GET /api/scraping/sources
        await self.test_get_source_details()   # 9) GET /api/scraping/sources/{source_id}
        await self.test_queue_status()         # 10) GET /api/scraping/queue
        await self.test_system_status_and_health()  # 11) GET /api/scraping/system/status + /api/health
        
        # TASK 15 - Analytics & Monitoring API Endpoints (8 tests)
        logger.info("=" * 60)
        logger.info("🎯 TASK 15 - ANALYTICS & MONITORING API ENDPOINTS")
        logger.info("=" * 60)
        
        await self.test_performance_analytics()    # 1) GET /api/scraping/analytics/performance
        await self.test_source_analytics()         # 2) GET /api/scraping/analytics/source
        await self.test_quality_analytics()        # 3) GET /api/scraping/analytics/quality
        await self.test_jobs_analytics()           # 4) GET /api/scraping/analytics/jobs
        await self.test_system_health_analytics()  # 5) GET /api/scraping/analytics/system-health
        await self.test_trends_analytics()         # 6) GET /api/scraping/analytics/trends
        await self.test_realtime_analytics()       # 7) GET /api/scraping/analytics/realtime
        await self.test_analytics_report()         # 8) POST /api/scraping/analytics/report
        
        total_time = time.time() - start_time
        
        # Generate comprehensive summary
        logger.info("=" * 80)
        logger.info("🎯 COMPREHENSIVE SCRAPING TESTS SUMMARY (TASKS 14-15)")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 80)
        
        # Show detailed results by task
        task_14_tests = [t for t in self.test_results["test_details"] if any(keyword in t["test_name"].lower() for keyword in ["job", "source", "queue", "system", "health"])]
        task_15_tests = [t for t in self.test_results["test_details"] if "analytics" in t["test_name"].lower()]
        
        task_14_passed = len([t for t in task_14_tests if t["success"]])
        task_15_passed = len([t for t in task_15_tests if t["success"]])
        
        logger.info(f"📊 TASK 14 Results: {task_14_passed}/{len(task_14_tests)} passed ({(task_14_passed/max(len(task_14_tests),1)*100):.1f}%)")
        logger.info(f"📊 TASK 15 Results: {task_15_passed}/{len(task_15_tests)} passed ({(task_15_passed/max(len(task_15_tests),1)*100):.1f}%)")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        # Compare against baseline
        success_rate = (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100
        baseline = 68.4
        if success_rate > baseline:
            logger.info(f"🎉 SUCCESS RATE IMPROVED: {success_rate:.1f}% vs {baseline}% baseline (+{success_rate-baseline:.1f}%)")
        elif success_rate == baseline:
            logger.info(f"📊 SUCCESS RATE MAINTAINED: {success_rate:.1f}% (matches {baseline}% baseline)")
        else:
            logger.info(f"⚠️ SUCCESS RATE REGRESSION: {success_rate:.1f}% vs {baseline}% baseline ({success_rate-baseline:.1f}%)")
        
        return self.test_results

async def main():
    """Main test execution function for Tasks 14-15 Comprehensive Testing"""
    logger.info("🚀 Starting Comprehensive Scraping Tests (Tasks 14-15)...")
    
    # Get backend URL from environment
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.split('=')[1].strip() + "/api"
                    break
            else:
                base_url = "https://endpoint-test-suite.preview.emergentagent.com/api"
    except:
        base_url = "https://endpoint-test-suite.preview.emergentagent.com/api"
    
    logger.info(f"🌐 Using backend URL: {base_url}")
    
    # Run Comprehensive Scraping Tests (Tasks 14-15) - 19 endpoints total
    async with ComprehensiveScrapingTester(base_url) as scraping_tester:
        scraping_results = await scraping_tester.run_all_tests()
    
    # Generate final summary
    logger.info("=" * 80)
    logger.info("🎯 FINAL COMPREHENSIVE SCRAPING TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"📊 Tasks 14-15 Combined: {scraping_results['passed_tests']}/{scraping_results['total_tests']} passed")
    logger.info(f"🎯 Overall Success Rate: {(scraping_results['passed_tests']/max(scraping_results['total_tests'],1)*100):.1f}%")
    
    # Compare against 68.4% baseline
    success_rate = (scraping_results['passed_tests']/max(scraping_results['total_tests'],1)*100)
    baseline = 68.4
    if success_rate > baseline:
        logger.info(f"🎉 IMPROVEMENT: {success_rate:.1f}% vs {baseline}% baseline (+{success_rate-baseline:.1f}%)")
    elif success_rate == baseline:
        logger.info(f"📊 MAINTAINED: {success_rate:.1f}% (matches {baseline}% baseline)")
    else:
        logger.info(f"⚠️ REGRESSION: {success_rate:.1f}% vs {baseline}% baseline ({success_rate-baseline:.1f}%)")
    
    logger.info("=" * 80)
    
    return scraping_results

if __name__ == "__main__":
    asyncio.run(main())