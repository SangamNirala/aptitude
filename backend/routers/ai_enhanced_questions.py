from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import uuid

from models.question_models import (
    EnhancedQuestion, QuestionCreateRequest, QuestionFilterRequest,
    PersonalizedQuestionRequest, QuestionBatch, BulkQuestionUpload,
    BulkProcessingResult, QuestionCategory, DifficultyLevel, InstantFeedbackRequest,
    HintRequest, DifficultyAssessmentRequest, DuplicateDetectionRequest
)
from ai_services.ai_coordinator import AICoordinator
from services.categorization_service import CategorizationService
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/api/questions", tags=["AI Enhanced Questions"])

# Database connection will be initialized when needed
def get_database():
    """Get database connection"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

# Initialize AI services lazily to avoid import-time errors
ai_coordinator = None
categorization_service = None

def get_ai_coordinator():
    """Get AI coordinator instance, initializing if needed"""
    global ai_coordinator
    if ai_coordinator is None:
        ai_coordinator = AICoordinator()
    return ai_coordinator

def get_categorization_service():
    """Get categorization service instance, initializing if needed"""
    global categorization_service
    if categorization_service is None:
        categorization_service = CategorizationService()
    return categorization_service

@router.post("/generate-ai", response_model=EnhancedQuestion)
async def generate_ai_question(
    category: QuestionCategory,
    difficulty: DifficultyLevel,
    topic: str,
    company_pattern: Optional[str] = None
):
    """Generate a new question using AI (Gemini)"""
    try:
        logger.info(f"Generating AI question - Category: {category}, Difficulty: {difficulty}, Topic: {topic}")
        
        # Generate question using Gemini
        question_data = await get_ai_coordinator().gemini.generate_question(
            category=category.value,
            difficulty=difficulty.value,
            topic=topic,
            company_pattern=company_pattern or ""
        )
        
        # Add required fields for processing
        question_data['category'] = category.value
        question_data['difficulty'] = difficulty.value
        question_data['source'] = 'ai_generated'
        
        # Process through complete AI pipeline
        enhanced_question = await get_ai_coordinator().process_new_question_complete(question_data)
        
        # Save to database
        db = get_database()
        await db.enhanced_questions.insert_one(enhanced_question.dict())
        
        logger.info(f"AI question generated and saved with ID: {enhanced_question.id}")
        return enhanced_question
        
    except Exception as e:
        logger.error(f"Error generating AI question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@router.post("/create-enhanced", response_model=EnhancedQuestion)  
async def create_enhanced_question(question_request: QuestionCreateRequest):
    """Create a new question with full AI enhancement"""
    try:
        logger.info(f"Creating enhanced question: {question_request.question_text[:50]}...")
        
        # Convert request to processing format
        question_data = {
            "question_text": question_request.question_text,
            "options": question_request.options,
            "correct_answer": question_request.correct_answer,
            "category": question_request.category.value,
            "difficulty": question_request.difficulty.value if question_request.difficulty else "placement_ready",
            "source": question_request.source.value if question_request.source else "manual",
            "source_url": question_request.source_url
        }
        
        # Process through AI pipeline
        enhanced_question = await get_ai_coordinator().process_new_question_complete(question_data)
        
        # Save to database
        db = get_database()
        await db.enhanced_questions.insert_one(enhanced_question.dict())
        
        logger.info(f"Enhanced question created with ID: {enhanced_question.id}")
        return enhanced_question
        
    except Exception as e:
        logger.error(f"Error creating enhanced question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question creation failed: {str(e)}")

@router.post("/generate-personalized", response_model=List[EnhancedQuestion])
async def generate_personalized_questions(request: PersonalizedQuestionRequest):
    """Generate personalized questions based on user's weak areas"""
    try:
        logger.info(f"Generating personalized questions for user: {request.user_id}")
        
        # Generate personalized questions using AI
        personalized_questions = await get_ai_coordinator().generate_personalized_question_set(
            user_weak_areas=request.weak_areas,
            target_companies=request.target_companies,
            count=request.count
        )
        
        if not personalized_questions:
            raise HTTPException(status_code=500, detail="Failed to generate personalized questions")
        
        # Save questions to database
        db = get_database()
        for question in personalized_questions:
            await db.enhanced_questions.insert_one(question.dict())
        
        logger.info(f"Generated {len(personalized_questions)} personalized questions")
        return personalized_questions
        
    except Exception as e:
        logger.error(f"Error generating personalized questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Personalized question generation failed: {str(e)}")

