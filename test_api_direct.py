#!/usr/bin/env python3
"""
Test API directly with proper async calls
"""

import os
import sys
import asyncio
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
sys.path.append('/app/backend')

async def test_api_directly():
    """Test API functionality directly"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Get database connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Check what's actually in the database
    print("🔍 Direct database query:")
    cursor = db.enhanced_questions.find({})
    questions = await cursor.to_list(length=10)
    
    print(f"   Found {len(questions)} questions in database")
    
    if questions:
        sample = questions[0]
        print(f"   Sample question structure:")
        for key in sample.keys():
            if key != '_id':
                print(f"     {key}: {type(sample[key])}")
    
    # Try the filter that the API uses
    filter_query = {"is_active": True}
    cursor = db.enhanced_questions.find(filter_query)
    active_questions = await cursor.to_list(length=10)
    
    print(f"   Questions with is_active=True: {len(active_questions)}")
    
    # Try filtering by category
    filter_query = {"category": "logical"}
    cursor = db.enhanced_questions.find(filter_query)
    logical_questions = await cursor.to_list(length=10)
    
    print(f"   Questions with category='logical': {len(logical_questions)}")
    
    # Check what categories exist
    categories = await db.enhanced_questions.distinct('category')
    print(f"   Available categories: {categories}")
    
    await client.close()

def main():
    asyncio.run(test_api_directly())

if __name__ == "__main__":
    main()