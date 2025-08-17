"""
Background Tasks Utilities
Utility functions and classes for background task management and execution
"""

import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from dataclasses import dataclass
import functools
import inspect
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

logger = logging.getLogger(__name__)

class TaskType(str, Enum):
    """Types of background tasks"""
    SCRAPING = "scraping"
    PROCESSING = "processing"
    CLEANUP = "cleanup"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"

class TaskStatus(str, Enum):
    """Background task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class ExecutionContext(str, Enum):
    """Task execution context"""
    ASYNCIO = "asyncio"
    THREAD = "thread"
    PROCESS = "process"

@dataclass
class TaskConfig:
    """Configuration for background task execution"""
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: Optional[float] = None
    execution_context: ExecutionContext = ExecutionContext.ASYNCIO
    priority: int = 1  # 1=highest, 5=lowest
    
@dataclass
class TaskResult:
    """Result of background task execution"""
    task_id: str
    success: bool
    result_data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class BackgroundTask:
    """Represents a background task"""
    
    def __init__(self, 
                 task_id: str,
                 task_func: Callable,
                 task_args: tuple = (),
                 task_kwargs: Dict[str, Any] = None,
                 task_type: TaskType = TaskType.CUSTOM,
                 config: Optional[TaskConfig] = None):
        
        self.task_id = task_id
        self.task_func = task_func
        self.task_args = task_args
        self.task_kwargs = task_kwargs or {}
        self.task_type = task_type
        self.config = config or TaskConfig()
        
        # Status tracking
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Execution tracking
        self.retry_count = 0
        self.last_error: Optional[str] = None
        self.progress_callback: Optional[Callable] = None
        
        # Result
        self.result: Optional[TaskResult] = None
    
    def set_progress_callback(self, callback: Callable):
        """Set progress callback for the task"""
        self.progress_callback = callback
    
    def update_progress(self, progress_data: Dict[str, Any]):
        """Update task progress"""
        if self.progress_callback:
            try:
                self.progress_callback(self.task_id, progress_data)
            except Exception as e:
                logger.warning(f"Error calling progress callback: {str(e)}")
    
    async def execute(self) -> TaskResult:
        """Execute the background task"""
        start_time = datetime.utcnow()
        self.started_at = start_time
        self.status = TaskStatus.RUNNING
        
        try:
            logger.info(f"Executing task {self.task_id} ({self.task_type.value})")
            
            # Execute based on context
            if self.config.execution_context == ExecutionContext.ASYNCIO:
                result_data = await self._execute_async()
            elif self.config.execution_context == ExecutionContext.THREAD:
                result_data = await self._execute_in_thread()
            elif self.config.execution_context == ExecutionContext.PROCESS:
                result_data = await self._execute_in_process()
            else:
                raise ValueError(f"Unknown execution context: {self.config.execution_context}")
            
            # Task completed successfully
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.result = TaskResult(
                task_id=self.task_id,
                success=True,
                result_data=result_data,
                execution_time_seconds=execution_time,
                retry_count=self.retry_count,
                metadata={
                    "task_type": self.task_type.value,
                    "execution_context": self.config.execution_context.value,
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
            
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            
            logger.info(f"Task {self.task_id} completed successfully in {execution_time:.2f}s")
            
            return self.result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_message = str(e)
            self.last_error = error_message
            
            self.result = TaskResult(
                task_id=self.task_id,
                success=False,
                error_message=error_message,
                execution_time_seconds=execution_time,
                retry_count=self.retry_count,
                metadata={
                    "task_type": self.task_type.value,
                    "execution_context": self.config.execution_context.value,
                    "failed_at": datetime.utcnow().isoformat()
                }
            )
            
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.utcnow()
            
            logger.error(f"Task {self.task_id} failed after {execution_time:.2f}s: {error_message}")
            
            return self.result
    
    async def execute_with_retry(self) -> TaskResult:
        """Execute task with retry logic"""
        for attempt in range(self.config.max_retries + 1):
            self.retry_count = attempt
            
            if attempt > 0:
                logger.info(f"Retrying task {self.task_id}, attempt {attempt + 1}/{self.config.max_retries + 1}")
                self.status = TaskStatus.RETRYING
                await asyncio.sleep(self.config.retry_delay_seconds * (2 ** attempt))  # Exponential backoff
            
            try:
                if self.config.timeout_seconds:
                    result = await asyncio.wait_for(self.execute(), timeout=self.config.timeout_seconds)
                else:
                    result = await self.execute()
                
                if result.success:
                    return result
                    
            except asyncio.TimeoutError:
                self.last_error = f"Task timed out after {self.config.timeout_seconds}s"
                logger.warning(f"Task {self.task_id} timed out on attempt {attempt + 1}")
                
            except Exception as e:
                self.last_error = str(e)
                logger.warning(f"Task {self.task_id} failed on attempt {attempt + 1}: {str(e)}")
        
        # All retries exhausted
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        
        if self.result:
            self.result.retry_count = self.retry_count
        
        logger.error(f"Task {self.task_id} failed after {self.config.max_retries + 1} attempts")
        
        return self.result or TaskResult(
            task_id=self.task_id,
            success=False,
            error_message=self.last_error,
            retry_count=self.retry_count
        )
    
    async def _execute_async(self) -> Any:
        """Execute task in async context"""
        if asyncio.iscoroutinefunction(self.task_func):
            return await self.task_func(*self.task_args, **self.task_kwargs)
        else:
            return self.task_func(*self.task_args, **self.task_kwargs)
    
    async def _execute_in_thread(self) -> Any:
        """Execute task in thread pool"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor() as executor:
            if asyncio.iscoroutinefunction(self.task_func):
                # Create a new event loop for the thread
                future = executor.submit(asyncio.run, self.task_func(*self.task_args, **self.task_kwargs))
            else:
                future = executor.submit(self.task_func, *self.task_args, **self.task_kwargs)
            
            return await loop.run_in_executor(None, future.result)
    
    async def _execute_in_process(self) -> Any:
        """Execute task in separate process"""
        if asyncio.iscoroutinefunction(self.task_func):
            raise ValueError("Cannot execute async function in process context")
        
        loop = asyncio.get_event_loop()
        
        with ProcessPoolExecutor() as executor:
            future = executor.submit(self.task_func, *self.task_args, **self.task_kwargs)
            return await loop.run_in_executor(None, future.result)
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        execution_time = None
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            execution_time = (end_time - self.started_at).total_seconds()
        
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_seconds": execution_time,
            "retry_count": self.retry_count,
            "max_retries": self.config.max_retries,
            "last_error": self.last_error,
            "success": self.result.success if self.result else None,
            "execution_context": self.config.execution_context.value,
            "priority": self.config.priority
        }

