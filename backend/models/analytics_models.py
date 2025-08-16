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

# =============================================================================
# SCRAPING ANALYTICS MODELS (Added for Phase 2)
# =============================================================================

class ScrapingSourceAnalytics(BaseModel):
    """Analytics for individual scraping sources"""
    source_id: str
    source_name: str
    source_type: str  # indiabix, geeksforgeeks, etc.
    
    # Performance Metrics
    total_scraping_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    success_rate: float = 0.0
    
    # Content Metrics
    total_questions_scraped: int = 0
    questions_approved: int = 0
    questions_rejected: int = 0
    avg_quality_score: float = 0.0
    
    # Timing Metrics
    avg_job_duration_minutes: float = 0.0
    avg_questions_per_minute: float = 0.0
    last_successful_scrape: Optional[datetime] = None
    
    # Quality Trends
    quality_trend: str = "stable"  # improving, declining, stable
    reliability_score: float = 100.0
    
    # Issues & Errors
    common_errors: List[str] = []
    blocking_incidents: int = 0
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ScrapingJobAnalytics(BaseModel):
    """Analytics for scraping job performance"""
    
    # Job Performance Summary
    total_jobs_executed: int = 0
    jobs_in_progress: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    
    # Content Processing Summary
    total_questions_extracted: int = 0
    questions_auto_approved: int = 0
    questions_auto_rejected: int = 0
    questions_under_review: int = 0
    
    # Quality Distribution
    quality_score_ranges: Dict[str, int] = {
        "90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "below-60": 0
    }
    
    # Processing Efficiency
    avg_processing_time_per_question: float = 0.0
    duplicate_detection_rate: float = 0.0
    ai_processing_success_rate: float = 0.0
    
    # Resource Utilization
    peak_concurrent_jobs: int = 0
    avg_memory_usage_mb: float = 0.0
    avg_cpu_utilization: float = 0.0
    
    # Trend Analysis
    daily_question_extraction: Dict[str, int] = {}  # date -> count
    weekly_quality_trends: Dict[str, float] = {}    # week -> avg_quality
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ContentQualityAnalytics(BaseModel):
    """Analytics for scraped content quality assessment"""
    
    # Quality Gate Performance
    auto_approval_rate: float = 0.0
    auto_rejection_rate: float = 0.0
    human_review_rate: float = 0.0
    
    # Quality Score Analysis
    avg_quality_score: float = 0.0
    median_quality_score: float = 0.0
    quality_score_std_dev: float = 0.0
    
    # AI Processing Results
    successful_ai_enhancements: int = 0
    ai_processing_failures: int = 0
    improvement_suggestions_generated: int = 0
    
    # Duplicate Detection Performance
    total_duplicates_detected: int = 0
    duplicate_clusters_created: int = 0
    false_positive_rate: float = 0.0  # If available from human feedback
    
    # Source Quality Comparison
    quality_by_source: Dict[str, float] = {}  # source_name -> avg_quality
    reliability_by_source: Dict[str, float] = {}
    
    # Content Categories
    quality_by_category: Dict[str, float] = {}
    extraction_success_by_category: Dict[str, float] = {}
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ScrapingSystemHealth(BaseModel):
    """System health metrics for scraping infrastructure"""
    
    # System Status
    active_scraping_jobs: int = 0
    queued_jobs: int = 0
    failed_jobs_last_24h: int = 0
    
    # Service Health
    selenium_driver_health: str = "healthy"  # healthy, degraded, down
    playwright_driver_health: str = "healthy"
    ai_services_health: Dict[str, str] = {}  # service -> status
    
    # Performance Indicators
    avg_response_time_ms: float = 0.0
    job_queue_length: int = 0
    memory_usage_percentage: float = 0.0
    
    # Error Rates
    extraction_error_rate: float = 0.0
    ai_processing_error_rate: float = 0.0
    network_timeout_rate: float = 0.0
    
    # Resource Limits
    concurrent_job_limit: int = 5
    current_concurrent_jobs: int = 0
    rate_limit_violations: int = 0
    
    # Alerts & Warnings
    active_alerts: List[str] = []
    performance_warnings: List[str] = []
    
    # Uptime
    system_uptime_hours: float = 0.0
    last_restart: Optional[datetime] = None
    
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str  # daily, weekly, monthly, custom
    
    # Report Data
    global_analytics: GlobalAnalytics
    question_insights: List[QuestionInsight] = []
    learning_path_analytics: List[LearningPathAnalytics] = []
    ai_performance: List[AIPerformanceMetrics] = []
    company_analytics: List[CompanyAnalytics] = []
    
    # Scraping Analytics (Added for Phase 2)
    scraping_source_analytics: List[ScrapingSourceAnalytics] = []
    scraping_job_analytics: Optional[ScrapingJobAnalytics] = None
    content_quality_analytics: Optional[ContentQualityAnalytics] = None
    scraping_system_health: Optional[ScrapingSystemHealth] = None
    
    # Summary Insights
    key_findings: List[str] = []
    recommendations: List[str] = []
    action_items: List[str] = []
    
    # Report Metadata
    generated_by: str = "ai_analytics_engine"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    report_period_start: datetime
    report_period_end: datetime