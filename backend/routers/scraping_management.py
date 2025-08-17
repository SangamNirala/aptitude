"""
TASK 14: Scraping Management API Endpoints
RESTful APIs for scraping operations management including job lifecycle, source management, 
real-time status monitoring, and bulk operations.
"""

import logging
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query, Path, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import uuid

# Import models and services
from models.scraping_models import (
    ScrapingJob, ScrapingJobStatus, ScrapingJobConfig, DataSourceConfig, ScrapingTarget,
    CreateScrapingJobRequest, ScrapingJobResponse, ScrapingJobStatusResponse, 
    BulkScrapingRequest, ScrapingBatchResult, SourceReliabilityReport,
    ScrapingSourceType, ContentExtractionMethod, QualityGate
)
from services.job_manager_service import BackgroundJobManager, JobPriority, create_job_manager
from services.source_management_service import SourceManagementService
from scraping.scraper_engine import ScrapingEngine, get_scraping_engine
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/scraping", tags=["Scraping Management"])

# Database connection (will be initialized on startup)
client: Optional[AsyncIOMotorClient] = None
db = None

# Global services (initialized on startup)
job_manager: Optional[BackgroundJobManager] = None
source_manager: Optional[SourceManagementService] = None
scraping_engine: Optional[ScrapingEngine] = None

# =============================================================================
# SERVICE INITIALIZATION
# =============================================================================

async def initialize_scraping_services():
    """Initialize scraping management services"""
    global job_manager, source_manager, scraping_engine, client, db
    
    # Initialize database connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        logger.info("Initializing scraping management services...")
        
        # Initialize job manager
        job_manager = create_job_manager(max_concurrent_jobs=5)
        await job_manager.start()
        
        # Initialize source management service  
        source_manager = SourceManagementService(db)
        await source_manager.initialize_default_sources()
        
        # Initialize scraping engine
        scraping_engine = get_scraping_engine()
        
        logger.info("✅ Scraping management services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing scraping services: {str(e)}")
        raise

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class JobStartRequest(BaseModel):
    """Request to start a job"""
    priority: JobPriority = JobPriority.NORMAL
    custom_config: Optional[Dict[str, Any]] = None

class JobControlResponse(BaseModel):
    """Response for job control operations"""
    job_id: str
    action: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SourceUpdateRequest(BaseModel):
    """Request to update source configuration"""
    is_active: Optional[bool] = None
    rate_limit_delay: Optional[float] = None
    max_concurrent_requests: Optional[int] = None
    selectors: Optional[Dict[str, str]] = None
    pagination_config: Optional[Dict[str, Any]] = None

class QueueStatusResponse(BaseModel):
    """Queue status response"""
    total_queued: int
    by_priority: Dict[str, int]
    active_jobs: int
    available_executors: int
    total_executors: int
    system_load: Dict[str, float]
    estimated_wait_time_minutes: float

class SystemStatusResponse(BaseModel):
    """System status response"""
    status: str
    services: Dict[str, str]
    active_jobs: int
    queue_length: int
    system_health: Dict[str, Any]
    uptime_hours: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# JOB MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/jobs", response_model=ScrapingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_job(
    request: CreateScrapingJobRequest,
    background_tasks: BackgroundTasks
) -> ScrapingJobResponse:
    """
    Create a new scraping job
    
    Creates a new scraping job and adds it to the execution queue.
    The job will be processed asynchronously by the background job manager.
    """
    try:
        logger.info(f"Creating new scraping job: {request.job_name}")
        
        if not job_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scraping services not initialized"
            )
        
        # Validate sources
        if not request.source_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one source must be specified"
            )
        
        # Get source configurations
        sources = []
        for source_name in request.source_names:
            source_config = await source_manager.get_source_by_name(source_name)
            if not source_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source '{source_name}' not found"
                )
            sources.append(source_config.id)
        
        # Create job configuration
        job_config = ScrapingJobConfig(
            job_name=request.job_name,
            description=request.description,
            source_ids=sources,
            max_questions_per_source=request.max_questions_per_source,
            quality_threshold=request.quality_threshold,
            enable_ai_processing=request.enable_ai_processing,
            enable_duplicate_detection=request.enable_duplicate_detection
        )
        
        # Create scraping job
        scraping_job = ScrapingJob(
            config=job_config,
            status=ScrapingJobStatus.PENDING
        )
        
        # Save job to database
        job_dict = scraping_job.dict()
        await db.scraping_jobs.insert_one(job_dict)
        
        # Submit to job manager
        priority = JobPriority.HIGH if request.priority_level <= 2 else JobPriority.NORMAL
        
        async def execute_scraping_job(job: ScrapingJob):
            """Job execution function"""
            return await scraping_engine.execute_job(job)
        
        job_id = await job_manager.submit_job(
            scraping_job,
            execute_scraping_job,
            priority=priority
        )
        
        logger.info(f"Scraping job {job_id} created and queued successfully")
        
        return ScrapingJobResponse(
            job_id=job_id,
            status=ScrapingJobStatus.PENDING,
            message=f"Scraping job '{request.job_name}' created and queued for execution",
            created_at=scraping_job.created_at,
            estimated_completion=datetime.utcnow() + timedelta(hours=2)  # Estimated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scraping job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scraping job: {str(e)}"
        )