@router.get("/filtered", response_model=QuestionBatch)
async def get_filtered_questions(
    category: Optional[QuestionCategory] = None,
    difficulty: Optional[DifficultyLevel] = None,
    min_quality_score: Optional[float] = Query(70.0, ge=0, le=100),
    company_pattern: Optional[str] = None,
    concepts: Optional[List[str]] = Query(None),
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0)
):
    """Get filtered questions based on criteria"""
    try:
        logger.info(f"Filtering questions - Category: {category}, Difficulty: {difficulty}")
        
        # Build filter query
        filter_query = {"is_active": True}
        
        if category:
            filter_query["category"] = category.value
            
        if difficulty:
            filter_query["difficulty"] = difficulty.value
            
        if min_quality_score:
            filter_query["ai_metrics.quality_score"] = {"$gte": min_quality_score}
            
        if company_pattern:
            filter_query["metadata.company_patterns"] = company_pattern
            
        if concepts:
            filter_query["metadata.concepts"] = {"$in": concepts}
        
        # Get database connection
        db = get_database()
        
        # Get total count
        total_count = await db.enhanced_questions.count_documents(filter_query)
        
        # Get filtered questions
        cursor = db.enhanced_questions.find(filter_query).skip(skip).limit(limit)
        question_docs = await cursor.to_list(length=limit)
        
        # Convert to EnhancedQuestion objects
        questions = [EnhancedQuestion(**doc) for doc in question_docs]
        
        # Calculate batch quality score
        if questions:
            avg_quality = sum(q.ai_metrics.quality_score for q in questions) / len(questions)
        else:
            avg_quality = 0.0
        
        question_batch = QuestionBatch(
            questions=questions,
            total_count=total_count,
            filtered_count=len(questions),
            batch_quality_score=avg_quality
        )
        
        logger.info(f"Returned {len(questions)} filtered questions out of {total_count} total")
        return question_batch
        
    except Exception as e:
        logger.error(f"Error filtering questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question filtering failed: {str(e)}")

@router.post("/instant-feedback")
async def get_instant_feedback(request: InstantFeedbackRequest):
    """Get instant AI-powered feedback on answer"""
    try:
        logger.info(f"Providing instant feedback for question: {request.question_id}")
        
        # Get ultra-fast feedback using Groq
        feedback = await get_ai_coordinator().instant_feedback_response(
            question_text=request.question_text,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer
        )
        
        # Log user attempt (background task)
        attempt_data = {
            "question_id": request.question_id,
            "user_answer": request.user_answer,
            "is_correct": feedback.get("is_correct", False),
            "timestamp": datetime.utcnow(),
            "response_time_ms": feedback.get("response_time_ms", 0)
        }
        
        # Store attempt in background
        db = get_database()
        await db.question_attempts.insert_one(attempt_data)
        
        return feedback
        
    except Exception as e:
        logger.error(f"Error providing instant feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Instant feedback failed: {str(e)}")

@router.post("/generate-hint")
async def generate_hint(request: HintRequest):
    """Generate contextual hint for question"""
    try:
        logger.info(f"Generating hint for question: {request.question_text[:50]}...")
        
        # Generate instant hint using Groq
        hint_result = await get_ai_coordinator().groq.generate_instant_hint(request.question_text, request.user_progress)
        
        return hint_result
        
    except Exception as e:
        logger.error(f"Error generating hint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hint generation failed: {str(e)}")

