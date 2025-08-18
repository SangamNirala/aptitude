#!/usr/bin/env python3
"""
Fix question format to match EnhancedQuestion model exactly
"""

import os
from pymongo import MongoClient
from datetime import datetime

def fix_questions_format():
    """Fix questions to match exact EnhancedQuestion model requirements"""
    
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    collection = db.enhanced_questions
    
    # Get all questions
    questions = list(collection.find({}))
    print(f"📝 Fixing {len(questions)} questions...")
    
    for question in questions:
        # Prepare the update
        update_fields = {}
        
        # Fix difficulty enum
        difficulty_mapping = {
            'easy': 'foundation',
            'medium': 'placement_ready', 
            'hard': 'campus_expert'
        }
        
        current_difficulty = question.get('difficulty', 'medium')
        if current_difficulty in difficulty_mapping:
            update_fields['difficulty'] = difficulty_mapping[current_difficulty]
        else:
            update_fields['difficulty'] = 'placement_ready'
        
        # Fix source enum
        update_fields['source'] = 'web_scraped'  # Since it's from IndiaBix
        
        # Fix ai_metrics to include all required fields
        current_ai_metrics = question.get('ai_metrics', {})
        update_fields['ai_metrics'] = {
            'quality_score': current_ai_metrics.get('quality_score', 85.0),
            'difficulty_score': 5.0,  # Scale 1-10, 5 for medium
            'relevance_score': 85.0,  # High relevance for placement
            'clarity_score': 90.0,    # Clear questions
            'confidence_score': current_ai_metrics.get('confidence_score', 0.95),
            'semantic_embedding': current_ai_metrics.get('semantic_embedding', []),
            'assessed_by': 'ai_system',
            'assessment_date': datetime.utcnow()
        }
        
        # Add missing analytics field
        update_fields['analytics'] = {
            'success_rate': question.get('success_rate', 0.65),
            'avg_time_taken': question.get('time_to_solve', 120),
            'attempt_count': 0,
            'correct_count': 0,
            'common_mistakes': [],
            'skip_rate': 0.0
        }
        
        # Update the question
        collection.update_one(
            {'_id': question['_id']},
            {'$set': update_fields}
        )
    
    print(f"✅ Fixed {len(questions)} questions")
    client.close()

def main():
    fix_questions_format()
    print("🎉 Question format fixing completed!")

if __name__ == "__main__":
    main()