#!/usr/bin/env python3
"""
High-Volume Scraping System Test
Comprehensive test script for validating the 10,000 question extraction system
"""

import asyncio
import logging
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "https://question-vault.preview.emergentagent.com"  # Backend URL
API_PREFIX = "/api"

class HighVolumeScrapingTester:
    """Comprehensive tester for high-volume scraping system"""
    
    def __init__(self):
        self.base_url = f"{BASE_URL}{API_PREFIX}"
        self.session = requests.Session()
        self.test_results = {}
        
    def test_api_health(self) -> bool:
        """Test basic API health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ API Health: {health_data.get('status', 'unknown')}")
                return True
            else:
                logger.error(f"❌ API Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API Health check error: {e}")
            return False
    
    def test_high_volume_system_status(self) -> Dict[str, Any]:
        """Test high-volume scraping system status"""
        try:
            response = self.session.get(f"{self.base_url}/high-volume-scraping/system-status")
            
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"✅ High-Volume System Status: {status_data.get('system_status')}")
                logger.info(f"  Supported Sources: {status_data.get('capabilities', {}).get('supported_sources')}")
                logger.info(f"  Max Questions: {status_data.get('capabilities', {}).get('max_questions_per_extraction')}")
                return status_data
            else:
                logger.error(f"❌ System status check failed: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ System status error: {e}")
            return {}
    
    def test_quick_extraction(self, source: str = "indiabix", max_questions: int = 10) -> Dict[str, Any]:
        """Test quick extraction functionality"""
        try:
            logger.info(f"🧪 Testing quick extraction for {source} (max {max_questions} questions)")
            
            test_request = {
                "source": source,
                "max_questions": max_questions
            }
            
            response = self.session.post(
                f"{self.base_url}/high-volume-scraping/test-extraction",
                json=test_request,
                timeout=120  # 2 minute timeout for test
            )
            
            if response.status_code == 200:
                result = response.json()
                
                logger.info(f"✅ Quick extraction test completed")
                logger.info(f"  Success: {result.get('success')}")
                logger.info(f"  Questions Extracted: {result.get('questions_extracted', 0)}")
                logger.info(f"  Execution Time: {result.get('execution_time', 0):.2f}s")
                
                if result.get('error'):
                    logger.warning(f"  Error: {result['error']}")
                
                return result
            else:
                logger.error(f"❌ Quick extraction test failed: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Quick extraction test error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_high_volume_extraction_start(self, target_questions: int = 100) -> str:
        """Test starting a high-volume extraction"""
        try:
            logger.info(f"🚀 Testing high-volume extraction start (target: {target_questions} questions)")
            
            extraction_request = {
                "target_questions_total": target_questions,
                "target_questions_per_source": target_questions // 2,
                "batch_size": 20,
                "max_concurrent_extractors": 2,
                "quality_threshold": 70.0,
                "enable_real_time_validation": True,
                "enable_duplicate_detection": True
            }
            
            response = self.session.post(
                f"{self.base_url}/high-volume-scraping/start-extraction",
                json=extraction_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                extraction_id = result.get("extraction_id")
                
                logger.info(f"✅ High-volume extraction started")
                logger.info(f"  Extraction ID: {extraction_id}")
                logger.info(f"  Status: {result.get('status')}")
                logger.info(f"  Estimated Duration: {result.get('estimated_duration_minutes')} minutes")
                
                return extraction_id
            else:
                logger.error(f"❌ High-volume extraction start failed: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ High-volume extraction start error: {e}")
            return ""
    
    def test_extraction_status(self, extraction_id: str) -> Dict[str, Any]:
        """Test extraction status monitoring"""
        try:
            response = self.session.get(f"{self.base_url}/high-volume-scraping/status/{extraction_id}")
            
            if response.status_code == 200:
                status = response.json()
                
                logger.info(f"📊 Extraction Status:")
                logger.info(f"  Status: {status.get('status')}")
                logger.info(f"  Progress: {status.get('progress_percentage', 0):.1f}%")
                logger.info(f"  Questions Extracted: {status.get('total_questions_extracted', 0)}")
                logger.info(f"  Questions Stored: {status.get('total_questions_stored', 0)}")
                logger.info(f"  Rate: {status.get('questions_per_minute', 0):.1f} questions/minute")
                logger.info(f"  Current Source: {status.get('current_source')}")
                
                return status
            else:
                logger.error(f"❌ Status check failed: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Status check error: {e}")
            return {}
    
    def test_active_extractions(self) -> Dict[str, Any]:
        """Test active extractions listing"""
        try:
            response = self.session.get(f"{self.base_url}/high-volume-scraping/active-extractions")
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(f"📋 Active Extractions:")
                logger.info(f"  Total Extractions: {data.get('total_extractions', 0)}")
                logger.info(f"  Running: {data.get('running_extractions', 0)}")
                logger.info(f"  Completed: {data.get('completed_extractions', 0)}")
                
                for extraction in data.get('active_extractions', []):
                    logger.info(f"    ID: {extraction.get('extraction_id')[:8]}... - "
                               f"Status: {extraction.get('status')} - "
                               f"Questions: {extraction.get('questions_extracted', 0)}")
                
                return data
            else:
                logger.error(f"❌ Active extractions check failed: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Active extractions error: {e}")
            return {}
    
    def monitor_extraction_progress(self, extraction_id: str, timeout_minutes: int = 10):
        """Monitor extraction progress until completion or timeout"""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        logger.info(f"⏱️ Monitoring extraction {extraction_id[:8]}... (timeout: {timeout_minutes} minutes)")
        
        while time.time() - start_time < timeout_seconds:
            status = self.test_extraction_status(extraction_id)
            
            if not status:
                logger.warning("Status check failed, continuing...")
                time.sleep(10)
                continue
            
            extraction_status = status.get('status', '')
            
            if extraction_status in ['completed', 'failed', 'stopped']:
                logger.info(f"🏁 Extraction {extraction_status}")
                
                if extraction_status == 'completed':
                    # Get final results
                    self.test_extraction_results(extraction_id)
                
                break
            
            # Wait before next status check
            time.sleep(15)
        
        else:
            logger.warning(f"⏰ Monitoring timeout after {timeout_minutes} minutes")
    
    def test_extraction_results(self, extraction_id: str) -> Dict[str, Any]:
        """Test extraction results retrieval"""
        try:
            response = self.session.get(f"{self.base_url}/high-volume-scraping/results/{extraction_id}")
            
            if response.status_code == 200:
                results = response.json()
                
                logger.info(f"📊 Extraction Results:")
                logger.info(f"  Success: {results.get('success')}")
                logger.info(f"  Total Extracted: {results.get('total_questions_extracted', 0)}")
                logger.info(f"  Total Stored: {results.get('total_questions_stored', 0)}")
                logger.info(f"  Target Achievement: {results.get('target_achievement_percentage', 0):.1f}%")
                logger.info(f"  Execution Time: {results.get('execution_time_seconds', 0):.1f}s")
                logger.info(f"  Questions/Minute: {results.get('questions_per_minute', 0):.1f}")
                
                source_breakdown = results.get('source_breakdown', {})
                if source_breakdown:
                    logger.info(f"  Source Breakdown:")
                    for source, count in source_breakdown.items():
                        logger.info(f"    {source}: {count} questions")
                
                return results
            else:
                logger.error(f"❌ Results retrieval failed: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Results retrieval error: {e}")
            return {}
    
    def test_database_questions(self) -> Dict[str, Any]:
        """Test questions in database"""
        try:
            response = self.session.get(f"{self.base_url}/questions/filtered?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(f"📚 Database Questions:")
                logger.info(f"  Total Count: {data.get('total_count', 0)}")
                logger.info(f"  Filtered Count: {data.get('filtered_count', 0)}")
                
                questions = data.get('questions', [])
                if questions:
                    logger.info(f"  Sample Questions:")
                    for i, q in enumerate(questions[:3]):
                        logger.info(f"    {i+1}. Category: {q.get('category')} - "
                                   f"Source: {q.get('source')} - "
                                   f"Quality: {q.get('ai_metrics', {}).get('quality_score', 0)}")
                
                return data
            else:
                logger.error(f"❌ Database questions check failed: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Database questions error: {e}")
            return {}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive high-volume scraping test"""
        logger.info("🎯 Starting Comprehensive High-Volume Scraping Test")
        logger.info("=" * 60)
        
        test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "overall_success": True
        }
        
        # Test 1: API Health
        logger.info("\n1️⃣ Testing API Health...")
        health_ok = self.test_api_health()
        test_results["tests"]["api_health"] = health_ok
        if not health_ok:
            test_results["overall_success"] = False
        
        # Test 2: System Status
        logger.info("\n2️⃣ Testing System Status...")
        system_status = self.test_high_volume_system_status()
        test_results["tests"]["system_status"] = bool(system_status)
        if not system_status:
            test_results["overall_success"] = False
        
        # Test 3: Quick Extraction Test (IndiaBix)
        logger.info("\n3️⃣ Testing Quick Extraction (IndiaBix)...")
        indiabix_result = self.test_quick_extraction("indiabix", 5)
        test_results["tests"]["indiabix_quick_test"] = indiabix_result.get("success", False)
        if not indiabix_result.get("success"):
            logger.warning(f"IndiaBix quick test failed: {indiabix_result.get('error')}")
        
        # Test 4: Quick Extraction Test (GeeksforGeeks)
        logger.info("\n4️⃣ Testing Quick Extraction (GeeksforGeeks)...")
        gfg_result = self.test_quick_extraction("geeksforgeeks", 5)
        test_results["tests"]["geeksforgeeks_quick_test"] = gfg_result.get("success", False)
        if not gfg_result.get("success"):
            logger.warning(f"GeeksforGeeks quick test failed: {gfg_result.get('error')}")
        
        # Test 5: High-Volume Extraction (small scale for testing)
        if test_results["tests"]["indiabix_quick_test"] or test_results["tests"]["geeksforgeeks_quick_test"]:
            logger.info("\n5️⃣ Testing High-Volume Extraction (50 questions)...")
            extraction_id = self.test_high_volume_extraction_start(50)
            
            if extraction_id:
                test_results["tests"]["high_volume_start"] = True
                
                # Monitor progress for a limited time
                logger.info("\n6️⃣ Monitoring Extraction Progress...")
                self.monitor_extraction_progress(extraction_id, timeout_minutes=5)
                
                # Check active extractions
                logger.info("\n7️⃣ Testing Active Extractions...")
                active_extractions = self.test_active_extractions()
                test_results["tests"]["active_extractions"] = bool(active_extractions)
            else:
                test_results["tests"]["high_volume_start"] = False
                test_results["overall_success"] = False
        
        # Test 6: Database Questions
        logger.info("\n8️⃣ Testing Database Questions...")
        db_questions = self.test_database_questions()
        test_results["tests"]["database_questions"] = bool(db_questions)
        
        # Final summary
        test_results["end_time"] = datetime.now().isoformat()
        test_results["total_tests"] = len(test_results["tests"])
        test_results["passed_tests"] = sum(1 for result in test_results["tests"].values() if result)
        test_results["success_rate"] = (test_results["passed_tests"] / test_results["total_tests"]) * 100
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {test_results['total_tests']}")
        logger.info(f"Passed Tests: {test_results['passed_tests']}")
        logger.info(f"Success Rate: {test_results['success_rate']:.1f}%")
        logger.info(f"Overall Success: {'✅' if test_results['overall_success'] else '❌'}")
        
        logger.info("\nDetailed Results:")
        for test_name, result in test_results["tests"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        return test_results

def main():
    """Main test function"""
    tester = HighVolumeScrapingTester()
    
    try:
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        
        # Save results to file
        with open('/app/high_volume_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n📄 Test results saved to: /app/high_volume_test_results.json")
        
        # Return appropriate exit code
        return 0 if results["overall_success"] else 1
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Test interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        return 3

if __name__ == "__main__":
    exit(main())