class TaskQueue:
    """Priority-based task queue for background tasks"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues = {
            1: asyncio.Queue(),  # Highest priority
            2: asyncio.Queue(),
            3: asyncio.Queue(), 
            4: asyncio.Queue(),
            5: asyncio.Queue()   # Lowest priority
        }
        self.task_registry: Dict[str, BackgroundTask] = {}
        
    async def put(self, task: BackgroundTask) -> bool:
        """Add task to queue"""
        if len(self.task_registry) >= self.max_size:
            logger.warning("Task queue is full")
            return False
        
        priority = task.config.priority
        if priority not in self.queues:
            priority = 3  # Default to medium priority
        
        await self.queues[priority].put(task)
        self.task_registry[task.task_id] = task
        
        logger.debug(f"Task {task.task_id} added to queue with priority {priority}")
        return True
    
    async def get(self) -> Optional[BackgroundTask]:
        """Get next task from queue (priority order)"""
        for priority in sorted(self.queues.keys()):
            queue = self.queues[priority]
            if not queue.empty():
                try:
                    task = await asyncio.wait_for(queue.get(), timeout=0.1)
                    return task
                except asyncio.TimeoutError:
                    continue
        
        return None
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID"""
        return self.task_registry.get(task_id)
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from registry"""
        if task_id in self.task_registry:
            del self.task_registry[task_id]
            return True
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        return {
            "total_tasks": len(self.task_registry),
            "by_priority": {
                str(priority): queue.qsize() 
                for priority, queue in self.queues.items()
            },
            "by_status": self._count_tasks_by_status(),
            "max_size": self.max_size
        }
    
    def _count_tasks_by_status(self) -> Dict[str, int]:
        """Count tasks by status"""
        status_counts = {}
        
        for task in self.task_registry.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts

class BackgroundTaskExecutor:
    """Executor for managing background tasks"""
    
    def __init__(self, 
                 max_concurrent_tasks: int = 5,
                 queue_size: int = 1000):
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue = TaskQueue(max_size=queue_size)
        self.active_tasks: Dict[str, BackgroundTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        
        # Execution control
        self.is_running = False
        self.shutdown_requested = False
        
        # Progress tracking
        self.progress_callbacks: Dict[str, Callable] = {}
        
        # Statistics
        self.stats = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }
    
    async def start(self):
        """Start the task executor"""
        if self.is_running:
            return
        
        self.is_running = True
        self.shutdown_requested = False
        
        logger.info("Starting BackgroundTaskExecutor")
        
        # Start task processing loop
        asyncio.create_task(self._task_processing_loop())
        
        logger.info("BackgroundTaskExecutor started")
    
    async def stop(self, wait_for_completion: bool = True):
        """Stop the task executor"""
        if not self.is_running:
            return
        
        logger.info("Stopping BackgroundTaskExecutor")
        
        self.shutdown_requested = True
        
        if wait_for_completion:
            # Wait for active tasks to complete
            while self.active_tasks:
                logger.info(f"Waiting for {len(self.active_tasks)} tasks to complete...")
                await asyncio.sleep(1.0)
        
        self.is_running = False
        
        logger.info("BackgroundTaskExecutor stopped")
    
    async def submit_task(self, 
                         task_func: Callable,
                         task_args: tuple = (),
                         task_kwargs: Dict[str, Any] = None,
                         task_type: TaskType = TaskType.CUSTOM,
                         config: Optional[TaskConfig] = None,
                         task_id: Optional[str] = None) -> str:
        """
        Submit a task for background execution
        
        Returns:
            Task ID
        """
        if not task_id:
            task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            task_id=task_id,
            task_func=task_func,
            task_args=task_args,
            task_kwargs=task_kwargs or {},
            task_type=task_type,
            config=config or TaskConfig()
        )
        
        # Set progress callback if available
        if task_id in self.progress_callbacks:
            task.set_progress_callback(self.progress_callbacks[task_id])
        
        success = await self.task_queue.put(task)
        if not success:
            raise Exception("Failed to add task to queue - queue is full")
        
        logger.info(f"Task {task_id} submitted for execution")
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].get_status_info()
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": TaskStatus.COMPLETED.value if result.success else TaskStatus.FAILED.value,
                "success": result.success,
                "execution_time_seconds": result.execution_time_seconds,
                "retry_count": result.retry_count,
                "error_message": result.error_message,
                "result_available": result.result_data is not None
            }
        
        # Check queued tasks
        task = self.task_queue.get_task(task_id)
        if task:
            return task.get_status_info()
        
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a completed task"""
        return self.completed_tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        # Check if task is active
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task {task_id} marked for cancellation")
            return True
        
        # Check if task is queued
        task = self.task_queue.get_task(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            self.task_queue.remove_task(task_id)
            logger.info(f"Queued task {task_id} cancelled")
            return True
        
        return False
    
    def set_progress_callback(self, task_id: str, callback: Callable):
        """Set progress callback for a task"""
        self.progress_callbacks[task_id] = callback
        
        # If task is already created, set the callback
        if task_id in self.active_tasks:
            self.active_tasks[task_id].set_progress_callback(callback)
        elif task_id in self.task_queue.task_registry:
            self.task_queue.task_registry[task_id].set_progress_callback(callback)
    
    def get_executor_status(self) -> Dict[str, Any]:
        """Get executor status"""
        return {
            "is_running": self.is_running,
            "shutdown_requested": self.shutdown_requested,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": len(self.active_tasks),
            "queue_status": self.task_queue.get_queue_status(),
            "statistics": self.stats.copy(),
            "completed_tasks_count": len(self.completed_tasks)
        }
    
    async def _task_processing_loop(self):
        """Main task processing loop"""
        logger.info("Starting task processing loop")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Check if we can process more tasks
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.5)
                    continue
                
                # Get next task
                task = await self.task_queue.get()
                if task is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Check if task was cancelled
                if task.status == TaskStatus.CANCELLED:
                    continue
                
                # Execute task
                self.active_tasks[task.task_id] = task
                asyncio.create_task(self._execute_task_with_tracking(task))
                
            except Exception as e:
                logger.error(f"Error in task processing loop: {str(e)}")
                await asyncio.sleep(1.0)
        
        logger.info("Task processing loop stopped")
    
    async def _execute_task_with_tracking(self, task: BackgroundTask):
        """Execute task with full tracking"""
        try:
            logger.debug(f"Starting execution of task {task.task_id}")
            
            # Execute task with retry
            result = await task.execute_with_retry()
            
            # Store result
            self.completed_tasks[task.task_id] = result
            
            # Update statistics
            self.stats["total_tasks_processed"] += 1
            
            if result.success:
                self.stats["successful_tasks"] += 1
            else:
                self.stats["failed_tasks"] += 1
            
            self.stats["total_execution_time"] += result.execution_time_seconds
            self.stats["avg_execution_time"] = (
                self.stats["total_execution_time"] / self.stats["total_tasks_processed"]
            )
            
            logger.debug(f"Task {task.task_id} execution completed: success={result.success}")
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {str(e)}")
            
            # Create failed result
            failed_result = TaskResult(
                task_id=task.task_id,
                success=False,
                error_message=f"Execution error: {str(e)}",
                retry_count=task.retry_count
            )
            
            self.completed_tasks[task.task_id] = failed_result
            self.stats["failed_tasks"] += 1
            
        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            # Remove from queue registry
            self.task_queue.remove_task(task.task_id)
            
            # Clean up progress callback
            if task.task_id in self.progress_callbacks:
                del self.progress_callbacks[task.task_id]

