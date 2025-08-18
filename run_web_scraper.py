#!/usr/bin/env python3
"""
Direct Web Scraper Execution Script
Runs the comprehensive web scraper to collect maximum questions from IndiaBix and GeeksforGeeks
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/scraper_execution.log')
    ]
)
logger = logging.getLogger(__name__)

class WebScraperRunner:
    def __init__(self):
        self.total_questions_collected = 0
        self.collection_results = {
            "indiabix": {"questions": 0, "categories": []},
            "geeksforgeeks": {"questions": 0, "categories": []},
            "execution_time": 0,
            "errors": [],
            "success_rate": 0.0
        }
    
    async def initialize_services(self):
        """Initialize all required services and database connections"""
        logger.info("🔧 Initializing scraping services...")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv('/app/backend/.env')
            
            # Initialize database
            from motor.motor_asyncio import AsyncIOMotorClient
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[os.environ.get('DB_NAME', 'aptitude_questions')]
            
            # Test database connection
            await self.db.command("ping")
            logger.info("✅ Database connection established")
            
            # Initialize source management service
            from services.source_management_service import SourceManagementService
            self.source_manager = SourceManagementService(self.db)
            await self.source_manager.initialize_default_sources()
            logger.info("✅ Source management service initialized")
            
            # Initialize scraping engine
            from scraping.scraper_engine import ScrapingEngine, ScrapingEngineConfig
            config = ScrapingEngineConfig(
                max_concurrent_jobs=3,
                max_questions_per_job=2000,
                job_timeout_minutes=120,
                enable_performance_monitoring=True,
                enable_anti_detection=True,
                enable_content_validation=True
            )
            
            self.scraping_engine = ScrapingEngine(config)
            logger.info("✅ Scraping engine initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing services: {str(e)}")
            return False
    
    async def create_comprehensive_scraping_jobs(self) -> List[str]:
        """Create multiple scraping jobs to maximize question collection"""
        logger.info("🎯 Creating comprehensive scraping jobs...")
        
        job_ids = []
        
        try:
            from models.scraping_models import ScrapingJobConfig, ScrapingTarget
            from config.scraping_config import get_source_targets
            
            # Job 1: IndiaBix Quantitative Aptitude (High Priority)
            indiabix_quant_targets = [t for t in get_source_targets("indiabix") 
                                    if t.category == "quantitative"]
            
            if indiabix_quant_targets:
                job_config_1 = ScrapingJobConfig(
                    job_name="IndiaBix Quantitative Collection",
                    target=indiabix_quant_targets[0],  # Take first target
                    max_questions=800,
                    max_pages=100,
                    extraction_method=indiabix_quant_targets[0].source_id
                )
                
                job_id_1 = self.scraping_engine.submit_scraping_job(job_config_1)
                job_ids.append(job_id_1)
                logger.info(f"✅ Created IndiaBix Quantitative job: {job_id_1}")
            
            # Job 2: IndiaBix Logical Reasoning
            indiabix_logical_targets = [t for t in get_source_targets("indiabix") 
                                      if t.category == "logical"]
            
            if indiabix_logical_targets:
                job_config_2 = ScrapingJobConfig(
                    job_name="IndiaBix Logical Reasoning Collection", 
                    target=indiabix_logical_targets[0],
                    max_questions=700,
                    max_pages=80,
                    extraction_method=indiabix_logical_targets[0].source_id
                )
                
                job_id_2 = self.scraping_engine.submit_scraping_job(job_config_2)
                job_ids.append(job_id_2)
                logger.info(f"✅ Created IndiaBix Logical job: {job_id_2}")
            
            # Job 3: IndiaBix Verbal Ability
            indiabix_verbal_targets = [t for t in get_source_targets("indiabix")
                                     if t.category == "verbal"]
            
            if indiabix_verbal_targets:
                job_config_3 = ScrapingJobConfig(
                    job_name="IndiaBix Verbal Ability Collection",
                    target=indiabix_verbal_targets[0],
                    max_questions=600,
                    max_pages=70,
                    extraction_method=indiabix_verbal_targets[0].source_id
                )
                
                job_id_3 = self.scraping_engine.submit_scraping_job(job_config_3)
                job_ids.append(job_id_3)
                logger.info(f"✅ Created IndiaBix Verbal job: {job_id_3}")
            
            # Job 4: GeeksforGeeks CS Fundamentals
            geeks_targets = [t for t in get_source_targets("geeksforgeeks") 
                           if t.category == "cs_fundamentals"]
            
            if geeks_targets:
                job_config_4 = ScrapingJobConfig(
                    job_name="GeeksforGeeks CS Fundamentals Collection",
                    target=geeks_targets[0],
                    max_questions=500,
                    max_pages=60,
                    extraction_method=geeks_targets[0].source_id
                )
                
                job_id_4 = self.scraping_engine.submit_scraping_job(job_config_4)
                job_ids.append(job_id_4)
                logger.info(f"✅ Created GeeksforGeeks CS job: {job_id_4}")
            
            logger.info(f"🎯 Created {len(job_ids)} scraping jobs for execution")
            return job_ids
            
        except Exception as e:
            logger.error(f"❌ Error creating scraping jobs: {str(e)}")
            return []
    
    async def monitor_and_execute_jobs(self, job_ids: List[str]) -> Dict[str, Any]:
        """Monitor job execution and collect results"""
        logger.info(f"👀 Monitoring execution of {len(job_ids)} jobs...")
        
        start_time = datetime.now()
        completed_jobs = 0
        total_questions = 0
        
        try:
            # Wait for all jobs to complete or timeout
            max_wait_time = 3600  # 1 hour timeout
            check_interval = 30   # Check every 30 seconds
            
            elapsed_time = 0
            while elapsed_time < max_wait_time and completed_jobs < len(job_ids):
                
                # Check status of all jobs
                for job_id in job_ids:
                    job_status = self.scraping_engine.get_job_status(job_id)
                    
                    if job_status:
                        status = job_status.get("status", "unknown")
                        questions_extracted = job_status.get("total_questions_extracted", 0)
                        
                        logger.info(f"Job {job_id[:8]}... - Status: {status}, Questions: {questions_extracted}")
                        
                        if status in ["completed", "failed", "cancelled"]:
                            if status == "completed":
                                total_questions += questions_extracted
                                self.total_questions_collected += questions_extracted
                                completed_jobs += 1
                            elif status == "failed":
                                self.collection_results["errors"].append(f"Job {job_id} failed: {job_status.get('error_message', 'Unknown error')}")
                
                if completed_jobs < len(job_ids):
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    
                    # Log progress every 2 minutes
                    if elapsed_time % 120 == 0:
                        logger.info(f"⏱️ Progress Update: {completed_jobs}/{len(job_ids)} jobs completed, {total_questions} questions collected")
            
            # Final collection summary
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Get engine statistics
            engine_stats = self.scraping_engine.get_engine_statistics()
            
            self.collection_results.update({
                "total_jobs_created": len(job_ids),
                "jobs_completed": completed_jobs,
                "total_questions_collected": total_questions,
                "execution_time_seconds": execution_time,
                "success_rate": (completed_jobs / len(job_ids)) * 100 if job_ids else 0,
                "questions_per_minute": (total_questions / (execution_time / 60)) if execution_time > 0 else 0,
                "engine_statistics": engine_stats
            })
            
            logger.info("🎉 SCRAPING EXECUTION COMPLETED!")
            logger.info(f"📊 Total Questions Collected: {total_questions}")
            logger.info(f"⏱️ Execution Time: {execution_time:.2f} seconds")
            logger.info(f"📈 Success Rate: {(completed_jobs / len(job_ids)) * 100:.1f}%")
            
            return self.collection_results
            
        except Exception as e:
            logger.error(f"❌ Error monitoring job execution: {str(e)}")
            self.collection_results["errors"].append(f"Monitoring error: {str(e)}")
            return self.collection_results
    
    async def save_results_to_database(self):
        """Save collected questions to database"""
        logger.info("💾 Saving scraping results to database...")
        
        try:
            # Count questions in database
            total_questions = await self.db.enhanced_questions.count_documents({})
            scraped_questions = await self.db.processed_scraped_questions.count_documents({})
            
            logger.info(f"📊 Database Summary:")
            logger.info(f"   - Total Enhanced Questions: {total_questions}")
            logger.info(f"   - Scraped Questions: {scraped_questions}")
            
            # Create summary document
            summary = {
                "scraping_session": {
                    "timestamp": datetime.now(),
                    "execution_results": self.collection_results,
                    "database_counts": {
                        "total_enhanced_questions": total_questions,
                        "scraped_questions": scraped_questions
                    }
                }
            }
            
            # Save summary
            await self.db.scraping_sessions.insert_one(summary)
            logger.info("✅ Scraping session results saved to database")
            
            return {
                "total_enhanced_questions": total_questions,
                "scraped_questions": scraped_questions
            }
            
        except Exception as e:
            logger.error(f"❌ Error saving results to database: {str(e)}")
            return {}
    
    async def run_comprehensive_scraping(self):
        """Run the complete web scraping process"""
        logger.info("🚀 STARTING COMPREHENSIVE WEB SCRAPING...")
        logger.info("=" * 80)
        
        try:
            # Initialize services
            if not await self.initialize_services():
                logger.error("Failed to initialize services. Aborting.")
                return False
            
            # Create scraping jobs
            job_ids = await self.create_comprehensive_scraping_jobs()
            
            if not job_ids:
                logger.error("No scraping jobs created. Aborting.")
                return False
            
            # Execute and monitor jobs
            results = await self.monitor_and_execute_jobs(job_ids)
            
            # Save results to database
            db_results = await self.save_results_to_database()
            
            # Final reporting
            logger.info("=" * 80)
            logger.info("🎯 COMPREHENSIVE WEB SCRAPING COMPLETED!")
            logger.info("=" * 80)
            logger.info(f"📊 COLLECTION SUMMARY:")
            logger.info(f"   - Jobs Created: {results.get('total_jobs_created', 0)}")
            logger.info(f"   - Jobs Completed: {results.get('jobs_completed', 0)}")
            logger.info(f"   - Success Rate: {results.get('success_rate', 0):.1f}%")
            logger.info(f"   - Total Questions Collected: {results.get('total_questions_collected', 0)}")
            logger.info(f"   - Questions Per Minute: {results.get('questions_per_minute', 0):.1f}")
            logger.info(f"   - Execution Time: {results.get('execution_time_seconds', 0):.2f}s")
            logger.info("=" * 80)
            logger.info(f"💾 DATABASE SUMMARY:")
            logger.info(f"   - Enhanced Questions in DB: {db_results.get('total_enhanced_questions', 0)}")
            logger.info(f"   - Scraped Questions in DB: {db_results.get('scraped_questions', 0)}")
            logger.info("=" * 80)
            
            if results.get('errors'):
                logger.warning("⚠️ ERRORS ENCOUNTERED:")
                for error in results['errors']:
                    logger.warning(f"   - {error}")
                logger.info("=" * 80)
            
            # Final question count
            total_in_system = db_results.get('total_enhanced_questions', 0)
            logger.info(f"🎉 FINAL RESULT: {total_in_system} QUESTIONS AVAILABLE IN SYSTEM!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical error in scraping process: {str(e)}")
            return False
        
        finally:
            # Cleanup
            if hasattr(self, 'scraping_engine'):
                self.scraping_engine.stop_engine()
            if hasattr(self, 'client'):
                self.client.close()

async def main():
    """Main execution function"""
    runner = WebScraperRunner()
    success = await runner.run_comprehensive_scraping()
    
    if success:
        logger.info("✅ Web scraping completed successfully!")
        return 0
    else:
        logger.error("❌ Web scraping failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)