@router.get("/jobs", response_model=List[ScrapingJobStatusResponse])
async def list_scraping_jobs(
    status_filter: Optional[ScrapingJobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip")
) -> List[ScrapingJobStatusResponse]:
    """
    List scraping jobs with optional filtering
    
    Returns a list of scraping jobs with their current status and progress information.
    Results can be filtered by status and paginated.
    """
    try:
        logger.info(f"Listing scraping jobs (status={status_filter}, limit={limit}, offset={offset})")
        
        # Build query filter
        query_filter = {}
        if status_filter:
            query_filter["status"] = status_filter.value
        
        # Get jobs from database
        cursor = db.scraping_jobs.find(query_filter).skip(offset).limit(limit).sort("created_at", -1)
        jobs = await cursor.to_list(length=limit)
        
        # Convert to response format
        job_responses = []
        for job_data in jobs:
            # Get live status from job manager if active
            live_status = None
            if job_manager and job_data["status"] in [ScrapingJobStatus.PENDING.value, ScrapingJobStatus.RUNNING.value]:
                live_status = await job_manager.get_job_status(job_data["id"])
            
            if live_status:
                job_responses.append(live_status)
            else:
                # Create response from database data
                elapsed_time = None
                if job_data.get("started_at") and job_data.get("completed_at"):
                    elapsed_time = (job_data["completed_at"] - job_data["started_at"]).total_seconds()
                elif job_data.get("started_at"):
                    elapsed_time = (datetime.utcnow() - job_data["started_at"]).total_seconds()
                
                job_responses.append(ScrapingJobStatusResponse(
                    job_id=job_data["id"],
                    status=ScrapingJobStatus(job_data["status"]),
                    current_phase=job_data.get("current_phase", "unknown"),
                    progress_percentage=job_data.get("progress_percentage", 0.0),
                    sources_processed=0,
                    total_sources=len(job_data.get("config", {}).get("source_ids", [])),
                    questions_extracted=job_data.get("questions_extracted", 0),
                    questions_processed=job_data.get("questions_approved", 0) + job_data.get("questions_rejected", 0),
                    started_at=job_data.get("started_at"),
                    estimated_completion=job_data.get("estimated_completion"),
                    elapsed_time_seconds=elapsed_time,
                    error_count=job_data.get("error_count", 0),
                    last_error=job_data.get("last_error"),
                    recent_logs=job_data.get("execution_logs", [])[-10:] if job_data.get("execution_logs") else []
                ))
        
        logger.info(f"Retrieved {len(job_responses)} scraping jobs")
        return job_responses
        
    except Exception as e:
        logger.error(f"Error listing scraping jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scraping jobs: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=ScrapingJobStatusResponse)
async def get_job_status(
    job_id: str = Path(..., description="Scraping job ID")
) -> ScrapingJobStatusResponse:
    """
    Get detailed status of a specific scraping job
    
    Returns comprehensive status information including progress, performance metrics,
    and execution logs for the specified job.
    """
    try:
        logger.info(f"Getting status for job {job_id}")
        
        # Check job manager first for live status
        if job_manager:
            live_status = await job_manager.get_job_status(job_id)
            if live_status:
                return live_status
        
        # Fall back to database
        job_data = await db.scraping_jobs.find_one({"id": job_id})
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Calculate elapsed time
        elapsed_time = None
        if job_data.get("started_at") and job_data.get("completed_at"):
            elapsed_time = (job_data["completed_at"] - job_data["started_at"]).total_seconds()
        elif job_data.get("started_at"):
            elapsed_time = (datetime.utcnow() - job_data["started_at"]).total_seconds()
        
        return ScrapingJobStatusResponse(
            job_id=job_id,
            status=ScrapingJobStatus(job_data["status"]),
            current_phase=job_data.get("current_phase", "unknown"),
            progress_percentage=job_data.get("progress_percentage", 0.0),
            sources_processed=0,
            total_sources=len(job_data.get("config", {}).get("source_ids", [])),
            questions_extracted=job_data.get("questions_extracted", 0),
            questions_processed=job_data.get("questions_approved", 0) + job_data.get("questions_rejected", 0),
            started_at=job_data.get("started_at"),
            estimated_completion=job_data.get("estimated_completion"),
            elapsed_time_seconds=elapsed_time,
            error_count=job_data.get("error_count", 0),
            last_error=job_data.get("last_error"),
            recent_logs=job_data.get("execution_logs", [])[-10:] if job_data.get("execution_logs") else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}"
        )

@router.put("/jobs/{job_id}/start", response_model=JobControlResponse)
async def start_job(
    job_id: str = Path(..., description="Scraping job ID"),
    request: JobStartRequest = Body(...)
) -> JobControlResponse:
    """
    Start a paused or queued scraping job
    
    Starts execution of a job that is currently paused or moves a queued job to higher priority.
    """
    try:
        logger.info(f"Starting job {job_id}")
        
        if not job_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Job manager not available"
            )
        
        # Get current job status from database first
        job_doc = await db.scraping_jobs.find_one({"id": job_id})
        if not job_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Try to get live status from job manager
        current_status = None
        if job_manager:
            current_status = await job_manager.get_job_status(job_id)
        
        # If no live status, use database status
        if not current_status:
            current_job_status = ScrapingJobStatus(job_doc["status"])
            # Create a minimal status response for database jobs
            class SimpleJobStatus:
                def __init__(self, status):
                    self.status = status
            current_status = SimpleJobStatus(current_job_status)
        else:
            current_job_status = current_status.status
        
        if current_job_status == ScrapingJobStatus.RUNNING:
            return JobControlResponse(
                job_id=job_id,
                action="start",
                status="already_running",
                message="Job is already running"
            )
        
        if current_job_status == ScrapingJobStatus.COMPLETED:
            return JobControlResponse(
                job_id=job_id,
                action="start",
                status="already_completed",
                message="Job has already completed"
            )
        
        # For PENDING jobs, resubmit to job manager
        if current_job_status == ScrapingJobStatus.PENDING and job_manager:
            try:
                # Recreate job object from database
                scraping_job = ScrapingJob(**job_doc)
                priority = JobPriority.HIGH
                
                async def execute_scraping_job(job: ScrapingJob):
                    """Job execution function"""
                    return await scraping_engine.execute_job(job)
                
                # Resubmit job 
                await job_manager.submit_job(
                    scraping_job,
                    execute_scraping_job,
                    priority=priority
                )
                
                # Update status in database to reflect it's running
                await db.scraping_jobs.update_one(
                    {"id": job_id},
                    {"$set": {"status": ScrapingJobStatus.RUNNING.value, "updated_at": datetime.utcnow()}}
                )
                
            except Exception as e:
                logger.warning(f"Failed to resubmit job to manager: {str(e)}")
        
        # For PAUSED jobs, update status to PENDING to restart
        if current_job_status == ScrapingJobStatus.PAUSED:
            await db.scraping_jobs.update_one(
                {"id": job_id},
                {"$set": {
                    "status": ScrapingJobStatus.PENDING.value, 
                    "updated_at": datetime.utcnow(),
                    "current_phase": "restarted"
                }}
            )
        
        return JobControlResponse(
            job_id=job_id,
            action="start",
            status="started",
            message="Job start request processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start job: {str(e)}"
        )

