#!/usr/bin/env python3
"""
IndiaBix Logical Questions Scraper
Focused script to extract exactly 10 logical reasoning questions from IndiaBix
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Set up environment
os.environ['DISPLAY'] = ':99'
load_dotenv()

# Add backend to path
sys.path.append('/app/backend')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# MongoDB imports
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/scraping.log')
    ]
)
logger = logging.getLogger(__name__)

class IndiaBixLogicalScraper:
    """Scraper focused on IndiaBix logical reasoning questions"""
    
    def __init__(self):
        self.driver = None
        self.questions_collected = []
        self.target_count = 10
        self.base_url = "https://www.indiabix.com/logical-reasoning"
        
        # Database setup
        self.setup_database()
        
    def setup_database(self):
        """Setup MongoDB connection"""
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            self.client = MongoClient(mongo_url)
            self.db = self.client.aptitude_questions
            self.collection = self.db.scraped_questions
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.client = None
            self.db = None
            self.collection = None
    
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        try:
            logger.info("🚀 Setting up Chrome driver...")
            
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--window-size=1920,1080")
            
            # Anti-detection measures
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Chromium binary path
            options.binary_location = "/usr/bin/chromium"
            
            # Chrome driver service
            service = ChromeService("/usr/bin/chromedriver")
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Execute anti-detection script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined,});")
            
            logger.info("✅ Chrome driver setup successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Chrome driver setup failed: {e}")
            return False
    
    def scrape_logical_questions(self):
        """Scrape logical reasoning questions from IndiaBix"""
        try:
            # Navigate to logical reasoning section
            logger.info("🌐 Navigating to IndiaBix logical reasoning...")
            self.driver.get("https://www.indiabix.com/logical-reasoning/logical-reasoning")
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if page loaded correctly
            page_title = self.driver.title
            logger.info(f"📄 Page title: {page_title}")
            
            # Look for questions on the page
            questions_found = 0
            page_num = 1
            
            while questions_found < self.target_count:
                logger.info(f"📖 Processing page {page_num}...")
                
                # Extract questions from current page
                questions = self.extract_questions_from_page()
                
                if not questions:
                    logger.warning(f"⚠️ No questions found on page {page_num}")
                    # Try to find and click next button
                    if not self.go_to_next_page():
                        logger.error("❌ No more pages available")
                        break
                    page_num += 1
                    continue
                
                # Add questions to collection
                for question in questions:
                    if questions_found >= self.target_count:
                        break
                    
                    self.questions_collected.append(question)
                    questions_found += 1
                    logger.info(f"✅ Question {questions_found}/10 collected")
                
                # If we haven't reached target, go to next page
                if questions_found < self.target_count:
                    if not self.go_to_next_page():
                        logger.warning("⚠️ No more pages available, stopping collection")
                        break
                    page_num += 1
                    time.sleep(2)  # Rate limiting
            
            logger.info(f"🎉 Successfully collected {len(self.questions_collected)} logical questions!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {e}")
            return False
    
    def extract_questions_from_page(self):
        """Extract questions from the current page"""
        questions = []
        
        try:
            # Wait for question content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.bix-div-container"))
            )
            
            # Look for question container
            question_container = self.driver.find_element(By.CSS_SELECTOR, "div.bix-div-container")
            
            if question_container:
                question_data = self.extract_single_question(question_container)
                if question_data:
                    questions.append(question_data)
            
        except TimeoutException:
            logger.warning("⚠️ Timeout waiting for questions to load")
        except NoSuchElementException:
            logger.warning("⚠️ Question container not found")
        except Exception as e:
            logger.warning(f"⚠️ Error extracting questions: {e}")
        
        return questions
    
    def extract_single_question(self, container):
        """Extract a single question from its container"""
        try:
            question_data = {
                'source': 'IndiaBix',
                'category': 'logical',
                'subcategory': 'logical_reasoning',
                'scraped_at': datetime.utcnow(),
                'url': self.driver.current_url
            }
            
            # Extract question text
            try:
                question_element = container.find_element(By.CSS_SELECTOR, "div.bix-td-qtxt")
                question_data['question_text'] = question_element.text.strip()
            except NoSuchElementException:
                logger.warning("⚠️ Question text not found")
                return None
            
            # Extract options
            try:
                option_elements = container.find_elements(By.CSS_SELECTOR, "table.bix-tbl-options td")
                options = []
                for option_elem in option_elements:
                    option_text = option_elem.text.strip()
                    if option_text and len(option_text) > 1:  # Skip empty or single character options
                        options.append(option_text)
                
                question_data['options'] = options[:4]  # Usually 4 options
            except NoSuchElementException:
                logger.warning("⚠️ Options not found")
                question_data['options'] = []
            
            # Extract answer/explanation (if available)
            try:
                answer_element = container.find_element(By.CSS_SELECTOR, "div.bix-div-answer")
                question_data['explanation'] = answer_element.text.strip()
            except NoSuchElementException:
                question_data['explanation'] = ""
            
            # Basic validation
            if len(question_data['question_text']) < 10:
                logger.warning("⚠️ Question text too short, skipping")
                return None
            
            if len(question_data['options']) < 2:
                logger.warning("⚠️ Not enough options found, skipping")
                return None
            
            logger.info(f"📝 Extracted question: {question_data['question_text'][:50]}...")
            return question_data
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting single question: {e}")
            return None
    
    def go_to_next_page(self):
        """Navigate to the next page"""
        try:
            # Look for next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a.bix-btn-next")
            if next_button and next_button.is_enabled():
                next_button.click()
                time.sleep(3)  # Wait for page load
                return True
        except NoSuchElementException:
            pass
        
        # If no next button, try pagination links
        try:
            # Get current page number
            current_page_elem = self.driver.find_element(By.CSS_SELECTOR, "span.current")
            current_page = int(current_page_elem.text)
            next_page = current_page + 1
            
            # Look for next page link
            next_page_link = self.driver.find_element(By.XPATH, f"//div[@class='bix-pagination']//a[text()='{next_page}']")
            if next_page_link:
                next_page_link.click()
                time.sleep(3)
                return True
        except (NoSuchElementException, ValueError):
            pass
        
        return False
    
    def save_to_database(self):
        """Save collected questions to MongoDB"""
        if not self.collection or not self.questions_collected:
            logger.warning("⚠️ No database connection or no questions to save")
            return False
        
        try:
            logger.info("💾 Saving questions to database...")
            
            # Insert questions into collection
            result = self.collection.insert_many(self.questions_collected)
            inserted_count = len(result.inserted_ids)
            
            logger.info(f"✅ Successfully saved {inserted_count} questions to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            return False
    
    def save_to_json(self):
        """Save collected questions to JSON file as backup"""
        try:
            filename = f"/app/indiabix_logical_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.questions_collected, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"✅ Questions saved to JSON file: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error saving to JSON: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("🧹 Driver cleaned up")
            
            if self.client:
                self.client.close()
                logger.info("🧹 Database connection closed")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting IndiaBix Logical Questions Scraper")
        logger.info(f"🎯 Target: {self.target_count} logical reasoning questions")
        
        try:
            # Setup driver
            if not self.setup_driver():
                logger.error("❌ Failed to setup driver")
                return False
            
            # Scrape questions
            if not self.scrape_logical_questions():
                logger.error("❌ Failed to scrape questions")
                return False
            
            # Save to database
            self.save_to_database()
            
            # Save backup JSON file
            json_file = self.save_to_json()
            
            # Summary
            logger.info("📊 SCRAPING SUMMARY:")
            logger.info(f"   📝 Questions collected: {len(self.questions_collected)}")
            logger.info(f"   💾 Database saved: {'Yes' if self.collection else 'No'}")
            logger.info(f"   📄 JSON backup: {json_file if json_file else 'Failed'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during execution: {e}")
            return False
            
        finally:
            self.cleanup()

def main():
    """Main function"""
    scraper = IndiaBixLogicalScraper()
    success = scraper.run()
    
    if success:
        print("\n🎉 SUCCESS: IndiaBix logical questions scraping completed!")
        print(f"✅ Collected {len(scraper.questions_collected)} questions")
    else:
        print("\n❌ FAILED: Scraping encountered errors")
        print("📋 Check /app/scraping.log for details")

if __name__ == "__main__":
    main()