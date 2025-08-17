"""
Cron-Based Scheduling System
Automated scheduling for regular content updates and maintenance tasks
"""

import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from dataclasses import dataclass, field
import cron_descriptor
from crontab import CronTab
import croniter
import signal
import os
from concurrent.futures import ThreadPoolExecutor
import weakref

from models.scraping_models import (
    ScrapingJob, ScrapingJobConfig, ScrapingJobStatus, 
    CreateScrapingJobRequest, DataSourceConfig
)
from services.job_manager_service import BackgroundJobManager, JobPriority
from utils.background_tasks import BackgroundTaskExecutor, TaskType, TaskConfig

logger = logging.getLogger(__name__)

class ScheduleType(str, Enum):
    """Types of scheduled tasks"""
    SCRAPING = "scraping"
    MAINTENANCE = "maintenance"
    CLEANUP = "cleanup"
    MONITORING = "monitoring"
    BACKUP = "backup"
    ANALYSIS = "analysis"
    CUSTOM = "custom"

class ScheduleStatus(str, Enum):
    """Schedule status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"

class TriggerType(str, Enum):
    """Schedule trigger types"""
    CRON = "cron"
    INTERVAL = "interval" 
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class ScheduleExecutionLog:
    """Log entry for schedule execution"""
    execution_id: str
    schedule_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    
@dataclass 
class ScheduleMetrics:
    """Metrics for scheduled task performance"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time: float = 0.0
    last_execution_time: Optional[datetime] = None
    next_execution_time: Optional[datetime] = None
    success_rate: float = 0.0
    
