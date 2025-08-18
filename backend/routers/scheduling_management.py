"""
Task 13: Cron-Based Scheduling System API Endpoints
Automated scheduling for regular content updates and maintenance tasks
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid

from models.scraping_models import (
    CreateScrapingJobRequest, ScrapingJobStatus, ScheduleType, ScheduleStatus,
    TriggerType
)
from services.job_manager_service import BackgroundJobManager, JobPriority
from scheduling.cron_scheduler import CronScheduler, ScheduledTask

logger = logging.getLogger(__name__)

# Global scheduler instance (initialized during startup)
scheduler_instance: Optional[CronScheduler] = None

# Pydantic Models for API

class ScheduleRequest(BaseModel):
    name: str = Field(..., description="Schedule name")
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 */6 * * *' for every 6 hours)")
    schedule_type: ScheduleType = Field(default=ScheduleType.SCRAPING, description="Type of scheduled task")
    description: Optional[str] = Field(None, description="Schedule description")
    task_function_name: str = Field(..., description="Task function name from registry")
    task_args: List[Any] = Field(default_factory=list, description="Task function arguments")
    task_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Task function keyword arguments")
    max_runtime_hours: float = Field(default=1.0, description="Maximum runtime hours")
    retry_on_failure: bool = Field(default=True, description="Retry on failure")
    max_retries: int = Field(default=3, description="Maximum retries")

class ScrapingScheduleRequest(BaseModel):
    name: str = Field(..., description="Schedule name")
    cron_expression: str = Field(..., description="Cron expression")
    sources: List[str] = Field(..., description="Source names to scrape")
    max_questions_per_source: int = Field(default=50, description="Maximum questions per source")
    target_categories: List[str] = Field(default_factory=list, description="Target categories")
    priority_level: JobPriority = Field(default=JobPriority.NORMAL, description="Job priority")
    description: Optional[str] = Field(None, description="Schedule description")

class ScheduleResponse(BaseModel):
    schedule_id: str
    name: str
    description: Optional[str]
    schedule_type: str
    status: str
    cron_expression: str
    cron_description: str
    timezone: str
    created_at: datetime
    last_modified: datetime
    is_running: bool
    next_execution_time: Optional[datetime]
    last_execution_time: Optional[datetime]
    metrics: Dict[str, Any]
    configuration: Dict[str, Any]

class SchedulerStatsResponse(BaseModel):
    total_schedules: int
    active_schedules: int
    paused_schedules: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time: float
    scheduler_uptime_hours: float
    system_health: Dict[str, Any]

class ScheduleUpdateRequest(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ScheduleStatus] = None
    max_runtime_hours: Optional[float] = None
    retry_on_failure: Optional[bool] = None
    max_retries: Optional[int] = None

# Create router
router = APIRouter(prefix="/api/scheduling", tags=["Scheduling Management"])

# Dependency to get scheduler instance
def get_scheduler() -> CronScheduler:
    if scheduler_instance is None:
        raise HTTPException(status_code=503, detail="Scheduler service not available")
    return scheduler_instance

# API Endpoints

@router.get("/", summary="Get Scheduler Status")
async def get_scheduler_status(scheduler: CronScheduler = Depends(get_scheduler)):
    """Get current scheduler status and statistics"""
    try:
        stats = scheduler.get_scheduler_stats()
        return {
            "status": "running" if scheduler.is_running else "stopped",
            "stats": stats,
            "check_interval_seconds": scheduler.check_interval_seconds,
            "max_concurrent_schedules": scheduler.max_concurrent_schedules
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(scheduler: CronScheduler = Depends(get_scheduler)):
    """Get list of all scheduled tasks"""
    try:
        schedules = []
        for schedule_task in scheduler.schedules.values():
            schedule_info = schedule_task.get_schedule_info()
            schedules.append(ScheduleResponse(**schedule_info))
        return schedules
    except Exception as e:
        logger.error(f"Error listing schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules", response_model=Dict[str, str])
async def create_schedule(
    request: ScheduleRequest,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Create a new scheduled task"""
    try:
        schedule_id = scheduler.add_schedule(
            name=request.name,
            cron_expression=request.cron_expression,
            task_function=request.task_function_name,
            task_args=tuple(request.task_args),
            task_kwargs=request.task_kwargs,
            schedule_type=request.schedule_type,
            description=request.description,
            max_runtime_hours=request.max_runtime_hours,
            retry_on_failure=request.retry_on_failure,
            max_retries=request.max_retries
        )
        
        logger.info(f"Created schedule {schedule_id}: {request.name}")
        
        return {
            "schedule_id": schedule_id,
            "message": "Schedule created successfully",
            "name": request.name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/scraping", response_model=Dict[str, str])
async def create_scraping_schedule(
    request: ScrapingScheduleRequest,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Create a new scheduled scraping task"""
    try:
        # Create scraping job configuration
        scraping_config = {
            "sources": request.sources,
            "max_questions_per_source": request.max_questions_per_source,
            "target_categories": request.target_categories,
            "priority_level": request.priority_level.value
        }
        
        schedule_id = scheduler.add_schedule(
            name=request.name,
            cron_expression=request.cron_expression,
            task_function="scheduled_scraping",
            task_kwargs=scraping_config,
            schedule_type=ScheduleType.SCRAPING,
            description=request.description or f"Scheduled scraping from {', '.join(request.sources)}"
        )
        
        logger.info(f"Created scraping schedule {schedule_id}: {request.name}")
        
        return {
            "schedule_id": schedule_id,
            "message": "Scraping schedule created successfully",
            "name": request.name,
            "sources": request.sources
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating scraping schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Get details of a specific scheduled task"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule_task = scheduler.schedules[schedule_id]
        schedule_info = schedule_task.get_schedule_info()
        
        return ScheduleResponse(**schedule_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateRequest,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Update an existing scheduled task"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        updated = scheduler.update_schedule(schedule_id, **request.dict(exclude_unset=True))
        
        if updated:
            logger.info(f"Updated schedule {schedule_id}")
            return {"message": "Schedule updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update schedule")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Delete a scheduled task"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        removed = scheduler.remove_schedule(schedule_id)
        
        if removed:
            logger.info(f"Deleted schedule {schedule_id}")
            return {"message": "Schedule deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete schedule")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(
    schedule_id: str,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Pause a scheduled task"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        paused = scheduler.pause_schedule(schedule_id)
        
        if paused:
            logger.info(f"Paused schedule {schedule_id}")
            return {"message": "Schedule paused successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to pause schedule")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(
    schedule_id: str,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Resume a paused scheduled task"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        resumed = scheduler.resume_schedule(schedule_id)
        
        if resumed:
            logger.info(f"Resumed schedule {schedule_id}")
            return {"message": "Schedule resumed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to resume schedule")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/{schedule_id}/execute")
async def execute_schedule_now(
    schedule_id: str,
    background_tasks: BackgroundTasks,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Execute a scheduled task immediately"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule_task = scheduler.schedules[schedule_id]
        
        # Execute in background
        background_tasks.add_task(scheduler.execute_schedule_now, schedule_id)
        
        logger.info(f"Manual execution triggered for schedule {schedule_id}")
        
        return {
            "message": "Schedule execution triggered",
            "schedule_id": schedule_id,
            "schedule_name": schedule_task.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/{schedule_id}/logs")
async def get_schedule_logs(
    schedule_id: str,
    limit: int = 10,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Get execution logs for a scheduled task"""
    try:
        if schedule_id not in scheduler.schedules:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        logs = scheduler.get_schedule_logs(schedule_id, limit=limit)
        
        return {
            "schedule_id": schedule_id,
            "logs": logs,
            "count": len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs for schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=SchedulerStatsResponse)
async def get_scheduler_stats(scheduler: CronScheduler = Depends(get_scheduler)):
    """Get comprehensive scheduler statistics"""
    try:
        stats = scheduler.get_scheduler_stats()
        system_health = scheduler._assess_system_health() if hasattr(scheduler, '_assess_system_health') else {"status": "unknown"}
        
        return SchedulerStatsResponse(
            **stats,
            system_health=system_health
        )
    except Exception as e:
        logger.error(f"Error getting scheduler stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_scheduler(scheduler: CronScheduler = Depends(get_scheduler)):
    """Start the scheduler"""
    try:
        if scheduler.is_running:
            return {"message": "Scheduler is already running"}
        
        await scheduler.start()
        
        logger.info("Scheduler started via API")
        
        return {"message": "Scheduler started successfully"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_scheduler(
    graceful: bool = True,
    scheduler: CronScheduler = Depends(get_scheduler)
):
    """Stop the scheduler"""
    try:
        if not scheduler.is_running:
            return {"message": "Scheduler is not running"}
        
        await scheduler.stop(graceful=graceful)
        
        logger.info("Scheduler stopped via API")
        
        return {"message": "Scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task-functions")
async def list_task_functions(scheduler: CronScheduler = Depends(get_scheduler)):
    """Get list of available task functions"""
    try:
        return {
            "task_functions": list(scheduler.task_functions.keys()),
            "count": len(scheduler.task_functions)
        }
    except Exception as e:
        logger.error(f"Error listing task functions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets")
async def get_schedule_presets():
    """Get preset schedule configurations"""
    try:
        presets = {
            "daily_scraping": {
                "name": "Daily Scraping",
                "cron_expression": "0 2 * * *",  # Daily at 2 AM
                "description": "Daily scraping of all configured sources",
                "schedule_type": "scraping"
            },
            "weekly_cleanup": {
                "name": "Weekly Cleanup",
                "cron_expression": "0 3 * * 0",  # Sunday at 3 AM
                "description": "Weekly system cleanup and maintenance",
                "schedule_type": "maintenance"
            },
            "hourly_monitoring": {
                "name": "Hourly Health Check",
                "cron_expression": "0 * * * *",  # Every hour
                "description": "Hourly system health monitoring",
                "schedule_type": "monitoring"
            },
            "twice_daily_scraping": {
                "name": "Twice Daily Scraping",
                "cron_expression": "0 6,18 * * *",  # 6 AM and 6 PM
                "description": "Scraping twice daily (morning and evening)",
                "schedule_type": "scraping"
            },
            "monthly_backup": {
                "name": "Monthly Backup",
                "cron_expression": "0 1 1 * *",  # First day of month at 1 AM
                "description": "Monthly data backup",
                "schedule_type": "backup"
            }
        }
        
        return {"presets": presets}
    except Exception as e:
        logger.error(f"Error getting schedule presets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialization functions

async def initialize_scheduling_services():
    """Initialize scheduling services"""
    global scheduler_instance
    
    try:
        logger.info("Initializing scheduling services...")
        
        # Import job manager for integration
        from routers.scraping_management import get_job_manager
        job_manager = get_job_manager()
        
        # Create scheduler instance
        scheduler_instance = CronScheduler(
            check_interval_seconds=30,
            max_concurrent_schedules=5,
            job_manager=job_manager
        )
        
        # Add default schedules
        await _add_default_schedules(scheduler_instance)
        
        # Start the scheduler
        await scheduler_instance.start()
        
        logger.info("✅ Scheduling services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing scheduling services: {str(e)}")
        raise

async def _add_default_schedules(scheduler: CronScheduler):
    """Add default system schedules"""
    try:
        # Daily scraping schedule (2 AM every day)
        scheduler.add_schedule(
            name="Daily System Scraping",
            cron_expression="0 2 * * *",
            task_function="scheduled_scraping",
            task_kwargs={
                "sources": ["indiabix", "geeksforgeeks"],
                "max_questions_per_source": 25,
                "target_categories": ["quantitative", "logical", "verbal"],
                "priority_level": "normal"
            },
            schedule_type=ScheduleType.SCRAPING,
            description="Daily scraping of IndiaBix and GeeksforGeeks"
        )
        
        # Weekly cleanup (Sunday 3 AM)
        scheduler.add_schedule(
            name="Weekly System Cleanup",
            cron_expression="0 3 * * 0",
            task_function="system_cleanup",
            schedule_type=ScheduleType.MAINTENANCE,
            description="Weekly cleanup of old data and logs"
        )
        
        # Hourly health monitoring
        scheduler.add_schedule(
            name="Hourly Health Monitoring",
            cron_expression="0 * * * *",
            task_function="health_monitoring",
            schedule_type=ScheduleType.MONITORING,
            description="Hourly system health checks"
        )
        
        logger.info("Added default system schedules")
        
    except Exception as e:
        logger.warning(f"Error adding default schedules: {str(e)}")

async def shutdown_scheduling_services():
    """Shutdown scheduling services gracefully"""
    global scheduler_instance
    
    try:
        if scheduler_instance and scheduler_instance.is_running:
            logger.info("Stopping scheduling services...")
            await scheduler_instance.stop(graceful=True)
            logger.info("✅ Scheduling services stopped")
        
    except Exception as e:
        logger.error(f"❌ Error stopping scheduling services: {str(e)}")

def get_scheduler_instance() -> Optional[CronScheduler]:
    """Get the global scheduler instance"""
    return scheduler_instance