# =============================================================================
# UTILITY FUNCTIONS AND DECORATORS
# =============================================================================

def background_task(task_type: TaskType = TaskType.CUSTOM, 
                   config: Optional[TaskConfig] = None):
    """Decorator to mark a function as a background task"""
    
    def decorator(func: Callable):
        func._is_background_task = True
        func._task_type = task_type
        func._task_config = config or TaskConfig()
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

async def run_in_background(task_func: Callable,
                          task_args: tuple = (),
                          task_kwargs: Dict[str, Any] = None,
                          task_type: TaskType = TaskType.CUSTOM,
                          config: Optional[TaskConfig] = None,
                          executor: Optional[BackgroundTaskExecutor] = None) -> str:
    """
    Convenience function to run a task in background
    
    Returns:
        Task ID
    """
    if executor is None:
        # Create a default executor
        executor = BackgroundTaskExecutor(max_concurrent_tasks=1)
        await executor.start()
    
    return await executor.submit_task(
        task_func=task_func,
        task_args=task_args,
        task_kwargs=task_kwargs or {},
        task_type=task_type,
        config=config
    )

async def wait_for_task_completion(task_id: str, 
                                 executor: BackgroundTaskExecutor,
                                 timeout: Optional[float] = None) -> TaskResult:
    """
    Wait for a task to complete and return its result
    
    Args:
        task_id: ID of the task to wait for
        executor: Task executor
        timeout: Maximum time to wait (seconds)
        
    Returns:
        Task result
        
    Raises:
        asyncio.TimeoutError: If timeout is reached
        ValueError: If task is not found
    """
    start_time = datetime.utcnow()
    
    while True:
        # Check if task is completed
        result = await executor.get_task_result(task_id)
        if result is not None:
            return result
        
        # Check timeout
        if timeout:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise asyncio.TimeoutError(f"Task {task_id} did not complete within {timeout}s")
        
        # Check if task exists
        status = await executor.get_task_status(task_id)
        if status is None:
            raise ValueError(f"Task {task_id} not found")
        
        await asyncio.sleep(0.5)