class ScheduledTask:
    """Represents a scheduled task"""
    
    def __init__(self, 
                 schedule_id: str,
                 name: str,
                 cron_expression: str,
                 task_function: Callable,
                 task_args: tuple = (),
                 task_kwargs: Dict[str, Any] = None,
                 schedule_type: ScheduleType = ScheduleType.CUSTOM,
                 description: Optional[str] = None,
                 timezone: str = "UTC",
                 max_runtime_hours: int = 24,
                 retry_on_failure: bool = True,
                 max_retries: int = 3):
        
        self.schedule_id = schedule_id
        self.name = name
        self.cron_expression = cron_expression
        self.task_function = task_function
        self.task_args = task_args
        self.task_kwargs = task_kwargs or {}
        self.schedule_type = schedule_type
        self.description = description or f"Scheduled {schedule_type.value} task"
        self.timezone = timezone
        self.max_runtime_hours = max_runtime_hours
        self.retry_on_failure = retry_on_failure
        self.max_retries = max_retries
        
        # Schedule state
        self.status = ScheduleStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.last_modified = datetime.utcnow()
        
        # Execution tracking
        self.execution_logs: List[ScheduleExecutionLog] = []
        self.metrics = ScheduleMetrics()
        
        # Cron iterator for next execution time
        try:
            self.cron_iter = croniter.croniter(cron_expression, datetime.utcnow())
            self.metrics.next_execution_time = self.cron_iter.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression '{cron_expression}': {str(e)}")
            self.status = ScheduleStatus.ERROR
            raise
        
        # Runtime tracking
        self.current_execution_id: Optional[str] = None
        self.is_running = False
        
    def get_next_execution_time(self) -> datetime:
        """Get the next scheduled execution time"""
        try:
            if self.status != ScheduleStatus.ACTIVE:
                return None
            
            # Create a new iterator from current time
            now = datetime.utcnow()
            cron_iter = croniter.croniter(self.cron_expression, now)
            next_time = cron_iter.get_next(datetime)
            
            self.metrics.next_execution_time = next_time
            return next_time
            
        except Exception as e:
            logger.error(f"Error calculating next execution time for schedule {self.schedule_id}: {str(e)}")
            return None
    
    def get_cron_description(self) -> str:
        """Get human-readable description of cron expression"""
        try:
            return cron_descriptor.get_description(self.cron_expression)
        except Exception as e:
            logger.warning(f"Could not get cron description: {str(e)}")
            return f"Custom schedule: {self.cron_expression}"
    
    def should_execute_now(self, current_time: Optional[datetime] = None) -> bool:
        """Check if task should execute now"""
        if self.status != ScheduleStatus.ACTIVE or self.is_running:
            return False
        
        current_time = current_time or datetime.utcnow()
        
        # Check if it's time to execute based on cron schedule
        try:
            cron_iter = croniter.croniter(self.cron_expression, current_time - timedelta(minutes=1))
            next_time = cron_iter.get_next(datetime)
            
            # If next scheduled time is within the last minute, it's time to execute
            return abs((next_time - current_time).total_seconds()) <= 60
            
        except Exception as e:
            logger.error(f"Error checking execution time for schedule {self.schedule_id}: {str(e)}")
            return False
    
    async def execute(self) -> ScheduleExecutionLog:
        """Execute the scheduled task"""
        execution_id = str(uuid.uuid4())
        self.current_execution_id = execution_id
        self.is_running = True
        
        start_time = datetime.utcnow()
        
        log_entry = ScheduleExecutionLog(
            execution_id=execution_id,
            schedule_id=self.schedule_id,
            started_at=start_time
        )
        
        try:
            logger.info(f"Executing scheduled task {self.schedule_id} ({self.name})")
            
            # Execute the task function
            if asyncio.iscoroutinefunction(self.task_function):
                result = await self.task_function(*self.task_args, **self.task_kwargs)
            else:
                result = self.task_function(*self.task_args, **self.task_kwargs)
            
            # Task completed successfully
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            log_entry.completed_at = end_time
            log_entry.success = True
            log_entry.result_data = result if isinstance(result, dict) else {"result": str(result)}
            log_entry.execution_time_seconds = execution_time
            
            # Update metrics
            self.metrics.total_executions += 1
            self.metrics.successful_executions += 1
            self.metrics.last_execution_time = end_time
            self._update_execution_metrics(execution_time)
            
            logger.info(f"Scheduled task {self.schedule_id} completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            error_message = str(e)
            
            log_entry.completed_at = end_time
            log_entry.success = False
            log_entry.error_message = error_message
            log_entry.execution_time_seconds = execution_time
            
            # Update metrics
            self.metrics.total_executions += 1
            self.metrics.failed_executions += 1
            self.metrics.last_execution_time = end_time
            self._update_execution_metrics(execution_time)
            
            logger.error(f"Scheduled task {self.schedule_id} failed: {error_message}")
            
        finally:
            # Add to execution log
            self.execution_logs.append(log_entry)
            
            # Keep only last 100 logs
            if len(self.execution_logs) > 100:
                self.execution_logs.pop(0)
            
            # Update next execution time
            self.get_next_execution_time()
            
            # Reset running state
            self.is_running = False
            self.current_execution_id = None
        
        return log_entry
    
    def _update_execution_metrics(self, execution_time: float):
        """Update execution metrics"""
        total_time = (self.metrics.avg_execution_time * (self.metrics.total_executions - 1)) + execution_time
        self.metrics.avg_execution_time = total_time / self.metrics.total_executions
        
        if self.metrics.total_executions > 0:
            self.metrics.success_rate = (self.metrics.successful_executions / self.metrics.total_executions) * 100
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """Get comprehensive schedule information"""
        return {
            "schedule_id": self.schedule_id,
            "name": self.name,
            "description": self.description,
            "schedule_type": self.schedule_type.value,
            "status": self.status.value,
            "cron_expression": self.cron_expression,
            "cron_description": self.get_cron_description(),
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "is_running": self.is_running,
            "current_execution_id": self.current_execution_id,
            "next_execution_time": self.metrics.next_execution_time.isoformat() if self.metrics.next_execution_time else None,
            "last_execution_time": self.metrics.last_execution_time.isoformat() if self.metrics.last_execution_time else None,
            "metrics": {
                "total_executions": self.metrics.total_executions,
                "successful_executions": self.metrics.successful_executions,
                "failed_executions": self.metrics.failed_executions,
                "success_rate": self.metrics.success_rate,
                "avg_execution_time": self.metrics.avg_execution_time
            },
            "configuration": {
                "max_runtime_hours": self.max_runtime_hours,
                "retry_on_failure": self.retry_on_failure,
                "max_retries": self.max_retries
            }
        }

class CronScheduler:
    """
    Comprehensive Cron-Based Scheduling System
    
    Features:
    1. Cron job configuration and management
    2. Scheduled scraping workflows
    3. Maintenance and cleanup tasks
    4. Schedule optimization based on source patterns
    5. Execution monitoring and error handling
    """
    
    def __init__(self, 
                 check_interval_seconds: int = 30,
                 max_concurrent_schedules: int = 10,
                 job_manager: Optional[BackgroundJobManager] = None):
        """
        Initialize Cron Scheduler
        
        Args:
            check_interval_seconds: How often to check for due schedules
            max_concurrent_schedules: Maximum concurrent schedule executions
            job_manager: Background job manager for heavy tasks
        """
        try:
            self.check_interval_seconds = check_interval_seconds
            self.max_concurrent_schedules = max_concurrent_schedules
            self.job_manager = job_manager
            
            # Schedule registry
            self.schedules: Dict[str, ScheduledTask] = {}
            self.active_executions: Dict[str, ScheduledTask] = {}
            
            # Built-in task functions registry
            self.task_functions: Dict[str, Callable] = {}
            
            # Scheduler control
            self.is_running = False
            self.scheduler_task: Optional[asyncio.Task] = None
            
            # Statistics
            self.stats = {
                "total_schedules": 0,
                "active_schedules": 0,
                "paused_schedules": 0,
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_execution_time": 0.0,
                "scheduler_uptime_hours": 0.0
            }
            
            # System schedules
            self._register_system_schedules()
            
            logger.info("CronScheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing CronScheduler: {str(e)}")
            raise
    
    async def start(self):
        """Start the cron scheduler"""
        if self.is_running:
            logger.warning("Cron scheduler is already running")
            return
        
        try:
            self.is_running = True
            
            logger.info("Starting Cron Scheduler")
            
            # Start scheduler loop
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            # Register signal handlers for graceful shutdown
            self._register_signal_handlers()
            
            logger.info("Cron Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting cron scheduler: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self, graceful: bool = True):
        """Stop the cron scheduler"""
        if not self.is_running:
            logger.warning("Cron scheduler is not running")
            return
        
        try:
            logger.info("Stopping Cron Scheduler")
            
            self.is_running = False
            
            # Cancel scheduler task
            if self.scheduler_task and not self.scheduler_task.done():
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass
            
            if graceful:
                # Wait for active executions to complete
                await self._wait_for_active_executions()
            else:
                # Cancel active executions
                await self._cancel_active_executions()
            
            logger.info("Cron Scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping cron scheduler: {str(e)}")
    
    def add_schedule(self, 
                    name: str,
                    cron_expression: str,
                    task_function: Union[Callable, str],
                    task_args: tuple = (),
                    task_kwargs: Dict[str, Any] = None,
                    schedule_type: ScheduleType = ScheduleType.CUSTOM,
                    description: Optional[str] = None,
                    schedule_id: Optional[str] = None,
                    **config_kwargs) -> str:
        """
        Add a new schedule
        
        Args:
            name: Schedule name
            cron_expression: Cron expression (e.g., "0 */6 * * *" for every 6 hours)
            task_function: Function to execute or function name from registry
            task_args: Arguments for the task function
            task_kwargs: Keyword arguments for the task function
            schedule_type: Type of scheduled task
            description: Description of the schedule
            schedule_id: Optional custom schedule ID
            **config_kwargs: Additional configuration options
            
        Returns:
            Schedule ID
        """
        try:
            if not schedule_id:
                schedule_id = str(uuid.uuid4())
            
            if schedule_id in self.schedules:
                raise ValueError(f"Schedule with ID {schedule_id} already exists")
            
            # Resolve task function
            if isinstance(task_function, str):
                if task_function not in self.task_functions:
                    raise ValueError(f"Task function '{task_function}' not found in registry")
                task_function = self.task_functions[task_function]
            
            # Create scheduled task
            scheduled_task = ScheduledTask(
                schedule_id=schedule_id,
                name=name,
                cron_expression=cron_expression,
                task_function=task_function,
                task_args=task_args,
                task_kwargs=task_kwargs or {},
                schedule_type=schedule_type,
                description=description,
                **config_kwargs
            )
            
            self.schedules[schedule_id] = scheduled_task
            
            # Update statistics
            self._update_schedule_stats()
            
            logger.info(f"Added schedule '{name}' (ID: {schedule_id}) with expression '{cron_expression}'")
            
            return schedule_id
            
        except Exception as e:
            logger.error(f"Error adding schedule: {str(e)}")
            raise
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule"""
        try:
            if schedule_id not in self.schedules:
                logger.warning(f"Schedule {schedule_id} not found")
                return False
            
            # Check if schedule is currently running
            if schedule_id in self.active_executions:
                logger.warning(f"Cannot remove schedule {schedule_id} - currently executing")
                return False
            
            # Remove schedule
            schedule = self.schedules.pop(schedule_id)
            
            # Update statistics
            self._update_schedule_stats()
            
            logger.info(f"Removed schedule '{schedule.name}' (ID: {schedule_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing schedule {schedule_id}: {str(e)}")
            return False
    
    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule"""
        try:
            if schedule_id not in self.schedules:
                logger.warning(f"Schedule {schedule_id} not found")
                return False
            
            schedule = self.schedules[schedule_id]
            schedule.status = ScheduleStatus.PAUSED
            schedule.last_modified = datetime.utcnow()
            
            self._update_schedule_stats()
            
            logger.info(f"Paused schedule '{schedule.name}' (ID: {schedule_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error pausing schedule {schedule_id}: {str(e)}")
            return False
    
    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule"""
        try:
            if schedule_id not in self.schedules:
                logger.warning(f"Schedule {schedule_id} not found")
                return False
            
            schedule = self.schedules[schedule_id]
            schedule.status = ScheduleStatus.ACTIVE
            schedule.last_modified = datetime.utcnow()
            
            # Update next execution time
            schedule.get_next_execution_time()
            
            self._update_schedule_stats()
            
            logger.info(f"Resumed schedule '{schedule.name}' (ID: {schedule_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error resuming schedule {schedule_id}: {str(e)}")
            return False
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule information"""
        try:
            if schedule_id not in self.schedules:
                return None
            
            return self.schedules[schedule_id].get_schedule_info()
            
        except Exception as e:
            logger.error(f"Error getting schedule {schedule_id}: {str(e)}")
            return None
    
    def list_schedules(self, 
                      status_filter: Optional[ScheduleStatus] = None,
                      schedule_type_filter: Optional[ScheduleType] = None) -> List[Dict[str, Any]]:
        """List all schedules with optional filtering"""
        try:
            schedules = []
            
            for schedule in self.schedules.values():
                # Apply filters
                if status_filter and schedule.status != status_filter:
                    continue
                if schedule_type_filter and schedule.schedule_type != schedule_type_filter:
                    continue
                
                schedules.append(schedule.get_schedule_info())
            
            # Sort by next execution time
            schedules.sort(key=lambda s: s.get("next_execution_time") or "9999-12-31T23:59:59")
            
            return schedules
            
        except Exception as e:
            logger.error(f"Error listing schedules: {str(e)}")
            return []
    
    def get_execution_logs(self, 
                          schedule_id: str, 
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution logs for a schedule"""
        try:
            if schedule_id not in self.schedules:
                return []
            
            schedule = self.schedules[schedule_id]
            logs = schedule.execution_logs[-limit:] if limit > 0 else schedule.execution_logs
            
            return [
                {
                    "execution_id": log.execution_id,
                    "started_at": log.started_at.isoformat(),
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "success": log.success,
                    "execution_time_seconds": log.execution_time_seconds,
                    "error_message": log.error_message,
                    "result_data": log.result_data
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error getting execution logs for {schedule_id}: {str(e)}")
            return []
    
    def register_task_function(self, name: str, function: Callable):
        """Register a task function that can be used in schedules"""
        self.task_functions[name] = function
        logger.info(f"Registered task function: {name}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get comprehensive scheduler status"""
        try:
            # Calculate uptime
            uptime_hours = self.stats.get("scheduler_uptime_hours", 0.0)
            
            # Get upcoming executions
            upcoming_executions = []
            for schedule in self.schedules.values():
                if schedule.status == ScheduleStatus.ACTIVE and schedule.metrics.next_execution_time:
                    upcoming_executions.append({
                        "schedule_id": schedule.schedule_id,
                        "name": schedule.name,
                        "next_execution_time": schedule.metrics.next_execution_time.isoformat(),
                        "cron_expression": schedule.cron_expression
                    })
            
            # Sort by next execution time
            upcoming_executions.sort(key=lambda x: x["next_execution_time"])
            
            status = {
                "is_running": self.is_running,
                "check_interval_seconds": self.check_interval_seconds,
                "max_concurrent_schedules": self.max_concurrent_schedules,
                "statistics": self.stats.copy(),
                "active_executions": len(self.active_executions),
                "upcoming_executions": upcoming_executions[:10],  # Next 10
                "schedule_distribution": self._get_schedule_distribution(),
                "system_health": self._assess_system_health()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {"error": str(e)}
    
    # Built-in Schedule Functions
    
    async def _system_cleanup_task(self) -> Dict[str, Any]:
        """Built-in system cleanup task"""
        logger.info("Running system cleanup task")
        
        cleanup_results = {
            "logs_cleaned": 0,
            "temp_files_removed": 0,
            "old_executions_purged": 0
        }
        
        # Clean up old execution logs (keep last 100 per schedule)
        for schedule in self.schedules.values():
            if len(schedule.execution_logs) > 100:
                removed = len(schedule.execution_logs) - 100
                schedule.execution_logs = schedule.execution_logs[-100:]
                cleanup_results["old_executions_purged"] += removed
        
        logger.info(f"System cleanup completed: {cleanup_results}")
        return cleanup_results
    
    async def _scheduled_scraping_task(self, 
                                     source_configs: List[Dict[str, Any]],
                                     job_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Built-in scheduled scraping task"""
        logger.info(f"Running scheduled scraping for {len(source_configs)} sources")
        
        if not self.job_manager:
            raise Exception("Job manager not available for scheduled scraping")
        
        # Create scraping job
        job_config = job_config or {}
        scraping_job_config = ScrapingJobConfig(
            job_name=f"Scheduled Scraping - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            description="Automated scheduled scraping job",
            source_ids=[config.get("source_id") for config in source_configs],
            **job_config
        )
        
        scraping_job = ScrapingJob(
            config=scraping_job_config,
            status=ScrapingJobStatus.PENDING
        )
        
        # Submit to job manager
        job_id = await self.job_manager.submit_job(
            scraping_job, 
            self._execute_scraping_workflow,
            JobPriority.NORMAL
        )
        
        return {
            "job_id": job_id,
            "sources_count": len(source_configs),
            "submitted_at": datetime.utcnow().isoformat()
        }
    
    async def _execute_scraping_workflow(self, job: ScrapingJob) -> Dict[str, Any]:
        """Execute scraping workflow for scheduled jobs"""
        # This would integrate with the scraping engine
        # For now, return a placeholder result
        
        logger.info(f"Executing scraping workflow for job {job.id}")
        
        # Simulate scraping work
        await asyncio.sleep(5.0)
        
        return {
            "job_id": job.id,
            "questions_scraped": 25,  # Placeholder
            "sources_processed": len(job.config.source_ids),
            "execution_time": 5.0,
            "success": True
        }
    
    async def _health_monitoring_task(self) -> Dict[str, Any]:
        """Built-in health monitoring task"""
        logger.info("Running health monitoring task")
        
        # Check scheduler health
        health_data = {
            "scheduler_status": "healthy",
            "active_schedules": len([s for s in self.schedules.values() if s.status == ScheduleStatus.ACTIVE]),
            "failed_schedules": len([s for s in self.schedules.values() if s.status == ScheduleStatus.ERROR]),
            "long_running_executions": [],
            "system_resources": {}
        }
        
        # Check for long-running executions
        now = datetime.utcnow()
        for schedule in self.active_executions.values():
            if schedule.current_execution_id:
                # Find the current execution log
                current_log = None
                for log in schedule.execution_logs:
                    if log.execution_id == schedule.current_execution_id and not log.completed_at:
                        current_log = log
                        break
                
                if current_log:
                    runtime_hours = (now - current_log.started_at).total_seconds() / 3600
                    if runtime_hours > schedule.max_runtime_hours:
                        health_data["long_running_executions"].append({
                            "schedule_id": schedule.schedule_id,
                            "name": schedule.name,
                            "runtime_hours": runtime_hours,
                            "max_runtime_hours": schedule.max_runtime_hours
                        })
        
        # Assess overall health
        if health_data["failed_schedules"] > 0 or health_data["long_running_executions"]:
            health_data["scheduler_status"] = "warning"
        
        logger.info(f"Health monitoring completed: {health_data['scheduler_status']}")
        return health_data
    
    # Internal Methods
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Starting scheduler loop")
        
        start_time = datetime.utcnow()
        
        while self.is_running:
            try:
                # Update uptime
                self.stats["scheduler_uptime_hours"] = (datetime.utcnow() - start_time).total_seconds() / 3600
                
                # Check for schedules that need to execute
                await self._check_and_execute_schedules()
                
                # Clean up completed executions
                await self._cleanup_completed_executions()
                
                # Update statistics
                self._update_schedule_stats()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(self.check_interval_seconds)
        
        logger.info("Scheduler loop stopped")
    
    async def _check_and_execute_schedules(self):
        """Check and execute due schedules"""
        current_time = datetime.utcnow()
        
        for schedule_id, schedule in self.schedules.items():
            try:
                # Skip if not active or already running
                if schedule.status != ScheduleStatus.ACTIVE or schedule.is_running:
                    continue
                
                # Check if schedule should execute
                if schedule.should_execute_now(current_time):
                    # Check concurrent execution limit
                    if len(self.active_executions) >= self.max_concurrent_schedules:
                        logger.warning(f"Max concurrent schedules reached. Skipping {schedule_id}")
                        continue
                    
                    # Execute schedule
                    await self._execute_schedule(schedule)
                    
            except Exception as e:
                logger.error(f"Error checking schedule {schedule_id}: {str(e)}")
                schedule.status = ScheduleStatus.ERROR
    
    async def _execute_schedule(self, schedule: ScheduledTask):
        """Execute a scheduled task"""
        try:
            logger.info(f"Executing schedule {schedule.schedule_id} ({schedule.name})")
            
            # Add to active executions
            self.active_executions[schedule.schedule_id] = schedule
            
            # Execute in background task
            asyncio.create_task(self._execute_schedule_with_tracking(schedule))
            
        except Exception as e:
            logger.error(f"Error starting execution of schedule {schedule.schedule_id}: {str(e)}")
            # Remove from active executions if it was added
            if schedule.schedule_id in self.active_executions:
                del self.active_executions[schedule.schedule_id]
    
    async def _execute_schedule_with_tracking(self, schedule: ScheduledTask):
        """Execute schedule with full tracking and error handling"""
        try:
            # Execute the schedule
            execution_log = await schedule.execute()
            
            # Update global statistics
            self.stats["total_executions"] += 1
            
            if execution_log.success:
                self.stats["successful_executions"] += 1
            else:
                self.stats["failed_executions"] += 1
            
            # Update average execution time
            if self.stats["total_executions"] > 0:
                total_time = (self.stats["avg_execution_time"] * (self.stats["total_executions"] - 1)) + execution_log.execution_time_seconds
                self.stats["avg_execution_time"] = total_time / self.stats["total_executions"]
            
        except Exception as e:
            logger.error(f"Error executing schedule {schedule.schedule_id}: {str(e)}")
            
            # Update failure statistics
            self.stats["total_executions"] += 1
            self.stats["failed_executions"] += 1
            
        finally:
            # Remove from active executions
            if schedule.schedule_id in self.active_executions:
                del self.active_executions[schedule.schedule_id]
    
    async def _cleanup_completed_executions(self):
        """Clean up completed executions from tracking"""
        # This is handled in _execute_schedule_with_tracking
        # Additional cleanup logic can be added here if needed
        pass
    
    def _register_system_schedules(self):
        """Register built-in system schedules"""
        
        # Register system task functions
        self.task_functions["system_cleanup"] = self._system_cleanup_task
        self.task_functions["scheduled_scraping"] = self._scheduled_scraping_task
        self.task_functions["health_monitoring"] = self._health_monitoring_task
        
        logger.info("Registered system task functions")
    
    def _update_schedule_stats(self):
        """Update schedule statistics"""
        self.stats["total_schedules"] = len(self.schedules)
        self.stats["active_schedules"] = len([s for s in self.schedules.values() if s.status == ScheduleStatus.ACTIVE])
        self.stats["paused_schedules"] = len([s for s in self.schedules.values() if s.status == ScheduleStatus.PAUSED])
    
    def _get_schedule_distribution(self) -> Dict[str, int]:
        """Get distribution of schedules by type"""
        distribution = {}
        
        for schedule in self.schedules.values():
            schedule_type = schedule.schedule_type.value
            distribution[schedule_type] = distribution.get(schedule_type, 0) + 1
        
        return distribution
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        health = {
            "status": "healthy",
            "issues": []
        }
        
        # Check for failed schedules
        failed_count = len([s for s in self.schedules.values() if s.status == ScheduleStatus.ERROR])
        if failed_count > 0:
            health["issues"].append(f"{failed_count} schedules in error state")
            health["status"] = "warning"
        
        # Check for high failure rate
        if self.stats["total_executions"] > 0:
            failure_rate = (self.stats["failed_executions"] / self.stats["total_executions"]) * 100
            if failure_rate > 20:
                health["issues"].append(f"High failure rate: {failure_rate:.1f}%")
                health["status"] = "warning"
            if failure_rate > 50:
                health["status"] = "critical"
        
        # Check concurrent execution capacity
        if len(self.active_executions) >= self.max_concurrent_schedules:
            health["issues"].append("Maximum concurrent executions reached")
            health["status"] = "warning"
        
        if not health["issues"]:
            health["issues"].append("All systems operating normally")
        
        return health
    
    async def _wait_for_active_executions(self):
        """Wait for active executions to complete"""
        timeout_seconds = 300  # 5 minutes timeout
        start_time = datetime.utcnow()
        
        while self.active_executions and (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
            logger.info(f"Waiting for {len(self.active_executions)} active executions to complete...")
            await asyncio.sleep(2.0)
        
        if self.active_executions:
            logger.warning(f"Timeout reached. {len(self.active_executions)} executions still active")
    
    async def _cancel_active_executions(self):
        """Cancel all active executions"""
        logger.info(f"Cancelling {len(self.active_executions)} active executions")
        
        for schedule_id, schedule in self.active_executions.items():
            schedule.is_running = False
            logger.info(f"Cancelled execution of schedule {schedule_id}")
        
        self.active_executions.clear()
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # Signal handlers not available in all environments
            logger.info("Signal handlers not available in this environment")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        asyncio.create_task(self.stop(graceful=True))


# =============================================================================
# UTILITY FUNCTIONS FOR COMMON SCHEDULE PATTERNS
# =============================================================================

def create_daily_schedule(name: str, 
                         hour: int, 
                         minute: int = 0,
                         task_function: Callable = None,
                         **kwargs) -> str:
    """Create a daily schedule at specified time"""
    cron_expression = f"{minute} {hour} * * *"
    
    return {
        "name": name,
        "cron_expression": cron_expression,
        "task_function": task_function,
        "schedule_type": ScheduleType.CUSTOM,
        **kwargs
    }

def create_hourly_schedule(name: str,
                          minute: int = 0,
                          task_function: Callable = None,
                          **kwargs) -> str:
    """Create an hourly schedule at specified minute"""
    cron_expression = f"{minute} * * * *"
    
    return {
        "name": name,
        "cron_expression": cron_expression,
        "task_function": task_function,
        "schedule_type": ScheduleType.CUSTOM,
        **kwargs
    }

def create_weekly_schedule(name: str,
                          day_of_week: int,  # 0=Sunday, 1=Monday, etc.
                          hour: int,
                          minute: int = 0,
                          task_function: Callable = None,
                          **kwargs) -> str:
    """Create a weekly schedule"""
    cron_expression = f"{minute} {hour} * * {day_of_week}"
    
    return {
        "name": name,
        "cron_expression": cron_expression,
        "task_function": task_function,
        "schedule_type": ScheduleType.CUSTOM,
        **kwargs
    }

def create_scraping_schedule(name: str,
                           cron_expression: str,
                           source_configs: List[Dict[str, Any]],
                           job_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a scraping schedule"""
    
    return {
        "name": name,
        "cron_expression": cron_expression,
        "task_function": "scheduled_scraping",
        "task_kwargs": {
            "source_configs": source_configs,
            "job_config": job_config or {}
        },
        "schedule_type": ScheduleType.SCRAPING,
        "description": f"Scheduled scraping for {len(source_configs)} sources"
    }

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_cron_scheduler(check_interval_seconds: int = 30,
                         max_concurrent_schedules: int = 10,
                         job_manager: Optional[BackgroundJobManager] = None) -> CronScheduler:
    """Factory function to create cron scheduler"""
    return CronScheduler(
        check_interval_seconds=check_interval_seconds,
        max_concurrent_schedules=max_concurrent_schedules,
        job_manager=job_manager
    )

async def add_system_maintenance_schedules(scheduler: CronScheduler):
    """Add common system maintenance schedules"""
    
    # Daily cleanup at 2 AM
    scheduler.add_schedule(
        name="Daily System Cleanup",
        cron_expression="0 2 * * *",
        task_function="system_cleanup",
        schedule_type=ScheduleType.CLEANUP,
        description="Daily system cleanup and maintenance"
    )
    
    # Health monitoring every 30 minutes
    scheduler.add_schedule(
        name="Health Monitoring",
        cron_expression="*/30 * * * *",
        task_function="health_monitoring",
        schedule_type=ScheduleType.MONITORING,
        description="Regular health monitoring checks"
    )
    
    logger.info("Added system maintenance schedules")