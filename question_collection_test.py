#!/usr/bin/env python3
"""
Focused test for question collection from web scraping
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuestionCollectionTester:
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://aptitude-test-repair.preview.emergentagent.com/api"
        except:
            self.base_url = "https://aptitude-test-repair.preview.emergentagent.com/api"
        
        self.session = None
        self.created_job_ids = []
        self.total_questions_collected = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_and_start_job(self, source_name, job_name, max_questions=50):
        """Create and start a scraping job"""
        try:
            payload = {
                "job_name": job_name,
                "source_names": [source_name],
                "max_questions_per_source": max_questions,
                "target_categories": ["quantitative", "logical", "verbal"] if source_name == "IndiaBix" else ["programming", "algorithms"],
                "priority_level": 1,
                "enable_ai_processing": False,
                "enable_duplicate_detection": False
            }
            
            # Create job
            async with self.session.post(f"{self.base_url}/scraping/jobs", json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    job_id = data.get("job_id")
                    self.created_job_ids.append(job_id)
                    logger.info(f"✅ Job created: {job_id} for {source_name}")
                    
                    # Start job
                    async with self.session.put(f"{self.base_url}/scraping/jobs/{job_id}/start") as start_response:
                        if start_response.status == 200:
                            start_data = await start_response.json()
                            logger.info(f"✅ Job started: {job_id} - Status: {start_data.get('status')}")
                            return job_id
                        else:
                            error_text = await start_response.text()
                            logger.error(f"❌ Failed to start job {job_id}: {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create job for {source_name}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Exception creating job for {source_name}: {str(e)}")
            return None
    
    async def monitor_job_progress(self, job_id, source_name, max_wait_minutes=10):
        """Monitor job progress and collect question statistics"""
        logger.info(f"📊 Monitoring job {job_id[:8]} for {source_name}...")
        
        max_checks = max_wait_minutes * 2  # Check every 30 seconds
        questions_collected = 0
        
        for check in range(max_checks):
            try:
                async with self.session.get(f"{self.base_url}/scraping/jobs/{job_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        status = data.get("status", "unknown")
                        error_message = data.get("error_message", "")
                        questions_extracted = data.get("questions_extracted", 0) or data.get("total_questions_extracted", 0)
                        
                        # Try to get questions from statistics or progress
                        statistics = data.get("statistics", {})
                        if statistics:
                            questions_extracted = max(questions_extracted, statistics.get("questions_extracted", 0))
                        
                        progress = data.get("progress", {})
                        if progress:
                            questions_extracted = max(questions_extracted, progress.get("questions_extracted", 0))
                        
                        logger.info(f"Check {check+1}: {source_name} - Status: {status}, Questions: {questions_extracted}")
                        
                        if questions_extracted > questions_collected:
                            questions_collected = questions_extracted
                        
                        if status == "completed":
                            logger.info(f"✅ Job {job_id[:8]} completed! Questions collected: {questions_collected}")
                            break
                        elif status == "failed":
                            logger.error(f"❌ Job {job_id[:8]} failed: {error_message}")
                            break
                        elif status == "running":
                            logger.info(f"🔄 Job {job_id[:8]} running... Questions so far: {questions_collected}")
                    else:
                        logger.warning(f"⚠️ Failed to get job status: {response.status}")
                
                await asyncio.sleep(30)  # Wait 30 seconds between checks
                
            except Exception as e:
                logger.error(f"❌ Error monitoring job {job_id[:8]}: {str(e)}")
        
        self.total_questions_collected += questions_collected
        logger.info(f"📊 Final count for {source_name}: {questions_collected} questions")
        return questions_collected
    
    async def test_question_collection(self):
        """Test question collection from both sources"""
        logger.info("🚀 Starting Question Collection Test...")
        
        # Create and start jobs for both sources
        indiabix_job_id = await self.create_and_start_job("IndiaBix", "IndiaBix_Collection_Test", 100)
        geeksforgeeks_job_id = await self.create_and_start_job("GeeksforGeeks", "GeeksforGeeks_Collection_Test", 100)
        
        # Monitor both jobs concurrently
        tasks = []
        if indiabix_job_id:
            tasks.append(self.monitor_job_progress(indiabix_job_id, "IndiaBix", 8))
        if geeksforgeeks_job_id:
            tasks.append(self.monitor_job_progress(geeksforgeeks_job_id, "GeeksforGeeks", 8))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            indiabix_questions = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else 0
            geeksforgeeks_questions = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else 0
            
            logger.info("=" * 80)
            logger.info("📊 QUESTION COLLECTION RESULTS")
            logger.info("=" * 80)
            logger.info(f"IndiaBix Questions Collected: {indiabix_questions}")
            logger.info(f"GeeksforGeeks Questions Collected: {geeksforgeeks_questions}")
            logger.info(f"Total Questions Collected: {self.total_questions_collected}")
            logger.info("=" * 80)
            
            return self.total_questions_collected
        else:
            logger.error("❌ No jobs were started successfully")
            return 0
    
    async def run_test(self):
        """Run the question collection test"""
        logger.info("🎯 CRITICAL TEST: Question Collection from Web Scraping")
        logger.info("🎯 Goal: Collect questions from IndiaBix and GeeksforGeeks sources")
        
        total_questions = await self.test_question_collection()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 QUESTION COLLECTION TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Questions Collected: {total_questions}")
        logger.info(f"Jobs Created: {len(self.created_job_ids)}")
        
        if total_questions > 0:
            logger.info("✅ SUCCESS: Questions were successfully collected from web scraping!")
        else:
            logger.error("❌ FAILURE: No questions were collected from web scraping")
        
        logger.info("=" * 80)
        
        return total_questions

async def main():
    async with QuestionCollectionTester() as tester:
        questions_collected = await tester.run_test()
        
        print(f"\n🎯 FINAL RESULT: {questions_collected} questions collected from web scraping")
        
        if questions_collected > 0:
            print("✅ QUESTION COLLECTION: SUCCESS")
        else:
            print("❌ QUESTION COLLECTION: FAILED")

if __name__ == "__main__":
    asyncio.run(main())