class TaskBatch:
    """Utility for managing batch task execution"""
    
    def __init__(self, batch_id: Optional[str] = None):
        self.batch_id = batch_id or str(uuid.uuid4())
        self.tasks: List[str] = []
        self.batch_config = TaskConfig()
    
    def add_task(self, 
                executor: BackgroundTaskExecutor,
                task_func: Callable,
                task_args: tuple = (),
                task_kwargs: Dict[str, Any] = None,
                task_type: TaskType = TaskType.CUSTOM) -> str:
        """Add a task to the batch"""
        
        task_id = f"{self.batch_id}_{len(self.tasks)}"
        
        asyncio.create_task(
            executor.submit_task(
                task_func=task_func,
                task_args=task_args,
                task_kwargs=task_kwargs or {},
                task_type=task_type,
                config=self.batch_config,
                task_id=task_id
            )
        )
        
        self.tasks.append(task_id)
        return task_id
    
    async def wait_for_completion(self, 
                                executor: BackgroundTaskExecutor,
                                timeout: Optional[float] = None) -> Dict[str, TaskResult]:
        """Wait for all tasks in batch to complete"""
        
        results = {}
        
        for task_id in self.tasks:
            try:
                result = await wait_for_task_completion(task_id, executor, timeout)
                results[task_id] = result
            except Exception as e:
                logger.error(f"Error waiting for task {task_id}: {str(e)}")
                results[task_id] = TaskResult(
                    task_id=task_id,
                    success=False,
                    error_message=str(e)
                )
        
        return results
    
    def get_batch_status(self, executor: BackgroundTaskExecutor) -> Dict[str, Any]:
        """Get status of all tasks in batch"""
        
        batch_status = {
            "batch_id": self.batch_id,
            "total_tasks": len(self.tasks),
            "task_statuses": {},
            "completed_count": 0,
            "failed_count": 0,
            "success_rate": 0.0
        }
        
        for task_id in self.tasks:
            status = asyncio.create_task(executor.get_task_status(task_id))
            batch_status["task_statuses"][task_id] = status
            
            if status and status.get("status") in ["completed", "failed"]:
                if status.get("success", False):
                    batch_status["completed_count"] += 1
                else:
                    batch_status["failed_count"] += 1
        
        processed_count = batch_status["completed_count"] + batch_status["failed_count"]
        if processed_count > 0:
            batch_status["success_rate"] = (batch_status["completed_count"] / processed_count) * 100
        
        return batch_status

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_task_executor(max_concurrent_tasks: int = 5) -> BackgroundTaskExecutor:
    """Factory function to create task executor"""
    return BackgroundTaskExecutor(max_concurrent_tasks=max_concurrent_tasks)

