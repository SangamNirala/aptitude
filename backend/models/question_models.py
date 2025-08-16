from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class DifficultyLevel(str, Enum):
    FOUNDATION = "foundation"
    PLACEMENT_READY = "placement_ready"
    CAMPUS_EXPERT = "campus_expert"

class QuestionCategory(str, Enum):
    QUANTITATIVE = "quantitative"
    LOGICAL = "logical"
    VERBAL = "verbal"
    DATA_INTERPRETATION = "data_interpretation"

class QuestionSource(str, Enum):
    AI_GENERATED = "ai_generated"
    WEB_SCRAPED = "web_scraped"
    MANUAL = "manual"

class AIQualityMetrics(BaseModel):
    quality_score: float = Field(ge=0, le=100)  # AI-assessed quality (0-100)
    difficulty_score: float = Field(ge=1, le=10)  # AI-assessed difficulty (1-10)
    relevance_score: float = Field(ge=0, le=100)  # Relevance for placement tests
    clarity_score: float = Field(ge=0, le=100)   # Question clarity assessment
    assessed_by: str = "ai_system"
    assessment_date: datetime = Field(default_factory=datetime.utcnow)

class QuestionMetadata(BaseModel):
    concepts: List[str] = []  # AI-extracted concepts
    company_patterns: List[str] = []  # Companies where this pattern appears
    topics: List[str] = []  # Detailed topic tags
    subtopics: List[str] = []  # Granular subtopic classification
    keywords: List[str] = []  # Important keywords
    time_estimate: int = 45  # Expected solving time in seconds

class QuestionAnalytics(BaseModel):
    success_rate: float = 0.0  # Actual success rate from users
    avg_time_taken: int = 0  # Average time taken by users
    attempt_count: int = 0  # Total attempts by all users
    correct_count: int = 0  # Total correct answers
    common_mistakes: List[str] = []  # AI-identified common errors
    skip_rate: float = 0.0  # How often users skip this question

class AIExplanation(BaseModel):
    step_by_step: str  # Detailed solution steps
    key_concept: str  # Main concept explanation
    alternative_methods: List[str] = []  # Other solving approaches
    tips_and_tricks: List[str] = []  # Shortcuts and tips
    common_errors: List[str] = []  # What to avoid
    generated_by: str = "gemini"
    confidence_score: float = 0.95

class EnhancedQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Question Data
    question_text: str
    options: List[str]
    correct_answer: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    
    # AI Enhancements
    ai_metrics: AIQualityMetrics
    metadata: QuestionMetadata
    analytics: QuestionAnalytics
    ai_explanation: Optional[AIExplanation] = None
    
    # Source Information
    source: QuestionSource
    source_url: Optional[str] = None
    scraped_from: Optional[str] = None
    duplicate_cluster_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_ai_processed: Optional[datetime] = None
    
    # Status Flags
    is_verified: bool = False
    is_active: bool = True
    needs_review: bool = False

class QuestionCreateRequest(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    category: QuestionCategory
    difficulty: Optional[DifficultyLevel] = DifficultyLevel.PLACEMENT_READY
    source: Optional[QuestionSource] = QuestionSource.MANUAL
    source_url: Optional[str] = None

class QuestionFilterRequest(BaseModel):
    category: Optional[QuestionCategory] = None
    difficulty: Optional[DifficultyLevel] = None
    min_quality_score: Optional[float] = 70.0
    company_pattern: Optional[str] = None
    concepts: Optional[List[str]] = None
    limit: int = Field(default=20, le=100)
    skip: int = 0

class PersonalizedQuestionRequest(BaseModel):
    user_id: str
    weak_areas: List[str]
    target_companies: List[str] = []
    difficulty_preference: Optional[DifficultyLevel] = None
    focus_concepts: List[str] = []
    count: int = Field(default=20, le=50)

class QuestionBatch(BaseModel):
    questions: List[EnhancedQuestion]
    total_count: int
    filtered_count: int
    ai_processing_status: str = "completed"
    batch_quality_score: float = 0.0

# Collection Models for Bulk Operations
class BulkQuestionUpload(BaseModel):
    questions: List[QuestionCreateRequest]
    source_batch_id: Optional[str] = None
    auto_process_ai: bool = True

class BulkProcessingResult(BaseModel):
    total_submitted: int
    successfully_processed: int
    failed_count: int
    failed_questions: List[str] = []
    processing_time_seconds: float
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# Request models for API endpoints
class InstantFeedbackRequest(BaseModel):
    question_id: str
    question_text: str
    user_answer: str
    correct_answer: str

class HintRequest(BaseModel):
    question_text: str
    user_progress: Optional[str] = ""

class DifficultyAssessmentRequest(BaseModel):
    question_text: str
    options: List[str]

class DuplicateDetectionRequest(BaseModel):
    question_text: str
    similarity_threshold: Optional[float] = 0.85