#!/usr/bin/env python3
"""
Fix questions in database to match the correct schema
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

def fix_questions_schema():
    """Fix the questions in database to match EnhancedQuestion schema"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db.enhanced_questions
    
    print("🔧 Fixing questions schema in database...")
    
    # Get all questions
    questions = list(collection.find({}))
    print(f"📊 Found {len(questions)} questions to fix")
    
    fixed_count = 0
    
    for question in questions:
        try:
            # Create the fixed question with proper schema
            fixed_question = {
                "id": question.get("id", str(uuid.uuid4())),
                
                # Basic Question Data
                "question_text": question.get("question_text", ""),
                "options": question.get("options", ["Option A", "Option B", "Option C", "Option D"]),
                "correct_answer": question.get("correct_answer", "Option A"),
                "category": "logical",  # Use enum value directly
                "difficulty": "placement_ready",  # Use valid enum value
                
                # AI Enhancements - with all required fields
                "ai_metrics": {
                    "quality_score": question.get("ai_metrics", {}).get("quality_score", 85.0),
                    "difficulty_score": question.get("ai_metrics", {}).get("difficulty_score", 5.0),
                    "relevance_score": 80.0,  # Required field that was missing
                    "clarity_score": question.get("ai_metrics", {}).get("clarity_score", 90.0),
                    "assessed_by": "ai_system",
                    "assessment_date": datetime.utcnow()
                },
                
                "metadata": {
                    "concepts": question.get("metadata", {}).get("concepts", ["logical_reasoning"]),
                    "company_patterns": [],
                    "topics": question.get("metadata", {}).get("tags", ["aptitude", "logical"]),
                    "subtopics": [],
                    "keywords": ["logical", "reasoning", "aptitude"],
                    "time_estimate": 90  # 90 seconds for logical questions
                },
                
                "analytics": {  # Required field that was missing
                    "success_rate": 0.0,
                    "avg_time_taken": 0,
                    "attempt_count": 0,
                    "correct_count": 0,
                    "common_mistakes": [],
                    "skip_rate": 0.0
                },
                
                "ai_explanation": None,  # Optional field
                
                # Source Information
                "source": "web_scraped",  # Use enum value directly
                "source_url": question.get("source_url"),
                "scraped_from": question.get("metadata", {}).get("source", "GeeksforGeeks"),
                "duplicate_cluster_id": None,
                
                # Timestamps
                "created_at": question.get("created_at", datetime.utcnow()),
                "updated_at": datetime.utcnow(),
                "last_ai_processed": None,
                
                # Status Flags
                "is_verified": False,
                "is_active": question.get("is_active", True),
                "needs_review": False
            }
            
            # Replace the question in database
            result = collection.replace_one(
                {"_id": question["_id"]},
                fixed_question
            )
            
            if result.modified_count > 0:
                fixed_count += 1
                print(f"✅ Fixed question: {fixed_question['question_text'][:50]}...")
            
        except Exception as e:
            print(f"❌ Error fixing question: {str(e)}")
            continue
    
    print(f"📊 Successfully fixed {fixed_count} questions")
    return fixed_count

def verify_api_works():
    """Test if the API works after fixing"""
    import requests
    
    try:
        response = requests.get("http://localhost:8001/api/questions/filtered?category=logical&limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API now works! Returned {len(data.get('questions', []))} questions")
            
            if data.get('questions'):
                print(f"📋 Sample question: {data['questions'][0].get('question_text', '')[:60]}...")
                
            return True
        else:
            print(f"❌ API still failing: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def main():
    print("🔧 Database Schema Fix for Logical Questions")
    print("=" * 60)
    
    # Fix questions schema
    fixed_count = fix_questions_schema()
    
    # Verify API works
    if fixed_count > 0:
        print(f"\n🧪 Testing API after fix...")
        api_works = verify_api_works()
        
        print(f"\n🎯 Results:")
        print(f"   Questions fixed: {fixed_count}")
        print(f"   API working: {'✅' if api_works else '❌'}")
    else:
        print("❌ No questions were fixed")

if __name__ == "__main__":
    main()