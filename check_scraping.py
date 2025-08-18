#!/usr/bin/env python3
"""
Quick status check for the running scraping job
"""
import requests
import json
import time

job_id = "bab173bf-84c1-4127-8cea-a56abed00465"
base_url = "http://localhost:8001/api"

print("🔍 LIVE SCRAPING STATUS CHECK")
print("=" * 50)

for i in range(5):  # Check 5 times
    try:
        print(f"\n📊 Check {i+1}/5 - {time.strftime('%H:%M:%S')}")
        
        # Get job status
        response = requests.get(f"{base_url}/scraping/jobs/{job_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            status = data.get('status', 'unknown')
            stats = data.get('statistics', {})
            questions = stats.get('questions_extracted', 0)
            pages = stats.get('pages_processed', 0)
            error = data.get('last_error', data.get('error_message', 'None'))
            
            print(f"   Status: {status}")
            print(f"   Questions extracted: {questions}")
            print(f"   Pages processed: {pages}")
            if error and error != 'None':
                print(f"   Last error: {error[:100]}...")
            
            if status in ['completed', 'failed']:
                print(f"\n🏁 Job {status}!")
                if questions > 0:
                    print(f"✅ SUCCESS: Extracted {questions} questions!")
                else:
                    print(f"❌ No questions extracted")
                break
        else:
            print(f"   ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️ Check failed: {e}")
    
    if i < 4:  # Don't sleep on last iteration
        time.sleep(15)  # Wait 15 seconds between checks

print(f"\n📋 Final Results:")
try:
    response = requests.get(f"{base_url}/scraping/jobs/{job_id}", timeout=5)
    if response.status_code == 200:
        data = response.json()
        stats = data.get('statistics', {})
        questions = stats.get('questions_extracted', 0)
        print(f"🎯 TOTAL QUESTIONS EXTRACTED: {questions}")
    else:
        print("❌ Could not get final status")
except:
    print("❌ Could not get final status")