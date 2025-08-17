#!/usr/bin/env python3
"""
Focused Testing for TASK 9 and TASK 10
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import uuid

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_task_9_ai_content_processing():
    """Test TASK 9 - AI Content Processing Pipeline"""
    logger.info("🤖 Testing TASK 9 - AI Content Processing Pipeline")
    
    try:
        from services.scraping_ai_processor import ScrapingAIProcessor, create_scraping_ai_processor
        from models.scraping_models import RawExtractedQuestion, ContentExtractionMethod
        
        # Test 1: Service initialization
        logger.info("1. Testing service initialization...")
        processor = create_scraping_ai_processor()
        logger.info(f"✅ ScrapingAIProcessor initialized successfully")
        
        # Test 2: Processing statistics
        logger.info("2. Testing processing statistics...")
        stats = processor.get_processing_statistics()
        logger.info(f"✅ Processing statistics: {stats['processing_stats']['total_processed']} processed")
        
        # Test 3: Single question processing
        logger.info("3. Testing single question processing...")
        raw_question = RawExtractedQuestion(
            id=str(uuid.uuid4()),
            source_id="test_source",
            source_url="https://test.com/question1",
            raw_question_text="What is 25% of 200?",
            raw_options=["A) 40", "B) 50", "C) 60", "D) 70"],
            raw_correct_answer="B) 50",
            extraction_method=ContentExtractionMethod.SELENIUM,
            extraction_confidence=0.95,
            completeness_score=0.90,
            detected_category="quantitative",
            page_number=1,
            extraction_timestamp=datetime.utcnow()
        )
        
        processed_result = await processor.process_raw_question(raw_question)
        if isinstance(processed_result, tuple) and len(processed_result) == 2:
            processed_question, enhanced_question = processed_result
            logger.info(f"✅ Single question processed: Quality={processed_question.quality_score:.1f}, Gate={processed_question.quality_gate_result.value}")
        else:
            logger.error(f"❌ Unexpected result format: {type(processed_result)}")
            return False
        
        # Test 4: Batch processing (5 questions for quick test)
        logger.info("4. Testing batch processing...")
        raw_questions = []
        for i in range(5):
            raw_q = RawExtractedQuestion(
                id=str(uuid.uuid4()),
                source_id=f"batch_test_{i}",
                source_url=f"https://test.com/batch/{i+1}",
                raw_question_text=f"Calculate {10 + i*5}% of {100 + i*20}",
                raw_options=[f"A) {10 + i*5}", f"B) {15 + i*5}", f"C) {20 + i*5}", f"D) {25 + i*5}"],
                raw_correct_answer=f"B) {15 + i*5}",
                extraction_method=ContentExtractionMethod.CSS_SELECTOR,
                extraction_confidence=0.85 + i*0.02,
                completeness_score=0.80 + i*0.03,
                detected_category="quantitative",
                page_number=1,
                extraction_timestamp=datetime.utcnow()
            )
            raw_questions.append(raw_q)
        
        batch_results = await processor.batch_process_questions(raw_questions, batch_size=3)
        if batch_results.get("status") == "completed":
            stats = batch_results["statistics"]
            logger.info(f"✅ Batch processing completed: {stats['processed_successfully']}/{stats['total_questions']} questions")
        else:
            logger.error(f"❌ Batch processing failed: {batch_results.get('error', 'Unknown error')}")
            return False
        
        logger.info("🎉 TASK 9 - AI Content Processing Pipeline: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ TASK 9 failed: {str(e)}")
        return False

async def test_task_10_duplicate_detection():
    """Test TASK 10 - Advanced Duplicate Detection System"""
    logger.info("🔍 Testing TASK 10 - Advanced Duplicate Detection System")
    
    try:
        from services.duplicate_detection_service import AdvancedDuplicateDetector, create_duplicate_detector
        
        # Test 1: Service initialization
        logger.info("1. Testing service initialization...")
        detector = create_duplicate_detector(similarity_threshold=0.85)
        logger.info(f"✅ AdvancedDuplicateDetector initialized with threshold: {detector.similarity_threshold}")
        
        # Test 2: Single duplicate detection
        logger.info("2. Testing single duplicate detection...")
        new_question = {
            "id": "test_q1",
            "question_text": "What is 25% of 100?",
            "source": "test_source_1",
            "quality_score": 85.0
        }
        
        existing_questions = [
            {
                "id": "existing_q1",
                "question_text": "Calculate 25% of 100",
                "source": "test_source_2",
                "quality_score": 80.0
            },
            {
                "id": "existing_q2", 
                "question_text": "Find the area of a circle with radius 5",
                "source": "test_source_1",
                "quality_score": 90.0
            }
        ]
        
        duplicate_result = await detector.detect_duplicates_single(new_question, existing_questions)
        if isinstance(duplicate_result, dict) and "is_duplicate" in duplicate_result:
            logger.info(f"✅ Single duplicate detection: Is duplicate={duplicate_result['is_duplicate']}, Confidence={duplicate_result.get('detection_confidence', 0):.3f}")
        else:
            logger.error(f"❌ Invalid duplicate detection result: {duplicate_result}")
            return False
        
        # Test 3: Batch duplicate detection
        logger.info("3. Testing batch duplicate detection...")
        test_questions = [
            {"id": "q1", "question_text": "What is 25% of 200?", "source": "source_a", "quality_score": 85.0},
            {"id": "q2", "question_text": "Calculate 25% of 200", "source": "source_b", "quality_score": 80.0},
            {"id": "q3", "question_text": "Find 25 percent of 200", "source": "source_c", "quality_score": 82.0},
            {"id": "q4", "question_text": "Solve the equation 2x + 5 = 15", "source": "source_a", "quality_score": 90.0},
            {"id": "q5", "question_text": "What is the capital of France?", "source": "source_b", "quality_score": 75.0}
        ]
        
        batch_results = await detector.batch_duplicate_detection(test_questions)
        if batch_results.get("status") == "completed":
            results = batch_results["results"]
            logger.info(f"✅ Batch duplicate detection: Found {len(results.get('clusters', []))} clusters, {len(results.get('duplicate_pairs', []))} duplicate pairs")
        else:
            logger.error(f"❌ Batch duplicate detection failed: {batch_results.get('error', 'Unknown error')}")
            return False
        
        # Test 4: Cross-source duplicate analysis
        logger.info("4. Testing cross-source duplicate analysis...")
        source_questions = {
            "source_a": [
                {"id": "a1", "question_text": "What is simple interest on Rs. 1000 at 10% for 2 years?", "source": "source_a", "quality_score": 85.0},
                {"id": "a2", "question_text": "Find 20% of 500", "source": "source_a", "quality_score": 80.0}
            ],
            "source_b": [
                {"id": "b1", "question_text": "Calculate simple interest on Rs. 1000 at 10% for 2 years", "source": "source_b", "quality_score": 87.0},
                {"id": "b2", "question_text": "What is 20 percent of 500?", "source": "source_b", "quality_score": 82.0}
            ]
        }
        
        cross_source_results = await detector.cross_source_duplicate_analysis(source_questions)
        if isinstance(cross_source_results, dict) and "total_cross_source_duplicates" in cross_source_results:
            total_duplicates = cross_source_results["total_cross_source_duplicates"]
            logger.info(f"✅ Cross-source analysis: Found {total_duplicates} cross-source duplicates")
        else:
            logger.error(f"❌ Cross-source analysis failed: {cross_source_results.get('error', 'Unknown error')}")
            return False
        
        # Test 5: Dashboard data generation
        logger.info("5. Testing duplicate management dashboard...")
        dashboard_data = detector.get_duplicate_management_dashboard()
        if isinstance(dashboard_data, dict) and "detection_statistics" in dashboard_data:
            stats = dashboard_data["detection_statistics"]
            logger.info(f"✅ Dashboard data: {stats['total_questions_processed']} questions processed, {stats['duplicates_detected']} duplicates detected")
        else:
            logger.error(f"❌ Dashboard generation failed: {dashboard_data.get('error', 'Unknown error')}")
            return False
        
        logger.info("🎉 TASK 10 - Advanced Duplicate Detection System: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ TASK 10 failed: {str(e)}")
        return False

async def main():
    """Main test execution"""
    logger.info("🚀 Starting TASK 9 & 10 Focused Testing")
    logger.info("=" * 60)
    
    # Test TASK 9
    task_9_success = await test_task_9_ai_content_processing()
    
    logger.info("")
    
    # Test TASK 10
    task_10_success = await test_task_10_duplicate_detection()
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎯 TESTING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"TASK 9 - AI Content Processing Pipeline: {'✅ PASSED' if task_9_success else '❌ FAILED'}")
    logger.info(f"TASK 10 - Advanced Duplicate Detection System: {'✅ PASSED' if task_10_success else '❌ FAILED'}")
    
    overall_success = task_9_success and task_10_success
    logger.info(f"Overall Result: {'🎉 ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    logger.info("=" * 60)
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())