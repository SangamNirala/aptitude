#!/usr/bin/env python3
"""
Quick IndiaBix Scraper using Backend API
Use the existing scraping infrastructure to create a job and collect questions
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# Add backend to path
sys.path.append('/app/backend')

def create_scraping_job():
    """Create a scraping job using the backend API"""
    url = "http://localhost:8001/api/scraping/jobs"
    
    job_data = {
        "job_name": "IndiaBix Logical Questions Collection",
        "description": "Collect 10 logical reasoning questions from IndiaBix",
        "source_names": ["IndiaBix"],
        "max_questions_per_source": 10,
        "quality_threshold": 60.0,
        "target_categories": ["logical"],
        "enable_ai_processing": True,
        "enable_duplicate_detection": False,
        "priority_level": 1
    }
    
    try:
        print("🚀 Creating scraping job...")
        response = requests.post(url, json=job_data)
        
        if response.status_code == 200:
            job_info = response.json()
            print(f"✅ Job created successfully: {job_info['job_id']}")
            return job_info['job_id']
        else:
            print(f"❌ Failed to create job: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating job: {e}")
        return None

def start_scraping_job(job_id):
    """Start the scraping job"""
    url = f"http://localhost:8001/api/scraping/jobs/{job_id}/start"
    
    try:
        print(f"▶️  Starting job {job_id}...")
        response = requests.post(url)
        
        if response.status_code == 200:
            print("✅ Job started successfully")
            return True
        else:
            print(f"❌ Failed to start job: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting job: {e}")
        return False

def monitor_job_progress(job_id, max_wait_minutes=5):
    """Monitor job progress"""
    url = f"http://localhost:8001/api/scraping/jobs/{job_id}/status"
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    print(f"📊 Monitoring job progress (max {max_wait_minutes} minutes)...")
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                status = response.json()
                progress = status.get('progress_percentage', 0)
                current_status = status.get('status', 'unknown')
                questions_extracted = status.get('questions_extracted', 0)
                
                print(f"   Status: {current_status} | Progress: {progress:.1f}% | Questions: {questions_extracted}")
                
                if current_status in ['completed', 'failed']:
                    print(f"🏁 Job finished with status: {current_status}")
                    return status
                    
            else:
                print(f"⚠️ Status check failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
        
        time.sleep(10)  # Check every 10 seconds
    
    print("⏰ Timeout reached while monitoring job")
    return None

def get_collected_questions():
    """Get the questions from the database"""
    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        
        load_dotenv()
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        
        client = MongoClient(mongo_url)
        db = client.aptitude_questions
        collection = db.enhanced_questions
        
        # Get questions scraped in the last hour
        recent_time = datetime.utcnow()
        recent_time = recent_time.replace(hour=recent_time.hour-1)
        
        questions = list(collection.find({
            "source": "IndiaBix",
            "category": "logical",
            "created_at": {"$gte": recent_time}
        }).limit(10))
        
        client.close()
        
        print(f"📚 Found {len(questions)} questions in database")
        return questions
        
    except Exception as e:
        print(f"❌ Error retrieving questions: {e}")
        return []

def save_questions_to_file(questions):
    """Save questions to JSON file"""
    if not questions:
        print("⚠️ No questions to save")
        return None
        
    filename = f"/app/collected_logical_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        # Convert ObjectId to string for JSON serialization
        questions_data = []
        for q in questions:
            question_data = dict(q)
            if '_id' in question_data:
                question_data['_id'] = str(question_data['_id'])
            questions_data.append(question_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"💾 Questions saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error saving questions: {e}")
        return None

def check_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8001/api/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def main():
    print("🎯 IndiaBix Logical Questions Collection")
    print("=" * 50)
    
    # Check if backend is running
    if not check_backend_status():
        print("❌ Backend is not accessible. Please start the backend server first.")
        return
    
    # Create scraping job
    job_id = create_scraping_job()
    if not job_id:
        return
    
    # Start the job
    if not start_scraping_job(job_id):
        return
    
    # Monitor progress
    final_status = monitor_job_progress(job_id)
    
    # Get results
    questions = get_collected_questions()
    
    # Save to file
    filename = save_questions_to_file(questions)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 COLLECTION SUMMARY")
    print(f"   Job ID: {job_id}")
    print(f"   Questions collected: {len(questions)}")
    print(f"   Results file: {filename}")
    
    if questions:
        print(f"\n📝 Sample questions:")
        for i, q in enumerate(questions[:3]):
            question_text = q.get('question_text', q.get('enhanced_question_text', 'No question text'))
            print(f"   {i+1}. {question_text[:60]}...")

if __name__ == "__main__":
    main()