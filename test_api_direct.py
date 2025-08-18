#!/usr/bin/env python3
"""
Test API directly with proper sync calls
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
sys.path.append('/app/backend')

def test_database_directly():
    """Test database contents directly"""
    
    # Get database connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = MongoClient(mongo_url)
    db = client[db_name]
    
    # Check what's actually in the database
    print("🔍 Direct database query:")
    questions = list(db.enhanced_questions.find({}).limit(10))
    
    print(f"   Found {len(questions)} questions in database")
    
    if questions:
        sample = questions[0]
        print(f"   Sample question structure:")
        for key in sample.keys():
            if key != '_id':
                value = sample[key]
                print(f"     {key}: {type(value).__name__} = {str(value)[:50]}")
    
    # Try the filter that the API uses
    active_questions = list(db.enhanced_questions.find({"is_active": True}).limit(10))
    print(f"   Questions with is_active=True: {len(active_questions)}")
    
    # Try filtering by category
    logical_questions = list(db.enhanced_questions.find({"category": "logical"}).limit(10))
    print(f"   Questions with category='logical': {len(logical_questions)}")
    
    # Check what categories exist
    categories = db.enhanced_questions.distinct('category')
    print(f"   Available categories: {categories}")
    
    # Check is_active field
    is_active_values = db.enhanced_questions.distinct('is_active')
    print(f"   Available is_active values: {is_active_values}")
    
    client.close()

def main():
    test_database_directly()

if __name__ == "__main__":
    main()