def create_task_config(max_retries: int = 3,
                      retry_delay_seconds: float = 1.0,
                      timeout_seconds: Optional[float] = None,
                      execution_context: ExecutionContext = ExecutionContext.ASYNCIO,
                      priority: int = 3) -> TaskConfig:
    """Factory function to create task configuration"""
    return TaskConfig(
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
        timeout_seconds=timeout_seconds,
        execution_context=execution_context,
        priority=priority
    )

# =============================================================================
# EXAMPLE USAGE PATTERNS
# =============================================================================

# Example 1: Simple background task
@background_task(task_type=TaskType.PROCESSING)
async def example_processing_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """Example processing task"""
    await asyncio.sleep(2.0)  # Simulate work
    return {"processed": True, "data_size": len(str(data))}

# Example 2: Task with progress reporting
async def example_scraping_task(urls: List[str], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """Example scraping task with progress reporting"""
    results = []
    
    for i, url in enumerate(urls):
        # Simulate scraping work
        await asyncio.sleep(1.0)
        
        result = {"url": url, "scraped": True}
        results.append(result)
        
        # Report progress
        if progress_callback:
            progress_callback({
                "completed": i + 1,
                "total": len(urls),
                "current_url": url,
                "percentage": ((i + 1) / len(urls)) * 100
            })
    
    return results