@router.post("/assess-difficulty")
async def assess_question_difficulty(request: DifficultyAssessmentRequest):
    """Assess question difficulty using AI"""
    try:
        logger.info(f"Assessing difficulty for question: {request.question_text[:50]}...")
        
        # Get instant difficulty assessment using Groq
        difficulty_result = await get_ai_coordinator().groq.assess_difficulty_instantly(request.question_text, request.options)
        
        return difficulty_result
        
    except Exception as e:
        logger.error(f"Error assessing difficulty: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Difficulty assessment failed: {str(e)}")

@router.post("/detect-duplicates")
async def detect_duplicate_questions(request: DuplicateDetectionRequest):
    """Detect if question is duplicate of existing questions"""
    try:
        logger.info(f"Detecting duplicates for question: {request.question_text[:50]}...")
        
        # Get database connection
        db = get_database()
        
        # Get existing questions from database (recent ones for efficiency)
        existing_cursor = db.enhanced_questions.find({"is_active": True}).limit(1000)
        existing_questions = await existing_cursor.to_list(length=1000)
        
        # Detect duplicates using HuggingFace
        duplicate_result = await get_ai_coordinator().detect_duplicate_questions(request.question_text, existing_questions)
        
        return duplicate_result
        
    except Exception as e:
        logger.error(f"Error detecting duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Duplicate detection failed: {str(e)}")

