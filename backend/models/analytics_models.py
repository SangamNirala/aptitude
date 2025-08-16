from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from .question_models import QuestionCategory, DifficultyLevel

class GlobalAnalytics(BaseModel):
    total_questions: int = 0
    total_users: int = 0
    total_attempts: int = 0
    average_success_rate: float = 0.0
    
    # Category Performance
    category_analytics: Dict[str, Dict[str, float]] = {}
    
    # Trending Topics
    trending_weak_areas: List[str] = []
    most_attempted_topics: List[str] = []
    
    # Quality Metrics
    avg_question_quality_score: float = 0.0
    questions_needing_review: int = 0
    
    # Company Patterns
    company_success_rates: Dict[str, float] = {}
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class QuestionInsight(BaseModel):
    question_id: str
    
    # Performance Metrics
    success_rate: float = 0.0
    attempt_count: int = 0
    avg_time_taken: float = 0.0
    skip_rate: float = 0.0
    
    # Difficulty Analysis
    perceived_difficulty: float = 0.0  # Based on user performance
    ai_difficulty_score: float = 0.0
    difficulty_accuracy: float = 0.0  # How accurate AI prediction was
    
    # Common Issues
    common_wrong_answers: Dict[str, int] = {}
    common_mistake_patterns: List[str] = []
    
    # Recommendations
    needs_explanation_improvement: bool = False
    needs_difficulty_adjustment: bool = False
    suggested_quality_score: Optional[float] = None
    
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)

class LearningPathAnalytics(BaseModel):
    path_name: str
    
    # Participation Metrics
    enrolled_users: int = 0
    completed_users: int = 0
    completion_rate: float = 0.0
    
    # Performance Metrics
    avg_improvement_rate: float = 0.0
    avg_completion_time_days: float = 0.0
    success_rate_by_company: Dict[str, float] = {}
    
    # Content Quality
    most_effective_topics: List[str] = []
    least_effective_topics: List[str] = []
    recommended_adjustments: List[str] = []
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AIPerformanceMetrics(BaseModel):
    service_name: str  # gemini, groq, huggingface
    
    # Usage Statistics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    
    # Quality Metrics
    question_generation_quality: float = 0.0
    explanation_quality_rating: float = 0.0
    difficulty_assessment_accuracy: float = 0.0
    
    # Cost Tracking
    total_cost_usd: float = 0.0
    cost_per_request: float = 0.0
    
    # Performance Trends
    daily_usage: Dict[str, int] = {}
    quality_trends: Dict[str, float] = {}
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class RealtimeAnalytics(BaseModel):
    # Current Active Users
    active_users_count: int = 0
    
    # Real-time Activity
    questions_answered_last_hour: int = 0
    new_users_today: int = 0
    current_success_rate: float = 0.0
    
    # System Health
    ai_services_status: Dict[str, str] = {}  # service_name: status
    database_performance: Dict[str, float] = {}
    
    # Popular Content
    top_categories_today: List[str] = []
    trending_companies: List[str] = []
    
    # Alerts
    system_alerts: List[str] = []
    performance_warnings: List[str] = []
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CompanyAnalytics(BaseModel):
    company_name: str
    
    # Question Patterns
    total_company_questions: int = 0
    difficulty_distribution: Dict[str, int] = {}
    category_distribution: Dict[str, int] = {}
    
    # Student Performance
    students_preparing: int = 0
    avg_readiness_score: float = 0.0
    predicted_success_rate: float = 0.0
    
    # Content Quality
    question_quality_score: float = 0.0
    needs_more_questions: List[str] = []  # Categories needing more questions
    
    # Trends
    popularity_trend: str = "stable"  # growing, declining, stable
    success_rate_trend: float = 0.0
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str  # daily, weekly, monthly, custom
    
    # Report Data
    global_analytics: GlobalAnalytics
    question_insights: List[QuestionInsight] = []
    learning_path_analytics: List[LearningPathAnalytics] = []
    ai_performance: List[AIPerformanceMetrics] = []
    company_analytics: List[CompanyAnalytics] = []
    
    # Summary Insights
    key_findings: List[str] = []
    recommendations: List[str] = []
    action_items: List[str] = []
    
    # Report Metadata
    generated_by: str = "ai_analytics_engine"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    report_period_start: datetime
    report_period_end: datetime