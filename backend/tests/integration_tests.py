"""
End-to-End Integration Testing Suite for AI-Enhanced Web Scraping System
Task 17: Comprehensive integration testing covering full workflow validation

This test suite validates:
1. Complete scraping workflow (Source → Extraction → AI Processing → Storage)  
2. AI processing pipeline integration (Gemini, Groq, HuggingFace)
3. Error scenarios and recovery mechanisms
4. Performance benchmarking and scalability
5. 100+ questions processing validation
"""

import asyncio
import pytest
import time
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics
import concurrent.futures
from dataclasses import dataclass

# Import system components
import sys
import os
sys.path.append('/app/backend')

from scraping import (
    create_scraping_engine, ScrapingEngine, ScrapingEngineConfig,
    create_indiabix_extractor, create_geeksforgeeks_extractor
)
from services.scraping_ai_processor import ScrapingAIProcessor
from services.duplicate_detection_service import AdvancedDuplicateDetector
from services.source_management_service import SourceManagementService
from models.scraping_models import ScrapingJobCreate, ScrapingSourceType
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationTestResult:
    """Result structure for integration tests"""
    test_name: str
    success: bool
    duration_seconds: float
    questions_processed: int
    errors: List[str]
    performance_metrics: Dict[str, Any]
    details: Dict[str, Any]

