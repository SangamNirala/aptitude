#!/usr/bin/env python3
"""
Focused Integration Testing for Task 17 - End-to-End Integration Testing
Tests the core integration functionality with correct imports
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

class FocusedIntegrationTester:
    """Focused integration tester for Task 17 validation"""
    
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://staging-healthcheck.preview.emergentagent.com/api"
        except:
            self.base_url = "https://staging-healthcheck.preview.emergentagent.com/api"
        
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "performance_metrics": {}
        }
        self.created_job_ids = []  # Track created jobs for cleanup
    
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
    
    async def test_full_scraping_workflow_integration(self):
        """Test 1: Full Scraping Workflow Integration"""
        logger.info("🔄 Testing Full Scraping Workflow Integration...")
        
        # Test system health first
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    ai_services = data.get("ai_services", {})
                    success = (
                        data.get("status") == "healthy" and
                        data.get("mongodb") == "healthy" and
                        ai_services.get("gemini") == "available" and
                        ai_services.get("groq") == "available" and
                        ai_services.get("huggingface") == "available"
                    )
                    details = f"System Health: {data.get('status')}, MongoDB: {data.get('mongodb')}, AI Services: {len([s for s in ai_services.values() if s == 'available'])}/3 available"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("System Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("System Health Check", False, f"Exception: {str(e)}")
        
        # Test scraping job creation
        try:
            start_time = time.time()
            payload = {
                "job_name": "Integration Test Job - Full Workflow",
                "source_names": ["indiabix"],
                "target_categories": ["quantitative"],
                "max_questions_per_source": 10,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True,
                "priority_level": 1
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
                        data["status"] in ["queued", "running"]
                    )
                    if success and "job_id" in data:
                        self.created_job_ids.append(data["job_id"])
                    details = f"Job created: {data.get('job_id')}, Status: {data.get('status')}, Message: {data.get('message', 'N/A')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Create Scraping Job", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Create Scraping Job", False, f"Exception: {str(e)}")
        
        # Test job monitoring
        if self.created_job_ids:
            job_id = self.created_job_ids[0]
            try:
                start_time = time.time()
                async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        success = (
                            "job_id" in data and
                            "status" in data and
                            "created_at" in data
                        )
                        details = f"Job {job_id}: Status={data.get('status')}, Progress={data.get('progress', {}).get('percentage', 0)}%"
                    else:
                        success = False
                        error_text = await response.text()
                        details = f"Status: {response.status}, Error: {error_text[:200]}"
                    
                    self.log_test_result("Monitor Scraping Job", success, details, response_time)
                    
            except Exception as e:
                self.log_test_result("Monitor Scraping Job", False, f"Exception: {str(e)}")
    
    async def test_ai_pipeline_integration(self):
        """Test 2: AI Pipeline Integration"""
        logger.info("🤖 Testing AI Pipeline Integration...")
        
        # Test AI question generation
        try:
            start_time = time.time()
            params = {
                "category": "quantitative",
                "difficulty": "placement_ready",
                "topic": "arithmetic",
                "company_pattern": "general"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-ai",
                params=params
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "question_text" in data and
                        "options" in data and
                        len(data.get("options", [])) >= 2 and
                        "ai_metrics" in data
                    )
                    details = f"Generated question with {len(data.get('options', []))} options, Quality score: {data.get('ai_metrics', {}).get('quality_score', 'N/A')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Question Generation (Gemini)", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("AI Question Generation (Gemini)", False, f"Exception: {str(e)}")
        
        # Test instant feedback (Groq)
        try:
            start_time = time.time()
            payload = {
                "question_id": "test-question-id-123",
                "question_text": "What is the result of 15 + 25?",
                "user_answer": "40",
                "correct_answer": "40"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/instant-feedback",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "feedback" in data and
                        "is_correct" in data and
                        "response_time_ms" in data
                    )
                    details = f"Feedback: {data.get('is_correct')}, Response time: {data.get('response_time_ms', 0)}ms"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Instant Feedback (Groq)", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("AI Instant Feedback (Groq)", False, f"Exception: {str(e)}")
        
        # Test duplicate detection (HuggingFace)
        try:
            start_time = time.time()
            payload = {
                "question_text": "What is 2 + 2?",
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
                        "duplicate_pairs" in data and
                        "similarity_threshold" in data
                    )
                    details = f"Duplicate pairs found: {len(data.get('duplicate_pairs', []))}, Threshold: {data.get('similarity_threshold', 0)}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Duplicate Detection (HuggingFace)", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("AI Duplicate Detection (HuggingFace)", False, f"Exception: {str(e)}")
    
    async def test_error_scenarios_and_recovery(self):
        """Test 3: Error Scenarios and Recovery"""
        logger.info("⚠️ Testing Error Scenarios and Recovery...")
        
        # Test invalid job configuration
        try:
            start_time = time.time()
            payload = {
                "job_name": "",  # Invalid empty name
                "source_names": ["invalid_source"],  # Invalid source
                "max_questions_per_source": -1,  # Invalid negative number
                "priority_level": 10  # Invalid priority level
            }
            
            async with self.session.post(
                f"{self.base_url}/scraping/jobs",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                # We expect this to fail with proper error handling
                success = response.status in [400, 422]  # Bad Request or Validation Error
                if success:
                    error_data = await response.json()
                    details = f"Properly handled invalid request: {response.status}, Error: {error_data.get('detail', 'Validation error')}"
                else:
                    details = f"Unexpected response: {response.status}"
                
                self.log_test_result("Invalid Job Configuration Handling", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Invalid Job Configuration Handling", False, f"Exception: {str(e)}")
        
        # Test non-existent job retrieval
        try:
            start_time = time.time()
            fake_job_id = "non-existent-job-id-12345"
            async with self.session.get(f"{self.base_url}/scraping/jobs/{fake_job_id}") as response:
                response_time = time.time() - start_time
                
                # We expect this to fail with 404
                success = response.status == 404
                if success:
                    details = f"Properly handled non-existent job: 404 Not Found"
                else:
                    details = f"Unexpected response: {response.status}"
                
                self.log_test_result("Non-existent Job Handling", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Non-existent Job Handling", False, f"Exception: {str(e)}")
    
    async def test_performance_benchmarking(self):
        """Test 4: Performance Benchmarking"""
        logger.info("⚡ Testing Performance Benchmarking...")
        
        # Test concurrent API calls
        try:
            start_time = time.time()
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = self.session.get(f"{self.base_url}/scraping/system-status")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            response_time = time.time() - start_time
            
            successful_responses = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
            success = successful_responses >= 4  # At least 4 out of 5 should succeed
            
            details = f"Concurrent requests: {successful_responses}/5 successful, Total time: {response_time:.2f}s"
            
            # Close responses
            for r in responses:
                if hasattr(r, 'close'):
                    r.close()
            
            self.log_test_result("Concurrent API Performance", success, details, response_time)
            
        except Exception as e:
            self.log_test_result("Concurrent API Performance", False, f"Exception: {str(e)}")
        
        # Test analytics performance
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/performance") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        response_time < 2.0 and  # Should respond within 2 seconds
                        "metrics" in data
                    )
                    details = f"Analytics response time: {response_time:.2f}s, Metrics sections: {len(data.get('metrics', {}))}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Analytics Performance", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Analytics Performance", False, f"Exception: {str(e)}")
    
    async def test_monitoring_dashboard_integration(self):
        """Test 5: Real-time Monitoring Dashboard Integration"""
        logger.info("📊 Testing Monitoring Dashboard Integration...")
        
        # Test monitoring status
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/monitoring/status") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data and
                        "uptime_hours" in data and
                        "timestamp" in data
                    )
                    details = f"Monitoring status: {data.get('status')}, Uptime: {data.get('uptime_hours', 0):.2f}h"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Monitoring Status", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Monitoring Status", False, f"Exception: {str(e)}")
        
        # Test dashboard data aggregation
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/monitoring/dashboard") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "system_health" in data and
                        "performance_metrics" in data and
                        "timestamp" in data
                    )
                    details = f"Dashboard data: System health={data.get('system_health', {}).get('overall_status', 'N/A')}, Metrics available"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Dashboard Data Aggregation", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Dashboard Data Aggregation", False, f"Exception: {str(e)}")
    
    async def cleanup_test_jobs(self):
        """Clean up created test jobs"""
        logger.info("🧹 Cleaning up test jobs...")
        
        for job_id in self.created_job_ids:
            try:
                async with self.session.delete(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                    if response.status in [200, 204, 404]:  # Success or already deleted
                        logger.info(f"✅ Cleaned up job {job_id}")
                    else:
                        logger.warning(f"⚠️ Could not clean up job {job_id}: {response.status}")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up job {job_id}: {str(e)}")
    
    async def run_comprehensive_integration_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting Comprehensive End-to-End Integration Testing Suite")
        logger.info(f"Testing backend at: {self.base_url}")
        
        overall_start_time = time.time()
        
        try:
            # Run all test suites
            await self.test_full_scraping_workflow_integration()
            await self.test_ai_pipeline_integration()
            await self.test_error_scenarios_and_recovery()
            await self.test_performance_benchmarking()
            await self.test_monitoring_dashboard_integration()
            
            # Clean up
            await self.cleanup_test_jobs()
            
        except Exception as e:
            logger.error(f"❌ Integration testing suite failed: {str(e)}")
        
        # Calculate overall results
        total_duration = time.time() - overall_start_time
        success_rate = self.test_results["passed_tests"] / max(self.test_results["total_tests"], 1)
        
        # Generate comprehensive report
        report = {
            'integration_test_report': {
                'overall_success': success_rate >= 0.8,  # 80% success rate required
                'timestamp': datetime.utcnow().isoformat(),
                'total_duration_seconds': total_duration,
                
                'summary_statistics': {
                    'total_tests_run': self.test_results["total_tests"],
                    'successful_tests': self.test_results["passed_tests"],
                    'failed_tests': self.test_results["failed_tests"],
                    'success_rate': success_rate,
                    'meets_integration_criteria': success_rate >= 0.8
                },
                
                'performance_metrics': {
                    'average_response_time': sum(t['response_time'] for t in self.test_results['test_details']) / max(len(self.test_results['test_details']), 1),
                    'total_processing_time_seconds': total_duration,
                    'tests_per_second': self.test_results["total_tests"] / max(total_duration, 1)
                },
                
                'test_categories': {
                    'full_scraping_workflow': {'description': 'Complete scraping workflow from source to storage'},
                    'ai_pipeline_integration': {'description': 'AI services integration (Gemini, Groq, HuggingFace)'},
                    'error_scenarios_recovery': {'description': 'Error handling and recovery mechanisms'},
                    'performance_benchmarking': {'description': 'Performance and scalability testing'},
                    'monitoring_dashboard': {'description': 'Real-time monitoring and dashboard integration'}
                },
                
                'test_results': self.test_results["test_details"]
            }
        }
        
        # Add recommendations
        recommendations = []
        
        if report['integration_test_report']['overall_success']:
            recommendations.append("SUCCESS: Integration tests meet acceptance criteria")
            recommendations.append("READY: End-to-end integration validated for production")
            
            if success_rate >= 0.9:
                recommendations.append("EXCELLENT: High success rate achieved (90%+)")
        else:
            failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
            
            if any("System Health" in t["test_name"] for t in failed_tests):
                recommendations.append("CRITICAL: System health issues - investigate AI services and database")
            
            if any("AI" in t["test_name"] for t in failed_tests):
                recommendations.append("CRITICAL: AI pipeline issues - verify AI service integration")
            
            if any("Scraping" in t["test_name"] for t in failed_tests):
                recommendations.append("CRITICAL: Scraping workflow issues - check scraping infrastructure")
        
        report['integration_test_report']['recommendations'] = recommendations
        
        return report

# Test execution function
async def run_integration_tests():
    """Main function to run integration tests"""
    async with FocusedIntegrationTester() as tester:
        return await tester.run_comprehensive_integration_tests()

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Focused End-to-End Integration Testing Suite...")
        report = await run_integration_tests()
        
        print("\n" + "="*80)
        print("FOCUSED INTEGRATION TEST REPORT")
        print("="*80)
        
        test_report = report.get('integration_test_report', {})
        print(f"Overall Success: {'✅ PASSED' if test_report.get('overall_success', False) else '❌ FAILED'}")
        print(f"Tests Successful: {test_report.get('summary_statistics', {}).get('successful_tests', 0)}/{test_report.get('summary_statistics', {}).get('total_tests_run', 0)}")
        print(f"Success Rate: {test_report.get('summary_statistics', {}).get('success_rate', 0):.1%}")
        print(f"Average Response Time: {test_report.get('performance_metrics', {}).get('average_response_time', 0):.2f}s")
        print(f"Total Duration: {test_report.get('total_duration_seconds', 0):.2f}s")
        
        print("\nTest Categories Covered:")
        for category, info in test_report.get('test_categories', {}).items():
            print(f"  • {category.replace('_', ' ').title()}: {info['description']}")
        
        print("\nRecommendations:")
        for rec in test_report.get('recommendations', []):
            print(f"  • {rec}")
        
        print("\nDetailed Test Results:")
        for test in test_report.get('test_results', []):
            status = "✅" if test['success'] else "❌"
            print(f"  {status} {test['test_name']}: {test['details']}")
        
        print("="*80)
        
        return report
    
    asyncio.run(main())