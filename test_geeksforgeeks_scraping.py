#!/usr/bin/env python3
"""
Test GeeksforGeeks scraping for logical aptitude questions
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001"

async def test_geeksforgeeks_scraping():
    """Test creating and running a GeeksforGeeks scraping job"""
    
    async with aiohttp.ClientSession() as session:
        print("🚀 Testing GeeksforGeeks Logical Questions Scraping")
        print("=" * 60)
        
        # Step 1: Check if API is accessible
        try:
            async with session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Backend Health: {health_data['status']}")
                    print(f"📊 MongoDB: {health_data['mongodb']}")
                    print(f"🤖 AI Services: {health_data['ai_services']}")
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Cannot connect to backend: {str(e)}")
            return

        # Step 2: Check available sources
        try:
            async with session.get(f"{BACKEND_URL}/api/scraping/sources") as response:
                if response.status == 200:
                    sources = await response.json()
                    print(f"\n📋 Available Sources: {len(sources)}")
                    for source in sources:
                        print(f"   - {source['name']} ({source['source_type']})")
                else:
                    print(f"❌ Failed to get sources: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error getting sources: {str(e)}")
            return

        # Step 3: Create scraping job for GeeksforGeeks logical questions
        job_payload = {
            "job_name": "GeeksforGeeks Logical Questions Collection",
            "description": "Extract 10 logical aptitude questions from GeeksforGeeks",
            "source_names": ["GeeksforGeeks"],
            "target_categories": ["logical"],
            "max_questions_per_source": 10,
            "priority_level": 1,
            "quality_threshold": 75.0,
            "enable_ai_processing": True,
            "enable_duplicate_detection": True
        }
        
        print(f"\n🔨 Creating scraping job...")
        try:
            async with session.post(
                f"{BACKEND_URL}/api/scraping/jobs",
                json=job_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    job_response = await response.json()
                    job_id = job_response["job_id"]
                    print(f"✅ Job created successfully: {job_id}")
                    print(f"📝 Status: {job_response['status']}")
                    print(f"💬 Message: {job_response['message']}")
                else:
                    error_text = await response.text()
                    print(f"❌ Job creation failed: {response.status}")
                    print(f"📄 Error: {error_text}")
                    return
        except Exception as e:
            print(f"❌ Error creating job: {str(e)}")
            return

        # Step 4: Start the job
        print(f"\n▶️  Starting job {job_id}...")
        try:
            async with session.put(
                f"{BACKEND_URL}/api/scraping/jobs/{job_id}/start",
                json={"priority": "high"}
            ) as response:
                if response.status == 200:
                    start_response = await response.json()
                    print(f"✅ Job started: {start_response['status']}")
                    print(f"💬 Message: {start_response['message']}")
                else:
                    error_text = await response.text()
                    print(f"❌ Job start failed: {response.status}")
                    print(f"📄 Error: {error_text}")
                    return
        except Exception as e:
            print(f"❌ Error starting job: {str(e)}")
            return

        # Step 5: Monitor job progress
        print(f"\n⏱️  Monitoring job progress...")
        max_wait_minutes = 10  # Maximum wait time
        start_time = time.time()
        
        while (time.time() - start_time) < (max_wait_minutes * 60):
            try:
                async with session.get(f"{BACKEND_URL}/api/scraping/jobs/{job_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        print(f"📊 Status: {status_data['status']} | Progress: {status_data.get('progress_percentage', 0):.1f}% | Questions: {status_data.get('questions_extracted', 0)}")
                        
                        if status_data['status'] in ['completed', 'failed', 'cancelled']:
                            print(f"\n🏁 Job finished with status: {status_data['status']}")
                            if status_data.get('questions_extracted', 0) > 0:
                                print(f"✅ Successfully extracted {status_data['questions_extracted']} questions!")
                            break
                    else:
                        print(f"❌ Status check failed: {response.status}")
                        
                await asyncio.sleep(10)  # Wait 10 seconds between checks
                
            except Exception as e:
                print(f"❌ Error monitoring job: {str(e)}")
                break
        
        # Step 6: Check final results
        print(f"\n📋 Final Results Summary:")
        try:
            async with session.get(f"{BACKEND_URL}/api/scraping/jobs/{job_id}") as response:
                if response.status == 200:
                    final_status = await response.json()
                    print(f"   Status: {final_status['status']}")
                    print(f"   Questions Extracted: {final_status.get('questions_extracted', 0)}")
                    print(f"   Questions Processed: {final_status.get('questions_processed', 0)}")
                    print(f"   Error Count: {final_status.get('error_count', 0)}")
                    
                    if final_status.get('last_error'):
                        print(f"   Last Error: {final_status['last_error']}")
        except Exception as e:
            print(f"❌ Error getting final results: {str(e)}")

        # Step 7: Check database for collected questions
        print(f"\n🗃️  Checking database for collected questions...")
        try:
            # Use the enhanced questions API to get logical questions
            async with session.get(f"{BACKEND_URL}/api/questions/filtered?category=logical&limit=10") as response:
                if response.status == 200:
                    questions_data = await response.json()
                    questions_count = len(questions_data.get('questions', []))
                    print(f"✅ Found {questions_count} logical questions in database")
                    
                    if questions_count > 0:
                        print(f"📝 Sample question:")
                        sample_q = questions_data['questions'][0]
                        print(f"   - {sample_q.get('question_text', 'N/A')[:100]}...")
                        print(f"   - Source: {sample_q.get('metadata', {}).get('source', 'N/A')}")
                else:
                    print(f"❌ Failed to get questions from database: {response.status}")
        except Exception as e:
            print(f"❌ Error checking database: {str(e)}")

        print(f"\n🎯 GeeksforGeeks Scraping Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_geeksforgeeks_scraping())