@router.put("/jobs/{job_id}/stop", response_model=JobControlResponse)
async def stop_job(
    job_id: str = Path(..., description="Scraping job ID")
) -> JobControlResponse:
    """
    Stop/cancel a running or queued scraping job
    
    Cancels execution of a running job or removes a queued job from the execution queue.
    """
    try:
        logger.info(f"Stopping job {job_id}")
        
        if not job_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Job manager not available"
            )
        
        success = await job_manager.cancel_job(job_id)
        
        if success:
            # Update database
            await db.scraping_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": ScrapingJobStatus.CANCELLED.value,
                        "current_phase": "cancelled",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return JobControlResponse(
                job_id=job_id,
                action="stop",
                status="cancelled",
                message="Job cancelled successfully"
            )
        else:
            return JobControlResponse(
                job_id=job_id,
                action="stop",
                status="not_found",
                message="Job not found or already completed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop job: {str(e)}"
        )

@router.put("/jobs/{job_id}/pause", response_model=JobControlResponse)
async def pause_job(
    job_id: str = Path(..., description="Scraping job ID")
) -> JobControlResponse:
    """
    Pause a running scraping job
    
    Pauses execution of a currently running job. The job can be resumed later.
    """
    try:
        logger.info(f"Pausing job {job_id}")
        
        # Check if job exists first
        job_doc = await db.scraping_jobs.find_one({"id": job_id})
        if not job_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        current_status = ScrapingJobStatus(job_doc["status"])
        
        # Check if job is in a pausable state
        if current_status not in [ScrapingJobStatus.RUNNING, ScrapingJobStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is in {current_status.value} state and cannot be paused"
            )
        
        # Update job status in database
        result = await db.scraping_jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": ScrapingJobStatus.PAUSED.value,
                    "current_phase": "paused",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update job status"
            )
        
        # Try to pause in job manager if available
        if job_manager:
            try:
                await job_manager.cancel_job(job_id)
            except Exception as e:
                logger.warning(f"Failed to pause job in manager: {str(e)}")
        
        return JobControlResponse(
            job_id=job_id,
            action="pause",
            status="paused",
            message="Job paused successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause job: {str(e)}"
        )

