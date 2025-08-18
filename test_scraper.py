#!/usr/bin/env python3
"""
Simple IndiaBix Scraper - Test and Collect Questions
Direct approach to scrape IndiaBix logical reasoning questions
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

# Add backend to path
sys.path.append('/app/backend')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions

# MongoDB imports
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_indiabix_page():
    """Test IndiaBix page and explore structure"""
    
    # Setup Chrome
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"
    
    service = ChromeService("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        logger.info("🌐 Testing IndiaBix page structure...")
        
        # Test different URLs
        test_urls = [
            "https://www.indiabix.com/logical-reasoning/logical-reasoning",
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/001001",
            "https://www.indiabix.com/aptitude/logical-reasoning/logical-reasoning",
        ]
        
        for url in test_urls:
            try:
                logger.info(f"🔍 Testing URL: {url}")
                driver.get(url)
                time.sleep(3)
                
                # Get page title
                title = driver.title
                logger.info(f"   Title: {title}")
                
                # Get page source length
                source_length = len(driver.page_source)
                logger.info(f"   Source length: {source_length}")
                
                # Look for common selectors
                selectors = [
                    "div.bix-div-container",
                    "div.bix-td-qtxt",
                    "table.bix-tbl-options",
                    "div.question",
                    "div.content",
                    "div.mcq",
                    ".question-text",
                    ".options"
                ]
                
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logger.info(f"   ✅ Found {len(elements)} elements with selector: {selector}")
                            if selector in ["div.bix-div-container", "div.bix-td-qtxt"]:
                                for i, elem in enumerate(elements[:2]):
                                    text = elem.text.strip()[:100]
                                    logger.info(f"      Element {i}: {text}...")
                        else:
                            logger.info(f"   ❌ No elements found for: {selector}")
                    except Exception as e:
                        logger.info(f"   ⚠️ Error with selector {selector}: {e}")
                
                # Look for any text that might be questions
                page_text = driver.page_source
                if "Question" in page_text or "Which" in page_text or "What" in page_text:
                    logger.info("   ✅ Page contains question-like content")
                else:
                    logger.info("   ❌ No obvious question content found")
                
                logger.info("   ---")
                
            except Exception as e:
                logger.error(f"   ❌ Error testing {url}: {e}")
                
    finally:
        driver.quit()

def scrape_indiabix_direct():
    """Direct scraping approach"""
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"
    
    service = ChromeService("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    questions_collected = []
    
    try:
        logger.info("🚀 Starting direct IndiaBix scraping...")
        
        # Try individual question pages
        base_urls = [
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/001001",
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/001002", 
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/001003",
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/001004",
            "https://www.indiabix.com/logical-reasoning/logical-reasoning/001005",
        ]
        
        for i, url in enumerate(base_urls):
            if len(questions_collected) >= 10:
                break
                
            try:
                logger.info(f"📖 Scraping question {i+1}: {url}")
                driver.get(url)
                time.sleep(2)
                
                # Extract question data
                question_data = {
                    'source': 'IndiaBix',
                    'category': 'logical',
                    'subcategory': 'logical_reasoning',
                    'scraped_at': datetime.utcnow(),
                    'url': url,
                    'question_number': i+1
                }
                
                # Try multiple approaches to find question text
                question_text = None
                question_selectors = [
                    "div.bix-td-qtxt",
                    "div.question-text",
                    "td.bix-td-qtxt",
                    ".question",
                    "div[class*='question']"
                ]
                
                for selector in question_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if elem and elem.text.strip():
                            question_text = elem.text.strip()
                            logger.info(f"   ✅ Found question with {selector}: {question_text[:50]}...")
                            break
                    except:
                        continue
                
                if not question_text:
                    # Try to find any text that looks like a question
                    page_text = driver.page_source
                    if "Which" in page_text or "What" in page_text or "How" in page_text:
                        # Extract first paragraph or div that contains question words
                        try:
                            all_text_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Which') or contains(text(), 'What') or contains(text(), 'How')]")
                            for elem in all_text_elements:
                                text = elem.text.strip()
                                if len(text) > 20 and ("?" in text or len(text.split()) > 5):
                                    question_text = text
                                    logger.info(f"   ✅ Found question from text search: {question_text[:50]}...")
                                    break
                        except:
                            pass
                
                if question_text:
                    question_data['question_text'] = question_text
                    
                    # Try to find options
                    options = []
                    option_selectors = [
                        "table.bix-tbl-options td",
                        "td.bix-td-option",
                        ".option",
                        "label",
                        "li"
                    ]
                    
                    for selector in option_selectors:
                        try:
                            option_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in option_elements:
                                opt_text = elem.text.strip()
                                if opt_text and len(opt_text) > 1 and len(opt_text) < 200:
                                    options.append(opt_text)
                            
                            if len(options) >= 2:
                                logger.info(f"   ✅ Found {len(options)} options with {selector}")
                                break
                        except:
                            continue
                    
                    question_data['options'] = options[:4]
                    
                    # Try to find explanation
                    explanation = ""
                    explanation_selectors = [
                        "div.bix-div-answer",
                        "div.explanation",
                        "div.answer"
                    ]
                    
                    for selector in explanation_selectors:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, selector)
                            if elem and elem.text.strip():
                                explanation = elem.text.strip()
                                break
                        except:
                            continue
                    
                    question_data['explanation'] = explanation
                    
                    # Add to collection if valid
                    if len(question_text) > 10:
                        questions_collected.append(question_data)
                        logger.info(f"   ✅ Question {len(questions_collected)} collected successfully")
                    else:
                        logger.warning(f"   ⚠️ Question too short, skipping")
                else:
                    logger.warning(f"   ⚠️ No question text found for {url}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error scraping {url}: {e}")
        
        # Save results
        logger.info(f"📊 Collected {len(questions_collected)} questions total")
        
        # Save to JSON
        filename = f"/app/indiabix_direct_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(questions_collected, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {filename}")
        
        # Save to database
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = MongoClient(mongo_url)
            db = client.aptitude_questions
            collection = db.scraped_questions
            
            if questions_collected:
                result = collection.insert_many(questions_collected)
                logger.info(f"💾 Saved {len(result.inserted_ids)} questions to database")
            
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
        
        return questions_collected
        
    finally:
        driver.quit()

def main():
    logger.info("🔬 Phase 1: Testing IndiaBix page structure")
    test_indiabix_page()
    
    logger.info("\n🚀 Phase 2: Direct scraping attempt")
    questions = scrape_indiabix_direct()
    
    print(f"\n📊 RESULTS:")
    print(f"   Questions collected: {len(questions)}")
    if questions:
        print(f"   Sample question: {questions[0]['question_text'][:100]}...")

if __name__ == "__main__":
    main()