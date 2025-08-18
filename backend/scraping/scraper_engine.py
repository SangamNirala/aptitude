"""
Main Scraping Coordinator - Central Orchestrator for All Scraping Operations
Comprehensive job management, driver coordination, error handling, and progress tracking
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import threading
import queue
import time

# Import required modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.scraping_models import (
    ScrapingJob, ScrapingJobStatus, ScrapingTarget, DataSourceConfig,
    ScrapingSourceType, ContentExtractionMethod, ScrapingJobConfig,
    RawExtractedQuestion, ProcessedScrapedQuestion
)
from scraping.extractors.base_extractor import BatchExtractionResult, create_extraction_context
from scraping.extractors.indiabix_extractor import IndiaBixExtractor, create_indiabix_extractor
from scraping.extractors.geeksforgeeks_extractor import GeeksforGeeksExtractor, create_geeksforgeeks_extractor
from scraping.drivers.selenium_driver import SeleniumDriver, create_indiabix_selenium_driver
from scraping.drivers.playwright_driver import PlaywrightDriver, create_geeksforgeeks_playwright_driver
from scraping.utils.content_validator import ContentValidator, validate_with_quality_gate
from scraping.utils.performance_monitor import PerformanceMonitor
from scraping.utils.anti_detection import AntiDetectionManager
from scraping.utils.rate_limiter import ExponentialBackoffLimiter

logger = logging.getLogger(__name__)

# =============================================================================
# SCRAPING ENGINE CONFIGURATION
# =============================================================================

@dataclass
class ScrapingEngineConfig:
    """Configuration for the main scraping engine"""
    max_concurrent_jobs: int = 3
    max_retries_per_job: int = 3
    retry_delay_base: float = 5.0
    job_timeout_minutes: int = 60
    enable_performance_monitoring: bool = True
    enable_anti_detection: bool = True
    enable_content_validation: bool = True
    auto_restart_failed_jobs: bool = True
    progress_update_interval: int = 10  # seconds
    max_questions_per_job: int = 1000
    driver_pool_size: int = 2

@dataclass
class JobProgress:
    """Progress tracking for scraping job"""
    job_id: str
    current_page: int
    total_pages: int
    questions_extracted: int
    questions_processed: int
    success_rate: float
    estimated_completion: Optional[datetime] = None
    last_update: datetime = datetime.now()
    current_status: str = "running"
    error_count: int = 0

@dataclass
class ScrapingStats:
    """Overall scraping statistics"""
    total_jobs_completed: int = 0
    total_questions_extracted: int = 0
    total_extraction_time: float = 0.0
    average_extraction_time: float = 0.0
    success_rate: float = 0.0
    failed_jobs: int = 0
    active_jobs: int = 0

# =============================================================================
# MAIN SCRAPING ENGINE CLASS
# =============================================================================

class ScrapingEngine:
    """
    Central orchestrator for all scraping operations
    Manages jobs, drivers, extractors, and provides comprehensive coordination
    """
    
    def __init__(self, config: Optional[ScrapingEngineConfig] = None):
        """
        Initialize the scraping engine
        
        Args:
            config: Engine configuration
        """
        self.config = config or ScrapingEngineConfig()
        
        # Core components
        self.job_queue = queue.Queue()
        self.active_jobs = {}
        self.completed_jobs = {}
        self.job_progress = {}
        
        # Driver pools
        self.selenium_drivers = {}
        self.playwright_drivers = {}
        
        # Extractors
        self.extractors = {}
        
        # Utilities
        self.performance_monitor = PerformanceMonitor()
        self.anti_detection = AntiDetectionManager(source_name="scraping_engine")
        self.content_validators = {}
        
        # Statistics
        self.stats = ScrapingStats()
        
        # Control flags
        self.is_running = False
        self.worker_threads = []
        
        # Job management lock
        self.job_lock = threading.Lock()
        
        logger.info("Scraping engine initialized with configuration")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all engine components"""
        try:
            # Initialize extractors
            self.extractors[ScrapingSourceType.INDIABIX] = create_indiabix_extractor(
                performance_monitor=self.performance_monitor
            )
            self.extractors[ScrapingSourceType.GEEKSFORGEEKS] = create_geeksforgeeks_extractor(
                performance_monitor=self.performance_monitor
            )
            
            # Initialize content validators
            from scraping.utils.content_validator import create_indiabix_validator, create_geeksforgeeks_validator
            self.content_validators[ScrapingSourceType.INDIABIX] = create_indiabix_validator()
            self.content_validators[ScrapingSourceType.GEEKSFORGEEKS] = create_geeksforgeeks_validator()
            
            logger.info("Scraping engine components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing scraping engine components: {e}")
            raise
    
    # =============================================================================
    # JOB MANAGEMENT
    # =============================================================================
    
    def submit_scraping_job(self, job_config: ScrapingJobConfig) -> str:
        """
        Submit a new scraping job to the engine
        
        Args:
            job_config: Configuration for the scraping job
            
        Returns:
            Job ID for tracking
        """
        try:
            # Create scraping job
            job = ScrapingJob(
                id=str(uuid.uuid4()),
                config=job_config,
                status=ScrapingJobStatus.QUEUED
            )
            
            # Add to queue
            with self.job_lock:
                self.job_queue.put(job)
                self.active_jobs[job.id] = job
                
                # Initialize progress tracking
                self.job_progress[job.id] = JobProgress(
                    job_id=job.id,
                    current_page=0,
                    total_pages=job_config.max_pages or 50,
                    questions_extracted=0,
                    questions_processed=0,
                    success_rate=0.0
                )
            
            logger.info(f"Scraping job submitted: {job.id} for {job_config.source_ids}")
            
            # Start processing if not already running
            if not self.is_running:
                self.start_engine()
            
            return job.id
            
        except Exception as e:
            logger.error(f"Error submitting scraping job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a scraping job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information or None if not found
        """
        try:
            with self.job_lock:
                # Check active jobs
                if job_id in self.active_jobs:
                    job = self.active_jobs[job_id]
                    progress = self.job_progress.get(job_id)
                    
                    return {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "created_at": job.created_at,
                        "updated_at": job.updated_at,
                        "progress": asdict(progress) if progress else None,
                        "total_questions_extracted": job.total_questions_extracted,
                        "successful_extractions": job.successful_extractions,
                        "failed_extractions": job.failed_extractions,
                        "error_message": job.error_message
                    }
                
                # Check completed jobs
                if job_id in self.completed_jobs:
                    job = self.completed_jobs[job_id]
                    return {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "created_at": job.created_at,
                        "updated_at": job.updated_at,
                        "completed_at": job.completed_at,
                        "total_questions_extracted": job.total_questions_extracted,
                        "successful_extractions": job.successful_extractions,
                        "failed_extractions": job.failed_extractions,
                        "error_message": job.error_message,
                        "execution_time_seconds": (
                            job.completed_at - job.created_at
                        ).total_seconds() if job.completed_at else None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting job status for {job_id}: {e}")
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running scraping job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Success status
        """
        try:
            with self.job_lock:
                if job_id in self.active_jobs:
                    job = self.active_jobs[job_id]
                    job.status = ScrapingJobStatus.CANCELLED
                    job.updated_at = datetime.now()
                    job.error_message = "Job cancelled by user"
                    
                    logger.info(f"Scraping job cancelled: {job_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def get_all_jobs(self) -> Dict[str, Any]:
        """
        Get information about all jobs
        
        Returns:
            Dictionary with job information
        """
        try:
            with self.job_lock:
                active_job_info = []
                for job_id, job in self.active_jobs.items():
                    progress = self.job_progress.get(job_id)
                    active_job_info.append({
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "source_type": job.source_type,
                        "created_at": job.created_at,
                        "progress": asdict(progress) if progress else None
                    })
                
                completed_job_info = []
                for job_id, job in self.completed_jobs.items():
                    completed_job_info.append({
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "source_type": job.source_type,
                        "created_at": job.created_at,
                        "completed_at": job.completed_at,
                        "total_questions": job.total_questions_extracted
                    })
                
                return {
                    "active_jobs": active_job_info,
                    "completed_jobs": completed_job_info,
                    "queue_size": self.job_queue.qsize(),
                    "statistics": asdict(self.stats)
                }
                
        except Exception as e:
            logger.error(f"Error getting all jobs information: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # ENGINE CONTROL
    # =============================================================================
    
    def start_engine(self):
        """Start the scraping engine"""
        if self.is_running:
            logger.warning("Scraping engine is already running")
            return
        
        self.is_running = True
        
        # Start worker threads
        for i in range(self.config.max_concurrent_jobs):
            worker = threading.Thread(
                target=self._job_worker,
                name=f"ScrapingWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        # Start progress monitor
        progress_monitor = threading.Thread(
            target=self._progress_monitor,
            name="ProgressMonitor",
            daemon=True
        )
        progress_monitor.start()
        self.worker_threads.append(progress_monitor)
        
        logger.info(f"Scraping engine started with {self.config.max_concurrent_jobs} workers")
    
    def stop_engine(self):
        """Stop the scraping engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all active jobs
        with self.job_lock:
            for job_id in list(self.active_jobs.keys()):
                self.cancel_job(job_id)
        
        # Close drivers
        self._cleanup_drivers()
        
        logger.info("Scraping engine stopped")
    
    def _job_worker(self):
        """Worker thread for processing scraping jobs"""
        thread_name = threading.current_thread().name
        logger.info(f"Job worker {thread_name} started")
        
        while self.is_running:
            try:
                # Get job from queue
                try:
                    job = self.job_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if job.status == ScrapingJobStatus.CANCELLED:
                    continue
                
                logger.info(f"Worker {thread_name} processing job {job.job_id}")
                
                # Process the job
                self._process_scraping_job(job)
                
                # Mark job as done
                self.job_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in job worker {thread_name}: {e}")
    
    def _progress_monitor(self):
        """Monitor and update job progress"""
        while self.is_running:
            try:
                with self.job_lock:
                    for job_id, progress in self.job_progress.items():
                        if job_id in self.active_jobs:
                            job = self.active_jobs[job_id]
                            
                            # Update progress from job
                            progress.questions_extracted = job.total_questions_extracted
                            progress.questions_processed = job.successful_extractions + job.failed_extractions
                            
                            if progress.questions_processed > 0:
                                progress.success_rate = job.successful_extractions / progress.questions_processed
                            
                            # Estimate completion time
                            if progress.current_page > 0:
                                pages_per_minute = progress.current_page / (
                                    (datetime.now() - job.created_at).total_seconds() / 60
                                )
                                if pages_per_minute > 0:
                                    remaining_pages = progress.total_pages - progress.current_page
                                    remaining_minutes = remaining_pages / pages_per_minute
                                    progress.estimated_completion = datetime.now() + timedelta(minutes=remaining_minutes)
                            
                            progress.last_update = datetime.now()
                
                time.sleep(self.config.progress_update_interval)
                
            except Exception as e:
                logger.error(f"Error in progress monitor: {e}")
    
    # =============================================================================
    # JOB PROCESSING
    # =============================================================================
    
    def _process_scraping_job(self, job: ScrapingJob):
        """
        Process a single scraping job
        
        Args:
            job: ScrapingJob to process
        """
        try:
            job.status = ScrapingJobStatus.RUNNING
            job.started_at = datetime.now()
            job.updated_at = datetime.now()
            
            logger.info(f"Starting scraping job {job.job_id} for {job.source_type}")
            
            with self.performance_monitor.monitor_operation(f"scraping_job_{job.job_id}"):
                # Get appropriate driver and extractor
                driver = self._get_driver(job.target_config.source_id, job.job_config.extraction_method)
                extractor = self._get_extractor(job.target_config.source_id)
                
                if not driver or not extractor:
                    self._fail_job(job, "Failed to initialize driver or extractor")
                    return
                
                try:
                    # Process job with retry logic
                    success = self._execute_job_with_retries(job, driver, extractor)
                    
                    if success:
                        self._complete_job(job)
                    else:
                        self._fail_job(job, "Job failed after all retry attempts")
                
                finally:
                    # Clean up driver
                    self._release_driver(driver)
        
        except Exception as e:
            logger.error(f"Error processing scraping job {job.job_id}: {e}")
            self._fail_job(job, f"Job processing error: {str(e)}")
    
    def _execute_job_with_retries(self, job: ScrapingJob, driver: Any, extractor: Any) -> bool:
        """Execute job with retry logic"""
        for attempt in range(self.config.max_retries_per_job + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for job {job.job_id}")
                    time.sleep(self.config.retry_delay_base * attempt)
                
                # Execute the actual scraping
                success = self._execute_single_job_attempt(job, driver, extractor)
                
                if success:
                    return True
                
                # Check if job was cancelled
                if job.status == ScrapingJobStatus.CANCELLED:
                    return False
                
            except Exception as e:
                logger.error(f"Job {job.job_id} attempt {attempt + 1} failed: {e}")
                job.error_message = f"Attempt {attempt + 1} failed: {str(e)}"
        
        return False
    
    def _execute_single_job_attempt(self, job: ScrapingJob, driver: Any, extractor: Any) -> bool:
        """Execute a single job attempt"""
        try:
            target = job.target_config
            job_config = job.job_config
            
            # Navigate to target URL
            self._navigate_to_url(driver, target.target_url)
            
            current_page = 1
            total_extracted = 0
            
            while current_page <= (job_config.max_pages or 50):
                # Check if job was cancelled
                if job.status == ScrapingJobStatus.CANCELLED:
                    return False
                
                # Check timeout
                if self._is_job_timeout(job):
                    job.error_message = "Job timeout exceeded"
                    return False
                
                # Update progress
                with self.job_lock:
                    if job.job_id in self.job_progress:
                        self.job_progress[job.job_id].current_page = current_page
                
                # Create extraction context
                context = create_extraction_context(
                    target=target,
                    page_url=self._get_current_url(driver),
                    page_number=current_page
                )
                
                # Extract questions from current page
                batch_result = extractor.extract_questions_from_page(driver, context)
                
                # Process extraction results
                self._process_batch_result(job, batch_result)
                
                total_extracted += batch_result.successful_extractions
                
                # Check if we've reached max questions
                if job_config.max_questions and total_extracted >= job_config.max_questions:
                    logger.info(f"Job {job.job_id} reached max questions limit: {job_config.max_questions}")
                    break
                
                # Handle pagination
                has_next, next_url = extractor.handle_pagination(driver, current_page, context)
                
                if not has_next:
                    logger.info(f"Job {job.job_id} completed all pages")
                    break
                
                # Navigate to next page
                if next_url:
                    self._navigate_to_url(driver, next_url)
                
                current_page += 1
                
                # Apply rate limiting
                self._apply_rate_limiting(job.target_config.source_id)
            
            # Job completed successfully if we extracted something
            return total_extracted > 0
            
        except Exception as e:
            logger.error(f"Error executing job attempt {job.job_id}: {e}")
            job.error_message = str(e)
            return False
    
    def _process_batch_result(self, job: ScrapingJob, batch_result: BatchExtractionResult):
        """Process results from a batch extraction"""
        try:
            # Update job statistics
            job.total_questions_extracted += batch_result.total_processed
            job.successful_extractions += batch_result.successful_extractions
            job.failed_extractions += batch_result.failed_extractions
            job.updated_at = datetime.now()
            
            # Validate and process extracted questions
            for extraction_result in batch_result.extraction_results:
                if extraction_result.success and extraction_result.question_data:
                    # Validate content if enabled
                    if self.config.enable_content_validation:
                        validator = self._get_content_validator(job.target_config.source_id)
                        quality_score, quality_gate = validate_with_quality_gate(
                            extraction_result.question_data.dict(), 
                            job.target_config.source_id
                        )
                        
                        # Store quality information
                        extraction_result.question_data.extraction_metadata.update({
                            "quality_score": quality_score.overall_score,
                            "quality_gate": quality_gate.value,
                            "validation_issues": len(quality_score.validation_issues)
                        })
            
            # Update statistics
            self.stats.total_questions_extracted += batch_result.successful_extractions
            
            logger.info(f"Job {job.job_id} batch processed: "
                       f"{batch_result.successful_extractions} successful, "
                       f"{batch_result.failed_extractions} failed")
            
        except Exception as e:
            logger.error(f"Error processing batch result for job {job.job_id}: {e}")
    
    # =============================================================================
    # DRIVER MANAGEMENT
    # =============================================================================
    
    def _get_driver(self, source_type: str, extraction_method: ContentExtractionMethod) -> Any:
        """Get appropriate driver for source and method"""
        try:
            if extraction_method == ContentExtractionMethod.SELENIUM:
                return self._get_selenium_driver(source_type)
            elif extraction_method == ContentExtractionMethod.PLAYWRIGHT:
                return self._get_playwright_driver(source_type)
            else:
                logger.error(f"Unsupported extraction method: {extraction_method}")
                return None
        
        except Exception as e:
            logger.error(f"Error getting driver for {source_type}: {e}")
            return None
    
    def _get_selenium_driver(self, source_type: str) -> Optional[SeleniumDriver]:
        """Get Selenium driver for source"""
        try:
            if source_type == "indiabix":
                return create_indiabix_selenium_driver(
                    anti_detection_manager=self.anti_detection
                )
            else:
                # Generic Selenium driver
                from scraping.drivers.selenium_driver import create_selenium_driver
                return create_selenium_driver()
        
        except Exception as e:
            logger.error(f"Error creating Selenium driver for {source_type}: {e}")
            return None
    
    def _get_playwright_driver(self, source_type: str) -> Optional[PlaywrightDriver]:
        """Get Playwright driver for source"""
        try:
            if source_type == "geeksforgeeks":
                return create_geeksforgeeks_playwright_driver()
            else:
                # Generic Playwright driver
                from scraping.drivers.playwright_driver import create_playwright_driver
                return create_playwright_driver()
        
        except Exception as e:
            logger.error(f"Error creating Playwright driver for {source_type}: {e}")
            return None
    
    def _release_driver(self, driver: Any):
        """Release driver resources"""
        try:
            if hasattr(driver, 'close'):
                driver.close()
            elif hasattr(driver, 'quit'):
                driver.quit()
        except Exception as e:
            logger.warning(f"Error releasing driver: {e}")
    
    def _cleanup_drivers(self):
        """Clean up all driver resources"""
        try:
            # Cleanup Selenium drivers
            for driver in self.selenium_drivers.values():
                self._release_driver(driver)
            self.selenium_drivers.clear()
            
            # Cleanup Playwright drivers
            for driver in self.playwright_drivers.values():
                self._release_driver(driver)
            self.playwright_drivers.clear()
            
            logger.info("All drivers cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up drivers: {e}")
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _get_extractor(self, source_type: str) -> Any:
        """Get extractor for source type"""
        return self.extractors.get(source_type)
    
    def _get_content_validator(self, source_type: str) -> ContentValidator:
        """Get content validator for source type"""
        return self.content_validators.get(source_type)
    
    def _navigate_to_url(self, driver: Any, url: str):
        """Navigate driver to URL"""
        try:
            if hasattr(driver, 'get'):  # Selenium
                driver.get(url)
            elif hasattr(driver, 'goto'):  # Playwright
                driver.goto(url)
            elif hasattr(driver, 'navigate'):  # Custom driver
                driver.navigate(url)
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    def _get_current_url(self, driver: Any) -> str:
        """Get current URL from driver"""
        try:
            if hasattr(driver, 'current_url'):  # Selenium
                return driver.current_url
            elif hasattr(driver, 'url'):  # Playwright
                return driver.url
            elif hasattr(driver, 'get_current_url'):  # Custom driver
                return driver.get_current_url()
        except Exception:
            return ""
        
        return ""
    
    def _apply_rate_limiting(self, source_type: str):
        """Apply rate limiting between requests"""
        try:
            # Get source-specific rate limits
            if source_type == "indiabix":
                delay = 3.0  # IndiaBix rate limit
            elif source_type == "geeksforgeeks":
                delay = 2.5  # GeeksforGeeks rate limit
            else:
                delay = 2.0  # Default rate limit
            
            time.sleep(delay)
            
        except Exception as e:
            logger.warning(f"Error applying rate limiting: {e}")
    
    def _is_job_timeout(self, job: ScrapingJob) -> bool:
        """Check if job has exceeded timeout"""
        if not job.started_at:
            return False
        
        elapsed = (datetime.now() - job.started_at).total_seconds()
        timeout = self.config.job_timeout_minutes * 60
        
        return elapsed > timeout
    
    def _complete_job(self, job: ScrapingJob):
        """Mark job as completed"""
        try:
            job.status = ScrapingJobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.updated_at = datetime.now()
            
            # Move to completed jobs
            with self.job_lock:
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
                self.completed_jobs[job.job_id] = job
                
                # Clean up progress tracking
                if job.job_id in self.job_progress:
                    del self.job_progress[job.job_id]
            
            # Update global statistics
            self.stats.total_jobs_completed += 1
            self.stats.active_jobs = len(self.active_jobs)
            
            # Calculate success rate
            if self.stats.total_jobs_completed > 0:
                self.stats.success_rate = (
                    self.stats.total_jobs_completed / 
                    (self.stats.total_jobs_completed + self.stats.failed_jobs)
                )
            
            logger.info(f"Job {job.job_id} completed successfully. "
                       f"Extracted: {job.successful_extractions}, Failed: {job.failed_extractions}")
            
        except Exception as e:
            logger.error(f"Error completing job {job.job_id}: {e}")
    
    def _fail_job(self, job: ScrapingJob, error_message: str):
        """Mark job as failed"""
        try:
            job.status = ScrapingJobStatus.FAILED
            job.completed_at = datetime.now()
            job.updated_at = datetime.now()
            job.error_message = error_message
            
            # Move to completed jobs
            with self.job_lock:
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
                self.completed_jobs[job.job_id] = job
                
                # Clean up progress tracking
                if job.job_id in self.job_progress:
                    del self.job_progress[job.job_id]
            
            # Update statistics
            self.stats.failed_jobs += 1
            self.stats.active_jobs = len(self.active_jobs)
            
            logger.error(f"Job {job.job_id} failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Error failing job {job.job_id}: {e}")
    
    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        try:
            with self.job_lock:
                return {
                    "engine_status": "running" if self.is_running else "stopped",
                    "active_jobs": len(self.active_jobs),
                    "queued_jobs": self.job_queue.qsize(),
                    "completed_jobs": len(self.completed_jobs),
                    "worker_threads": len(self.worker_threads),
                    "statistics": asdict(self.stats),
                    "performance_metrics": self.performance_monitor.get_performance_summary(),
                    "configuration": asdict(self.config)
                }
        except Exception as e:
            logger.error(f"Error getting engine statistics: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform engine health check"""
        try:
            health_status = {
                "engine_running": self.is_running,
                "worker_threads_active": len([t for t in self.worker_threads if t.is_alive()]),
                "queue_processing": not self.job_queue.empty() or len(self.active_jobs) > 0,
                "extractors_available": len(self.extractors),
                "validators_available": len(self.content_validators),
                "performance_monitor_active": self.performance_monitor is not None,
                "anti_detection_active": self.anti_detection is not None,
                "memory_usage_mb": self._get_memory_usage(),
                "timestamp": datetime.now()
            }
            
            # Overall health score
            health_factors = [
                health_status["engine_running"],
                health_status["worker_threads_active"] > 0,
                health_status["extractors_available"] > 0,
                health_status["validators_available"] > 0,
                health_status["performance_monitor_active"],
                health_status["anti_detection_active"]
            ]
            
            health_status["health_score"] = sum(health_factors) / len(health_factors)
            health_status["status"] = "healthy" if health_status["health_score"] >= 0.8 else "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
        except Exception:
            return 0.0

# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

def create_scraping_engine(config: Optional[ScrapingEngineConfig] = None) -> ScrapingEngine:
    """
    Create and initialize scraping engine
    
    Args:
        config: Optional engine configuration
        
    Returns:
        Configured ScrapingEngine instance
    """
    return ScrapingEngine(config)

def create_quick_scraping_job(source_type: str, 
                            category: str,
                            subcategory: str,
                            max_questions: int = 100) -> ScrapingJobConfig:
    """
    Create a quick scraping job configuration
    
    Args:
        source_type: Source type (indiabix, geeksforgeeks)
        category: Question category
        subcategory: Question subcategory
        max_questions: Maximum questions to extract
        
    Returns:
        ScrapingJobConfig for the job
    """
    from config.scraping_config import INDIABIX_TARGETS, GEEKSFORGEEKS_TARGETS
    
    # Find matching target
    targets = INDIABIX_TARGETS if source_type == "indiabix" else GEEKSFORGEEKS_TARGETS
    
    matching_target = None
    for target in targets:
        if target.category == category and target.subcategory == subcategory:
            matching_target = target
            break
    
    if not matching_target:
        raise ValueError(f"No target found for {source_type}/{category}/{subcategory}")
    
    return ScrapingJobConfig(
        target=matching_target,
        max_questions=max_questions,
        max_pages=min(max_questions // 10, 50),  # Estimate pages needed
        extraction_method=ContentExtractionMethod.SELENIUM if source_type == "indiabix" else ContentExtractionMethod.PLAYWRIGHT,
        enable_content_validation=True,
        quality_threshold=75.0
    )

# Global engine instance for singleton access
_global_scraping_engine = None

def get_scraping_engine() -> ScrapingEngine:
    """Get global scraping engine instance"""
    global _global_scraping_engine
    
    if _global_scraping_engine is None:
        _global_scraping_engine = create_scraping_engine()
    
    return _global_scraping_engine

def shutdown_scraping_engine():
    """Shutdown global scraping engine"""
    global _global_scraping_engine
    
    if _global_scraping_engine:
        _global_scraping_engine.stop_engine()
        _global_scraping_engine = None