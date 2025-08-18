#!/usr/bin/env python3
"""
Analyze IndiaBix HTML structure to find proper selectors
"""

import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IndiaBixAnalyzer:
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
    
    def analyze_page(self, url):
        """Analyze the HTML structure of an IndiaBix page"""
        logger.info(f"🔍 Analyzing: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            logger.info(f"📄 Page title: {self.driver.title}")
            logger.info(f"📊 Page size: {len(page_source)} characters")
            
            # Save HTML for inspection
            with open(f'/app/indiabix_page_source.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info("💾 Page source saved to /app/indiabix_page_source.html")
            
            # Analyze structure
            self.analyze_structure(soup)
            
            # Look for quiz/question patterns
            self.find_quiz_patterns(soup)
            
            # Suggest selectors
            self.suggest_selectors(soup)
            
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
    
    def analyze_structure(self, soup):
        """Analyze general HTML structure"""
        logger.info("📋 HTML Structure Analysis:")
        
        # Count elements
        divs = soup.find_all('div')
        logger.info(f"  Total divs: {len(divs)}")
        
        # Find divs with classes
        divs_with_classes = [div for div in divs if div.get('class')]
        logger.info(f"  Divs with classes: {len(divs_with_classes)}")
        
        # Collect unique classes
        all_classes = set()
        for div in divs_with_classes:
            classes = div.get('class', [])
            for cls in classes:
                all_classes.add(cls)
        
        logger.info(f"  Unique CSS classes: {len(all_classes)}")
        
        # Show common class patterns
        class_patterns = {}
        for cls in all_classes:
            if any(keyword in cls.lower() for keyword in ['question', 'quiz', 'test', 'option', 'answer', 'problem']):
                class_patterns[cls] = cls
        
        if class_patterns:
            logger.info("  🎯 Relevant classes found:")
            for cls in sorted(class_patterns.keys()):
                logger.info(f"    .{cls}")
        else:
            logger.info("  ⚠️ No obviously relevant classes found")
            # Show some sample classes
            sample_classes = sorted(list(all_classes))[:20]
            logger.info("  📝 Sample classes:")
            for cls in sample_classes:
                logger.info(f"    .{cls}")
    
    def find_quiz_patterns(self, soup):
        """Look for quiz/question patterns"""
        logger.info("🎯 Quiz Pattern Analysis:")
        
        # Look for text patterns that indicate questions
        text_patterns = [
            (r'\d+\.\s+[A-Z]', 'Numbered questions'),
            (r'[A-D]\)\s+', 'Multiple choice options'),
            (r'Answer:\s*[A-D]', 'Answer indicators'),
            (r'Explanation:\s*', 'Explanation sections'),
            (r'\?\s*$', 'Question marks at end of lines'),
        ]
        
        page_text = soup.get_text()
        for pattern, description in text_patterns:
            matches = len(re.findall(pattern, page_text, re.MULTILINE))
            if matches > 0:
                logger.info(f"  {description}: {matches} matches")
        
        # Look for form elements (often used in quizzes)
        forms = soup.find_all('form')
        inputs = soup.find_all('input')
        buttons = soup.find_all('button')
        
        logger.info(f"  Forms: {len(forms)}")
        logger.info(f"  Input elements: {len(inputs)}")
        logger.info(f"  Buttons: {len(buttons)}")
        
        # Check input types
        input_types = {}
        for input_elem in inputs:
            input_type = input_elem.get('type', 'text')
            input_types[input_type] = input_types.get(input_type, 0) + 1
        
        for input_type, count in input_types.items():
            logger.info(f"    {input_type}: {count}")
    
    def suggest_selectors(self, soup):
        """Suggest CSS selectors based on analysis"""
        logger.info("💡 Selector Suggestions:")
        
        # Find elements containing question-like text
        potential_questions = []
        
        # Look for elements with question marks
        for elem in soup.find_all(['div', 'p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = elem.get_text(strip=True)
            if text and ('?' in text or 'find' in text.lower() or 'calculate' in text.lower() or 'what' in text.lower()):
                classes = elem.get('class', [])
                tag_info = f"{elem.name}"
                if classes:
                    tag_info += f".{'.'.join(classes)}"
                
                # Avoid very long text (probably not questions)
                if len(text) < 500 and len(text) > 10:
                    potential_questions.append({
                        'selector': tag_info,
                        'text': text[:100] + '...' if len(text) > 100 else text,
                        'element': elem
                    })
        
        if potential_questions:
            logger.info("  🎯 Potential question elements:")
            for i, q in enumerate(potential_questions[:10]):  # Show first 10
                logger.info(f"    [{i}] {q['selector']}: {q['text']}")
        
        # Look for option-like patterns
        potential_options = []
        for elem in soup.find_all(['li', 'div', 'span', 'p']):
            text = elem.get_text(strip=True)
            # Check if text looks like multiple choice options
            if text and re.match(r'^[A-D][\)\.]\s+', text):
                classes = elem.get('class', [])
                tag_info = f"{elem.name}"
                if classes:
                    tag_info += f".{'.'.join(classes)}"
                potential_options.append({
                    'selector': tag_info,
                    'text': text[:80] + '...' if len(text) > 80 else text,
                    'element': elem
                })
        
        if potential_options:
            logger.info("  📝 Potential option elements:")
            for i, opt in enumerate(potential_options[:10]):
                logger.info(f"    [{i}] {opt['selector']}: {opt['text']}")
        
        # Generate recommended selectors
        logger.info("  🎯 Recommended selectors to try:")
        
        # Extract unique class combinations from potential questions
        question_selectors = set()
        for q in potential_questions:
            elem = q['element']
            classes = elem.get('class', [])
            if classes:
                question_selectors.add(f"{elem.name}.{'.'.join(classes)}")
            question_selectors.add(elem.name)
        
        for selector in sorted(question_selectors)[:10]:
            logger.info(f"    {selector}")
    
    def analyze_multiple_pages(self):
        """Analyze multiple IndiaBix pages to understand structure"""
        urls_to_try = [
            "https://www.indiabix.com/aptitude/arithmetic-aptitude",
            "https://www.indiabix.com/online-test/aptitude-test",
            "https://www.indiabix.com/aptitude/time-and-work",
            "https://www.indiabix.com/aptitude/problems-on-numbers",
        ]
        
        logger.info("🎯 Analyzing multiple IndiaBix pages...")
        
        for url in urls_to_try:
            try:
                logger.info(f"\n{'='*60}")
                self.analyze_page(url)
                time.sleep(3)  # Be respectful to the website
            except Exception as e:
                logger.error(f"Error analyzing {url}: {e}")
    
    def run(self):
        """Run the complete analysis"""
        logger.info("🚀 Starting IndiaBix HTML structure analysis...")
        
        try:
            if not self.setup_driver():
                return False
            
            self.analyze_multiple_pages()
            
            logger.info("\n" + "="*60)
            logger.info("✅ Analysis completed! Check the logs above for selector suggestions.")
            logger.info("📁 Page source saved to /app/indiabix_page_source.html for manual inspection")
            
            return True
            
        except Exception as e:
            logger.error(f"Critical error: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    analyzer = IndiaBixAnalyzer()
    success = analyzer.run()
    
    if success:
        logger.info("✅ Analysis completed successfully!")
        return 0
    else:
        logger.error("❌ Analysis failed!")
        return 1

if __name__ == "__main__":
    os.environ['DISPLAY'] = ':99'
    exit_code = main()
    exit(exit_code)