@router.delete("/jobs/{job_id}", response_model=JobControlResponse)
async def delete_job(
    job_id: str = Path(..., description="Scraping job ID"),
    force: bool = Query(False, description="Force delete even if job is running")
) -> JobControlResponse:
    """
    Delete a scraping job
    
    Removes a job from the system. Running jobs must be stopped first unless force=true.
    """
    try:
        logger.info(f"Deleting job {job_id} (force={force})")
        
        # Get job from database
        job_data = await db.scraping_jobs.find_one({"id": job_id})
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if job is running
        current_status = ScrapingJobStatus(job_data["status"])
        if current_status == ScrapingJobStatus.RUNNING and not force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete running job. Stop the job first or use force=true"
            )
        
        # Cancel job if it's active
        if job_manager and current_status in [ScrapingJobStatus.RUNNING, ScrapingJobStatus.PENDING]:
            await job_manager.cancel_job(job_id)
        
        # Delete from database
        await db.scraping_jobs.delete_one({"id": job_id})
        
        # Also delete related data
        await db.raw_extracted_questions.delete_many({"job_id": job_id})
        await db.processed_scraped_questions.delete_many({"raw_question_id": {"$regex": f".*{job_id}.*"}})
        
        return JobControlResponse(
            job_id=job_id,
            action="delete",
            status="deleted",
            message="Job and related data deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )

# =============================================================================
# SOURCE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/sources", response_model=List[DataSourceConfig])
async def list_sources(
    source_type: Optional[ScrapingSourceType] = Query(None, description="Filter by source type"),
    active_only: bool = Query(True, description="Return only active sources")
) -> List[DataSourceConfig]:
    """
    List available scraping sources
    
    Returns a list of configured scraping sources with their current status and configuration.
    """
    try:
        logger.info(f"Listing sources (type={source_type}, active_only={active_only})")
        
        if not source_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Source management service not available"
            )
        
        # Build filter
        filters = {}
        if source_type:
            filters["source_type"] = source_type.value
        if active_only:
            filters["is_active"] = True
        
        sources = await source_manager.get_sources(filters)
        
        logger.info(f"Retrieved {len(sources)} sources")
        return sources
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sources: {str(e)}"
        )

@router.get("/sources/{source_id}", response_model=DataSourceConfig)
async def get_source(
    source_id: str = Path(..., description="Source ID")
) -> DataSourceConfig:
    """
    Get detailed information about a specific source
    
    Returns comprehensive configuration and status information for the specified source.
    """
    try:
        logger.info(f"Getting source {source_id}")
        
        if not source_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Source management service not available"
            )
        
        source = await source_manager.get_source(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_id} not found"
            )
        
        return source
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source {source_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve source: {str(e)}"
        )

