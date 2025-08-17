"""
Background Job Management System
Asynchronous scraping job execution with monitoring, error handling, and resource management
"""

import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from dataclasses import dataclass, asdict
import queue
import signal
import psutil
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import weakref

from models.scraping_models import (
    ScrapingJob, ScrapingJobStatus, ScrapingJobConfig, 
    CreateScrapingJobRequest, ScrapingJobResponse, ScrapingJobStatusResponse
)

logger = logging.getLogger(__name__)

class JobPriority(str, Enum):
    """Job priority levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    NORMAL = "normal"
    LOW = "low"

class ResourceType(str, Enum):
    """System resource types to monitor"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"

class JobExecutionMode(str, Enum):
    """Job execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"

@dataclass
class ResourceLimits:
    """Resource usage limits for jobs"""
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 2048
    max_concurrent_jobs: int = 5
    max_job_duration_hours: int = 12
    max_queue_size: int = 100

@dataclass
class JobExecutionContext:
    """Context information for job execution"""
    job_id: str
    executor_id: str
    start_time: datetime
    resource_snapshot: Dict[str, Any]
    execution_metadata: Dict[str, Any]
    
@dataclass
class JobResult:
    """Result of job execution"""
    job_id: str
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    resource_usage: Dict[str, Any] = None
    
class JobExecutor:
    """Individual job executor with resource monitoring"""
    
    def __init__(self, executor_id: str, resource_limits: ResourceLimits):
        self.executor_id = executor_id
        self.resource_limits = resource_limits
        self.current_job: Optional[ScrapingJob] = None
        self.execution_context: Optional[JobExecutionContext] = None
        self.is_running = False
        self.process = psutil.Process()
        
    async def execute_job(self, job: ScrapingJob, job_function: Callable) -> JobResult:
        """Execute a job with resource monitoring"""
        
        start_time = datetime.utcnow()
        self.current_job = job
        self.is_running = True
        
        try:
            logger.info(f"Executor {self.executor_id} starting job {job.id}")
            
            # Create execution context
            self.execution_context = JobExecutionContext(
                job_id=job.id,
                executor_id=self.executor_id,
                start_time=start_time,
                resource_snapshot=self._get_resource_snapshot(),
                execution_metadata={"job_config": asdict(job.config)}
            )
            
            # Pre-execution resource check
            if not self._check_resource_availability():
                raise Exception("Insufficient resources to execute job")
            
            # Update job status
            job.status = ScrapingJobStatus.RUNNING
            job.started_at = start_time
            job.current_phase = "executing"
            
            # Execute the job function
            result_data = None
            if asyncio.iscoroutinefunction(job_function):
                result_data = await job_function(job)
            else:
                result_data = await asyncio.to_thread(job_function, job)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get final resource usage
            resource_usage = self._get_resource_usage_summary()
            
            logger.info(f"Job {job.id} completed successfully in {execution_time:.2f}s")
            
            return JobResult(
                job_id=job.id,
                success=True,
                result_data=result_data,
                execution_time_seconds=execution_time,
                resource_usage=resource_usage
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_message = f"Job execution failed: {str(e)}"
            
            logger.error(f"Job {job.id} failed: {error_message}")
            logger.error(traceback.format_exc())
            
            return JobResult(
                job_id=job.id,
                success=False,
                error_message=error_message,
                execution_time_seconds=execution_time,
                resource_usage=self._get_resource_usage_summary()
            )
            
        finally:
            self.is_running = False
            self.current_job = None
            self.execution_context = None
    
    def _check_resource_availability(self) -> bool:
        """Check if sufficient resources are available"""
        try:
            # CPU check
            cpu_percent = self.process.cpu_percent(interval=0.1)
            if cpu_percent > self.resource_limits.max_cpu_percent:
                logger.warning(f"CPU usage ({cpu_percent:.1f}%) exceeds limit ({self.resource_limits.max_cpu_percent}%)")
                return False
            
            # Memory check
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            if memory_mb > self.resource_limits.max_memory_mb:
                logger.warning(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.resource_limits.max_memory_mb}MB)")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Resource check failed: {str(e)}")
            return True  # Allow execution if check fails
    
    def _get_resource_snapshot(self) -> Dict[str, Any]:
        """Get current resource usage snapshot"""
        try:
            memory_info = self.process.memory_info()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": self.process.cpu_percent(interval=0.1),
                "memory_mb": memory_info.rss / (1024 * 1024),
                "memory_percent": self.process.memory_percent(),
                "num_threads": self.process.num_threads(),
                "open_files": len(self.process.open_files()) if hasattr(self.process, 'open_files') else 0
            }
        except Exception as e:
            logger.warning(f"Failed to get resource snapshot: {str(e)}")
            return {"error": str(e)}
    
    def _get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get resource usage summary for completed job"""
        try:
            current_snapshot = self._get_resource_snapshot()
            
            if self.execution_context and self.execution_context.resource_snapshot:
                initial_snapshot = self.execution_context.resource_snapshot
                
                return {
                    "initial": initial_snapshot,
                    "final": current_snapshot,
                    "peak_memory_mb": max(
                        initial_snapshot.get("memory_mb", 0),
                        current_snapshot.get("memory_mb", 0)
                    ),
                    "avg_cpu_percent": (
                        initial_snapshot.get("cpu_percent", 0) +
                        current_snapshot.get("cpu_percent", 0)
                    ) / 2
                }
            
            return current_snapshot
            
        except Exception as e:
            logger.warning(f"Failed to get resource usage summary: {str(e)}")
            return {"error": str(e)}
    
    def get_executor_status(self) -> Dict[str, Any]:
        """Get current executor status"""
        return {
            "executor_id": self.executor_id,
            "is_running": self.is_running,
            "current_job_id": self.current_job.id if self.current_job else None,
            "resource_limits": asdict(self.resource_limits),
            "current_resources": self._get_resource_snapshot()
        }

