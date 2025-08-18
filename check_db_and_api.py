#!/usr/bin/env python3
"""
Check database for logical questions and test API
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json
import requests

# Load environment variables
load_dotenv('/app/backend/.env')

def check_database():
    """Check MongoDB directly for questions"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = MongoClient(mongo_url)
    db = client[db_name]
    
    print("🔍 Checking MongoDB directly...")
    
    # Check enhanced_questions collection
    total_questions = db.enhanced_questions.count_documents({})
    logical_questions = db.enhanced_questions.count_documents({"category": "logical"})
    
    print(f"📊 Total questions in enhanced_questions: {total_questions}")
    print(f"📊 Logical questions in enhanced_questions: {logical_questions}")
    
    # Show sample questions
    if logical_questions > 0:
        sample_questions = list(db.enhanced_questions.find(
            {"category": "logical"}, 
            {"question_text": 1, "category": 1, "source": 1, "is_active": 1}
        ).limit(3))
        
        print(f"\n📋 Sample questions from database:")
        for i, q in enumerate(sample_questions, 1):
            print(f"   {i}. {q['question_text'][:80]}...")
            print(f"      Category: {q.get('category')} | Source: {q.get('source')} | Active: {q.get('is_active')}")
    
    # Check other collections
    collections = db.list_collection_names()
    print(f"\n📂 Available collections: {', '.join(collections)}")
    
    return logical_questions > 0

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8001"
    
    print(f"\n🌐 Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"✅ Health endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {str(e)}")
        return False
    
    # Test questions endpoint
    try:
        response = requests.get(f"{base_url}/api/questions/filtered?category=logical&limit=10", timeout=10)
        print(f"✅ Questions endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API returned {len(data.get('questions', []))} questions")
            print(f"🔢 Total count: {data.get('total_count', 0)}")
            print(f"🔢 Filtered count: {data.get('filtered_count', 0)}")
            
            if data.get('questions'):
                print(f"📋 First question from API: {data['questions'][0].get('question_text', 'N/A')[:60]}...")
        else:
            print(f"❌ Questions endpoint returned: {response.text}")
    except Exception as e:
        print(f"❌ Questions endpoint failed: {str(e)}")
        return False
    
    return True

def main():
    print("🔍 Database and API Verification")
    print("=" * 50)
    
    # Check database
    db_has_questions = check_database()
    
    # Test API
    api_working = test_api()
    
    print(f"\n🎯 Summary:")
    print(f"   Database has logical questions: {'✅' if db_has_questions else '❌'}")
    print(f"   API is working: {'✅' if api_working else '❌'}")

if __name__ == "__main__":
    main()