@router.put("/sources/{source_id}", response_model=DataSourceConfig)
async def update_source(
    source_id: str = Path(..., description="Source ID"),
    request: SourceUpdateRequest = Body(...)
) -> DataSourceConfig:
    """
    Update source configuration
    
    Updates the configuration settings for a scraping source such as rate limits,
    active status, and extraction parameters.
    """
    try:
        logger.info(f"Updating source {source_id}")
        
        if not source_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Source management service not available"
            )
        
        # Get current source
        source = await source_manager.get_source(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_id} not found"
            )
        
        # Update fields
        update_data = {}
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.rate_limit_delay is not None:
            update_data["rate_limit_delay"] = request.rate_limit_delay
        if request.max_concurrent_requests is not None:
            update_data["max_concurrent_requests"] = request.max_concurrent_requests
        if request.selectors is not None:
            update_data["selectors"] = request.selectors
        if request.pagination_config is not None:
            update_data["pagination_config"] = request.pagination_config
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update in database
            await db.data_sources.update_one(
                {"id": source_id},
                {"$set": update_data}
            )
            
            # Get updated source
            updated_source = await source_manager.get_source(source_id)
            if updated_source:
                return updated_source
        
        return source
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating source {source_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update source: {str(e)}"
        )

# =============================================================================
# BULK OPERATIONS ENDPOINTS  
# =============================================================================

@router.post("/bulk-jobs", response_model=ScrapingBatchResult, status_code=status.HTTP_201_CREATED)
async def create_bulk_jobs(
    request: BulkScrapingRequest,
    background_tasks: BackgroundTasks
) -> ScrapingBatchResult:
    """
    Create multiple scraping jobs in bulk
    
    Creates multiple scraping jobs and optionally executes them sequentially or in parallel.
    Returns a batch result with summary statistics.
    """
    try:
        logger.info(f"Creating bulk scraping jobs: {len(request.jobs)} jobs")
        
        if not job_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scraping services not initialized"
            )
        
        job_ids = []
        failed_jobs = 0
        
        for job_request in request.jobs:
            try:
                # Create individual job (reuse existing logic)
                response = await create_scraping_job(job_request, background_tasks)
                job_ids.append(response.job_id)
                
                # Add delay for sequential execution
                if request.execute_sequentially:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"Failed to create job '{job_request.job_name}': {str(e)}")
                failed_jobs += 1
        
        # Calculate batch statistics
        batch_result = ScrapingBatchResult(
            job_ids=job_ids,
            total_jobs=len(request.jobs),
            completed_jobs=len(job_ids),
            failed_jobs=failed_jobs,
            total_questions_extracted=0,  # Will be updated as jobs complete
            total_questions_approved=0,
            avg_quality_score=0.0,
            total_execution_time_seconds=0.0,
            avg_questions_per_minute=0.0,
            batch_status="partially_created" if failed_jobs > 0 else "created"
        )
        
        # Store batch result
        batch_dict = batch_result.dict()
        await db.scraping_batch_results.insert_one(batch_dict)
        
        logger.info(f"Bulk job creation completed: {len(job_ids)} created, {failed_jobs} failed")
        
        return batch_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk jobs: {str(e)}"
        )

# =============================================================================
# QUEUE AND SYSTEM STATUS ENDPOINTS
# =============================================================================

@router.get("/queue-status", response_model=QueueStatusResponse)
async def get_queue_status() -> QueueStatusResponse:
    """
    Get current queue status and system load
    
    Returns information about the job queue, active jobs, and system resource utilization.
    """
    try:
        logger.info("Getting queue status")
        
        if not job_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Job manager not available"
            )
        
        # Get queue status from job manager
        queue_status = await job_manager.get_queue_status()
        
        # Get performance metrics
        performance_metrics = await job_manager.get_performance_metrics()
        system_resources = performance_metrics.get("system_resources", {})
        
        # Calculate estimated wait time (simplified)
        total_queued = queue_status.get("total_queued", 0)
        active_jobs = queue_status.get("active_jobs", 0)
        available_executors = queue_status.get("available_executors", 0)
        
        estimated_wait_minutes = 0.0
        if total_queued > 0 and available_executors > 0:
            avg_job_time = 30.0  # Assume 30 minutes average job time
            estimated_wait_minutes = (total_queued / max(1, available_executors)) * avg_job_time
        
        return QueueStatusResponse(
            total_queued=total_queued,
            by_priority=queue_status.get("by_priority", {}),
            active_jobs=active_jobs,
            available_executors=available_executors,
            total_executors=queue_status.get("total_executors", 0),
            system_load={
                "cpu_percent": system_resources.get("cpu_percent", 0.0),
                "memory_percent": system_resources.get("memory_percent", 0.0),
                "disk_percent": system_resources.get("disk_percent", 0.0)
            },
            estimated_wait_time_minutes=estimated_wait_minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve queue status: {str(e)}"
        )

