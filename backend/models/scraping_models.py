from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

# =============================================================================
# SCRAPING SOURCE ENUMS
# =============================================================================

class ScrapingSourceType(str, Enum):
    INDIABIX = "indiabix"
    GEEKSFORGEEKS = "geeksforgeeks"
    CUSTOM = "custom"

class ScrapingJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ContentExtractionMethod(str, Enum):
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    REQUESTS = "requests"
    HYBRID = "hybrid"

class QualityGate(str, Enum):
    AUTO_APPROVE = "auto_approve"  # High quality, auto-approved
    AUTO_REJECT = "auto_reject"    # Low quality, auto-rejected  
    HUMAN_REVIEW = "human_review"  # Medium quality, needs review

# =============================================================================
# DATA SOURCE MODELS
# =============================================================================

class DataSourceConfig(BaseModel):
    """Configuration for a scraping data source"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source_type: ScrapingSourceType
    base_url: str
    
    # Extraction Configuration
    extraction_method: ContentExtractionMethod = ContentExtractionMethod.SELENIUM
    selectors: Dict[str, str] = {}  # CSS selectors for different elements
    pagination_config: Dict[str, Any] = {}
    
    # Rate Limiting & Ethics
    rate_limit_delay: float = 2.0  # Seconds between requests
    max_concurrent_requests: int = 3
    respect_robots_txt: bool = True
    user_agent_rotation: bool = True
    
    # Status & Metadata
    is_active: bool = True
    last_scraped: Optional[datetime] = None
    total_questions_scraped: int = 0
    success_rate: float = 0.0
    
    # Quality Metrics
    avg_quality_score: float = 0.0
    reliability_score: float = 100.0  # Source reliability (0-100)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapingTarget(BaseModel):
    """Specific target within a data source"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str  # Reference to DataSourceConfig
    
    # Target Details
    category: str  # e.g., "quantitative", "logical"
    subcategory: Optional[str] = None
    target_url: str
    expected_question_count: Optional[int] = None
    
    # Extraction Specifics
    question_selectors: Dict[str, str] = {}
    custom_extraction_rules: Dict[str, Any] = {}
    
    # Progress Tracking
    last_scraped_page: int = 0
    total_pages: Optional[int] = None
    questions_extracted: int = 0
    
    # Status
    is_active: bool = True
    priority: int = 1  # 1=highest, 5=lowest
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# SCRAPING JOB MODELS  
# =============================================================================

class ScrapingJobConfig(BaseModel):
    """Configuration for a scraping job"""
    
    # Basic Job Info
    job_name: str
    description: Optional[str] = None
    source_ids: List[str]  # Data sources to scrape
    target_ids: Optional[List[str]] = None  # Specific targets (optional)
    
    # Job Parameters
    max_questions_per_source: Optional[int] = 1000
    quality_threshold: float = 70.0  # Minimum quality score to accept
    enable_ai_processing: bool = True
    enable_duplicate_detection: bool = True
    
    # Scheduling
    is_scheduled: bool = False
    schedule_cron: Optional[str] = None  # Cron expression for scheduling
    
    # Advanced Options
    custom_filters: Dict[str, Any] = {}
    priority_keywords: List[str] = []
    exclude_patterns: List[str] = []
    
class ScrapingJob(BaseModel):
    """Active or completed scraping job"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: ScrapingJobConfig
    
    # Job Execution Status
    status: ScrapingJobStatus = ScrapingJobStatus.PENDING
    current_phase: str = "initialization"
    progress_percentage: float = 0.0
    
    # Execution Details
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Results Summary
    total_pages_processed: int = 0
    questions_extracted: int = 0
    questions_approved: int = 0
    questions_rejected: int = 0
    questions_pending_review: int = 0
    
    # Error Tracking
    error_count: int = 0
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Performance Metrics
    avg_extraction_time_per_page: float = 0.0
    success_rate: float = 0.0
    
    # Logs & Debugging
    execution_logs: List[str] = []
    debug_screenshots: List[str] = []  # Paths to debug screenshots
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# EXTRACTED CONTENT MODELS
# =============================================================================

class RawExtractedQuestion(BaseModel):
    """Raw question data extracted from source before AI processing"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Source Information
    source_id: str
    source_url: str
    job_id: str
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Raw Extracted Data
    raw_question_text: str
    raw_options: List[str] = []
    raw_correct_answer: Optional[str] = None
    raw_explanation: Optional[str] = None
    
    # Extraction Metadata
    page_number: Optional[int] = None
    question_index: Optional[int] = None
    extraction_method: ContentExtractionMethod
    
    # Raw Classification (before AI enhancement)
    detected_category: Optional[str] = None
    detected_difficulty: Optional[str] = None
    
    # Quality Indicators (before AI processing)
    extraction_confidence: float = 0.0  # How confident the extractor is
    completeness_score: float = 0.0     # How complete the extracted data is
    
    # Status
    processing_status: str = "raw"  # raw, processing, processed, failed
    ai_processed: bool = False
    