class BackgroundJobManager:
    """
    Comprehensive Background Job Management System
    
    Features:
    1. Asynchronous job execution with monitoring
    2. Resource management and limiting
    3. Job prioritization and queuing
    4. Error handling and recovery
    5. Performance monitoring and statistics
    6. Graceful shutdown handling
    """
    
    def __init__(self, 
                 max_concurrent_jobs: int = 5,
                 resource_limits: Optional[ResourceLimits] = None,
                 execution_mode: JobExecutionMode = JobExecutionMode.ADAPTIVE):
        """
        Initialize Background Job Manager
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent jobs
            resource_limits: Resource usage limits
            execution_mode: Job execution mode
        """
        try:
            self.max_concurrent_jobs = max_concurrent_jobs
            self.resource_limits = resource_limits or ResourceLimits()
            self.execution_mode = execution_mode
            
            # Job management
            self.job_queue = asyncio.Queue(maxsize=self.resource_limits.max_queue_size)
            self.priority_queues = {
                JobPriority.CRITICAL: asyncio.Queue(),
                JobPriority.HIGH: asyncio.Queue(),
                JobPriority.NORMAL: asyncio.Queue(),
                JobPriority.LOW: asyncio.Queue()
            }
            
            # Job tracking
            self.active_jobs: Dict[str, ScrapingJob] = {}
            self.completed_jobs: Dict[str, JobResult] = {}
            self.failed_jobs: Dict[str, JobResult] = {}
            self.job_history: List[Dict[str, Any]] = []
            
            # Executors
            self.executors: List[JobExecutor] = []
            self.executor_pool = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
            
            # Statistics and monitoring
            self.stats = {
                "total_jobs_processed": 0,
                "successful_jobs": 0,
                "failed_jobs": 0,
                "avg_execution_time": 0.0,
                "total_execution_time": 0.0,
                "queue_length": 0,
                "active_jobs_count": 0,
                "resource_usage_history": []
            }
            
            # Job functions registry
            self.job_functions: Dict[str, Callable] = {}
            
            # Control flags
            self.is_running = False
            self.shutdown_requested = False
            
            # Initialize executors
            for i in range(max_concurrent_jobs):
                executor = JobExecutor(f"executor_{i}", self.resource_limits)
                self.executors.append(executor)
            
            logger.info(f"BackgroundJobManager initialized with {max_concurrent_jobs} executors")
            
        except Exception as e:
            logger.error(f"Error initializing BackgroundJobManager: {str(e)}")
            raise
    
    async def start(self):
        """Start the job manager"""
        if self.is_running:
            logger.warning("Job manager is already running")
            return
        
        try:
            self.is_running = True
            self.shutdown_requested = False
            
            logger.info("Starting Background Job Manager")
            
            # Start job processing task
            asyncio.create_task(self._job_processing_loop())
            
            # Start monitoring task  
            asyncio.create_task(self._monitoring_loop())
            
            # Register shutdown handlers
            self._register_shutdown_handlers()
            
            logger.info("Background Job Manager started successfully")
            
        except Exception as e:
            logger.error(f"Error starting job manager: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self, graceful: bool = True, timeout: int = 30):
        """Stop the job manager"""
        if not self.is_running:
            logger.warning("Job manager is not running")
            return
        
        try:
            logger.info(f"Stopping Background Job Manager (graceful={graceful})")
            
            self.shutdown_requested = True
            
            if graceful:
                # Wait for active jobs to complete (with timeout)
                await self._wait_for_active_jobs_completion(timeout)
            else:
                # Cancel active jobs
                await self._cancel_active_jobs()
            
            # Shutdown executor pool
            self.executor_pool.shutdown(wait=graceful)
            
            self.is_running = False
            
            logger.info("Background Job Manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping job manager: {str(e)}")
            self.is_running = False
    
    async def submit_job(self, 
                        job: ScrapingJob, 
                        job_function: Callable,
                        priority: JobPriority = JobPriority.NORMAL) -> str:
        """
        Submit a job for execution
        
        Args:
            job: Scraping job to execute
            job_function: Function to execute for the job
            priority: Job priority level
            
        Returns:
            Job ID
        """
        try:
            logger.info(f"Submitting job {job.id} with priority {priority.value}")
            
            # Validate job
            if job.id in self.active_jobs:
                raise ValueError(f"Job {job.id} is already active")
            
            # Check queue capacity
            if self.job_queue.qsize() >= self.resource_limits.max_queue_size:
                raise Exception("Job queue is full")
            
            # Register job function
            self.job_functions[job.id] = job_function
            
            # Set job status
            job.status = ScrapingJobStatus.PENDING
            job.current_phase = "queued"
            
            # Add to priority queue
            await self.priority_queues[priority].put((job, priority))
            
            # Update statistics
            self.stats["queue_length"] = sum(q.qsize() for q in self.priority_queues.values())
            
            logger.info(f"Job {job.id} queued successfully")
            
            return job.id
            
        except Exception as e:
            logger.error(f"Error submitting job {job.id}: {str(e)}")
            job.status = ScrapingJobStatus.FAILED
            job.last_error = str(e)
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[ScrapingJobStatusResponse]:
        """Get current status of a job"""
        try:
            # Check active jobs
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                
                elapsed_time = None
                if job.started_at:
                    elapsed_time = (datetime.utcnow() - job.started_at).total_seconds()
                
                return ScrapingJobStatusResponse(
                    job_id=job_id,
                    status=job.status,
                    current_phase=job.current_phase,
                    progress_percentage=job.progress_percentage,
                    sources_processed=0,  # Would be updated by job function
                    total_sources=len(job.config.source_ids) if job.config.source_ids else 0,
                    questions_extracted=job.questions_extracted,
                    questions_processed=job.questions_approved + job.questions_rejected,
                    started_at=job.started_at,
                    estimated_completion=job.estimated_completion,
                    elapsed_time_seconds=elapsed_time,
                    error_count=job.error_count,
                    last_error=job.last_error,
                    recent_logs=job.execution_logs[-10:] if job.execution_logs else []
                )
            
            # Check completed jobs
            if job_id in self.completed_jobs:
                result = self.completed_jobs[job_id]
                return ScrapingJobStatusResponse(
                    job_id=job_id,
                    status=ScrapingJobStatus.COMPLETED,
                    current_phase="completed",
                    progress_percentage=100.0,
                    sources_processed=1,
                    total_sources=1,
                    questions_extracted=0,
                    questions_processed=0,
                    elapsed_time_seconds=result.execution_time_seconds,
                    error_count=0,
                    recent_logs=[f"Job completed successfully in {result.execution_time_seconds:.2f}s"]
                )
            
            # Check failed jobs
            if job_id in self.failed_jobs:
                result = self.failed_jobs[job_id]
                return ScrapingJobStatusResponse(
                    job_id=job_id,
                    status=ScrapingJobStatus.FAILED,
                    current_phase="failed",
                    progress_percentage=0.0,
                    sources_processed=0,
                    total_sources=0,
                    questions_extracted=0,
                    questions_processed=0,
                    elapsed_time_seconds=result.execution_time_seconds,
                    error_count=1,
                    last_error=result.error_message,
                    recent_logs=[f"Job failed: {result.error_message}"]
                )
            
            # Job not found
            return None
            
        except Exception as e:
            logger.error(f"Error getting job status for {job_id}: {str(e)}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        try:
            logger.info(f"Cancelling job {job_id}")
            
            # Check if job is active
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = ScrapingJobStatus.CANCELLED
                job.current_phase = "cancelled"
                
                # Note: In a more sophisticated implementation, we would need
                # to actually interrupt the job execution
                logger.info(f"Job {job_id} marked for cancellation")
                return True
            
            logger.warning(f"Job {job_id} not found in active jobs")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            queue_status = {
                "total_queued": sum(q.qsize() for q in self.priority_queues.values()),
                "by_priority": {
                    priority.value: queue.qsize() 
                    for priority, queue in self.priority_queues.items()
                },
                "active_jobs": len(self.active_jobs),
                "available_executors": len([e for e in self.executors if not e.is_running]),
                "total_executors": len(self.executors)
            }
            
            return queue_status
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {"error": str(e)}
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and statistics"""
        try:
            # Current resource usage
            current_resources = self._get_system_resource_usage()
            
            # Executor status
            executor_status = [executor.get_executor_status() for executor in self.executors]
            
            metrics = {
                "job_statistics": self.stats.copy(),
                "system_resources": current_resources,
                "executor_status": executor_status,
                "queue_metrics": await self.get_queue_status(),
                "recent_performance": self._get_recent_performance_data(),
                "health_indicators": self._calculate_health_indicators()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {"error": str(e)}
    
    def register_job_function(self, job_type: str, function: Callable):
        """Register a job function for a specific job type"""
        self.job_functions[job_type] = function
        logger.info(f"Registered job function for type: {job_type}")
    
    # Internal Methods
    
    async def _job_processing_loop(self):
        """Main job processing loop"""
        logger.info("Starting job processing loop")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Get next job with priority
                job, priority = await self._get_next_job()
                
                if job is None:
                    await asyncio.sleep(0.1)  # Short sleep if no jobs
                    continue
                
                # Find available executor
                available_executor = self._get_available_executor()
                
                if available_executor is None:
                    # Put job back in queue if no executor available
                    await self.priority_queues[priority].put((job, priority))
                    await asyncio.sleep(0.5)  # Wait for executor to become available
                    continue
                
                # Get job function
                job_function = self.job_functions.get(job.id)
                if job_function is None:
                    logger.error(f"No job function registered for job {job.id}")
                    job.status = ScrapingJobStatus.FAILED
                    job.last_error = "No job function registered"
                    continue
                
                # Execute job asynchronously
                asyncio.create_task(self._execute_job_with_tracking(available_executor, job, job_function))
                
            except Exception as e:
                logger.error(f"Error in job processing loop: {str(e)}")
                await asyncio.sleep(1.0)  # Longer sleep on error
        
        logger.info("Job processing loop stopped")
    
    async def _monitoring_loop(self):
        """Resource and performance monitoring loop"""
        logger.info("Starting monitoring loop")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Collect resource usage data
                resource_data = self._get_system_resource_usage()
                
                # Add timestamp and store in history
                resource_data["timestamp"] = datetime.utcnow().isoformat()
                self.stats["resource_usage_history"].append(resource_data)
                
                # Keep only last 100 entries
                if len(self.stats["resource_usage_history"]) > 100:
                    self.stats["resource_usage_history"].pop(0)
                
                # Update statistics
                self._update_statistics()
                
                # Check for resource alerts
                self._check_resource_alerts(resource_data)
                
                await asyncio.sleep(30.0)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60.0)  # Longer sleep on error
        
        logger.info("Monitoring loop stopped")
    
    async def _get_next_job(self) -> Optional[tuple]:
        """Get next job from priority queues"""
        # Check queues in priority order
        for priority in [JobPriority.CRITICAL, JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW]:
            queue = self.priority_queues[priority]
            if not queue.empty():
                try:
                    return await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
        
        return None, None
    
    def _get_available_executor(self) -> Optional[JobExecutor]:
        """Get an available executor"""
        for executor in self.executors:
            if not executor.is_running:
                return executor
        return None
    
    async def _execute_job_with_tracking(self, executor: JobExecutor, job: ScrapingJob, job_function: Callable):
        """Execute job with full tracking and error handling"""
        try:
            # Add to active jobs
            self.active_jobs[job.id] = job
            self.stats["active_jobs_count"] = len(self.active_jobs)
            
            logger.info(f"Starting execution of job {job.id} with executor {executor.executor_id}")
            
            # Execute job
            result = await executor.execute_job(job, job_function)
            
            # Process result
            if result.success:
                job.status = ScrapingJobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress_percentage = 100.0
                job.current_phase = "completed"
                
                self.completed_jobs[job.id] = result
                self.stats["successful_jobs"] += 1
                
                logger.info(f"Job {job.id} completed successfully")
            else:
                job.status = ScrapingJobStatus.FAILED
                job.completed_at = datetime.utcnow()
                job.last_error = result.error_message
                job.error_count += 1
                job.current_phase = "failed"
                
                self.failed_jobs[job.id] = result
                self.stats["failed_jobs"] += 1
                
                logger.error(f"Job {job.id} failed: {result.error_message}")
            
            # Update statistics
            self.stats["total_jobs_processed"] += 1
            self.stats["total_execution_time"] += result.execution_time_seconds
            self.stats["avg_execution_time"] = (
                self.stats["total_execution_time"] / self.stats["total_jobs_processed"]
            )
            
            # Add to history
            self.job_history.append({
                "job_id": job.id,
                "status": job.status.value,
                "execution_time": result.execution_time_seconds,
                "success": result.success,
                "completed_at": datetime.utcnow().isoformat(),
                "executor_id": executor.executor_id
            })
            
            # Keep only last 1000 history entries
            if len(self.job_history) > 1000:
                self.job_history.pop(0)
            
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            job.status = ScrapingJobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.last_error = f"Execution error: {str(e)}"
            job.error_count += 1
            
            self.stats["failed_jobs"] += 1
            
        finally:
            # Remove from active jobs
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            
            # Clean up job function
            if job.id in self.job_functions:
                del self.job_functions[job.id]
            
            self.stats["active_jobs_count"] = len(self.active_jobs)
    
    def _get_system_resource_usage(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network (if available)
            network_io = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_used_gb": memory.used / (1024**3),
                "memory_percent": memory.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_used_gb": disk.used / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100,
                "network_bytes_sent": network_io.bytes_sent if network_io else 0,
                "network_bytes_recv": network_io.bytes_recv if network_io else 0
            }
            
        except Exception as e:
            logger.warning(f"Error getting system resource usage: {str(e)}")
            return {"error": str(e)}
    
    def _update_statistics(self):
        """Update internal statistics"""
        try:
            # Update queue length
            self.stats["queue_length"] = sum(q.qsize() for q in self.priority_queues.values())
            
            # Update active jobs count
            self.stats["active_jobs_count"] = len(self.active_jobs)
            
        except Exception as e:
            logger.warning(f"Error updating statistics: {str(e)}")
    
    def _check_resource_alerts(self, resource_data: Dict[str, Any]):
        """Check for resource usage alerts"""
        try:
            # CPU alert
            cpu_percent = resource_data.get("cpu_percent", 0)
            if cpu_percent > self.resource_limits.max_cpu_percent:
                logger.warning(f"High CPU usage: {cpu_percent:.1f}% (limit: {self.resource_limits.max_cpu_percent}%)")
            
            # Memory alert
            memory_percent = resource_data.get("memory_percent", 0)
            if memory_percent > 90.0:  # 90% memory usage threshold
                logger.warning(f"High memory usage: {memory_percent:.1f}%")
            
            # Disk alert
            disk_percent = resource_data.get("disk_percent", 0)
            if disk_percent > 85.0:  # 85% disk usage threshold
                logger.warning(f"High disk usage: {disk_percent:.1f}%")
            
        except Exception as e:
            logger.warning(f"Error checking resource alerts: {str(e)}")
    
    def _get_recent_performance_data(self) -> Dict[str, Any]:
        """Get recent performance data"""
        try:
            if not self.job_history:
                return {"message": "No recent job history"}
            
            recent_jobs = self.job_history[-20:]  # Last 20 jobs
            
            execution_times = [job["execution_time"] for job in recent_jobs]
            success_count = sum(1 for job in recent_jobs if job["success"])
            
            return {
                "recent_jobs_count": len(recent_jobs),
                "success_rate": (success_count / len(recent_jobs)) * 100,
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "jobs_per_hour": len(recent_jobs) / max(1, self._get_hours_since_oldest_recent_job())
            }
            
        except Exception as e:
            logger.warning(f"Error getting recent performance data: {str(e)}")
            return {"error": str(e)}
    
    def _get_hours_since_oldest_recent_job(self) -> float:
        """Calculate hours since oldest recent job"""
        try:
            if not self.job_history:
                return 1.0
            
            oldest_job = self.job_history[-20] if len(self.job_history) >= 20 else self.job_history[0]
            oldest_time = datetime.fromisoformat(oldest_job["completed_at"])
            
            return (datetime.utcnow() - oldest_time).total_seconds() / 3600
            
        except Exception as e:
            logger.warning(f"Error calculating hours since oldest job: {str(e)}")
            return 1.0
    
    def _calculate_health_indicators(self) -> Dict[str, Any]:
        """Calculate system health indicators"""
        try:
            health = {
                "overall_status": "healthy",
                "issues": []
            }
            
            # Check queue backup
            total_queued = sum(q.qsize() for q in self.priority_queues.values())
            if total_queued > 50:
                health["issues"].append(f"High queue backup: {total_queued} jobs queued")
                health["overall_status"] = "warning"
            
            # Check failure rate
            if self.stats["total_jobs_processed"] > 0:
                failure_rate = (self.stats["failed_jobs"] / self.stats["total_jobs_processed"]) * 100
                if failure_rate > 20:
                    health["issues"].append(f"High failure rate: {failure_rate:.1f}%")
                    health["overall_status"] = "warning"
                if failure_rate > 50:
                    health["overall_status"] = "critical"
            
            # Check executor availability
            available_executors = len([e for e in self.executors if not e.is_running])
            if available_executors == 0 and total_queued > 0:
                health["issues"].append("No available executors with jobs in queue")
                health["overall_status"] = "warning"
            
            if not health["issues"]:
                health["issues"].append("All systems operating normally")
            
            return health
            
        except Exception as e:
            logger.warning(f"Error calculating health indicators: {str(e)}")
            return {"overall_status": "unknown", "error": str(e)}
    
    async def _wait_for_active_jobs_completion(self, timeout: int):
        """Wait for active jobs to complete with timeout"""
        start_time = datetime.utcnow()
        
        while self.active_jobs and (datetime.utcnow() - start_time).total_seconds() < timeout:
            logger.info(f"Waiting for {len(self.active_jobs)} active jobs to complete...")
            await asyncio.sleep(2.0)
        
        if self.active_jobs:
            logger.warning(f"Timeout reached. {len(self.active_jobs)} jobs still active.")
    
    async def _cancel_active_jobs(self):
        """Cancel all active jobs"""
        logger.info(f"Cancelling {len(self.active_jobs)} active jobs")
        
        for job_id, job in self.active_jobs.items():
            job.status = ScrapingJobStatus.CANCELLED
            job.current_phase = "cancelled"
            logger.info(f"Cancelled job {job_id}")
    
    def _register_shutdown_handlers(self):
        """Register graceful shutdown handlers"""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # Signals not available in all environments (e.g., threads)
            logger.info("Signal handlers not available in this environment")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        asyncio.create_task(self.stop(graceful=True, timeout=30))


# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

def create_job_manager(max_concurrent_jobs: int = 5, 
                      resource_limits: Optional[ResourceLimits] = None) -> BackgroundJobManager:
    """Factory function to create job manager"""
    return BackgroundJobManager(max_concurrent_jobs, resource_limits)

async def execute_job_with_monitoring(job: ScrapingJob, 
                                    job_function: Callable,
                                    priority: JobPriority = JobPriority.NORMAL) -> JobResult:
    """Convenience function to execute a single job with monitoring"""
    
    manager = create_job_manager(max_concurrent_jobs=1)
    
    try:
        await manager.start()
        
        job_id = await manager.submit_job(job, job_function, priority)
        
        # Wait for completion
        while True:
            status = await manager.get_job_status(job_id)
            if status and status.status in [ScrapingJobStatus.COMPLETED, ScrapingJobStatus.FAILED, ScrapingJobStatus.CANCELLED]:
                break
            await asyncio.sleep(1.0)
        
        # Get result
        if job_id in manager.completed_jobs:
            return manager.completed_jobs[job_id]
        elif job_id in manager.failed_jobs:
            return manager.failed_jobs[job_id]
        else:
            return JobResult(job_id=job_id, success=False, error_message="Job status unknown")
            
    finally:
        await manager.stop()

class JobManagerDashboard:
    """Dashboard for monitoring job manager status"""
    
    def __init__(self, job_manager: BackgroundJobManager):
        self.job_manager = job_manager
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            performance_metrics = await self.job_manager.get_performance_metrics()
            queue_status = await self.job_manager.get_queue_status()
            
            dashboard_data = {
                "job_manager_status": {
                    "is_running": self.job_manager.is_running,
                    "shutdown_requested": self.job_manager.shutdown_requested,
                    "execution_mode": self.job_manager.execution_mode.value,
                    "max_concurrent_jobs": self.job_manager.max_concurrent_jobs
                },
                "performance_metrics": performance_metrics,
                "queue_status": queue_status,
                "recent_jobs": self.job_manager.job_history[-10:] if self.job_manager.job_history else [],
                "resource_limits": asdict(self.job_manager.resource_limits),
                "dashboard_generated_at": datetime.utcnow().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return {"error": str(e)}
    
    def generate_status_report(self) -> str:
        """Generate human-readable status report"""
        try:
            stats = self.job_manager.stats
            active_count = len(self.job_manager.active_jobs)
            queue_length = sum(q.qsize() for q in self.job_manager.priority_queues.values())
            
            if stats["total_jobs_processed"] > 0:
                success_rate = (stats["successful_jobs"] / stats["total_jobs_processed"]) * 100
            else:
                success_rate = 0.0
            
            report = (
                f"Job Manager Status Report\n"
                f"========================\n"
                f"Running: {self.job_manager.is_running}\n"
                f"Active Jobs: {active_count}\n"
                f"Queued Jobs: {queue_length}\n"
                f"Total Processed: {stats['total_jobs_processed']}\n"
                f"Success Rate: {success_rate:.1f}%\n"
                f"Average Execution Time: {stats['avg_execution_time']:.2f}s\n"
                f"Available Executors: {len([e for e in self.job_manager.executors if not e.is_running])}/{len(self.job_manager.executors)}"
            )
            
            return report
            
        except Exception as e:
            return f"Error generating status report: {str(e)}"