@router.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """
    Get comprehensive system status
    
    Returns overall system health, service status, and key performance indicators.
    """
    try:
        logger.info("Getting system status")
        
        services_status = {}
        system_health = {}
        
        # Check job manager
        if job_manager and job_manager.is_running:
            services_status["job_manager"] = "healthy"
            performance_metrics = await job_manager.get_performance_metrics()
            system_health = performance_metrics.get("health_indicators", {})
        else:
            services_status["job_manager"] = "down"
        
        # Check source manager
        if source_manager:
            services_status["source_manager"] = "healthy"
        else:
            services_status["source_manager"] = "down"
        
        # Check scraping engine
        if scraping_engine:
            services_status["scraping_engine"] = "healthy"
        else:
            services_status["scraping_engine"] = "down"
        
        # Check database
        try:
            await db.command("ping")
            services_status["database"] = "healthy"
        except:
            services_status["database"] = "down"
        
        # Get active jobs count
        active_jobs_count = 0
        queue_length = 0
        
        if job_manager:
            queue_status = await job_manager.get_queue_status()
            active_jobs_count = queue_status.get("active_jobs", 0)
            queue_length = queue_status.get("total_queued", 0)
        
        # Determine overall status
        overall_status = "healthy"
        if any(status == "down" for status in services_status.values()):
            overall_status = "degraded"
        if services_status.get("database") == "down":
            overall_status = "critical"
        
        return SystemStatusResponse(
            status=overall_status,
            services=services_status,
            active_jobs=active_jobs_count,
            queue_length=queue_length,
            system_health=system_health,
            uptime_hours=24.0  # Placeholder - would calculate actual uptime
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system status: {str(e)}"
        )

# =============================================================================
# SOURCE RELIABILITY REPORTING
# =============================================================================

@router.get("/sources/{source_id}/reliability", response_model=SourceReliabilityReport)
async def get_source_reliability(
    source_id: str = Path(..., description="Source ID")
) -> SourceReliabilityReport:
    """
    Get reliability report for a specific source
    
    Returns comprehensive reliability and performance analysis for the specified source
    including uptime, quality metrics, and recommendations.
    """
    try:
        logger.info(f"Getting reliability report for source {source_id}")
        
        if not source_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Source management service not available"
            )
        
        # Get source
        source = await source_manager.get_source(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_id} not found"
            )
        
        # Get reliability metrics from database
        # This would typically aggregate data from job history, error logs, etc.
        
        reliability_report = SourceReliabilityReport(
            source_id=source_id,
            source_name=source.name,
            reliability_score=source.reliability_score,
            uptime_percentage=95.0,  # Placeholder
            avg_response_time=2.5,  # Placeholder
            total_questions_scraped=source.total_questions_scraped,
            avg_quality_score=source.avg_quality_score,
            success_rate=source.success_rate,
            quality_trend="stable",
            recommended_actions=[
                "Monitor extraction success rate",
                "Review rate limiting configuration"
            ],
            recent_errors=[],
            blocking_incidents=0,
            last_successful_scrape=source.last_scraped
        )
        
        return reliability_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source reliability {source_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve source reliability: {str(e)}"
        )

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health")
async def scraping_health_check():
    """
    Health check endpoint for scraping services
    
    Returns basic health status of all scraping-related services and components.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {}
        }
        
        # Check each service
        if job_manager and job_manager.is_running:
            health_status["services"]["job_manager"] = "healthy"
        else:
            health_status["services"]["job_manager"] = "down"
            health_status["status"] = "degraded"
        
        if source_manager:
            health_status["services"]["source_manager"] = "healthy"
        else:
            health_status["services"]["source_manager"] = "down"
            health_status["status"] = "degraded"
        
        if scraping_engine:
            health_status["services"]["scraping_engine"] = "healthy"
        else:
            health_status["services"]["scraping_engine"] = "down"
            health_status["status"] = "degraded"
        
        # Database check
        try:
            await db.command("ping")
            health_status["services"]["database"] = "healthy"
        except:
            health_status["services"]["database"] = "down"
            health_status["status"] = "critical"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in scraping health check: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

# =============================================================================
# STARTUP EVENT HANDLER
# =============================================================================

@router.on_event("startup")
async def startup_scraping_management():
    """Initialize scraping management services on startup"""
    try:
        await initialize_scraping_services()
    except Exception as e:
        logger.error(f"Failed to initialize scraping management services: {str(e)}")

logger.info("✅ Scraping Management API endpoints loaded successfully")