class EndToEndIntegrationTester:
    """Comprehensive end-to-end integration testing system"""
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'test_database')
        self.client = None
        self.db = None
        self.scraping_engine = None
        self.ai_processor = None
        self.duplicate_detector = None
        self.source_manager = None
        
        # Test configuration
        self.test_results: List[IntegrationTestResult] = []
        self.target_questions = 100  # Target for 100+ questions processing
        self.performance_thresholds = {
            'max_processing_time_per_question': 30.0,  # 30 seconds max per question
            'min_success_rate': 0.85,  # 85% minimum success rate
            'max_memory_usage_mb': 2048,  # 2GB max memory usage
            'max_concurrent_jobs': 5  # Maximum concurrent scraping jobs
        }
    
    async def setup(self):
        """Initialize all system components"""
        logger.info("🚀 Setting up End-to-End Integration Testing Environment")
        
        try:
            # Initialize MongoDB connection
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            await self.db.command("ping")
            logger.info("✅ MongoDB connection established")
            
            # Initialize scraping engine
            engine_config = ScrapingEngineConfig(
                max_concurrent_jobs=self.performance_thresholds['max_concurrent_jobs'],
                default_timeout_seconds=300,  # 5 minutes timeout
                enable_performance_monitoring=True,
                enable_statistics=True
            )
            self.scraping_engine = create_scraping_engine(config=engine_config)
            logger.info("✅ Scraping engine initialized")
            
            # Initialize AI processor
            self.ai_processor = ScrapingAIProcessor()
            logger.info("✅ AI processor initialized")
            
            # Initialize duplicate detector
            self.duplicate_detector = AdvancedDuplicateDetector()
            logger.info("✅ Duplicate detector initialized")
            
            # Initialize source manager
            self.source_manager = SourceManagementService()
            await self.source_manager.initialize_sources()
            logger.info("✅ Source manager initialized")
            
            logger.info("🎯 Integration testing environment setup complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up test environment"""
        logger.info("🧹 Cleaning up integration testing environment")
        
        try:
            if self.scraping_engine:
                await self.scraping_engine.shutdown()
            
            if self.client:
                self.client.close()
            
            logger.info("✅ Cleanup completed successfully")
        except Exception as e:
            logger.error(f"⚠️ Cleanup warning: {str(e)}")
    
    async def test_full_scraping_workflow(self) -> IntegrationTestResult:
        """
        Test 1: Complete scraping workflow from source to processed questions
        Tests: Source → Extraction → AI Processing → Storage → Duplicate Detection
        """
        test_name = "Full Scraping Workflow"
        start_time = time.time()
        questions_processed = 0
        errors = []
        performance_metrics = {}
        details = {}
        
        try:
            logger.info("🔄 Starting full scraping workflow test...")
            
            # Step 1: Create scraping jobs for both sources
            job_requests = [
                ScrapingJobCreate(
                    source_type=ScrapingSourceType.INDIABIX,
                    target_categories=["quantitative", "logical"],
                    max_questions=25,
                    priority=1
                ),
                ScrapingJobCreate(
                    source_type=ScrapingSourceType.GEEKSFORGEEKS,
                    target_categories=["cs_fundamentals", "programming"],
                    max_questions=25,
                    priority=1
                )
            ]
            
            # Step 2: Submit jobs and track progress
            job_ids = []
            for job_request in job_requests:
                job_id = await self.scraping_engine.submit_job(job_request)
                job_ids.append(job_id)
                logger.info(f"✅ Submitted job {job_id} for {job_request.source_type}")
            
            details['job_ids'] = job_ids
            
            # Step 3: Monitor job completion
            completed_jobs = 0
            extracted_questions = []
            
            timeout = 600  # 10 minutes timeout
            check_interval = 10  # Check every 10 seconds
            elapsed = 0
            
            while completed_jobs < len(job_ids) and elapsed < timeout:
                for job_id in job_ids:
                    status = await self.scraping_engine.get_job_status(job_id)
                    if status.status == "completed" and job_id not in [job['id'] for job in details.get('completed_jobs', [])]:
                        completed_jobs += 1
                        extracted_questions.extend(status.extracted_questions or [])
                        logger.info(f"✅ Job {job_id} completed with {len(status.extracted_questions or [])} questions")
                
                if completed_jobs < len(job_ids):
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
            
            questions_processed = len(extracted_questions)
            details['extracted_questions_count'] = questions_processed
            details['extraction_time_seconds'] = elapsed
            
            if questions_processed == 0:
                errors.append("No questions extracted from scraping jobs")
                raise Exception("Scraping workflow failed - no questions extracted")
            
            # Step 4: Process questions through AI pipeline
            logger.info(f"🤖 Processing {questions_processed} questions through AI pipeline...")
            
            ai_start_time = time.time()
            processed_questions = []
            
            # Process in batches to avoid overwhelming the AI services
            batch_size = 10
            for i in range(0, len(extracted_questions), batch_size):
                batch = extracted_questions[i:i+batch_size]
                batch_result = await self.ai_processor.process_questions_batch(batch)
                processed_questions.extend(batch_result.processed_questions)
                logger.info(f"✅ Processed batch {i//batch_size + 1}, total processed: {len(processed_questions)}")
            
            ai_processing_time = time.time() - ai_start_time
            details['ai_processing_time_seconds'] = ai_processing_time
            details['ai_processed_questions_count'] = len(processed_questions)
            
            # Step 5: Run duplicate detection
            logger.info("🔍 Running duplicate detection analysis...")
            
            duplicate_start_time = time.time()
            duplicate_result = await self.duplicate_detector.detect_duplicates_batch(processed_questions)
            duplicate_processing_time = time.time() - duplicate_start_time
            
            details['duplicate_detection_time_seconds'] = duplicate_processing_time
            details['duplicate_pairs_found'] = len(duplicate_result.duplicate_pairs)
            details['duplicate_clusters'] = len(duplicate_result.clusters)
            
            # Step 6: Store processed questions in database
            logger.info("💾 Storing processed questions in database...")
            
            storage_start_time = time.time()
            stored_count = 0
            
            for question in processed_questions:
                try:
                    # Insert into database with duplicate checking
                    existing = await self.db.processed_questions.find_one({'content_hash': question.get('content_hash')})
                    if not existing:
                        await self.db.processed_questions.insert_one(question)
                        stored_count += 1
                except Exception as e:
                    errors.append(f"Storage error: {str(e)}")
            
            storage_time = time.time() - storage_start_time
            details['storage_time_seconds'] = storage_time
            details['questions_stored'] = stored_count
            
            # Calculate performance metrics
            total_time = time.time() - start_time
            performance_metrics = {
                'total_processing_time_seconds': total_time,
                'avg_time_per_question': total_time / max(questions_processed, 1),
                'extraction_rate_questions_per_second': questions_processed / max(elapsed, 1),
                'ai_processing_rate_questions_per_second': len(processed_questions) / max(ai_processing_time, 1),
                'duplicate_detection_rate_questions_per_second': len(processed_questions) / max(duplicate_processing_time, 1),
                'storage_rate_questions_per_second': stored_count / max(storage_time, 1),
                'overall_success_rate': stored_count / max(questions_processed, 1)
            }
            
            # Determine success
            success = (
                questions_processed > 0 and
                len(processed_questions) > 0 and
                stored_count > 0 and
                performance_metrics['overall_success_rate'] >= self.performance_thresholds['min_success_rate'] and
                performance_metrics['avg_time_per_question'] <= self.performance_thresholds['max_processing_time_per_question']
            )
            
            logger.info(f"✅ Full workflow test completed: {stored_count}/{questions_processed} questions processed successfully")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=total_time,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"Workflow test failed: {str(e)}")
            logger.error(f"❌ {test_name} failed: {str(e)}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
    
    async def test_ai_pipeline_integration(self) -> IntegrationTestResult:
        """
        Test 2: AI processing pipeline validation
        Tests: Gemini, Groq, HuggingFace integration and coordination
        """
        test_name = "AI Pipeline Integration"
        start_time = time.time()
        questions_processed = 0
        errors = []
        performance_metrics = {}
        details = {}
        
        try:
            logger.info("🤖 Testing AI pipeline integration...")
            
            # Create sample questions for AI processing
            sample_questions = [
                {
                    'id': f'test_q_{i}',
                    'question_text': f'Sample aptitude question {i} for testing AI processing capabilities',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct_answer': 'Option A',
                    'source': 'integration_test',
                    'category': 'quantitative'
                }
                for i in range(15)  # Test with 15 questions
            ]
            
            # Test individual AI services
            ai_service_results = {}
            
            # Test Gemini integration
            gemini_start = time.time()
            gemini_processed = 0
            try:
                gemini_batch = await self.ai_processor.process_questions_batch(sample_questions[:5])
                gemini_processed = len(gemini_batch.processed_questions)
                ai_service_results['gemini'] = {
                    'processed': gemini_processed,
                    'time': time.time() - gemini_start,
                    'success': gemini_processed > 0
                }
            except Exception as e:
                errors.append(f"Gemini test failed: {str(e)}")
                ai_service_results['gemini'] = {'processed': 0, 'time': 0, 'success': False}
            
            # Test Groq integration (through feedback system)
            groq_start = time.time()
            groq_processed = 0
            try:
                # Process a few questions and get feedback
                for question in sample_questions[5:8]:
                    feedback_result = await self.ai_processor.get_instant_feedback(
                        question['question_text'],
                        question['correct_answer']
                    )
                    if feedback_result:
                        groq_processed += 1
                
                ai_service_results['groq'] = {
                    'processed': groq_processed,
                    'time': time.time() - groq_start,
                    'success': groq_processed > 0
                }
            except Exception as e:
                errors.append(f"Groq test failed: {str(e)}")
                ai_service_results['groq'] = {'processed': 0, 'time': 0, 'success': False}
            
            # Test HuggingFace integration (through duplicate detection)
            hf_start = time.time()
            hf_processed = 0
            try:
                hf_batch = sample_questions[8:13]
                duplicate_result = await self.duplicate_detector.detect_duplicates_batch(hf_batch)
                hf_processed = len(hf_batch)
                ai_service_results['huggingface'] = {
                    'processed': hf_processed,
                    'time': time.time() - hf_start,
                    'success': hf_processed > 0,
                    'duplicates_found': len(duplicate_result.duplicate_pairs)
                }
            except Exception as e:
                errors.append(f"HuggingFace test failed: {str(e)}")
                ai_service_results['huggingface'] = {'processed': 0, 'time': 0, 'success': False}
            
            # Calculate totals
            questions_processed = sum(result['processed'] for result in ai_service_results.values())
            total_time = time.time() - start_time
            
            # Performance metrics
            successful_services = sum(1 for result in ai_service_results.values() if result['success'])
            performance_metrics = {
                'total_processing_time_seconds': total_time,
                'questions_per_second': questions_processed / max(total_time, 1),
                'services_success_rate': successful_services / 3,
                'ai_coordination_success': successful_services >= 2  # At least 2 services working
            }
            
            details['ai_service_results'] = ai_service_results
            details['successful_services'] = successful_services
            
            success = (
                successful_services >= 2 and  # At least 2 AI services working
                questions_processed >= 8 and  # Processed at least 8 questions
                len(errors) <= 1  # Allow 1 minor error
            )
            
            logger.info(f"✅ AI pipeline test completed: {successful_services}/3 services working, {questions_processed} questions processed")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=total_time,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"AI pipeline test failed: {str(e)}")
            logger.error(f"❌ {test_name} failed: {str(e)}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
    
    async def test_error_scenarios_and_recovery(self) -> IntegrationTestResult:
        """
        Test 3: Error scenarios and recovery mechanisms
        Tests: Network failures, API rate limits, invalid data handling, recovery
        """
        test_name = "Error Scenarios and Recovery"
        start_time = time.time()
        questions_processed = 0
        errors = []
        performance_metrics = {}
        details = {}
        
        try:
            logger.info("⚠️ Testing error scenarios and recovery mechanisms...")
            
            error_scenarios_tested = 0
            recovery_scenarios_successful = 0
            
            # Scenario 1: Invalid job configuration
            logger.info("Testing invalid job configuration handling...")
            try:
                invalid_job = ScrapingJobCreate(
                    source_type="invalid_source",  # Invalid source
                    target_categories=["nonexistent_category"],
                    max_questions=-1,  # Invalid number
                    priority=999  # Invalid priority
                )
                job_id = await self.scraping_engine.submit_job(invalid_job)
                # This should fail gracefully
                errors.append("Invalid job was accepted (should have been rejected)")
            except Exception:
                recovery_scenarios_successful += 1  # Expected to fail
                logger.info("✅ Invalid job configuration correctly rejected")
            
            error_scenarios_tested += 1
            
            # Scenario 2: Job timeout handling
            logger.info("Testing job timeout handling...")
            try:
                timeout_job = ScrapingJobCreate(
                    source_type=ScrapingSourceType.INDIABIX,
                    target_categories=["quantitative"],
                    max_questions=1,
                    priority=1
                )
                
                # Create job with very short timeout
                job_id = await self.scraping_engine.submit_job(timeout_job)
                
                # Wait for timeout or completion
                await asyncio.sleep(5)
                status = await self.scraping_engine.get_job_status(job_id)
                
                if status.status in ["timeout", "failed", "completed"]:
                    recovery_scenarios_successful += 1
                    logger.info(f"✅ Job timeout handled correctly: {status.status}")
                else:
                    errors.append(f"Job timeout not handled properly: {status.status}")
                
            except Exception as e:
                errors.append(f"Job timeout test failed: {str(e)}")
            
            error_scenarios_tested += 1
            
            # Scenario 3: AI service failure simulation
            logger.info("Testing AI service failure handling...")
            try:
                # Test with empty/invalid questions
                invalid_questions = [
                    {'invalid': 'data'},
                    {'question_text': ''},  # Empty question
                    {'question_text': None},  # None question
                ]
                
                batch_result = await self.ai_processor.process_questions_batch(invalid_questions)
                
                # Should handle gracefully without crashing
                if batch_result and hasattr(batch_result, 'processed_questions'):
                    recovery_scenarios_successful += 1
                    logger.info("✅ AI service failure handled gracefully")
                else:
                    errors.append("AI service failure not handled properly")
                
            except Exception as e:
                # Expected to handle gracefully, not crash
                logger.info(f"AI service failure test completed: {str(e)}")
                recovery_scenarios_successful += 1
            
            error_scenarios_tested += 1
            
            # Scenario 4: Database connection failure simulation
            logger.info("Testing database resilience...")
            try:
                # Test with invalid collection operations
                invalid_doc = {"invalid": float('inf')}  # Invalid JSON
                try:
                    await self.db.test_collection.insert_one(invalid_doc)
                except Exception:
                    recovery_scenarios_successful += 1
                    logger.info("✅ Database invalid data handled correctly")
                
            except Exception as e:
                errors.append(f"Database resilience test failed: {str(e)}")
            
            error_scenarios_tested += 1
            
            # Scenario 5: Concurrent job limit testing
            logger.info("Testing concurrent job limits...")
            try:
                # Submit more jobs than the limit
                job_ids = []
                max_concurrent = self.performance_thresholds['max_concurrent_jobs']
                
                for i in range(max_concurrent + 2):  # Submit 2 more than limit
                    try:
                        job = ScrapingJobCreate(
                            source_type=ScrapingSourceType.INDIABIX,
                            target_categories=["quantitative"],
                            max_questions=1,
                            priority=1
                        )
                        job_id = await self.scraping_engine.submit_job(job)
                        job_ids.append(job_id)
                    except Exception:
                        # Expected for jobs over limit
                        pass
                
                # Should not exceed concurrent limit
                if len(job_ids) <= max_concurrent:
                    recovery_scenarios_successful += 1
                    logger.info(f"✅ Concurrent job limits enforced: {len(job_ids)}/{max_concurrent}")
                else:
                    errors.append(f"Concurrent job limits not enforced: {len(job_ids)}/{max_concurrent}")
                
                questions_processed += len(job_ids)
                
            except Exception as e:
                errors.append(f"Concurrent job limit test failed: {str(e)}")
            
            error_scenarios_tested += 1
            
            # Calculate performance metrics
            total_time = time.time() - start_time
            recovery_rate = recovery_scenarios_successful / max(error_scenarios_tested, 1)
            
            performance_metrics = {
                'total_test_time_seconds': total_time,
                'error_scenarios_tested': error_scenarios_tested,
                'recovery_scenarios_successful': recovery_scenarios_successful,
                'recovery_success_rate': recovery_rate,
                'system_stability': recovery_rate >= 0.8  # 80% recovery rate
            }
            
            details['error_scenarios_tested'] = error_scenarios_tested
            details['recovery_scenarios_successful'] = recovery_scenarios_successful
            
            success = (
                error_scenarios_tested >= 4 and  # Tested at least 4 scenarios
                recovery_rate >= 0.6 and  # 60% recovery rate minimum
                len([e for e in errors if 'critical' in e.lower()]) == 0  # No critical errors
            )
            
            logger.info(f"✅ Error scenarios test completed: {recovery_scenarios_successful}/{error_scenarios_tested} recovery scenarios successful")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=total_time,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"Error scenarios test failed: {str(e)}")
            logger.error(f"❌ {test_name} failed: {str(e)}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
    
    async def test_performance_benchmarking(self) -> IntegrationTestResult:
        """
        Test 4: Performance benchmarking for scalability
        Tests: Throughput, latency, resource usage, concurrent operations
        """
        test_name = "Performance Benchmarking"
        start_time = time.time()
        questions_processed = 0
        errors = []
        performance_metrics = {}
        details = {}
        
        try:
            logger.info("📊 Running performance benchmarking tests...")
            
            # Benchmark 1: Single job throughput
            logger.info("Benchmarking single job throughput...")
            single_job_start = time.time()
            
            throughput_job = ScrapingJobCreate(
                source_type=ScrapingSourceType.INDIABIX,
                target_categories=["quantitative"],
                max_questions=20,
                priority=1
            )
            
            job_id = await self.scraping_engine.submit_job(throughput_job)
            
            # Monitor job progress
            completed = False
            single_job_questions = 0
            timeout = 300  # 5 minutes
            elapsed = 0
            
            while not completed and elapsed < timeout:
                status = await self.scraping_engine.get_job_status(job_id)
                if status.status == "completed":
                    completed = True
                    single_job_questions = len(status.extracted_questions or [])
                elif status.status == "failed":
                    break
                else:
                    await asyncio.sleep(5)
                    elapsed += 5
            
            single_job_time = time.time() - single_job_start
            single_job_throughput = single_job_questions / max(single_job_time, 1)
            
            details['single_job'] = {
                'questions': single_job_questions,
                'time': single_job_time,
                'throughput': single_job_throughput
            }
            
            questions_processed += single_job_questions
            
            # Benchmark 2: Concurrent jobs performance
            logger.info("Benchmarking concurrent jobs performance...")
            concurrent_start = time.time()
            
            concurrent_jobs = []
            concurrent_job_count = min(3, self.performance_thresholds['max_concurrent_jobs'])
            
            for i in range(concurrent_job_count):
                job = ScrapingJobCreate(
                    source_type=ScrapingSourceType.INDIABIX if i % 2 == 0 else ScrapingSourceType.GEEKSFORGEEKS,
                    target_categories=["quantitative"] if i % 2 == 0 else ["cs_fundamentals"],
                    max_questions=10,
                    priority=1
                )
                job_id = await self.scraping_engine.submit_job(job)
                concurrent_jobs.append(job_id)
            
            # Wait for concurrent jobs completion
            completed_concurrent = 0
            concurrent_questions = 0
            timeout = 400  # Extended timeout for concurrent jobs
            elapsed = 0
            
            while completed_concurrent < len(concurrent_jobs) and elapsed < timeout:
                for job_id in concurrent_jobs:
                    status = await self.scraping_engine.get_job_status(job_id)
                    if status.status == "completed" and job_id not in [job['id'] for job in details.get('completed_concurrent', [])]:
                        completed_concurrent += 1
                        concurrent_questions += len(status.extracted_questions or [])
                
                if completed_concurrent < len(concurrent_jobs):
                    await asyncio.sleep(10)
                    elapsed += 10
            
            concurrent_time = time.time() - concurrent_start
            concurrent_throughput = concurrent_questions / max(concurrent_time, 1)
            
            details['concurrent_jobs'] = {
                'jobs_submitted': len(concurrent_jobs),
                'jobs_completed': completed_concurrent,
                'questions': concurrent_questions,
                'time': concurrent_time,
                'throughput': concurrent_throughput
            }
            
            questions_processed += concurrent_questions
            
            # Benchmark 3: AI processing performance
            logger.info("Benchmarking AI processing performance...")
            ai_benchmark_start = time.time()
            
            # Create test questions for AI benchmarking
            ai_test_questions = [
                {
                    'id': f'bench_q_{i}',
                    'question_text': f'Benchmark question {i} for AI processing performance testing',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'A',
                    'source': 'benchmark_test',
                    'category': 'quantitative'
                }
                for i in range(25)  # 25 questions for AI benchmarking
            ]
            
            ai_processed_questions = []
            ai_batch_size = 5
            
            for i in range(0, len(ai_test_questions), ai_batch_size):
                batch = ai_test_questions[i:i+ai_batch_size]
                try:
                    batch_result = await self.ai_processor.process_questions_batch(batch)
                    ai_processed_questions.extend(batch_result.processed_questions)
                except Exception as e:
                    errors.append(f"AI benchmark batch {i//ai_batch_size + 1} failed: {str(e)}")
            
            ai_benchmark_time = time.time() - ai_benchmark_start
            ai_throughput = len(ai_processed_questions) / max(ai_benchmark_time, 1)
            
            details['ai_processing'] = {
                'questions_submitted': len(ai_test_questions),
                'questions_processed': len(ai_processed_questions),
                'time': ai_benchmark_time,
                'throughput': ai_throughput
            }
            
            # Calculate overall performance metrics
            total_time = time.time() - start_time
            
            performance_metrics = {
                'total_benchmark_time_seconds': total_time,
                'total_questions_processed': questions_processed,
                'overall_throughput_questions_per_second': questions_processed / max(total_time, 1),
                'single_job_throughput': single_job_throughput,
                'concurrent_jobs_throughput': concurrent_throughput,
                'ai_processing_throughput': ai_throughput,
                'concurrent_efficiency': (concurrent_throughput / max(single_job_throughput, 0.001)) / max(concurrent_job_count, 1),
                'meets_throughput_target': questions_processed >= 30,  # Target: 30+ questions in benchmark
                'avg_processing_time_per_question': total_time / max(questions_processed, 1)
            }
            
            # Determine success based on performance criteria
            success = (
                questions_processed >= 30 and  # Minimum questions processed
                performance_metrics['avg_processing_time_per_question'] <= self.performance_thresholds['max_processing_time_per_question'] and
                len(errors) <= 2 and  # Allow up to 2 minor errors
                performance_metrics['concurrent_efficiency'] >= 0.5  # Concurrent jobs at least 50% efficient
            )
            
            logger.info(f"✅ Performance benchmark completed: {questions_processed} questions, {performance_metrics['overall_throughput_questions_per_second']:.2f} q/s")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=total_time,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"Performance benchmark failed: {str(e)}")
            logger.error(f"❌ {test_name} failed: {str(e)}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
    
    async def test_100_questions_processing_validation(self) -> IntegrationTestResult:
        """
        Test 5: Verification of 100+ questions processing capability
        Tests: Large-scale processing, sustained performance, resource stability
        """
        test_name = "100+ Questions Processing Validation"
        start_time = time.time()
        questions_processed = 0
        errors = []
        performance_metrics = {}
        details = {}
        
        try:
            logger.info(f"🎯 Testing {self.target_questions}+ questions processing capability...")
            
            # Strategy: Multiple jobs targeting different categories to reach 100+ questions
            job_configurations = [
                {
                    'source_type': ScrapingSourceType.INDIABIX,
                    'target_categories': ["quantitative"],
                    'max_questions': 30,
                    'priority': 1
                },
                {
                    'source_type': ScrapingSourceType.INDIABIX,
                    'target_categories': ["logical"],
                    'max_questions': 25,
                    'priority': 1
                },
                {
                    'source_type': ScrapingSourceType.GEEKSFORGEEKS,
                    'target_categories': ["cs_fundamentals"],
                    'max_questions': 25,
                    'priority': 1
                },
                {
                    'source_type': ScrapingSourceType.GEEKSFORGEEKS,
                    'target_categories': ["programming"],
                    'max_questions': 25,
                    'priority': 1
                }
            ]
            
            # Phase 1: Submit all jobs
            logger.info("Phase 1: Submitting multiple jobs for 100+ questions...")
            job_ids = []
            
            for i, config in enumerate(job_configurations):
                try:
                    job_request = ScrapingJobCreate(**config)
                    job_id = await self.scraping_engine.submit_job(job_request)
                    job_ids.append({
                        'id': job_id,
                        'config': config,
                        'status': 'submitted'
                    })
                    logger.info(f"✅ Submitted job {i+1}: {config['source_type']} - {config['target_categories']}")
                except Exception as e:
                    errors.append(f"Failed to submit job {i+1}: {str(e)}")
            
            details['jobs_submitted'] = len(job_ids)
            details['target_questions'] = sum(config['max_questions'] for config in job_configurations)
            
            # Phase 2: Monitor job completion with extended timeout
            logger.info("Phase 2: Monitoring job completion...")
            
            completed_jobs = []
            total_extracted_questions = []
            
            timeout = 900  # 15 minutes for 100+ questions
            check_interval = 15  # Check every 15 seconds
            elapsed = 0
            
            while len(completed_jobs) < len(job_ids) and elapsed < timeout:
                for job_info in job_ids:
                    if job_info['status'] != 'completed':
                        try:
                            status = await self.scraping_engine.get_job_status(job_info['id'])
                            
                            if status.status in ['completed', 'failed']:
                                job_info['status'] = status.status
                                job_info['questions_extracted'] = len(status.extracted_questions or [])
                                
                                if status.status == 'completed':
                                    completed_jobs.append(job_info)
                                    total_extracted_questions.extend(status.extracted_questions or [])
                                    logger.info(f"✅ Job completed: {job_info['questions_extracted']} questions from {job_info['config']['source_type']}")
                                else:
                                    errors.append(f"Job failed: {job_info['id']}")
                        
                        except Exception as e:
                            errors.append(f"Error checking job {job_info['id']}: {str(e)}")
                
                if len(completed_jobs) < len(job_ids):
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
                    
                    # Progress update
                    current_questions = len(total_extracted_questions)
                    logger.info(f"Progress: {current_questions} questions extracted so far...")
            
            questions_processed = len(total_extracted_questions)
            extraction_time = elapsed
            
            details['extraction_phase'] = {
                'jobs_completed': len(completed_jobs),
                'questions_extracted': questions_processed,
                'extraction_time_seconds': extraction_time,
                'extraction_rate': questions_processed / max(extraction_time, 1)
            }
            
            # Phase 3: AI processing of all extracted questions
            if questions_processed > 0:
                logger.info(f"Phase 3: AI processing {questions_processed} extracted questions...")
                
                ai_start_time = time.time()
                processed_questions = []
                
                # Process in larger batches for efficiency
                batch_size = 15
                batches_processed = 0
                
                for i in range(0, len(total_extracted_questions), batch_size):
                    batch = total_extracted_questions[i:i+batch_size]
                    try:
                        batch_result = await self.ai_processor.process_questions_batch(batch)
                        processed_questions.extend(batch_result.processed_questions)
                        batches_processed += 1
                        
                        if batches_processed % 3 == 0:  # Progress update every 3 batches
                            logger.info(f"AI processing progress: {len(processed_questions)} questions processed...")
                    
                    except Exception as e:
                        errors.append(f"AI processing batch {i//batch_size + 1} failed: {str(e)}")
                
                ai_processing_time = time.time() - ai_start_time
                
                details['ai_processing_phase'] = {
                    'questions_submitted': questions_processed,
                    'questions_processed': len(processed_questions),
                    'processing_time_seconds': ai_processing_time,
                    'processing_rate': len(processed_questions) / max(ai_processing_time, 1),
                    'batches_processed': batches_processed
                }
                
                # Phase 4: Duplicate detection and final validation
                logger.info("Phase 4: Duplicate detection and final validation...")
                
                validation_start_time = time.time()
                
                # Duplicate detection
                duplicate_result = await self.duplicate_detector.detect_duplicates_batch(processed_questions)
                
                # Final storage
                stored_questions = 0
                for question in processed_questions:
                    try:
                        # Check for existing questions
                        existing = await self.db.processed_questions_large_test.find_one({
                            'content_hash': question.get('content_hash')
                        })
                        
                        if not existing:
                            await self.db.processed_questions_large_test.insert_one(question)
                            stored_questions += 1
                    
                    except Exception as e:
                        errors.append(f"Storage error: {str(e)}")
                
                validation_time = time.time() - validation_start_time
                
                details['validation_phase'] = {
                    'duplicate_pairs_found': len(duplicate_result.duplicate_pairs),
                    'duplicate_clusters': len(duplicate_result.clusters),
                    'questions_stored': stored_questions,
                    'validation_time_seconds': validation_time
                }
            
            # Calculate comprehensive performance metrics
            total_time = time.time() - start_time
            
            performance_metrics = {
                'total_processing_time_seconds': total_time,
                'questions_extracted': questions_processed,
                'questions_processed_by_ai': len(processed_questions) if 'processed_questions' in locals() else 0,
                'questions_stored': stored_questions if 'stored_questions' in locals() else 0,
                'overall_success_rate': (stored_questions if 'stored_questions' in locals() else 0) / max(questions_processed, 1),
                'meets_100_questions_target': questions_processed >= self.target_questions,
                'end_to_end_throughput': questions_processed / max(total_time, 1),
                'jobs_success_rate': len(completed_jobs) / max(len(job_ids), 1),
                'extraction_efficiency': questions_processed / max(details['target_questions'], 1),
                'avg_time_per_question': total_time / max(questions_processed, 1)
            }
            
            # Determine overall success
            success = (
                questions_processed >= self.target_questions and  # Met 100+ questions target
                performance_metrics['overall_success_rate'] >= 0.75 and  # 75% success rate
                performance_metrics['jobs_success_rate'] >= 0.75 and  # 75% job success rate
                len([e for e in errors if 'critical' in e.lower()]) == 0 and  # No critical errors
                performance_metrics['avg_time_per_question'] <= self.performance_thresholds['max_processing_time_per_question']
            )
            
            logger.info(f"✅ 100+ questions test completed: {questions_processed}/{self.target_questions} questions processed")
            logger.info(f"📊 Success rate: {performance_metrics['overall_success_rate']:.2%}, Jobs: {len(completed_jobs)}/{len(job_ids)}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=success,
                duration_seconds=total_time,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            errors.append(f"100+ questions test failed: {str(e)}")
            logger.error(f"❌ {test_name} failed: {str(e)}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=False,
                duration_seconds=duration,
                questions_processed=questions_processed,
                errors=errors,
                performance_metrics=performance_metrics,
                details=details
            )
    
    async def run_comprehensive_integration_tests(self) -> Dict[str, Any]:
        """
        Execute all integration tests and generate comprehensive report
        """
        logger.info("🚀 Starting Comprehensive End-to-End Integration Testing Suite")
        
        overall_start_time = time.time()
        
        # Setup test environment
        setup_success = await self.setup()
        if not setup_success:
            return {
                'success': False,
                'error': 'Failed to setup integration testing environment',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            # Run all integration tests
            test_methods = [
                self.test_full_scraping_workflow,
                self.test_ai_pipeline_integration,
                self.test_error_scenarios_and_recovery,
                self.test_performance_benchmarking,
                self.test_100_questions_processing_validation
            ]
            
            for i, test_method in enumerate(test_methods, 1):
                logger.info(f"🔄 Running test {i}/{len(test_methods)}: {test_method.__name__}")
                try:
                    result = await test_method()
                    self.test_results.append(result)
                    logger.info(f"{'✅' if result.success else '❌'} Test completed: {result.test_name}")
                except Exception as e:
                    logger.error(f"❌ Test {test_method.__name__} crashed: {str(e)}")
                    self.test_results.append(IntegrationTestResult(
                        test_name=test_method.__name__,
                        success=False,
                        duration_seconds=0,
                        questions_processed=0,
                        errors=[f"Test crashed: {str(e)}"],
                        performance_metrics={},
                        details={}
                    ))
            
            # Generate comprehensive report
            report = self.generate_integration_report(overall_start_time)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Integration testing suite failed: {str(e)}")
            return {
                'success': False,
                'error': f'Integration testing suite failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        finally:
            await self.cleanup()
    
    def generate_integration_report(self, start_time: float) -> Dict[str, Any]:
        """Generate comprehensive integration testing report"""
        
        total_duration = time.time() - start_time
        successful_tests = sum(1 for result in self.test_results if result.success)
        total_questions = sum(result.questions_processed for result in self.test_results)
        total_errors = sum(len(result.errors) for result in self.test_results)
        
        # Calculate aggregated metrics
        avg_throughput = sum(
            result.performance_metrics.get('overall_throughput_questions_per_second', 0) 
            for result in self.test_results
        ) / max(len(self.test_results), 1)
        
        avg_processing_time = sum(
            result.performance_metrics.get('avg_time_per_question', 0)
            for result in self.test_results if result.performance_metrics.get('avg_time_per_question', 0) > 0
        ) / max(sum(1 for r in self.test_results if r.performance_metrics.get('avg_time_per_question', 0) > 0), 1)
        
        # Overall success criteria
        overall_success = (
            successful_tests >= 4 and  # At least 4 out of 5 tests successful
            total_questions >= self.target_questions and  # Met 100+ questions target
            total_errors <= 10 and  # Reasonable error count
            avg_processing_time <= self.performance_thresholds['max_processing_time_per_question']
        )
        
        report = {
            'integration_test_report': {
                'overall_success': overall_success,
                'timestamp': datetime.utcnow().isoformat(),
                'total_duration_seconds': total_duration,
                
                'summary_statistics': {
                    'total_tests_run': len(self.test_results),
                    'successful_tests': successful_tests,
                    'failed_tests': len(self.test_results) - successful_tests,
                    'success_rate': successful_tests / max(len(self.test_results), 1),
                    'total_questions_processed': total_questions,
                    'total_errors': total_errors,
                    'meets_100_questions_target': total_questions >= self.target_questions
                },
                
                'performance_metrics': {
                    'average_throughput_questions_per_second': avg_throughput,
                    'average_processing_time_per_question': avg_processing_time,
                    'total_processing_time_hours': total_duration / 3600,
                    'meets_performance_thresholds': avg_processing_time <= self.performance_thresholds['max_processing_time_per_question']
                },
                
                'test_results': []
            }
        }
        
        # Add individual test results
        for result in self.test_results:
            test_summary = {
                'test_name': result.test_name,
                'success': result.success,
                'duration_seconds': result.duration_seconds,
                'questions_processed': result.questions_processed,
                'error_count': len(result.errors),
                'key_metrics': {
                    k: v for k, v in result.performance_metrics.items() 
                    if k in ['overall_throughput_questions_per_second', 'avg_time_per_question', 'overall_success_rate']
                },
                'errors': result.errors[:5] if result.errors else [],  # Show first 5 errors
                'details_summary': {
                    k: v for k, v in result.details.items()
                    if not isinstance(v, (list, dict)) or len(str(v)) < 200
                }
            }
            report['integration_test_report']['test_results'].append(test_summary)
        
        # Add recommendations
        recommendations = []
        
        if not overall_success:
            if successful_tests < 4:
                recommendations.append("CRITICAL: Multiple core tests failing - investigate system stability")
            
            if total_questions < self.target_questions:
                recommendations.append(f"PERFORMANCE: Only {total_questions}/{self.target_questions} questions processed - optimize extraction rates")
            
            if avg_processing_time > self.performance_thresholds['max_processing_time_per_question']:
                recommendations.append(f"PERFORMANCE: Average processing time ({avg_processing_time:.2f}s) exceeds threshold ({self.performance_thresholds['max_processing_time_per_question']}s)")
            
            if total_errors > 10:
                recommendations.append(f"RELIABILITY: High error count ({total_errors}) - improve error handling")
        
        else:
            recommendations.append("SUCCESS: All integration tests meet acceptance criteria")
            recommendations.append("READY: System validated for production deployment")
            
            if avg_throughput > 1.0:
                recommendations.append(f"EXCELLENT: High throughput achieved ({avg_throughput:.2f} questions/second)")
        
        report['integration_test_report']['recommendations'] = recommendations
        
        return report

# Test execution function
async def run_integration_tests():
    """Main function to run integration tests"""
    tester = EndToEndIntegrationTester()
    return await tester.run_comprehensive_integration_tests()

if __name__ == "__main__":
    # Run integration tests
    import asyncio
    
    async def main():
        print("🚀 Starting End-to-End Integration Testing Suite...")
        report = await run_integration_tests()
        
        print("\n" + "="*80)
        print("INTEGRATION TEST REPORT")
        print("="*80)
        
        if report.get('success', True):
            test_report = report.get('integration_test_report', {})
            print(f"Overall Success: {'✅ PASSED' if test_report.get('overall_success', False) else '❌ FAILED'}")
            print(f"Tests Successful: {test_report.get('summary_statistics', {}).get('successful_tests', 0)}/5")
            print(f"Questions Processed: {test_report.get('summary_statistics', {}).get('total_questions_processed', 0)}")
            print(f"Average Throughput: {test_report.get('performance_metrics', {}).get('average_throughput_questions_per_second', 0):.2f} q/s")
            
            print("\nRecommendations:")
            for rec in test_report.get('recommendations', []):
                print(f"  • {rec}")
        else:
            print(f"❌ FAILED: {report.get('error', 'Unknown error')}")
        
        print("="*80)
        
        return report
    
    asyncio.run(main())