from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from .question_models import QuestionCategory, DifficultyLevel

class WeakAreaAnalysis(BaseModel):
    topic: str
    accuracy: float = Field(ge=0, le=100)
    confidence_level: str = "medium"  # low, medium, high
    questions_attempted: int = 0
    improvement_suggestion: str = ""
    priority_score: float = Field(ge=0, le=10)

class PerformancePrediction(BaseModel):
    company_name: str
    success_probability: float = Field(ge=0, le=100)
    readiness_date: Optional[datetime] = None
    current_level: str = "placement_ready"
    areas_to_improve: List[str] = []
    confidence_score: float = 0.85

class AIStudyPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    daily_question_target: int = 25
    focus_areas: List[str] = []
    estimated_improvement_days: int = 28
    weekly_milestones: Dict[str, str] = {}
    success_metrics: Dict[str, float] = {}
    generated_date: datetime = Field(default_factory=datetime.utcnow)

class UserPerformanceSnapshot(BaseModel):
    category: QuestionCategory
    accuracy: float = Field(ge=0, le=100)
    questions_attempted: int = 0
    questions_correct: int = 0
    avg_time_per_question: float = 0.0
    improvement_trend: str = "stable"  # improving, declining, stable
    last_practice_date: Optional[datetime] = None

class UserAnalytics(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Overall Performance
    overall_accuracy: float = 0.0
    total_questions_attempted: int = 0
    study_streak_days: int = 0
    current_level: DifficultyLevel = DifficultyLevel.FOUNDATION
    
    # Category-wise Performance
    performance_by_category: Dict[str, UserPerformanceSnapshot] = {}
    
    # AI-Generated Insights
    weak_areas: List[WeakAreaAnalysis] = []
    performance_predictions: List[PerformancePrediction] = []
    ai_study_plan: Optional[AIStudyPlan] = None
    
    # Learning Patterns
    best_study_time: Optional[str] = None  # morning, afternoon, evening
    preferred_difficulty: DifficultyLevel = DifficultyLevel.PLACEMENT_READY
    learning_speed: str = "medium"  # slow, medium, fast
    
    # Engagement Metrics
    login_streak: int = 0
    last_login: Optional[datetime] = None
    total_study_time_minutes: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_ai_analysis: Optional[datetime] = None

class QuestionAttempt(BaseModel):
    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    question_id: str
    
    # Attempt Details
    selected_answer: str
    is_correct: bool
    time_taken_seconds: int
    difficulty_level: DifficultyLevel
    
    # Context
    study_mode: str = "practice"  # practice, mock_test, challenge, etc.
    company_focus: Optional[str] = None
    
    # AI Insights
    mistake_category: Optional[str] = None  # calculation, concept, careless
    hint_used: bool = False
    explanation_viewed: bool = False
    
    # Timestamps
    attempted_at: datetime = Field(default_factory=datetime.utcnow)

class StudySession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Session Details
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_questions: int = 0
    correct_answers: int = 0
    
    # Session Configuration
    focus_category: Optional[QuestionCategory] = None
    target_difficulty: Optional[DifficultyLevel] = None
    study_mode: str = "practice"
    
    # Performance Metrics
    accuracy_percentage: float = 0.0
    avg_time_per_question: float = 0.0
    improvement_from_last_session: float = 0.0
    
    # AI Feedback
    session_feedback: Optional[str] = None
    recommendations: List[str] = []
    
    # Questions Attempted
    question_attempts: List[QuestionAttempt] = []

class UserPreferences(BaseModel):
    user_id: str
    
    # Learning Preferences  
    preferred_difficulty: DifficultyLevel = DifficultyLevel.PLACEMENT_READY
    target_companies: List[str] = []
    focus_categories: List[QuestionCategory] = []
    daily_question_goal: int = 25
    
    # Study Settings
    enable_hints: bool = True
    auto_show_explanations: bool = False
    time_limit_warnings: bool = True
    
    # AI Features
    enable_ai_recommendations: bool = True
    enable_personalized_questions: bool = True
    enable_performance_predictions: bool = True
    
    # Notifications
    daily_reminder: bool = True
    streak_notifications: bool = True
    achievement_notifications: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)