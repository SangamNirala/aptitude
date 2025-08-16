#!/usr/bin/env python3
"""
Comprehensive Backend Testing for AI-Enhanced Aptitude Questions API
Tests all AI services integration and endpoints
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

class AIAptitudeAPITester:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = "https://prep-genius-3.preview.emergentagent.com/api"
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
    
    async def test_health_endpoints(self):
        """Test basic health and status endpoints"""
        logger.info("🔍 Testing Health & Status Endpoints...")
        
        # Test root endpoint
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/") as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    "AI-Enhanced Aptitude Questions API" in data.get("message", "") and
                    "features" in data and
                    len(data["features"]) >= 4
                )
                
                details = f"Status: {response.status}, Features: {len(data.get('features', []))}"
                self.log_test_result("Root Endpoint", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Root Endpoint", False, f"Exception: {str(e)}")
        
        # Test health endpoint
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                ai_services = data.get("ai_services", {})
                success = (
                    response.status == 200 and
                    data.get("status") == "healthy" and
                    ai_services.get("gemini") == "available" and
                    ai_services.get("groq") == "available" and
                    ai_services.get("huggingface") == "available"
                )
                
                details = f"MongoDB: {data.get('mongodb')}, AI Services: {ai_services}"
                self.log_test_result("Health Check", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Health Check", False, f"Exception: {str(e)}")
    
    async def test_ai_question_generation(self):
        """Test AI question generation endpoints"""
        logger.info("🤖 Testing AI Question Generation...")
        
        # Test generate-ai endpoint
        try:
            start_time = time.time()
            payload = {
                "category": "quantitative",
                "difficulty": "placement_ready", 
                "topic": "percentages",
                "company_pattern": "TCS"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-ai",
                params=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "question_text" in data and
                        "options" in data and
                        len(data["options"]) == 4 and
                        "correct_answer" in data and
                        "ai_metrics" in data and
                        data["ai_metrics"]["quality_score"] > 0
                    )
                    details = f"Generated question with quality score: {data.get('ai_metrics', {}).get('quality_score', 0)}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("AI Question Generation", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("AI Question Generation", False, f"Exception: {str(e)}")
        
        # Test create-enhanced endpoint
        try:
            start_time = time.time()
            payload = {
                "question_text": "If 20% of a number is 40, what is 50% of the same number?",
                "options": ["A) 80", "B) 100", "C) 120", "D) 160"],
                "correct_answer": "B) 100",
                "category": "quantitative",
                "difficulty": "placement_ready",
                "source": "manual"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/create-enhanced",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        data["question_text"] == payload["question_text"] and
                        "ai_metrics" in data and
                        "metadata" in data and
                        data["ai_metrics"]["quality_score"] > 0
                    )
                    details = f"Enhanced question created with quality: {data.get('ai_metrics', {}).get('quality_score', 0)}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Create Enhanced Question", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Create Enhanced Question", False, f"Exception: {str(e)}")
    
    async def test_instant_feedback_system(self):
        """Test ultra-fast Groq-powered feedback system"""
        logger.info("⚡ Testing Instant Feedback System...")
        
        try:
            start_time = time.time()
            payload = {
                "question_id": "test-question-123",
                "question_text": "What is 25% of 200?",
                "user_answer": "50",
                "correct_answer": "50"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/instant-feedback",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "is_correct" in data and
                        "feedback" in data and
                        "response_time_ms" in data and
                        response_time < 2.0  # Should be ultra-fast
                    )
                    details = f"Feedback in {response_time:.3f}s, Correct: {data.get('is_correct')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Instant Feedback", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Instant Feedback", False, f"Exception: {str(e)}")
    
    async def test_ai_analysis_features(self):
        """Test AI analysis features (hints, difficulty assessment, duplicates)"""
        logger.info("🧠 Testing AI Analysis Features...")
        
        # Test generate-hint
        try:
            start_time = time.time()
            payload = {
                "question_text": "A train travels 120 km in 2 hours. What is its speed?",
                "user_progress": "I know distance and time but stuck on formula"
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-hint",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "hint" in data and
                        len(data["hint"]) > 10 and
                        response_time < 2.0
                    )
                    details = f"Hint generated in {response_time:.3f}s"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Generate Hint", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Generate Hint", False, f"Exception: {str(e)}")
        
        # Test assess-difficulty
        try:
            start_time = time.time()
            payload = {
                "question_text": "Find the compound interest on Rs. 10000 at 10% per annum for 2 years compounded annually",
                "options": ["A) Rs. 2000", "B) Rs. 2100", "C) Rs. 2200", "D) Rs. 2300"]
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/assess-difficulty",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "difficulty_score" in data and
                        "difficulty_level" in data and
                        1 <= data["difficulty_score"] <= 10
                    )
                    details = f"Difficulty: {data.get('difficulty_level')} (Score: {data.get('difficulty_score')})"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Assess Difficulty", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Assess Difficulty", False, f"Exception: {str(e)}")
        
        # Test detect-duplicates
        try:
            start_time = time.time()
            payload = {
                "question_text": "What is 10% of 100?",
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
                        "is_duplicate" in data and
                        "similarity_scores" in data
                    )
                    details = f"Duplicate check completed, Is duplicate: {data.get('is_duplicate')}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Detect Duplicates", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Detect Duplicates", False, f"Exception: {str(e)}")
    
    async def test_smart_features(self):
        """Test smart features like personalized questions and quality stats"""
        logger.info("🎯 Testing Smart Features...")
        
        # Test generate-personalized
        try:
            start_time = time.time()
            payload = {
                "user_id": "test-user-123",
                "weak_areas": ["percentages", "profit_loss"],
                "target_companies": ["TCS", "Infosys"],
                "count": 3
            }
            
            async with self.session.post(
                f"{self.base_url}/questions/generate-personalized",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, list) and
                        len(data) > 0 and
                        all("question_text" in q for q in data)
                    )
                    details = f"Generated {len(data)} personalized questions"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Generate Personalized Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Generate Personalized Questions", False, f"Exception: {str(e)}")
        
        # Test quality-stats
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/quality-stats") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "total_questions" in data and
                        "avg_quality_score" in data and
                        isinstance(data["total_questions"], int)
                    )
                    details = f"Total questions: {data.get('total_questions')}, Avg quality: {data.get('avg_quality_score', 0):.1f}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Quality Stats", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Quality Stats", False, f"Exception: {str(e)}")
    
    async def test_database_operations(self):
        """Test database operations with AI-enhanced models"""
        logger.info("💾 Testing Database Operations...")
        
        # Test filtered questions
        try:
            start_time = time.time()
            params = {
                "category": "quantitative",
                "difficulty": "placement_ready",
                "min_quality_score": 70.0,
                "limit": 5
            }
            
            async with self.session.get(
                f"{self.base_url}/questions/filtered",
                params=params
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        "questions" in data and
                        "total_count" in data and
                        "batch_quality_score" in data and
                        isinstance(data["questions"], list)
                    )
                    details = f"Found {len(data.get('questions', []))} questions, Quality: {data.get('batch_quality_score', 0):.1f}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Filtered Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Filtered Questions", False, f"Exception: {str(e)}")
        
        # Test company-specific questions
        try:
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/questions/company-specific/TCS",
                params={"count": 3}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        isinstance(data, list) and
                        len(data) >= 0  # May be empty if no TCS questions exist yet
                    )
                    details = f"Found {len(data)} TCS-specific questions"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("Company-Specific Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Company-Specific Questions", False, f"Exception: {str(e)}")
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for AI services"""
        logger.info("⏱️ Testing Performance Benchmarks...")
        
        # Test multiple instant feedback calls for performance
        feedback_times = []
        for i in range(3):
            try:
                start_time = time.time()
                payload = {
                    "question_id": f"perf-test-{i}",
                    "question_text": f"What is {10 + i * 5}% of 100?",
                    "user_answer": str(10 + i * 5),
                    "correct_answer": str(10 + i * 5)
                }
                
                async with self.session.post(
                    f"{self.base_url}/questions/instant-feedback",
                    json=payload
                ) as response:
                    response_time = time.time() - start_time
                    feedback_times.append(response_time)
                    
            except Exception as e:
                logger.error(f"Performance test {i} failed: {str(e)}")
        
        if feedback_times:
            avg_time = sum(feedback_times) / len(feedback_times)
            max_time = max(feedback_times)
            success = avg_time < 2.0 and max_time < 3.0
            details = f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s"
            self.log_test_result("Performance Benchmark", success, details, avg_time)
            
            self.test_results["performance_metrics"] = {
                "avg_feedback_time": avg_time,
                "max_feedback_time": max_time,
                "feedback_samples": len(feedback_times)
            }
    
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting Comprehensive AI-Enhanced Backend Testing...")
        start_time = time.time()
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_ai_question_generation()
        await self.test_instant_feedback_system()
        await self.test_ai_analysis_features()
        await self.test_smart_features()
        await self.test_database_operations()
        await self.test_performance_benchmarks()
        
        total_time = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        
        if self.test_results["performance_metrics"]:
            logger.info(f"Avg Feedback Time: {self.test_results['performance_metrics']['avg_feedback_time']:.3f}s")
        
        logger.info("=" * 60)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results

async def main():
    """Main test execution"""
    async with AIAptitudeAPITester() as tester:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open('/app/test_results_backend.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📊 Test results saved to test_results_backend.json")
        
        # Return exit code based on results
        if results["failed_tests"] > 0:
            logger.error("Some tests failed!")
            return 1
        else:
            logger.info("All tests passed! 🎉")
            return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)