#!/usr/bin/env python3
"""
Advanced IndiaBix Scraper - Get 10 Logical Questions
Robust scraper to collect exactly 10 logical reasoning questions with proper options
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Set up environment
os.environ['DISPLAY'] = ':99'
load_dotenv()

sys.path.append('/app/backend')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedIndiaBixScraper:
    def __init__(self):
        self.questions_collected = []
        self.target_count = 10
        
    def setup_driver(self):
        """Setup Chrome driver"""
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.binary_location = "/usr/bin/chromium"
        
        service = ChromeService("/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined,});")
        
    def analyze_page_structure(self, url):
        """Analyze the page structure to understand how to extract data"""
        logger.info(f"🔍 Analyzing page structure: {url}")
        
        self.driver.get(url)
        time.sleep(3)
        
        # Take a screenshot for debugging
        screenshot_path = f"/app/debug_page_{int(time.time())}.png"
        self.driver.save_screenshot(screenshot_path)
        logger.info(f"📸 Screenshot saved: {screenshot_path}")
        
        # Check if this is the actual question page structure
        page_source = self.driver.page_source
        
        # Look for question patterns
        if "question" in page_source.lower():
            logger.info("✅ Page contains 'question' text")
        
        # Try to find the main content area
        main_content_selectors = [
            "div.main-content",
            "div.content-area", 
            "div.question-area",
            "div#main",
            "div.container",
            "body"
        ]
        
        for selector in main_content_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    content_text = element.text
                    logger.info(f"📝 Found content area with {selector}: {len(content_text)} characters")
                    if len(content_text) > 100:
                        return element
            except:
                continue
        
        return None
    
    def extract_question_from_content(self, content_element, url, question_num):
        """Extract question data from content element"""
        try:
            question_data = {
                'source': 'IndiaBix',
                'category': 'logical',
                'subcategory': 'logical_reasoning',
                'scraped_at': datetime.utcnow(),
                'url': url,
                'question_number': question_num
            }
            
            # Get all text content
            all_text = content_element.text
            
            # Split into lines and analyze
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Look for question text (usually contains patterns like "Look at", "What", "Which")
            question_text = None
            question_indicators = ["Look at", "What", "Which", "How", "Find", "Choose", "Select"]
            
            for line in lines:
                for indicator in question_indicators:
                    if indicator in line and len(line) > 20 and "?" in line:
                        question_text = line
                        logger.info(f"   🎯 Found question: {question_text}")
                        break
                if question_text:
                    break
            
            if not question_text:
                # Try to find any line that looks like a question
                for line in lines:
                    if len(line) > 30 and ("?" in line or len(line.split()) > 8):
                        # Check if it's not navigation or title text
                        if not any(nav in line.lower() for nav in ["home", "about", "contact", "menu", "nav"]):
                            question_text = line
                            logger.info(f"   🎯 Found alternative question: {question_text}")
                            break
            
            if not question_text:
                logger.warning(f"   ❌ No question text found")
                return None
            
            question_data['question_text'] = question_text
            
            # Look for options - they usually come after the question
            options = []
            question_index = None
            
            # Find where the question appears in the lines
            for i, line in enumerate(lines):
                if question_text in line:
                    question_index = i
                    break
            
            if question_index is not None:
                # Look for options after the question
                potential_options = lines[question_index + 1:question_index + 8]  # Look in next 7 lines
                
                for line in potential_options:
                    # Options are usually short, single statements
                    if (len(line) > 5 and len(line) < 100 and 
                        not any(skip in line.lower() for skip in ["home", "about", "contact", "view answer", "workspace", "report", "discuss"]) and
                        line not in question_text):
                        
                        # Check if it looks like an option (starts with A), B), etc. or is a short statement)
                        if (line.startswith(("A)", "B)", "C)", "D)", "A.", "B.", "C.", "D.", "1)", "2)", "3)", "4)")) or
                            (len(line.split()) < 8 and not line.endswith(":") and "?" not in line)):
                            options.append(line)
            
            # If we still don't have good options, try a different approach
            if len(options) < 2:
                options = []
                # Look for any short lines that could be options
                for line in lines:
                    if (5 < len(line) < 50 and 
                        len(line.split()) < 6 and
                        line != question_text and
                        not any(skip in line.lower() for skip in ["home", "view", "answer", "report", "discuss", "workspace"])):
                        options.append(line)
                    
                    if len(options) >= 4:
                        break
            
            question_data['options'] = options[:4]  # Max 4 options
            
            # Look for explanation/answer (usually after "Answer" or "Explanation")
            explanation = ""
            for i, line in enumerate(lines):
                if any(word in line.lower() for word in ["answer", "explanation", "solution"]):
                    if i + 1 < len(lines):
                        explanation = lines[i + 1]
                        break
            
            question_data['explanation'] = explanation
            
            logger.info(f"   ✅ Extracted question with {len(options)} options")
            return question_data
            
        except Exception as e:
            logger.error(f"   ❌ Error extracting question: {e}")
            return None
    
    def scrape_questions(self):
        """Main scraping method"""
        logger.info("🚀 Starting advanced IndiaBix scraping")
        
        # Try different URL patterns to find questions
        url_patterns = [
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/{:06d}",
            "https://www.indiabix.com/logical-reasoning/logical-sequences-and-series/{:06d}",
            "https://www.indiabix.com/logical-reasoning/verbal-classification/{:06d}",
            "https://www.indiabix.com/logical-reasoning/analogy/{:06d}",
        ]
        
        question_count = 0
        
        for pattern in url_patterns:
            if question_count >= self.target_count:
                break
                
            logger.info(f"🔍 Trying pattern: {pattern}")
            
            for i in range(1, 20):  # Try first 20 questions in each category
                if question_count >= self.target_count:
                    break
                    
                url = pattern.format(i)
                
                try:
                    logger.info(f"📖 Scraping question {question_count + 1}: {url}")
                    
                    content_element = self.analyze_page_structure(url)
                    
                    if content_element:
                        question_data = self.extract_question_from_content(content_element, url, question_count + 1)
                        
                        if question_data and len(question_data['question_text']) > 20:
                            self.questions_collected.append(question_data)
                            question_count += 1
                            logger.info(f"   ✅ Successfully collected question {question_count}/{self.target_count}")
                        else:
                            logger.warning(f"   ⚠️ Invalid question data, skipping")
                    else:
                        logger.warning(f"   ⚠️ No content found on page")
                        
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"   ❌ Error scraping {url}: {e}")
                    continue
        
        logger.info(f"🎉 Scraping completed! Collected {len(self.questions_collected)} questions")
        return self.questions_collected
    
    def save_results(self):
        """Save results to JSON and database"""
        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"/app/indiabix_advanced_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.questions_collected, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {filename}")
        
        # Save to database
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = MongoClient(mongo_url)
            db = client.aptitude_questions
            collection = db.scraped_questions
            
            if self.questions_collected:
                result = collection.insert_many(self.questions_collected)
                logger.info(f"💾 Saved {len(result.inserted_ids)} questions to MongoDB")
            
            client.close()
            
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
        
        return filename
    
    def run(self):
        """Main execution method"""
        try:
            self.setup_driver()
            questions = self.scrape_questions()
            filename = self.save_results()
            
            return questions, filename
            
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    scraper = AdvancedIndiaBixScraper()
    questions, filename = scraper.run()
    
    print(f"\n🎉 SCRAPING COMPLETED!")
    print(f"📊 Total questions collected: {len(questions)}")
    print(f"💾 Results saved to: {filename}")
    
    if questions:
        print(f"\n📝 Sample questions:")
        for i, q in enumerate(questions[:3]):
            print(f"{i+1}. {q['question_text'][:80]}...")
            if q['options']:
                print(f"   Options: {q['options'][:2]}")

if __name__ == "__main__":
    main()