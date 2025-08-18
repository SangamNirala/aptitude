#!/usr/bin/env python3
"""
Test Web Scraping with Updated Selectors
Direct scraping test to verify the fixes work
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time

# Add backend to path
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectScrapingTest:
    def __init__(self):
        self.driver = None
        self.questions_found = []
        
    def setup_chrome_driver(self):
        """Setup Chrome driver with proper configuration"""
        try:
            logger.info("🚗 Setting up Chrome driver...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("✅ Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up Chrome driver: {e}")
            return False
    
    def test_indiabix_scraping(self):
        """Test scraping IndiaBix with updated selectors"""
        logger.info("🎯 Testing IndiaBix scraping...")
        
        try:
            # Navigate to IndiaBix aptitude page
            url = "https://www.indiabix.com/aptitude/arithmetic-aptitude"
            logger.info(f"📍 Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(5)  # Allow page to load
            
            # Get page source and check with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            logger.info(f"📄 Page loaded - Title: {self.driver.title}")
            logger.info(f"📊 Page size: {len(page_source)} characters")
            
            # Test updated selectors from the fix
            updated_selectors = [
                ("div.question-content", "question content"),
                ("div.problem-statement", "problem statement"),
                (".question-text", "question text"),
                ("div.options li", "options list items"),
                ("ul.options li", "options unordered list"),
                ("div.choice-container", "choice container"),
                (".option-item", "option items"),
                ("div[class*='option']", "option divs"),
                ("div.answer-explanation", "answer explanation"),
                ("div.solution", "solution"),
                (".correct-answer", "correct answer"),
            ]
            
            logger.info("🔍 Testing updated selectors:")
            questions_found = 0
            
            for selector, description in updated_selectors:
                try:
                    elements = soup.select(selector)
                    logger.info(f"  {selector} ({description}): {len(elements)} elements")
                    
                    if elements:
                        questions_found += len(elements)
                        # Log sample content
                        for i, elem in enumerate(elements[:2]):
                            text = elem.get_text(strip=True)[:100]
                            if text:
                                logger.info(f"    Sample [{i}]: {text}...")
                except Exception as e:
                    logger.error(f"    Error with selector {selector}: {e}")
            
            # Try to find any quiz/question related content
            logger.info("🔎 Looking for any quiz content:")
            
            # Look for forms (quiz questions often in forms)
            forms = soup.find_all('form')
            logger.info(f"  Forms found: {len(forms)}")
            
            # Look for radio buttons/checkboxes (common in MCQs)
            inputs = soup.find_all('input', type=['radio', 'checkbox'])
            logger.info(f"  Radio/checkbox inputs: {len(inputs)}")
            
            # Look for any text containing question markers
            question_indicators = ['?', 'A)', 'B)', 'C)', 'D)', 'Answer:', 'Question']
            for indicator in question_indicators:
                count = page_source.count(indicator)
                if count > 0:
                    logger.info(f"  '{indicator}' found: {count} times")
            
            # Check if this is actually a quiz page
            if 'quiz' in page_source.lower():
                logger.info("  ✅ Page contains quiz content")
            else:
                logger.warning("  ⚠️ Page may not have quiz content - might need different URL")
                
                # Try to find quiz links
                quiz_links = soup.find_all('a', href=True)
                quiz_urls = []
                for link in quiz_links:
                    href = link.get('href', '')
                    if 'quiz' in href.lower() or 'test' in href.lower():
                        quiz_urls.append(href)
                
                if quiz_urls:
                    logger.info(f"  📝 Found {len(quiz_urls)} potential quiz links")
                    for i, url in enumerate(quiz_urls[:3]):
                        logger.info(f"    [{i}]: {url}")
                        
                        # Try the first quiz link
                        if i == 0 and not url.startswith('http'):
                            full_url = 'https://www.indiabix.com' + url if url.startswith('/') else url
                            logger.info(f"  🎯 Trying quiz link: {full_url}")
                            
                            try:
                                self.driver.get(full_url)
                                time.sleep(3)
                                quiz_source = self.driver.page_source
                                quiz_soup = BeautifulSoup(quiz_source, 'html.parser')
                                
                                # Test selectors on quiz page
                                for selector, description in updated_selectors[:5]:
                                    elements = quiz_soup.select(selector)
                                    if elements:
                                        logger.info(f"    Quiz page - {selector}: {len(elements)} elements")
                                        questions_found += len(elements)
                            
                            except Exception as e:
                                logger.error(f"    Error accessing quiz link: {e}")
            
            logger.info(f"🎉 IndiaBix test completed - Total potential questions found: {questions_found}")
            return questions_found > 0
            
        except Exception as e:
            logger.error(f"❌ Error testing IndiaBix: {e}")
            return False
    
    def check_database_for_questions(self):
        """Check if any questions were stored in the database"""
        logger.info("💾 Checking database for questions...")
        
        try:
            from dotenv import load_dotenv
            load_dotenv('/app/backend/.env')
            
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            
            async def check_db():
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                client = AsyncIOMotorClient(mongo_url)
                db = client[os.environ.get('DB_NAME', 'test_database')]
                
                # Check different collections for questions
                collections_to_check = [
                    'enhanced_questions',
                    'processed_scraped_questions', 
                    'raw_extracted_questions',
                    'scraping_jobs'
                ]
                
                total_questions = 0
                for collection_name in collections_to_check:
                    count = await db[collection_name].count_documents({})
                    logger.info(f"  {collection_name}: {count} documents")
                    if 'question' in collection_name.lower():
                        total_questions += count
                
                # Get latest scraping jobs
                jobs = await db.scraping_jobs.find().sort('created_at', -1).limit(3).to_list(3)
                for job in jobs:
                    job_name = job.get('config', {}).get('job_name', 'Unknown')
                    status = job.get('status', 'unknown')
                    logger.info(f"  Recent job: {job_name} - Status: {status}")
                
                client.close()
                return total_questions
            
            total_questions = asyncio.run(check_db())
            logger.info(f"📊 Total questions in database: {total_questions}")
            return total_questions
            
        except Exception as e:
            logger.error(f"❌ Error checking database: {e}")
            return 0
    
    def run_test(self):
        """Run the complete test"""
        logger.info("🚀 Starting direct web scraping test...")
        logger.info("=" * 60)
        
        try:
            # Setup Chrome driver
            if not self.setup_chrome_driver():
                return False
            
            # Test IndiaBix scraping
            indiabix_success = self.test_indiabix_scraping()
            
            # Check database
            questions_in_db = self.check_database_for_questions()
            
            logger.info("=" * 60)
            logger.info("🎯 TEST RESULTS:")
            logger.info(f"  IndiaBix selector test: {'✅ PASSED' if indiabix_success else '❌ FAILED'}")
            logger.info(f"  Questions in database: {questions_in_db}")
            logger.info("=" * 60)
            
            if indiabix_success and questions_in_db > 0:
                logger.info("🎉 SUCCESS: Scraping system is working!")
                return True
            elif indiabix_success:
                logger.info("⚠️ PARTIAL SUCCESS: Selectors working but need to run full scraping job")
                return True
            else:
                logger.info("❌ FAILURE: Selectors still need adjustment")
                return False
                
        except Exception as e:
            logger.error(f"❌ Critical error in test: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main test execution"""
    test = DirectScrapingTest()
    success = test.run_test()
    
    if success:
        logger.info("✅ Web scraping test completed successfully!")
        return 0
    else:
        logger.error("❌ Web scraping test failed!")
        return 1

if __name__ == "__main__":
    # Set display for headless operation
    os.environ['DISPLAY'] = ':99'
    exit_code = main()
    exit(exit_code)