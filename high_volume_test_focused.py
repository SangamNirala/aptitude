#!/usr/bin/env python3
"""
High-Volume Scraping System Testing - Focused on Review Request
Tests the high-volume scraping system endpoints with focus on quick extraction and API validation
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

class HighVolumeScrapingTester:
    """Focused tester for High-Volume Scraping System"""
    
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
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

async def test_high_volume_scraping_system():
    """
    HIGH-VOLUME SCRAPING SYSTEM TESTING - FOCUSED ON REVIEW REQUEST
    Test the high-volume scraping system with focus on quick extraction and API validation
    """
    logger.info("🎯 HIGH-VOLUME SCRAPING SYSTEM TESTING")
    logger.info("=" * 80)
    logger.info("TESTING REQUIREMENTS FROM REVIEW REQUEST:")
    logger.info("1. Quick Extraction Tests: Test both IndiaBix and GeeksforGeeks quick extraction endpoints")
    logger.info("2. High-Volume System Status: Verify the system status endpoint is working")
    logger.info("3. High-Volume Extraction Start: Test starting extraction with small parameters (50-100 questions)")
    logger.info("4. Progress Monitoring: If extraction starts successfully, test status monitoring")
    logger.info("5. Active Extractions: Test the active extractions listing endpoint")
    logger.info("6. API Validation: Check for API validation errors (estimated_duration_minutes field)")
    logger.info("7. Chrome/Chromium Integration: Verify drivers initialize properly")
    logger.info("=" * 80)
    
    test_results = {
        "system_status_test": False,
        "quick_test_indiabix": False,
        "quick_test_geeksforgeeks": False,
        "high_volume_start_test": False,
        "progress_monitoring_test": False,
        "active_extractions_test": False,
        "api_validation_test": False,
        "chrome_integration_test": False,
        "extraction_id": None,
        "indiabix_questions": 0,
        "geeksforgeeks_questions": 0,
        "errors_found": []
    }
    
    async with HighVolumeScrapingTester() as tester:
        # Test 1: System Status Check
        logger.info("🔧 TEST 1: High-Volume System Status - GET /api/high-volume-scraping/system-status")
        try:
            start_time = time.time()
            async with tester.session.get(f"{tester.base_url}/high-volume-scraping/system-status") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify required fields in system status
                    required_fields = ["system_status", "capabilities", "current_usage", "performance_metrics"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        capabilities = data.get("capabilities", {})
                        supported_sources = capabilities.get("supported_sources", [])
                        
                        # Check if both required sources are supported
                        has_indiabix = "indiabix" in supported_sources
                        has_geeksforgeeks = "geeksforgeeks" in supported_sources
                        
                        if has_indiabix and has_geeksforgeeks:
                            test_results["system_status_test"] = True
                            logger.info(f"✅ System status check PASSED - Status: {data.get('system_status')}, Sources: {supported_sources}")
                        else:
                            test_results["errors_found"].append(f"Missing required sources - IndiaBix: {has_indiabix}, GeeksforGeeks: {has_geeksforgeeks}")
                            logger.error(f"❌ Missing required sources - IndiaBix: {has_indiabix}, GeeksforGeeks: {has_geeksforgeeks}")
                    else:
                        test_results["errors_found"].append(f"System status missing fields: {missing_fields}")
                        logger.error(f"❌ System status missing fields: {missing_fields}")
                else:
                    error_text = await response.text()
                    test_results["errors_found"].append(f"System status failed: {response.status} - {error_text[:200]}")
                    logger.error(f"❌ System status failed: {response.status} - {error_text[:200]}")
                    
        except Exception as e:
            test_results["errors_found"].append(f"System status exception: {str(e)}")
            logger.error(f"❌ System status exception: {e}")
        
        # Test 2: Quick Test Extraction - IndiaBix (CRITICAL TEST)
        logger.info("🔧 TEST 2: Quick Test Extraction - IndiaBix (should return actual questions, not 0)")
        try:
            payload = {"source": "indiabix", "max_questions": 12}
            start_time = time.time()
            
            async with tester.session.post(f"{tester.base_url}/high-volume-scraping/test-extraction", json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify test extraction response format
                    if "success" in data and "questions_extracted" in data:
                        questions_extracted = data.get("questions_extracted", 0)
                        success = data.get("success", False)
                        
                        test_results["indiabix_questions"] = questions_extracted
                        
                        if success and questions_extracted > 0:  # Should return actual questions, not 0
                            test_results["quick_test_indiabix"] = True
                            logger.info(f"✅ IndiaBix quick test PASSED - Extracted: {questions_extracted} questions (SUCCESS: Not 0!)")
                        else:
                            test_results["errors_found"].append(f"IndiaBix test returned 0 questions: {questions_extracted} questions, success: {success}")
                            logger.error(f"❌ IndiaBix test returned 0 questions: {questions_extracted} questions, success: {success}")
                            
                            # Log additional error details
                            if "error" in data:
                                logger.error(f"   Error details: {data['error']}")
                                test_results["errors_found"].append(f"IndiaBix error: {data['error']}")
                    else:
                        test_results["errors_found"].append("IndiaBix test response missing required fields")
                        logger.error("❌ IndiaBix test response missing required fields")
                else:
                    error_text = await response.text()
                    test_results["errors_found"].append(f"IndiaBix test failed: {response.status} - {error_text[:200]}")
                    logger.error(f"❌ IndiaBix test failed: {response.status} - {error_text[:200]}")
                    
        except Exception as e:
            test_results["errors_found"].append(f"IndiaBix test exception: {str(e)}")
            logger.error(f"❌ IndiaBix test exception: {e}")
        
        # Test 3: Quick Test Extraction - GeeksforGeeks (CRITICAL TEST)
        logger.info("🔧 TEST 3: Quick Test Extraction - GeeksforGeeks (should return actual questions, not 0)")
        try:
            payload = {"source": "geeksforgeeks", "max_questions": 8}
            start_time = time.time()
            
            async with tester.session.post(f"{tester.base_url}/high-volume-scraping/test-extraction", json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify test extraction response format
                    if "success" in data and "questions_extracted" in data:
                        questions_extracted = data.get("questions_extracted", 0)
                        success = data.get("success", False)
                        
                        test_results["geeksforgeeks_questions"] = questions_extracted
                        
                        if success and questions_extracted > 0:  # Should return actual questions, not 0
                            test_results["quick_test_geeksforgeeks"] = True
                            logger.info(f"✅ GeeksforGeeks quick test PASSED - Extracted: {questions_extracted} questions (SUCCESS: Not 0!)")
                        else:
                            test_results["errors_found"].append(f"GeeksforGeeks test returned 0 questions: {questions_extracted} questions, success: {success}")
                            logger.error(f"❌ GeeksforGeeks test returned 0 questions: {questions_extracted} questions, success: {success}")
                            
                            # Log additional error details
                            if "error" in data:
                                logger.error(f"   Error details: {data['error']}")
                                test_results["errors_found"].append(f"GeeksforGeeks error: {data['error']}")
                    else:
                        test_results["errors_found"].append("GeeksforGeeks test response missing required fields")
                        logger.error("❌ GeeksforGeeks test response missing required fields")
                else:
                    error_text = await response.text()
                    test_results["errors_found"].append(f"GeeksforGeeks test failed: {response.status} - {error_text[:200]}")
                    logger.error(f"❌ GeeksforGeeks test failed: {response.status} - {error_text[:200]}")
                    
        except Exception as e:
            test_results["errors_found"].append(f"GeeksforGeeks test exception: {str(e)}")
            logger.error(f"❌ GeeksforGeeks test exception: {e}")
        
        # Test 4: Start High-Volume Extraction (Small Parameters - 50-100 questions)
        logger.info("🔧 TEST 4: Start High-Volume Extraction (Small Parameters - 75 questions)")
        try:
            payload = {
                "target_questions_total": 75,  # Small parameter as requested
                "target_questions_per_source": 40,
                "batch_size": 10,
                "max_concurrent_extractors": 2,
                "quality_threshold": 70.0,
                "enable_real_time_validation": True,
                "enable_duplicate_detection": False  # Disable to focus on extraction
            }
            start_time = time.time()
            
            async with tester.session.post(f"{tester.base_url}/high-volume-scraping/start-extraction", json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API validation issues (estimated_duration_minutes field)
                    if "extraction_id" in data and "status" in data:
                        test_results["extraction_id"] = data.get("extraction_id")
                        test_results["high_volume_start_test"] = True
                        
                        # Check estimated_duration_minutes field (should be string as per fix)
                        estimated_duration = data.get("estimated_duration_minutes")
                        if estimated_duration is not None:
                            test_results["api_validation_test"] = True
                            logger.info(f"✅ High-volume extraction started successfully - ID: {data.get('extraction_id')}")
                            logger.info(f"   Estimated duration: {estimated_duration} minutes")
                        else:
                            test_results["errors_found"].append("Missing estimated_duration_minutes field")
                            logger.warning("⚠️ Missing estimated_duration_minutes field")
                    else:
                        test_results["errors_found"].append("High-volume start response missing required fields")
                        logger.error("❌ High-volume start response missing required fields")
                else:
                    error_text = await response.text()
                    test_results["errors_found"].append(f"High-volume start failed: {response.status} - {error_text[:200]}")
                    logger.error(f"❌ High-volume start failed: {response.status} - {error_text[:200]}")
                    
                    # Check for specific API validation errors
                    if response.status == 422:
                        logger.error("🚨 API VALIDATION ERROR (422) - Check field validation issues")
                        test_results["errors_found"].append("API validation error (422) - field validation issues")
                    elif response.status == 500:
                        logger.error("🚨 INTERNAL SERVER ERROR (500) - Backend processing issues")
                        test_results["errors_found"].append("Internal server error (500) - backend processing issues")
                    
        except Exception as e:
            test_results["errors_found"].append(f"High-volume start exception: {str(e)}")
            logger.error(f"❌ High-volume start exception: {e}")
        
        # Test 5: Progress Monitoring (if extraction started successfully)
        if test_results["extraction_id"]:
            logger.info("🔧 TEST 5: Progress Monitoring - GET /api/high-volume-scraping/status/{extraction_id}")
            try:
                extraction_id = test_results["extraction_id"]
                
                # Wait a moment for extraction to initialize
                await asyncio.sleep(5)
                
                async with tester.session.get(f"{tester.base_url}/high-volume-scraping/status/{extraction_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verify progress response format
                        required_fields = ["extraction_id", "status", "progress_percentage", "total_questions_extracted"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if not missing_fields:
                            test_results["progress_monitoring_test"] = True
                            logger.info(f"✅ Progress monitoring PASSED - Status: {data.get('status')}, Progress: {data.get('progress_percentage'):.1f}%")
                            logger.info(f"   Questions extracted: {data.get('total_questions_extracted')}")
                        else:
                            test_results["errors_found"].append(f"Progress response missing fields: {missing_fields}")
                            logger.error(f"❌ Progress response missing fields: {missing_fields}")
                    else:
                        error_text = await response.text()
                        test_results["errors_found"].append(f"Progress monitoring failed: {response.status} - {error_text[:200]}")
                        logger.error(f"❌ Progress monitoring failed: {response.status} - {error_text[:200]}")
                        
            except Exception as e:
                test_results["errors_found"].append(f"Progress monitoring exception: {str(e)}")
                logger.error(f"❌ Progress monitoring exception: {e}")
        else:
            logger.warning("⚠️ Skipping progress monitoring - no extraction ID available")
        
        # Test 6: Active Extractions Listing
        logger.info("🔧 TEST 6: Active Extractions Listing - GET /api/high-volume-scraping/active-extractions")
        try:
            async with tester.session.get(f"{tester.base_url}/high-volume-scraping/active-extractions") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify active extractions response format
                    if "active_extractions" in data and "total_extractions" in data:
                        test_results["active_extractions_test"] = True
                        active_count = len(data.get("active_extractions", []))
                        total_count = data.get("total_extractions", 0)
                        logger.info(f"✅ Active extractions PASSED - Active: {active_count}, Total: {total_count}")
                    else:
                        test_results["errors_found"].append("Active extractions response missing required fields")
                        logger.error("❌ Active extractions response missing required fields")
                else:
                    error_text = await response.text()
                    test_results["errors_found"].append(f"Active extractions failed: {response.status} - {error_text[:200]}")
                    logger.error(f"❌ Active extractions failed: {response.status} - {error_text[:200]}")
                    
        except Exception as e:
            test_results["errors_found"].append(f"Active extractions exception: {str(e)}")
            logger.error(f"❌ Active extractions exception: {e}")
        
        # Chrome/Chromium Integration Test (implicit in quick tests)
        if test_results["quick_test_indiabix"] or test_results["quick_test_geeksforgeeks"]:
            test_results["chrome_integration_test"] = True
            logger.info("✅ Chrome/Chromium integration working - drivers initialized successfully in quick tests")
        else:
            logger.error("❌ Chrome/Chromium integration issues - no successful driver initialization detected")
    
    # FINAL ASSESSMENT
    logger.info("=" * 80)
    logger.info("🎯 HIGH-VOLUME SCRAPING SYSTEM TEST RESULTS")
    logger.info("=" * 80)
    
    total_tests = 6
    passed_tests = sum([
        test_results["system_status_test"],
        test_results["quick_test_indiabix"],
        test_results["quick_test_geeksforgeeks"],
        test_results["high_volume_start_test"],
        test_results["progress_monitoring_test"],
        test_results["active_extractions_test"]
    ])
    
    success_rate = (passed_tests / total_tests) * 100
    
    logger.info(f"📊 OVERALL RESULTS:")
    logger.info(f"   • System Status Check: {'✅ PASSED' if test_results['system_status_test'] else '❌ FAILED'}")
    logger.info(f"   • IndiaBix Quick Test: {'✅ PASSED' if test_results['quick_test_indiabix'] else '❌ FAILED'} ({test_results['indiabix_questions']} questions)")
    logger.info(f"   • GeeksforGeeks Quick Test: {'✅ PASSED' if test_results['quick_test_geeksforgeeks'] else '❌ FAILED'} ({test_results['geeksforgeeks_questions']} questions)")
    logger.info(f"   • High-Volume Start: {'✅ PASSED' if test_results['high_volume_start_test'] else '❌ FAILED'}")
    logger.info(f"   • Progress Monitoring: {'✅ PASSED' if test_results['progress_monitoring_test'] else '❌ FAILED'}")
    logger.info(f"   • Active Extractions: {'✅ PASSED' if test_results['active_extractions_test'] else '❌ FAILED'}")
    logger.info(f"   • API Validation: {'✅ PASSED' if test_results['api_validation_test'] else '❌ FAILED'}")
    logger.info(f"   • Chrome Integration: {'✅ PASSED' if test_results['chrome_integration_test'] else '❌ FAILED'}")
    logger.info(f"   • SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    # Critical Issues Summary
    critical_issues = []
    if test_results["indiabix_questions"] == 0:
        critical_issues.append("IndiaBix quick test returned 0 questions (should return actual questions)")
    if test_results["geeksforgeeks_questions"] == 0:
        critical_issues.append("GeeksforGeeks quick test returned 0 questions (should return actual questions)")
    if not test_results["api_validation_test"]:
        critical_issues.append("API validation issues found (estimated_duration_minutes field)")
    if not test_results["high_volume_start_test"]:
        critical_issues.append("High-volume extraction start failed (500/422 errors)")
    
    if critical_issues:
        logger.info("🚨 CRITICAL ISSUES FOUND:")
        for issue in critical_issues:
            logger.info(f"   - {issue}")
    
    if test_results["errors_found"]:
        logger.info("❌ DETAILED ERRORS:")
        for error in test_results["errors_found"]:
            logger.info(f"   - {error}")
    
    logger.info("=" * 80)
    
    return test_results

# Main execution
if __name__ == "__main__":
    asyncio.run(test_high_volume_scraping_system())