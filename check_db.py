#!/usr/bin/env python3
"""
Check database contents and fix question format
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import json

load_dotenv()
sys.path.append('/app/backend')

def check_database():
    """Check what's in the database"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.aptitude_questions
    
    print("📊 Database Contents:")
    print("=" * 50)
    
    collections = db.list_collection_names()
    print(f"Collections: {collections}")
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        print(f"\n📚 {collection_name}: {count} documents")
        
        if count > 0:
            # Show sample document
            sample = collection.find_one()
            print(f"   Sample keys: {list(sample.keys()) if sample else 'None'}")
            
            # Show category breakdown if it has category field
            if sample and 'category' in sample:
                categories = collection.distinct('category')
                print(f"   Categories: {categories}")
                
                for cat in categories:
                    cat_count = collection.count_documents({'category': cat})
                    print(f"     {cat}: {cat_count} questions")
    
    client.close()

def fix_question_format():
    """Convert manual questions to proper EnhancedQuestion format"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client.aptitude_questions
    
    enhanced_collection = db.enhanced_questions
    
    # Get all questions
    questions = list(enhanced_collection.find({}))
    
    print(f"\n🔧 Found {len(questions)} questions to check/fix")
    
    fixed_count = 0
    for question in questions:
        needs_update = False
        updates = {}
        
        # Ensure required fields for EnhancedQuestion model
        required_fields = {
            'enhanced_question_text': question.get('question_text', ''),
            'enhanced_options': question.get('options', []),
            'correct_answer': question.get('correct_answer', ''),
            'enhanced_explanation': question.get('explanation', ''),
            'is_active': True,
            'ai_metrics': {
                'quality_score': question.get('quality_score', 85.0),
                'confidence_score': question.get('confidence_score', 0.95),
                'semantic_embedding': []
            },
            'metadata': {
                'company_patterns': question.get('companies', []),
                'concepts': [question.get('subcategory', 'logical_reasoning')],
                'difficulty_factors': ['medium'],
                'learning_objectives': ['logical_reasoning']
            },
            'performance_analytics': {
                'avg_time_to_solve': question.get('time_to_solve', 120),
                'success_rate': question.get('success_rate', 0.65),
                'common_mistakes': []
            }
        }
        
        for field, value in required_fields.items():
            if field not in question:
                updates[field] = value
                needs_update = True
        
        if needs_update:
            enhanced_collection.update_one(
                {'_id': question['_id']},
                {'$set': updates}
            )
            fixed_count += 1
    
    print(f"✅ Fixed {fixed_count} questions")
    client.close()
    return fixed_count

def main():
    check_database()
    fixed = fix_question_format()
    
    print(f"\n🎉 Database check completed!")
    print(f"Fixed {fixed} questions to proper format")

if __name__ == "__main__":
    main()