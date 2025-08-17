#!/usr/bin/env python3
"""
Simplified End-to-End Integration Testing for Task 17
Tests the core integration functionality without complex dependencies
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Simplified integration test runner for Task 17"""
    
    def __init__(self):
        # Use localhost for testing since external URL might have issues
        self.base_url = "http://localhost:8001/api"
        
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "performance_metrics": {}
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
    
    async def test_system_health_and_ai_services(self):
        """Test 1: System health and AI services availability"""
        logger.info("🏥 Testing System Health and AI Services...")
        
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
                    details = f"MongoDB: {data.get('mongodb')}, AI Services: Gemini={ai_services.get('gemini')}, Groq={ai_services.get('groq')}, HF={ai_services.get('huggingface')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("System Health & AI Services", success, details, response_time)
                return success
                
        except Exception as e:
            import traceback
            logger.error(f"Exception in health test: {e}")
            logger.error(traceback.format_exc())
            self.log_test_result("System Health & AI Services", False, f"Exception: {str(e)}")
            return False
    
    async def test_scraping_management_endpoints(self):
        """Test 2: Scraping management API endpoints"""
        logger.info("🔧 Testing Scraping Management Endpoints...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test list sources
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/sources") as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = isinstance(data, list) and len(data) > 0
                    details = f"Retrieved {len(data)} sources"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("List Scraping Sources", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("List Scraping Sources", False, f"Exception: {str(e)}")
        
        # Test system status
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/system-status") as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "system_health" in data and
                        "active_jobs" in data and
                        "timestamp" in data
                    )
                    details = f"System health: {data.get('system_health')}, Active jobs: {data.get('active_jobs', 0)}"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Scraping System Status", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("Scraping System Status", False, f"Exception: {str(e)}")
        
        # Test create scraping job
        try:
            start_time = time.time()
            payload = {
                "source_type": "indiabix",
                "target_categories": ["quantitative"],
                "max_questions": 5,
                "priority": 1
            }
            
            async with self.session.post(
                f"{self.base_url}/scraping/jobs",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 201:
                    data = await response.json()
                    success = (
                        "job_id" in data and
                        "status" in data and
                        data["status"] in ["queued", "running"]
                    )
                    details = f"Job created: {data.get('job_id')}, Status: {data.get('status')}"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Create Scraping Job", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("Create Scraping Job", False, f"Exception: {str(e)}")
        
        return tests_passed, total_tests
    
    async def test_analytics_endpoints(self):
        """Test 3: Analytics and monitoring endpoints"""
        logger.info("📊 Testing Analytics Endpoints...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test performance metrics
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/performance") as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "timestamp" in data and
                        "metrics" in data
                    )
                    details = f"Performance metrics retrieved with {len(data.get('metrics', {}))} sections"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Performance Analytics", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("Performance Analytics", False, f"Exception: {str(e)}")
        
        # Test system health analytics
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/scraping/analytics/system-health") as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "system_status" in data and
                        "timestamp" in data
                    )
                    details = f"System health: {data.get('system_status')}"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("System Health Analytics", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("System Health Analytics", False, f"Exception: {str(e)}")
        
        return tests_passed, total_tests
    
    async def test_monitoring_dashboard_endpoints(self):
        """Test 4: Real-time monitoring dashboard endpoints"""
        logger.info("📈 Testing Monitoring Dashboard Endpoints...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test monitoring status
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/monitoring/status") as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "status" in data and
                        "timestamp" in data
                    )
                    details = f"Monitoring status: {data.get('status')}"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Monitoring Status", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("Monitoring Status", False, f"Exception: {str(e)}")
        
        # Test dashboard data
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/monitoring/dashboard") as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "system_health" in data and
                        "timestamp" in data
                    )
                    details = f"Dashboard data retrieved with system health: {data.get('system_health', {}).get('overall_status', 'N/A')}"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Dashboard Data", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("Dashboard Data", False, f"Exception: {str(e)}")
        
        return tests_passed, total_tests
    
    async def test_ai_enhanced_endpoints(self):
        """Test 5: AI-enhanced question endpoints"""
        logger.info("🤖 Testing AI-Enhanced Question Endpoints...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test AI question generation
        try:
            start_time = time.time()
            payload = {
                "category": "quantitative",
                "difficulty": "medium",
                "count": 2,
                "company_focus": "general"
            }
            
            async with self.session.post(
                f"{self.base_url}/ai-questions/generate",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "questions" in data and
                        isinstance(data["questions"], list) and
                        len(data["questions"]) > 0
                    )
                    details = f"Generated {len(data.get('questions', []))} AI questions"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Question Generation", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("AI Question Generation", False, f"Exception: {str(e)}")
        
        # Test instant feedback
        try:
            start_time = time.time()
            payload = {
                "question_text": "What is 2 + 2?",
                "user_answer": "4",
                "correct_answer": "4"
            }
            
            async with self.session.post(
                f"{self.base_url}/ai-questions/feedback",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                total_tests += 1
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "feedback" in data and
                        "is_correct" in data
                    )
                    details = f"Feedback received: {data.get('is_correct', 'N/A')}"
                    if success:
                        tests_passed += 1
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Instant Feedback", success, details, response_time)
                
        except Exception as e:
            total_tests += 1
            self.log_test_result("AI Instant Feedback", False, f"Exception: {str(e)}")
        
        return tests_passed, total_tests
    
    async def run_comprehensive_integration_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting Comprehensive End-to-End Integration Testing Suite")
        logger.info(f"Testing backend at: {self.base_url}")
        
        overall_start_time = time.time()
        
        # Test 1: System Health and AI Services
        logger.info("Running Test 1: System Health and AI Services")
        health_success = await self.test_system_health_and_ai_services()
        logger.info(f"Test 1 result: {health_success}")
        
        # Test 2: Scraping Management
        logger.info("Running Test 2: Scraping Management")
        scraping_passed, scraping_total = await self.test_scraping_management_endpoints()
        logger.info(f"Test 2 result: {scraping_passed}/{scraping_total}")
        
        # Test 3: Analytics
        logger.info("Running Test 3: Analytics")
        analytics_passed, analytics_total = await self.test_analytics_endpoints()
        logger.info(f"Test 3 result: {analytics_passed}/{analytics_total}")
        
        # Test 4: Monitoring Dashboard
        logger.info("Running Test 4: Monitoring Dashboard")
        monitoring_passed, monitoring_total = await self.test_monitoring_dashboard_endpoints()
        logger.info(f"Test 4 result: {monitoring_passed}/{monitoring_total}")
        
        # Test 5: AI-Enhanced Questions
        logger.info("Running Test 5: AI-Enhanced Questions")
        ai_passed, ai_total = await self.test_ai_enhanced_endpoints()
        logger.info(f"Test 5 result: {ai_passed}/{ai_total}")
        
        # Calculate overall results
        total_duration = time.time() - overall_start_time
        
        # Generate comprehensive report
        report = {
            'integration_test_report': {
                'overall_success': self.test_results["passed_tests"] >= (self.test_results["total_tests"] * 0.7),  # 70% success rate
                'timestamp': datetime.utcnow().isoformat(),
                'total_duration_seconds': total_duration,
                
                'summary_statistics': {
                    'total_tests_run': self.test_results["total_tests"],
                    'successful_tests': self.test_results["passed_tests"],
                    'failed_tests': self.test_results["failed_tests"],
                    'success_rate': self.test_results["passed_tests"] / max(self.test_results["total_tests"], 1),
                    'meets_integration_criteria': self.test_results["passed_tests"] >= 8  # At least 8 tests passing
                },
                
                'test_categories': {
                    'system_health': {'passed': 1 if health_success else 0, 'total': 1},
                    'scraping_management': {'passed': scraping_passed, 'total': scraping_total},
                    'analytics': {'passed': analytics_passed, 'total': analytics_total},
                    'monitoring_dashboard': {'passed': monitoring_passed, 'total': monitoring_total},
                    'ai_enhanced_questions': {'passed': ai_passed, 'total': ai_total}
                },
                
                'performance_metrics': {
                    'average_response_time': sum(t['response_time'] for t in self.test_results['test_details']) / max(len(self.test_results['test_details']), 1),
                    'total_processing_time_seconds': total_duration,
                    'tests_per_second': self.test_results["total_tests"] / max(total_duration, 1)
                },
                
                'test_results': self.test_results["test_details"]
            }
        }
        
        # Add recommendations
        recommendations = []
        
        if report['integration_test_report']['overall_success']:
            recommendations.append("SUCCESS: Integration tests meet acceptance criteria")
            recommendations.append("READY: Core system components validated for production")
            
            if report['integration_test_report']['summary_statistics']['success_rate'] >= 0.9:
                recommendations.append("EXCELLENT: High success rate achieved (90%+)")
        else:
            if not health_success:
                recommendations.append("CRITICAL: System health check failed - investigate AI services")
            
            if scraping_passed < scraping_total * 0.5:
                recommendations.append("CRITICAL: Scraping management endpoints failing - check scraping infrastructure")
            
            if ai_passed < ai_total * 0.5:
                recommendations.append("CRITICAL: AI-enhanced endpoints failing - verify AI service integration")
        
        report['integration_test_report']['recommendations'] = recommendations
        
        return report

# Test execution function
async def run_integration_tests():
    """Main function to run integration tests"""
    async with IntegrationTestRunner() as tester:
        return await tester.run_comprehensive_integration_tests()

if __name__ == "__main__":
    async def main():
        print("🚀 Starting End-to-End Integration Testing Suite...")
        report = await run_integration_tests()
        
        print("\n" + "="*80)
        print("INTEGRATION TEST REPORT")
        print("="*80)
        
        test_report = report.get('integration_test_report', {})
        print(f"Overall Success: {'✅ PASSED' if test_report.get('overall_success', False) else '❌ FAILED'}")
        print(f"Tests Successful: {test_report.get('summary_statistics', {}).get('successful_tests', 0)}/{test_report.get('summary_statistics', {}).get('total_tests_run', 0)}")
        print(f"Success Rate: {test_report.get('summary_statistics', {}).get('success_rate', 0):.1%}")
        print(f"Average Response Time: {test_report.get('performance_metrics', {}).get('average_response_time', 0):.2f}s")
        
        print("\nTest Categories:")
        for category, results in test_report.get('test_categories', {}).items():
            print(f"  • {category.replace('_', ' ').title()}: {results['passed']}/{results['total']} passed")
        
        print("\nRecommendations:")
        for rec in test_report.get('recommendations', []):
            print(f"  • {rec}")
        
        print("="*80)
        
        return report
    
    asyncio.run(main())