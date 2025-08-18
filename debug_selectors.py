#!/usr/bin/env python3
"""
Debug CSS selectors for IndiaBix and GeeksforGeeks
"""

import sys
import os
import time
import requests
from bs4 import BeautifulSoup

# Test with simple HTTP request first
def test_indiabix_structure():
    """Test IndiaBix page structure with simple HTTP request"""
    print("🔍 Testing IndiaBix page structure...")
    
    url = "https://www.indiabix.com/aptitude/arithmetic-aptitude"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Test current selectors
            current_selectors = {
                'div.bix-div-container': 'question_container',
                'div.bix-td-qtxt': 'question_text',
                'table.bix-tbl-options': 'options_table',
                'div.bix-ans-description': 'answer'
            }
            
            print("\n📋 Testing current selectors:")
            for selector, description in current_selectors.items():
                elements = soup.select(selector)
                print(f"  {selector} ({description}): {len(elements)} elements")
                if elements and len(elements) < 5:
                    for i, elem in enumerate(elements[:2]):
                        text = elem.get_text(strip=True)[:100]
                        print(f"    [{i}]: {text}...")
            
            # Look for alternative selectors
            print("\n🔍 Looking for alternative selectors:")
            
            # Check for any divs with 'bix' in class name
            bix_elements = soup.find_all('div', class_=lambda x: x and 'bix' in str(x).lower())
            print(f"  Divs with 'bix' in class: {len(bix_elements)}")
            for elem in bix_elements[:3]:
                classes = elem.get('class', [])
                print(f"    Classes: {classes}")
            
            # Check for question-related content
            question_patterns = ['question', 'quiz', 'problem', 'test']
            for pattern in question_patterns:
                elements = soup.find_all(attrs={'class': lambda x: x and pattern in str(x).lower()})
                if elements:
                    print(f"  Elements with '{pattern}' in class: {len(elements)}")
            
            # Check page structure
            print(f"\n📄 Page info:")
            print(f"  Title: {soup.title.string if soup.title else 'No title'}")
            print(f"  Total divs: {len(soup.find_all('div'))}")
            print(f"  Total tables: {len(soup.find_all('table'))}")
            print(f"  Total paragraphs: {len(soup.find_all('p'))}")
            
            # Look for specific IndiaBix patterns in HTML
            html_content = str(soup)
            patterns = ['bix-', 'question', 'quiz', 'aptitude']
            for pattern in patterns:
                count = html_content.lower().count(pattern)
                print(f"  '{pattern}' occurrences: {count}")
            
            # Check if this is a quiz page or listing page
            if 'quiz' in html_content.lower():
                print("  ✅ Appears to be a quiz page")
            else:
                print("  ⚠️ May not be a quiz page - could be a listing page")
                
        else:
            print(f"❌ Failed to fetch page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_geeksforgeeks_structure():
    """Test GeeksforGeeks page structure"""
    print("\n🔍 Testing GeeksforGeeks page structure...")
    
    url = "https://www.geeksforgeeks.org/practice/data-structures/arrays"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Test current selectors
            current_selectors = {
                'div.problemStatement': 'question_text',
                'div.options label': 'options',
                'div.solution-approach': 'answer'
            }
            
            print("\n📋 Testing current selectors:")
            for selector, description in current_selectors.items():
                elements = soup.select(selector)
                print(f"  {selector} ({description}): {len(elements)} elements")
            
            print(f"\n📄 Page info:")
            print(f"  Title: {soup.title.string if soup.title else 'No title'}")
            print(f"  Total divs: {len(soup.find_all('div'))}")
            
        else:
            print(f"❌ Failed to fetch page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_indiabix_structure()
    test_geeksforgeeks_structure()