class ProcessedScrapedQuestion(BaseModel):
    """Scraped question after AI processing and quality assessment"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_question_id: str  # Reference to RawExtractedQuestion
    
    # AI Enhanced Data (using existing question models structure)
    enhanced_question_id: Optional[str] = None  # If converted to EnhancedQuestion
    
    # Quality Assessment Results
    quality_gate_result: QualityGate
    quality_score: float = 0.0
    quality_reasons: List[str] = []
    
    # Duplicate Detection Results
    is_duplicate: bool = False
    duplicate_cluster_id: Optional[str] = None
    similarity_scores: Dict[str, float] = {}  # question_id -> similarity_score
    
    # AI Processing Results
    ai_categorization: Optional[str] = None
    ai_difficulty_assessment: Optional[str] = None
    ai_quality_improvements: List[str] = []
    
    # Human Review (if required)
    requires_human_review: bool = False
    human_review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    
    # Final Status
    final_status: str = "pending"  # pending, approved, rejected, needs_review
    approved_at: Optional[datetime] = None
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# QUALITY & MONITORING MODELS
# =============================================================================

class ScrapingQualityMetrics(BaseModel):
    """Quality metrics for scraped content"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    source_id: str
    
    # Content Quality Metrics
    total_questions_extracted: int = 0
    auto_approved_count: int = 0
    auto_rejected_count: int = 0
    human_review_count: int = 0
    
    # Quality Distribution
    quality_score_distribution: Dict[str, int] = {}  # score_range -> count
    avg_quality_score: float = 0.0
    quality_improvement_rate: float = 0.0
    
    # Duplicate Detection Metrics
    duplicates_detected: int = 0
    duplicate_clusters: int = 0
    unique_questions: int = 0
    
    # Processing Performance
    avg_processing_time_per_question: float = 0.0
    ai_processing_success_rate: float = 0.0
    extraction_accuracy: float = 0.0
    
    # Trend Analysis
    quality_trend: str = "stable"  # improving, declining, stable
    
    measured_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapingPerformanceLog(BaseModel):
    """Performance and monitoring logs for scraping operations"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    
    # Performance Metrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operation: str  # page_load, extraction, ai_processing, etc.
    duration_seconds: float
    success: bool
    
    # Resource Usage
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Details
    details: Dict[str, Any] = {}
    error_message: Optional[str] = None
    
class AntiDetectionLog(BaseModel):
    """Logs for anti-detection measures"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    source_url: str
    
    # Detection Measures Used
    user_agent: str
    proxy_used: Optional[str] = None
    request_delay: float
    
    # Response Analysis
    response_status: int
    response_time: float
    potential_blocking_detected: bool = False
    blocking_indicators: List[str] = []
    
    # Rate Limiting
    requests_in_window: int
    rate_limit_triggered: bool = False
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# REQUEST/RESPONSE MODELS FOR API
# =============================================================================

class CreateScrapingJobRequest(BaseModel):
    """Request model for creating a new scraping job"""
    
    job_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    source_names: List[str]  # Names of sources (e.g., ["indiabix", "geeksforgeeks"])
    
    # Optional Parameters
    max_questions_per_source: Optional[int] = Field(1000, ge=1, le=10000)
    quality_threshold: Optional[float] = Field(70.0, ge=0.0, le=100.0)
    target_categories: Optional[List[str]] = None
    
    # Advanced Options
    enable_ai_processing: bool = True
    enable_duplicate_detection: bool = True
    priority_level: int = Field(1, ge=1, le=5)

class ScrapingJobResponse(BaseModel):
    """Response model for scraping job operations"""
    
    job_id: str
    status: ScrapingJobStatus
    message: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None

class ScrapingJobStatusResponse(BaseModel):
    """Detailed status response for a scraping job"""
    
    job_id: str
    status: ScrapingJobStatus
    current_phase: str
    progress_percentage: float
    
    # Progress Details
    sources_processed: int
    total_sources: int
    questions_extracted: int
    questions_processed: int
    
    # Time Information
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    elapsed_time_seconds: Optional[float] = None
    
    # Error Information
    error_count: int
    last_error: Optional[str] = None
    
    # Recent Logs (last 10)
    recent_logs: List[str] = []

class BulkScrapingRequest(BaseModel):
    """Request for bulk scraping operations"""
    
    jobs: List[CreateScrapingJobRequest]
    execute_sequentially: bool = False
    global_rate_limit: Optional[float] = None

class ScrapingAnalyticsRequest(BaseModel):
    """Request for scraping analytics data"""
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_ids: Optional[List[str]] = None
    job_ids: Optional[List[str]] = None
    include_quality_metrics: bool = True
    include_performance_data: bool = False

# =============================================================================
# COLLECTION MODELS FOR BATCH OPERATIONS
# =============================================================================

class ScrapingBatchResult(BaseModel):
    """Results from a batch scraping operation"""
    
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_ids: List[str]
    
    # Batch Summary
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    
    # Content Summary  
    total_questions_extracted: int
    total_questions_approved: int
    avg_quality_score: float
    
    # Performance Summary
    total_execution_time_seconds: float
    avg_questions_per_minute: float
    
    # Status
    batch_status: str  # completed, partial, failed
    completion_timestamp: datetime = Field(default_factory=datetime.utcnow)

class SourceReliabilityReport(BaseModel):
    """Report on the reliability and performance of data sources"""
    
    source_id: str
    source_name: str
    
    # Reliability Metrics
    reliability_score: float  # 0-100
    uptime_percentage: float
    avg_response_time: float
    
    # Content Quality
    total_questions_scraped: int
    avg_quality_score: float
    success_rate: float
    
    # Trend Analysis
    quality_trend: str  # improving, stable, declining
    recommended_actions: List[str] = []
    
    # Issues & Errors
    recent_errors: List[str] = []
    blocking_incidents: int = 0
    last_successful_scrape: Optional[datetime] = None
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# VALIDATORS - Applied to existing ScrapingJobConfig class above
# =============================================================================