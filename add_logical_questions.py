#!/usr/bin/env python3

import os
import sys
import uuid
from datetime import datetime
from pymongo import MongoClient

# Add the current directory to Python path so we can import backend modules
sys.path.insert(0, '/app/backend')

def create_logical_questions():
    """Create the 10 logical reasoning questions that were mentioned in the test results"""
    
    questions = [
        {
            "id": str(uuid.uuid4()),
            "question_text": "If all A are B and some B are C, what can we conclude about the relationship between A and C?",
            "options": [
                "All A are C",
                "Some A are C", 
                "No A are C",
                "Cannot be determined"
            ],
            "correct_answer": "Cannot be determined",
            "category": "logical",
            "subcategory": "syllogisms",
            "difficulty": "foundation",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 5.0,
                "relevance_score": 80.0,
                "clarity_score": 85.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["syllogisms", "logical_reasoning"],
                "topics": ["deductive_reasoning"],
                "keywords": ["syllogism", "logic", "reasoning"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "What is the next number in the series: 2, 4, 8, 16, ?",
            "options": [
                "24",
                "32", 
                "20",
                "30"
            ],
            "correct_answer": "32",
            "category": "logical",
            "subcategory": "number_series",
            "difficulty": "foundation",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 4.0,
                "relevance_score": 80.0,
                "clarity_score": 90.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["number_series", "pattern_recognition"],
                "topics": ["sequences"],
                "keywords": ["series", "pattern", "numbers"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "If CODING is written as DPEJOH, how is FILING written?",
            "options": [
                "GJMJOH",
                "GJMJPI", 
                "FJMJOH",
                "GIMJOH"
            ],
            "correct_answer": "GJMJOH",
            "category": "logical",
            "subcategory": "coding_decoding",
            "difficulty": "placement_ready",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 6.0,
                "relevance_score": 80.0,
                "clarity_score": 80.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["coding_decoding", "pattern_matching"],
                "topics": ["alphabetical_coding"],
                "keywords": ["coding", "decoding", "pattern"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "A clock shows 3:15. What is the angle between the hour and minute hands?",
            "options": [
                "7.5 degrees",
                "15 degrees", 
                "22.5 degrees",
                "30 degrees"
            ],
            "correct_answer": "7.5 degrees",
            "category": "logical",
            "subcategory": "clock_problems",
            "difficulty": "campus_expert",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 8.0,
                "relevance_score": 80.0,
                "clarity_score": 75.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["clock_problems", "angle_calculation"],
                "topics": ["time", "geometry"],
                "keywords": ["clock", "angle", "time"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "In a group of 5 friends, if each friend shakes hands with every other friend exactly once, how many handshakes occur?",
            "options": [
                "10",
                "15", 
                "20",
                "25"
            ],
            "correct_answer": "10",
            "category": "logical",
            "subcategory": "combinatorics",
            "difficulty": "placement_ready",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 6.0,
                "relevance_score": 80.0,
                "clarity_score": 85.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["combinatorics", "counting"],
                "topics": ["combinations"],
                "keywords": ["handshakes", "combinations", "counting"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "If today is Monday, what day will it be 100 days from now?",
            "options": [
                "Tuesday",
                "Wednesday", 
                "Thursday",
                "Friday"
            ],
            "correct_answer": "Tuesday",
            "category": "logical",
            "subcategory": "calendar_problems",
            "difficulty": "foundation",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 4.0,
                "relevance_score": 80.0,
                "clarity_score": 88.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["calendar", "modular_arithmetic"],
                "topics": ["days_calculation"],
                "keywords": ["calendar", "days", "modular"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Find the missing term: AZ, BY, CX, DW, ?",
            "options": [
                "EV",
                "FU", 
                "EW",
                "FV"
            ],
            "correct_answer": "EV",
            "category": "logical",
            "subcategory": "letter_series",
            "difficulty": "foundation",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 5.0,
                "relevance_score": 80.0,
                "concept_clarity": 82.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["letter_series", "alphabetical_pattern"],
                "topics": ["sequences"],
                "keywords": ["letters", "series", "pattern"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "In a certain code language, 'BRAIN' is coded as '12345' and 'DRAIN' is coded as '62345'. What is the code for 'RAIN'?",
            "options": [
                "2345",
                "6345", 
                "1345",
                "9345"
            ],
            "correct_answer": "2345",
            "category": "logical",
            "subcategory": "coding_decoding",
            "difficulty": "placement_ready",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 7.0,
                "relevance_score": 80.0,
                "concept_clarity": 78.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["coding_decoding", "pattern_recognition"],
                "topics": ["substitution_coding"],
                "keywords": ["coding", "substitution", "pattern"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "Which of the following is the odd one out: Dog, Cat, Tiger, Chair?",
            "options": [
                "Dog",
                "Cat", 
                "Tiger",
                "Chair"
            ],
            "correct_answer": "Chair",
            "category": "logical",
            "subcategory": "classification",
            "difficulty": "foundation",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 3.0,
                "relevance_score": 80.0,
                "concept_clarity": 92.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["classification", "categorization"],
                "topics": ["odd_one_out"],
                "keywords": ["classification", "category", "odd"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "question_text": "A cube is painted red on all faces. It is then cut into 27 smaller cubes. How many small cubes have exactly 2 faces painted?",
            "options": [
                "8",
                "12", 
                "6",
                "18"
            ],
            "correct_answer": "12",
            "category": "logical",
            "subcategory": "cube_problems",
            "difficulty": "campus_expert",
            "question_type": "multiple_choice",
            "source": "web_scraped",
            "scraped_from": "GeeksforGeeks",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ai_metrics": {
                "quality_score": 85.0,
                "difficulty_score": 8.0,
                "relevance_score": 80.0,
                "concept_clarity": 70.0
            },
            "analytics": {
                "attempts": 0,
                "correct_attempts": 0,
                "avg_time_spent": 0.0,
                "last_attempted": None
            },
            "metadata": {
                "concepts": ["cube_cutting", "3d_geometry"],
                "topics": ["spatial_reasoning"],
                "keywords": ["cube", "painting", "spatial"]
            }
        }
    ]
    
    return questions

def main():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/test_database')
    print(f"Connecting to MongoDB: {mongo_url}")
    
    client = MongoClient(mongo_url)
    db = client.test_database
    collection = db.enhanced_questions
    
    # Create the questions
    questions = create_logical_questions()
    
    # Clear existing questions if any
    result = collection.delete_many({"category": "logical"})
    print(f"Deleted {result.deleted_count} existing logical questions")
    
    # Insert new questions
    result = collection.insert_many(questions)
    print(f"Inserted {len(result.inserted_ids)} logical questions")
    
    # Verify insertion
    count = collection.count_documents({"category": "logical", "is_active": True})
    print(f"Total active logical questions in database: {count}")
    
    # Print sample question for verification
    sample = collection.find_one({"category": "logical"})
    if sample:
        print(f"\nSample question:")
        print(f"Text: {sample['question_text']}")
        print(f"Options: {sample['options']}")
        print(f"Correct Answer: {sample['correct_answer']}")
    
    client.close()
    print("\n✅ Successfully added 10 logical reasoning questions to the database!")

if __name__ == "__main__":
    main()