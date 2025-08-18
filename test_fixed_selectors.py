#!/usr/bin/env python3
"""
Test the fixed BIX selectors on actual IndiaBix question pages
"""

import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedSelectorsTest:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver"""
        try:
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
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def test_question_page(self, url, page_name):
        """Test selectors on a specific question page"""
        logger.info(f"🎯 Testing {page_name}: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            logger.info(f"📄 Page title: {self.driver.title}")
            logger.info(f"📊 Page size: {len(page_source)} characters")
            
            # Test our fixed BIX selectors
            selectors_to_test = {
                "div.bix-td-qtxt": "question text",
                "table.bix-tbl-options": "options table", 
                "div.bix-div-answer": "answer",
                "div.bix-td-qno": "question number",
                "div.bix-div-container": "question container"
            }
            
            total_elements = 0
            successful_selectors = 0
            
            logger.info("🔍 Testing fixed BIX selectors:")
            for selector, description in selectors_to_test.items():
                try:
                    elements = soup.select(selector)
                    count = len(elements)
                    total_elements += count
                    
                    if count > 0:
                        successful_selectors += 1
                        logger.info(f"  ✅ {selector} ({description}): {count} elements found")
                        
                        # Show sample content for first few elements
                        for i, elem in enumerate(elements[:3]):
                            text = elem.get_text(strip=True)
                            if text and len(text) > 10:
                                sample_text = text[:80] + "..." if len(text) > 80 else text
                                logger.info(f"    [{i+1}]: {sample_text}")
                    else:
                        logger.warning(f"  ❌ {selector} ({description}): 0 elements found")
                        
                except Exception as e:
                    logger.error(f"    Error testing {selector}: {e}")
            
            # Test for option-specific content
            logger.info("🔍 Looking for multiple choice options:")
            option_patterns = [
                "td.bix-td-option",
                "td.bix-td-option-val", 
                "div.bix-ans-option",
                "table.bix-tbl-options td"
            ]
            
            options_found = 0
            for pattern in option_patterns:
                elements = soup.select(pattern)
                if elements:
                    logger.info(f"  ✅ {pattern}: {len(elements)} option elements")
                    options_found += len(elements)
                    
                    # Show sample options
                    for i, elem in enumerate(elements[:4]):
                        text = elem.get_text(strip=True)
                        if text and len(text) < 100:
                            logger.info(f"    Option [{i+1}]: {text}")
            
            # Summary
            logger.info(f"📊 Results for {page_name}:")
            logger.info(f"  Total elements found: {total_elements}")
            logger.info(f"  Successful selectors: {successful_selectors}/{len(selectors_to_test)}")
            logger.info(f"  Multiple choice options: {options_found}")
            
            success = total_elements > 0 and successful_selectors >= 3
            status = "✅ SUCCESSFUL" if success else "❌ NEEDS WORK"
            logger.info(f"  Status: {status}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error testing {page_name}: {e}")
            return False
    
    def test_multiple_question_pages(self):
        """Test on multiple actual question pages"""
        question_pages = [
            ("https://www.indiabix.com/aptitude/time-and-work", "Time and Work"),
            ("https://www.indiabix.com/aptitude/problems-on-numbers", "Problems on Numbers"),
            ("https://www.indiabix.com/aptitude/percentage", "Percentage"),
            ("https://www.indiabix.com/aptitude/profit-and-loss", "Profit and Loss"),
            ("https://www.indiabix.com/logical-reasoning/logical-sequence-of-words", "Logical Sequence"),
        ]
        
        successful_pages = 0
        total_pages = len(question_pages)
        
        logger.info("🚀 Testing fixed BIX selectors on multiple question pages...")
        logger.info("=" * 70)
        
        for url, name in question_pages:
            try:
                success = self.test_question_page(url, name)
                if success:
                    successful_pages += 1
                logger.info("-" * 70)
            except Exception as e:
                logger.error(f"Failed to test {name}: {e}")
            
            time.sleep(2)  # Be respectful to the website
        
        # Final results
        logger.info("=" * 70)
        logger.info("🎯 FINAL TEST RESULTS:")
        logger.info(f"  Successful pages: {successful_pages}/{total_pages}")
        logger.info(f"  Success rate: {(successful_pages/total_pages)*100:.1f}%")
        
        if successful_pages >= 3:
            logger.info("✅ SELECTORS ARE WORKING! Ready for full scraping.")
            return True
        else:
            logger.info("❌ Selectors need more adjustment.")
            return False
    
    def run(self):
        """Run the complete test"""
        logger.info("🚀 Starting fixed selectors test...")
        
        try:
            if not self.setup_driver():
                return False
            
            success = self.test_multiple_question_pages()
            
            if success:
                logger.info("🎉 SUCCESS! The fixed BIX selectors are working properly!")
                logger.info("💡 Recommendation: Run a full scraping job to collect questions.")
                return True
            else:
                logger.error("❌ The selectors need further refinement.")
                return False
                
        except Exception as e:
            logger.error(f"Critical error: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    test = FixedSelectorsTest()
    success = test.run()
    
    if success:
        logger.info("✅ Fixed selectors test passed!")
        return 0
    else:
        logger.error("❌ Fixed selectors test failed!")
        return 1

if __name__ == "__main__":
    os.environ['DISPLAY'] = ':99'
    exit_code = main()
    exit(exit_code)