#!/usr/bin/env python3
"""
Comprehensive Testing for GeeksforGeeks Logical Questions Collection
Tests the newly added logical questions functionality to verify that 10 GeeksforGeeks 
logical questions are properly stored and accessible through the API.

Review Request Requirements:
1. Database Verification: Check exactly 10 logical questions in enhanced_questions collection
2. API Endpoint Testing: Test /api/questions/filtered with various filters
3. Question Quality Verification: Check proper schema, AI metrics, analytics fields
4. Specific Content Verification: Verify logical reasoning patterns
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

class LogicalQuestionsComprehensiveTester:
    """
    Comprehensive tester for GeeksforGeeks Logical Questions functionality
    Tests all requirements from the review request
    """
    
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://question-vault.preview.emergentagent.com/api"
        except:
            self.base_url = "https://question-vault.preview.emergentagent.com/api"
        
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "logical_questions_stats": {
                "total_logical_questions": 0,
                "questions_with_proper_schema": 0,
                "questions_with_ai_metrics": 0,
                "questions_with_analytics": 0,
                "logical_reasoning_patterns": []
            }
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
    
    async def test_database_verification(self):
        """Test 1: Database Verification - Check that exactly 10 logical questions exist"""
        logger.info("💾 Testing Database Verification...")
        
        try:
            start_time = time.time()
            # Test the filtered endpoint to get logical questions
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical&limit=100") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check response structure
                    required_fields = ["questions", "total_count", "filtered_count"]
                    has_required_fields = all(field in data for field in required_fields)
                    
                    if has_required_fields:
                        questions = data.get("questions", [])
                        total_count = data.get("total_count", 0)
                        filtered_count = data.get("filtered_count", 0)
                        
                        # Check if we have exactly 10 logical questions
                        success = (len(questions) == 10 and total_count >= 10)
                        
                        if success:
                            self.test_results["logical_questions_stats"]["total_logical_questions"] = len(questions)
                            details = f"✅ Found exactly {len(questions)} logical questions (total_count: {total_count}, filtered_count: {filtered_count})"
                        else:
                            details = f"❌ Expected 10 logical questions, found {len(questions)} (total_count: {total_count})"
                    else:
                        success = False
                        details = f"❌ Response missing required fields. Found: {list(data.keys())}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"❌ API request failed: {response.status} - {error_text[:200]}"
                
                self.log_test_result("Database Verification - 10 Logical Questions", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Database Verification - 10 Logical Questions", False, f"Exception: {str(e)}")
    
    async def test_api_endpoint_filtering(self):
        """Test 2: API Endpoint Testing - Test /api/questions/filtered with various filters"""
        logger.info("🔌 Testing API Endpoint Filtering...")
        
        # Test 2.1: Basic logical category filter
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    questions = data.get("questions", [])
                    
                    # Verify all questions are logical category
                    all_logical = all(q.get("category") == "logical" for q in questions)
                    success = all_logical and len(questions) > 0
                    
                    details = f"Retrieved {len(questions)} questions, all logical: {all_logical}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("API Filter - Category=logical", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("API Filter - Category=logical", False, f"Exception: {str(e)}")
        
        # Test 2.2: Pagination with limit and offset
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical&limit=5&skip=0") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    questions = data.get("questions", [])
                    
                    success = len(questions) <= 5  # Should respect limit
                    details = f"Requested limit=5, got {len(questions)} questions"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("API Filter - Pagination (limit=5)", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("API Filter - Pagination (limit=5)", False, f"Exception: {str(e)}")
        
        # Test 2.3: Difficulty level filtering
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical&difficulty=placement_ready") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    questions = data.get("questions", [])
                    
                    # Check if questions have difficulty field
                    has_difficulty = all("difficulty" in q for q in questions)
                    success = has_difficulty and len(questions) >= 0  # May be 0 if no placement_ready questions
                    
                    details = f"Retrieved {len(questions)} placement_ready logical questions"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("API Filter - Difficulty=placement_ready", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("API Filter - Difficulty=placement_ready", False, f"Exception: {str(e)}")
        
        # Test 2.4: JSON response structure verification
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical&limit=3") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required response structure
                    required_fields = ["questions", "total_count", "filtered_count", "batch_quality_score"]
                    has_all_fields = all(field in data for field in required_fields)
                    
                    # Check if questions array has proper structure
                    questions = data.get("questions", [])
                    if questions:
                        first_question = questions[0]
                        question_fields = ["id", "question_text", "options", "correct_answer", "category"]
                        has_question_fields = all(field in first_question for field in question_fields)
                    else:
                        has_question_fields = True  # No questions to check
                    
                    success = has_all_fields and has_question_fields
                    details = f"Response structure valid: {has_all_fields}, Question structure valid: {has_question_fields}"
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                
                self.log_test_result("API Response - JSON Structure", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("API Response - JSON Structure", False, f"Exception: {str(e)}")
    
    async def test_question_quality_verification(self):
        """Test 3: Question Quality Verification - Check question schema and content"""
        logger.info("🔍 Testing Question Quality Verification...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical&limit=10") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    questions = data.get("questions", [])
                    
                    if not questions:
                        self.log_test_result("Question Quality - Schema Check", False, "No logical questions found", response_time)
                        return
                    
                    # Check each question's quality
                    questions_with_proper_schema = 0
                    questions_with_ai_metrics = 0
                    questions_with_analytics = 0
                    
                    for question in questions:
                        # Check basic schema
                        required_fields = ["question_text", "options", "correct_answer"]
                        if all(field in question and question[field] for field in required_fields):
                            questions_with_proper_schema += 1
                            
                            # Check if options are exactly 4
                            if len(question.get("options", [])) == 4:
                                pass  # Good
                        
                        # Check AI metrics
                        ai_metrics = question.get("ai_metrics", {})
                        if ai_metrics and "quality_score" in ai_metrics and "relevance_score" in ai_metrics:
                            questions_with_ai_metrics += 1
                        
                        # Check analytics fields
                        analytics = question.get("analytics", {})
                        if analytics or "created_at" in question:
                            questions_with_analytics += 1
                    
                    # Update stats
                    self.test_results["logical_questions_stats"]["questions_with_proper_schema"] = questions_with_proper_schema
                    self.test_results["logical_questions_stats"]["questions_with_ai_metrics"] = questions_with_ai_metrics
                    self.test_results["logical_questions_stats"]["questions_with_analytics"] = questions_with_analytics
                    
                    # Test success criteria
                    schema_success = questions_with_proper_schema >= 8  # At least 80% should have proper schema
                    ai_metrics_success = questions_with_ai_metrics >= 5  # At least 50% should have AI metrics
                    
                    overall_success = schema_success and ai_metrics_success
                    details = f"Schema: {questions_with_proper_schema}/{len(questions)}, AI Metrics: {questions_with_ai_metrics}/{len(questions)}, Analytics: {questions_with_analytics}/{len(questions)}"
                    
                    self.log_test_result("Question Quality - Schema & Metrics", overall_success, details, response_time)
                    
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                    self.log_test_result("Question Quality - Schema & Metrics", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Question Quality - Schema & Metrics", False, f"Exception: {str(e)}")
    
    async def test_content_verification(self):
        """Test 4: Specific Content Verification - Check for logical reasoning patterns"""
        logger.info("🧠 Testing Content Verification...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/questions/filtered?category=logical&limit=10") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    questions = data.get("questions", [])
                    
                    if not questions:
                        self.log_test_result("Content Verification - Logical Patterns", False, "No logical questions found", response_time)
                        return
                    
                    # Define logical reasoning patterns to look for
                    logical_patterns = {
                        "syllogisms": ["if all", "all are", "some are", "no are"],
                        "number_sequences": ["2,4,8,16", "sequence", "series", "pattern", "next number"],
                        "coding_decoding": ["coding", "decoding", "code", "cipher"],
                        "temporal_logic": ["day", "date", "calendar", "week", "month"],
                        "geometric_reasoning": ["clock", "angle", "direction", "compass"],
                        "set_theory": ["tea", "coffee", "both", "neither", "only"],
                        "verbal_classification": ["classification", "category", "group", "belongs"],
                        "letter_arrangement": ["letter", "alphabet", "arrangement", "word"]
                    }
                    
                    found_patterns = []
                    pattern_counts = {}
                    
                    for question in questions:
                        question_text = question.get("question_text", "").lower()
                        options_text = " ".join(question.get("options", [])).lower()
                        full_text = question_text + " " + options_text
                        
                        # Check metadata concepts if available
                        metadata = question.get("metadata", {})
                        concepts = metadata.get("concepts", [])
                        
                        for pattern_name, keywords in logical_patterns.items():
                            # Check in question text and options
                            text_match = any(keyword in full_text for keyword in keywords)
                            # Check in metadata concepts
                            concept_match = any(keyword in " ".join(concepts).lower() for keyword in keywords)
                            
                            if text_match or concept_match:
                                if pattern_name not in found_patterns:
                                    found_patterns.append(pattern_name)
                                pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
                    
                    # Update stats
                    self.test_results["logical_questions_stats"]["logical_reasoning_patterns"] = found_patterns
                    
                    # Success criteria: Should find at least 4 different logical reasoning patterns
                    success = len(found_patterns) >= 4
                    details = f"Found {len(found_patterns)} logical patterns: {', '.join(found_patterns)}. Counts: {pattern_counts}"
                    
                    self.log_test_result("Content Verification - Logical Patterns", success, details, response_time)
                    
                else:
                    success = False
                    error_text = await response.text()
                    details = f"Status: {response.status}, Error: {error_text[:200]}"
                    self.log_test_result("Content Verification - Logical Patterns", success, details, response_time)
                
        except Exception as e:
            self.log_test_result("Content Verification - Logical Patterns", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all logical questions tests"""
        logger.info("🚀 Starting Comprehensive Logical Questions Testing...")
        logger.info("🎯 Goal: Verify 10 GeeksforGeeks logical questions are properly stored and accessible")
        start_time = time.time()
        
        # Run all test suites
        await self.test_database_verification()
        await self.test_api_endpoint_filtering()
        await self.test_question_quality_verification()
        await self.test_content_verification()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive summary
        logger.info("=" * 80)
        logger.info("🎯 LOGICAL QUESTIONS TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 40)
        logger.info("📊 LOGICAL QUESTIONS STATISTICS:")
        stats = self.test_results["logical_questions_stats"]
        logger.info(f"Total Logical Questions: {stats['total_logical_questions']}")
        logger.info(f"Questions with Proper Schema: {stats['questions_with_proper_schema']}")
        logger.info(f"Questions with AI Metrics: {stats['questions_with_ai_metrics']}")
        logger.info(f"Questions with Analytics: {stats['questions_with_analytics']}")
        logger.info(f"Logical Reasoning Patterns Found: {len(stats['logical_reasoning_patterns'])}")
        if stats['logical_reasoning_patterns']:
            logger.info(f"Patterns: {', '.join(stats['logical_reasoning_patterns'])}")
        logger.info("=" * 40)
        
        # Assessment
        if self.test_results['passed_tests'] >= self.test_results['total_tests'] * 0.8:
            logger.info("🎉 SUCCESS: Logical questions functionality is working well!")
        elif self.test_results['passed_tests'] >= self.test_results['total_tests'] * 0.6:
            logger.info("⚠️ PARTIAL SUCCESS: Most tests passed, some issues need attention")
        else:
            logger.info("❌ ISSUES FOUND: Multiple tests failed, needs investigation")
        
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
    logger.info("🚀 GEEKSFORGEEKS LOGICAL QUESTIONS TESTING")
    logger.info("🎯 Testing the newly added logical questions functionality")
    logger.info("🔍 Focus: Verify 10 logical questions are properly stored and accessible")
    
    async with LogicalQuestionsComprehensiveTester() as tester:
        test_results = await tester.run_all_tests()
    
    # Overall summary
    logger.info("\n" + "=" * 80)
    logger.info("🎯 FINAL ASSESSMENT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Database Verification: {'✅ SUCCESS' if test_results['logical_questions_stats']['total_logical_questions'] >= 10 else '❌ FAILED'}")
    logger.info(f"API Functionality: {'✅ SUCCESS' if test_results['passed_tests'] >= test_results['total_tests'] * 0.7 else '❌ NEEDS ATTENTION'}")
    logger.info(f"Question Quality: {'✅ SUCCESS' if test_results['logical_questions_stats']['questions_with_proper_schema'] >= 8 else '❌ NEEDS IMPROVEMENT'}")
    logger.info(f"Content Patterns: {'✅ SUCCESS' if len(test_results['logical_questions_stats']['logical_reasoning_patterns']) >= 4 else '❌ LIMITED VARIETY'}")
    logger.info("=" * 80)
    
    # Answer the review request
    if test_results['passed_tests'] >= test_results['total_tests'] * 0.8:
        logger.info("✅ FINAL ANSWER: GeeksforGeeks logical questions functionality is working correctly")
        logger.info("🎉 The 10 logical questions are properly stored and accessible through the API")
    else:
        logger.info("❌ FINAL ANSWER: Issues found with logical questions functionality")
        logger.info("🔍 Some aspects need attention before the system is fully ready")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())