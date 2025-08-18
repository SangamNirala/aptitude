#!/usr/bin/env python3
"""
Simple Web Scraper using API Endpoints
Direct API calls to run comprehensive web scraping and collect maximum questions
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleWebScraperRunner:
    def __init__(self):
        self.base_url = "http://localhost:8001/api/scraping"
        self.session = None
        self.job_ids = []
        self.total_questions_collected = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_system_health(self) -> bool:
        """Check if the scraping system is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📊 System Health: {data.get('status', 'unknown')}")
                    return data.get('status') in ['healthy', 'degraded']
                else:
                    logger.error(f"Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return False
    
    async def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get list of available scraping sources"""
        try:
            async with self.session.get(f"{self.base_url}/sources") as response:
                if response.status == 200:
                    sources = await response.json()
                    logger.info(f"📋 Available sources: {len(sources)}")
                    for source in sources:
                        logger.info(f"   - {source['name']}: {source['base_url']}")
                    return sources
                else:
                    logger.error(f"Failed to get sources: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting sources: {str(e)}")
            return []
    
    async def create_scraping_job(self, job_config: Dict[str, Any]) -> str:
        """Create a new scraping job"""
        try:
            headers = {'Content-Type': 'application/json'}
            async with self.session.post(
                f"{self.base_url}/jobs", 
                json=job_config, 
                headers=headers
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    job_id = data.get('job_id')
                    logger.info(f"✅ Created job: {job_config['job_name']} - ID: {job_id}")
                    return job_id
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create job '{job_config['job_name']}': {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error creating job '{job_config['job_name']}': {str(e)}")
            return None
    
    async def start_job(self, job_id: str) -> bool:
        """Start a scraping job"""
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {'priority': 'high'}
            async with self.session.put(
                f"{self.base_url}/jobs/{job_id}/start",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"🚀 Started job: {job_id} - Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to start job {job_id}: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error starting job {job_id}: {str(e)}")
            return False
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a scraping job"""
        try:
            async with self.session.get(f"{self.base_url}/jobs/{job_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to get job status for {job_id}: {response.status}")
                    return {}
        except Exception as e:
            logger.warning(f"Error getting job status for {job_id}: {str(e)}")
            return {}
    
    async def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """Get status of all jobs"""
        try:
            async with self.session.get(f"{self.base_url}/jobs") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to get all jobs status: {response.status}")
                    return []
        except Exception as e:
            logger.warning(f"Error getting all jobs status: {str(e)}")
            return []
    
    async def monitor_jobs(self, job_ids: List[str], timeout_minutes: int = 60) -> Dict[str, Any]:
        """Monitor job execution until completion or timeout"""
        logger.info(f"👁️ Monitoring {len(job_ids)} jobs for up to {timeout_minutes} minutes...")
        
        start_time = time.time()
        completed_jobs = 0
        total_questions = 0
        
        while time.time() - start_time < timeout_minutes * 60:
            try:
                all_jobs = await self.get_all_jobs_status()
                monitored_jobs = [job for job in all_jobs if job.get('job_id') in job_ids]
                
                active_count = 0
                current_total = 0
                
                for job in monitored_jobs:
                    status = job.get('status', 'unknown')
                    questions = job.get('questions_extracted', 0)
                    current_total += questions
                    
                    if status in ['running', 'pending']:
                        active_count += 1
                    elif status == 'completed':
                        if questions > 0:
                            logger.info(f"✅ Job completed: {job.get('job_id', 'unknown')[:8]}... - Questions: {questions}")
                
                # Update totals
                total_questions = current_total
                self.total_questions_collected = total_questions
                
                # Log progress every 2 minutes
                elapsed_minutes = (time.time() - start_time) / 60
                if int(elapsed_minutes) % 2 == 0 and elapsed_minutes > 1:
                    logger.info(f"⏱️ Progress: {elapsed_minutes:.1f} min elapsed, {active_count} active jobs, {total_questions} questions collected")
                
                # Check if all jobs completed
                if active_count == 0:
                    logger.info("🎉 All jobs completed!")
                    break
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring jobs: {str(e)}")
                await asyncio.sleep(30)
        
        return {
            'total_jobs': len(job_ids),
            'total_questions_collected': total_questions,
            'execution_time_minutes': (time.time() - start_time) / 60
        }
    
    async def create_comprehensive_jobs(self) -> List[str]:
        """Create comprehensive scraping jobs for maximum collection"""
        logger.info("🎯 Creating comprehensive scraping jobs...")
        
        job_configs = [
            {
                "job_name": "IndiaBix Maximum Collection - Quantitative",
                "description": "High volume collection from IndiaBix quantitative aptitude",
                "source_names": ["indiabix"],
                "max_questions_per_source": 1500,
                "target_categories": ["quantitative"],
                "quality_threshold": 65.0,
                "priority_level": 1,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True
            },
            {
                "job_name": "IndiaBix Maximum Collection - Logical",
                "description": "High volume collection from IndiaBix logical reasoning",
                "source_names": ["indiabix"],
                "max_questions_per_source": 1200,
                "target_categories": ["logical"],
                "quality_threshold": 65.0,
                "priority_level": 1,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True
            },
            {
                "job_name": "IndiaBix Maximum Collection - Verbal",
                "description": "High volume collection from IndiaBix verbal ability",
                "source_names": ["indiabix"],
                "max_questions_per_source": 1000,
                "target_categories": ["verbal"],
                "quality_threshold": 65.0,
                "priority_level": 1,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True
            },
            {
                "job_name": "GeeksforGeeks Maximum Collection - CS",
                "description": "High volume collection from GeeksforGeeks CS fundamentals",
                "source_names": ["geeksforgeeks"],
                "max_questions_per_source": 1200,
                "target_categories": ["cs_fundamentals"],
                "quality_threshold": 65.0,
                "priority_level": 1,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True
            },
            {
                "job_name": "GeeksforGeeks Maximum Collection - Programming",
                "description": "High volume collection from GeeksforGeeks programming",
                "source_names": ["geeksforgeeks"],
                "max_questions_per_source": 1000,
                "target_categories": ["programming"],
                "quality_threshold": 65.0,
                "priority_level": 1,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True
            },
            {
                "job_name": "Mixed Sources Ultra Collection",
                "description": "Ultra high volume mixed source collection",
                "source_names": ["indiabix", "geeksforgeeks"],
                "max_questions_per_source": 800,
                "target_categories": ["quantitative", "logical", "cs_fundamentals"],
                "quality_threshold": 60.0,
                "priority_level": 1,
                "enable_ai_processing": True,
                "enable_duplicate_detection": True
            }
        ]
        
        created_job_ids = []
        
        for job_config in job_configs:
            job_id = await self.create_scraping_job(job_config)
            if job_id:
                created_job_ids.append(job_id)
                # Start the job immediately
                await self.start_job(job_id)
                await asyncio.sleep(2)  # Small delay between job starts
        
        logger.info(f"🎯 Created and started {len(created_job_ids)} scraping jobs")
        return created_job_ids
    
    async def get_final_question_count(self) -> Dict[str, int]:
        """Get final count of questions in the database"""
        try:
            # We'll use the system status to get question counts
            async with self.session.get(f"{self.base_url}/system-status") as response:
                if response.status == 200:
                    data = await response.json()
                    # Try to extract question counts from system status
                    return {
                        "system_questions": data.get('total_questions', 0),
                        "active_jobs": data.get('active_jobs', 0)
                    }
        except Exception as e:
            logger.error(f"Error getting final question count: {str(e)}")
        
        return {"system_questions": 0, "active_jobs": 0}
    
    async def run_comprehensive_scraping(self):
        """Run the comprehensive web scraping process"""
        logger.info("🚀 STARTING COMPREHENSIVE WEB SCRAPING VIA API...")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Check system health
            if not await self.check_system_health():
                logger.error("❌ System health check failed. Aborting.")
                return False
            
            # Get available sources
            sources = await self.get_available_sources()
            if not sources:
                logger.error("❌ No sources available. Aborting.")
                return False
            
            # Create comprehensive scraping jobs
            job_ids = await self.create_comprehensive_jobs()
            if not job_ids:
                logger.error("❌ No jobs created. Aborting.")
                return False
            
            self.job_ids = job_ids
            
            # Monitor job execution
            logger.info(f"👁️ Starting monitoring of {len(job_ids)} jobs...")
            results = await self.monitor_jobs(job_ids, timeout_minutes=90)
            
            # Get final counts
            final_counts = await self.get_final_question_count()
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Final reporting
            logger.info("=" * 80)
            logger.info("🎉 COMPREHENSIVE WEB SCRAPING COMPLETED!")
            logger.info("=" * 80)
            logger.info(f"📊 EXECUTION SUMMARY:")
            logger.info(f"   - Jobs Created: {results.get('total_jobs', 0)}")
            logger.info(f"   - Questions Collected: {results.get('total_questions_collected', 0)}")
            logger.info(f"   - Execution Time: {execution_time / 60:.1f} minutes")
            logger.info(f"   - Questions per Minute: {results.get('total_questions_collected', 0) / max(execution_time / 60, 1):.1f}")
            logger.info("=" * 80)
            logger.info(f"💾 FINAL DATABASE STATUS:")
            logger.info(f"   - Questions in System: {final_counts.get('system_questions', 0)}")
            logger.info(f"   - Active Jobs: {final_counts.get('active_jobs', 0)}")
            logger.info("=" * 80)
            logger.info(f"🎯 FINAL RESULT: {self.total_questions_collected} QUESTIONS COLLECTED!")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical error in scraping process: {str(e)}")
            return False

async def main():
    """Main execution function"""
    async with SimpleWebScraperRunner() as runner:
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