@router.post("/bulk-upload", response_model=BulkProcessingResult)
async def bulk_upload_questions(
    upload_request: BulkQuestionUpload,
    background_tasks: BackgroundTasks
):
    """Upload multiple questions for AI processing"""
    try:
        logger.info(f"Starting bulk upload of {len(upload_request.questions)} questions")
        
        batch_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        if upload_request.auto_process_ai:
            # Process with AI enhancement
            question_data_list = []
            for q in upload_request.questions:
                question_data = {
                    "question_text": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "category": q.category.value,
                    "difficulty": q.difficulty.value if q.difficulty else "placement_ready",
                    "source": q.source.value if q.source else "manual",
                    "source_url": q.source_url
                }
                question_data_list.append(question_data)
            
            # Process in background for large uploads
            if len(question_data_list) > 10:
                background_tasks.add_task(
                    _process_bulk_questions_background,
                    question_data_list, batch_id
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                return BulkProcessingResult(
                    total_submitted=len(upload_request.questions),
                    successfully_processed=0,  # Will be updated by background task
                    failed_count=0,
                    processing_time_seconds=processing_time,
                    batch_id=batch_id
                )
            else:
                # Process immediately for small uploads
                enhanced_questions = await get_ai_coordinator().bulk_process_questions(question_data_list)
                
                # Save to database
                db = get_database()
                for question in enhanced_questions:
                    await db.enhanced_questions.insert_one(question.dict())
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                return BulkProcessingResult(
                    total_submitted=len(upload_request.questions),
                    successfully_processed=len(enhanced_questions),
                    failed_count=len(upload_request.questions) - len(enhanced_questions),
                    processing_time_seconds=processing_time,
                    batch_id=batch_id
                )
        else:
            # Simple upload without AI processing
            simple_questions = []
            for q in upload_request.questions:
                simple_question = EnhancedQuestion(
                    question_text=q.question_text,
                    options=q.options,
                    correct_answer=q.correct_answer,
                    category=q.category,
                    difficulty=q.difficulty or DifficultyLevel.PLACEMENT_READY,
                    source=q.source or "manual"
                )
                simple_questions.append(simple_question.dict())
            
            # Insert to database
            db = get_database()
            await db.enhanced_questions.insert_many(simple_questions)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return BulkProcessingResult(
                total_submitted=len(upload_request.questions),
                successfully_processed=len(simple_questions),
                failed_count=0,
                processing_time_seconds=processing_time,
                batch_id=batch_id
            )
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")

@router.get("/by-weak-areas/{user_id}")
async def get_questions_by_weak_areas(
    user_id: str,
    weak_areas: List[str] = Query(...),
    count: int = Query(20, le=50)
):
    """Get questions targeting user's weak areas"""
    try:
        logger.info(f"Getting questions for user {user_id} weak areas: {weak_areas}")
        
        # Build query for weak areas
        filter_query = {
            "is_active": True,
            "metadata.concepts": {"$in": weak_areas},
            "ai_metrics.quality_score": {"$gte": 70.0}
        }
        
        # Get questions
        db = get_database()
        cursor = db.enhanced_questions.find(filter_query).limit(count)
        question_docs = await cursor.to_list(length=count)
        
        questions = [EnhancedQuestion(**doc) for doc in question_docs]
        
        logger.info(f"Found {len(questions)} questions for weak areas")
        return questions
        
    except Exception as e:
        logger.error(f"Error getting questions by weak areas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get questions for weak areas: {str(e)}")

@router.get("/company-specific/{company_name}")
async def get_company_specific_questions(
    company_name: str,
    category: Optional[QuestionCategory] = None,
    count: int = Query(20, le=50)
):
    """Get questions specific to a company's pattern"""
    try:
        logger.info(f"Getting {company_name} specific questions")
        
        # Build query
        filter_query = {
            "is_active": True,
            "metadata.company_patterns": company_name,
            "ai_metrics.quality_score": {"$gte": 75.0}
        }
        
        if category:
            filter_query["category"] = category.value
        
        # Get questions
        db = get_database()
        cursor = db.enhanced_questions.find(filter_query).limit(count)
        question_docs = await cursor.to_list(length=count)
        
        questions = [EnhancedQuestion(**doc) for doc in question_docs]
        
        logger.info(f"Found {len(questions)} {company_name} specific questions")
        return questions
        
    except Exception as e:
        logger.error(f"Error getting company specific questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get {company_name} questions: {str(e)}")

@router.get("/quality-stats")
async def get_question_quality_stats():
    """Get overall question quality statistics"""
    try:
        # Aggregation pipeline for quality stats
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": None,
                "total_questions": {"$sum": 1},
                "avg_quality_score": {"$avg": "$ai_metrics.quality_score"},
                "avg_difficulty_score": {"$avg": "$ai_metrics.difficulty_score"},
                "high_quality_count": {
                    "$sum": {"$cond": [{"$gte": ["$ai_metrics.quality_score", 85]}, 1, 0]}
                },
                "verified_count": {"$sum": {"$cond": ["$is_verified", 1, 0]}}
            }}
        ]
        
        db = get_database()
        cursor = db.enhanced_questions.aggregate(pipeline)
        stats = await cursor.to_list(length=1)
        
        if stats:
            result = stats[0]
            result["high_quality_percentage"] = (result["high_quality_count"] / result["total_questions"]) * 100
            result["verified_percentage"] = (result["verified_count"] / result["total_questions"]) * 100
        else:
            result = {
                "total_questions": 0,
                "avg_quality_score": 0,
                "avg_difficulty_score": 0,
                "high_quality_count": 0,
                "verified_count": 0,
                "high_quality_percentage": 0,
                "verified_percentage": 0
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting quality stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality stats: {str(e)}")

async def _process_bulk_questions_background(question_data_list: List[Dict], batch_id: str):
    """Background task for processing large bulk uploads"""
    try:
        logger.info(f"Starting background processing for batch {batch_id}")
        
        enhanced_questions = await get_ai_coordinator().bulk_process_questions(question_data_list)
        
        # Save to database
        db = get_database()
        for question in enhanced_questions:
            await db.enhanced_questions.insert_one(question.dict())
        
        # Update batch status
        await db.bulk_processing_status.update_one(
            {"batch_id": batch_id},
            {"$set": {
                "status": "completed",
                "successfully_processed": len(enhanced_questions),
                "failed_count": len(question_data_list) - len(enhanced_questions),
                "completed_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        logger.info(f"Background processing completed for batch {batch_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")
        db = get_database()
        await db.bulk_processing_status.update_one(
            {"batch_id": batch_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow()
            }},
            upsert=True
        )
