"""
High-Volume Web Scraper for 10,000 Questions Target
Enhanced scraping system designed for large-scale question extraction with comprehensive error handling, 
performance optimization, and intelligent batch processing.
"""

import asyncio
import logging
import time
import random
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.scraping_models import (
    ScrapingJob, ScrapingJobStatus, ScrapingTarget, DataSourceConfig,
    ScrapingSourceType, ContentExtractionMethod, ScrapingJobConfig,
    RawExtractedQuestion, ProcessedScrapedQuestion
)
from config.scraping_config import (
    INDIABIX_CONFIG, GEEKSFORGEEKS_CONFIG, 
    INDIABIX_TARGETS, GEEKSFORGEEKS_TARGETS,
    get_source_config, get_source_targets
)
from scraping.drivers.selenium_driver import create_selenium_driver, create_indiabix_selenium_driver
from scraping.extractors.indiabix_extractor import create_indiabix_extractor
from scraping.extractors.geeksforgeeks_extractor import GeeksForGeeksExtractor
from scraping.utils.anti_detection import AntiDetectionManager
from scraping.utils.rate_limiter import ExponentialBackoffLimiter, RateLimitConfig
from scraping.utils.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# =============================================================================
# HIGH-VOLUME SCRAPING CONFIGURATION
# =============================================================================

@dataclass
class HighVolumeScrapingConfig:
    """Configuration for high-volume scraping operations"""
    
    # Target Configuration
    target_questions_total: int = 10000
    target_questions_per_source: int = 5000
    batch_size: int = 50  # Questions per batch
    max_concurrent_extractors: int = 3
    
    # Performance Configuration
    max_pages_per_target: int = 100
    questions_per_page_estimate: int = 10
    request_delay_range: Tuple[float, float] = (2.0, 5.0)
    page_load_timeout: int = 30
    
    # Error Handling
    max_retries_per_page: int = 3
    max_consecutive_failures: int = 5
    recovery_delay_seconds: int = 30
    
    # Quality Control
    enable_real_time_validation: bool = True
    quality_threshold: float = 75.0
    duplicate_check_enabled: bool = True
    
    # Monitoring
    progress_report_interval: int = 100  # Report every N questions
    performance_snapshot_interval: int = 300  # Every 5 minutes
    
    # Storage
    enable_batch_storage: bool = True
    storage_batch_size: int = 25

@dataclass
class ExtractionProgress:
    """Real-time extraction progress tracking"""
    source_name: str
    category: str
    total_targets: int = 0
    completed_targets: int = 0
    current_page: int = 0
    questions_extracted: int = 0
    questions_validated: int = 0
    questions_stored: int = 0
    start_time: datetime = None
    last_update: datetime = None
    estimated_completion: Optional[datetime] = None
    success_rate: float = 0.0
    current_url: str = ""
    status: str = "initializing"

@dataclass
class HighVolumeStats:
    """Comprehensive statistics for high-volume operations"""
    total_questions_extracted: int = 0
    total_questions_validated: int = 0
    total_questions_stored: int = 0
    total_pages_processed: int = 0
    total_targets_completed: int = 0
    sources_processed: Dict[str, int] = None
    categories_processed: Dict[str, int] = None
    avg_extraction_time_per_question: float = 0.0
    avg_validation_time_per_question: float = 0.0
    overall_success_rate: float = 0.0
    start_time: datetime = None
    last_update: datetime = None
    
    def __post_init__(self):
        if self.sources_processed is None:
            self.sources_processed = {}
        if self.categories_processed is None:
            self.categories_processed = {}

# =============================================================================
# HIGH-VOLUME SCRAPER CLASS
# =============================================================================

class HighVolumeScraper:
    """
    High-volume web scraper optimized for extracting 10,000+ questions
    Features intelligent batch processing, error recovery, and real-time monitoring
    """
    
    def __init__(self, config: HighVolumeScrapingConfig = None):
        """Initialize high-volume scraper"""
        self.config = config or HighVolumeScrapingConfig()
        
        # Core components
        self.driver_pool = {}
        self.extractor_pool = {}
        self.anti_detection_managers = {}
        self.rate_limiters = {}
        
        # Monitoring and statistics
        self.stats = HighVolumeStats(start_time=datetime.now())
        self.progress_tracker = {}  # source -> ExtractionProgress
        self.performance_monitor = PerformanceMonitor()
        
        # Threading and concurrency
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_extractors)
        self.extraction_queue = Queue()
        self.result_queue = Queue()
        self.is_running = False
        
        # Storage
        self.extracted_questions = []
        self.batch_storage_buffer = []
        
        logger.info(f"🚀 HighVolumeScraper initialized with target: {self.config.target_questions_total} questions")
    
    def initialize_components(self) -> bool:
        """Initialize all scraping components"""
        try:
            logger.info("🔧 Initializing high-volume scraping components...")
            
            # Initialize for each source
            sources = ["indiabix", "geeksforgeeks"]
            
            for source in sources:
                # Initialize anti-detection
                self.anti_detection_managers[source] = AntiDetectionManager(
                    source_name=source,
                    config={
                        "enable_user_agent_rotation": True,
                        "enable_behavior_simulation": True,
                        "detection_risk_threshold": 0.7
                    }
                )
                
                # Initialize rate limiters
                rate_config = RateLimitConfig(
                    base_delay=2.0 if source == "indiabix" else 1.5,
                    max_delay=10.0,
                    requests_per_second=0.3 if source == "indiabix" else 0.4
                )
                self.rate_limiters[source] = ExponentialBackoffLimiter(rate_config)
                
                # Initialize progress tracking
                self.progress_tracker[source] = ExtractionProgress(
                    source_name=source,
                    category="all",
                    start_time=datetime.now()
                )
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            return False
    
    def create_driver_for_source(self, source_name: str) -> Any:
        """Create optimized driver for specific source"""
        try:
            logger.info(f"🚗 Creating driver for {source_name}")
            
            if source_name.lower() == "indiabix":
                driver = create_indiabix_selenium_driver(
                    anti_detection_config={
                        "source_name": source_name,
                        "enable_user_agent_rotation": True,
                        "enable_behavior_simulation": True
                    }
                )
            else:
                driver = create_selenium_driver(
                    source_name=source_name,
                    browser="chrome",
                    headless=True,
                    page_load_timeout=self.config.page_load_timeout
                )
            
            if driver.initialize_driver():
                self.driver_pool[source_name] = driver
                logger.info(f"✅ Driver created for {source_name}")
                return driver
            else:
                logger.error(f"❌ Failed to initialize driver for {source_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating driver for {source_name}: {e}")
            return None
    
    def create_extractor_for_source(self, source_name: str) -> Any:
        """Create optimized extractor for specific source"""
        try:
            if source_name.lower() == "indiabix":
                extractor = create_indiabix_extractor()
            elif source_name.lower() == "geeksforgeeks":
                from scraping.extractors.geeksforgeeks_extractor import create_geeksforgeeks_extractor
                extractor = create_geeksforgeeks_extractor()
            else:
                logger.error(f"Unknown source: {source_name}")
                return None
            
            self.extractor_pool[source_name] = extractor
            logger.info(f"✅ Extractor created for {source_name}")
            return extractor
            
        except Exception as e:
            logger.error(f"❌ Error creating extractor for {source_name}: {e}")
            return None
    
    async def extract_questions_high_volume(self) -> Dict[str, Any]:
        """
        Main method to extract questions at high volume
        Orchestrates the entire extraction process for 10,000 questions
        """
        try:
            logger.info(f"🎯 Starting high-volume extraction for {self.config.target_questions_total} questions")
            
            # Initialize components
            if not self.initialize_components():
                return {"success": False, "error": "Component initialization failed"}
            
            # Create extraction plan
            extraction_plan = self.create_extraction_plan()
            
            # Start monitoring
            monitoring_task = asyncio.create_task(self.monitor_progress())
            
            # Execute extraction plan
            results = await self.execute_extraction_plan(extraction_plan)
            
            # Stop monitoring
            monitoring_task.cancel()
            
            # Generate final report
            final_report = self.generate_final_report()
            
            logger.info(f"🎉 High-volume extraction completed! Total questions: {self.stats.total_questions_extracted}")
            
            return {
                "success": True,
                "total_questions_extracted": self.stats.total_questions_extracted,
                "total_questions_validated": self.stats.total_questions_validated,
                "total_questions_stored": self.stats.total_questions_stored,
                "extraction_results": results,
                "final_report": final_report,
                "execution_time": (datetime.now() - self.stats.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"❌ High-volume extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_extraction_plan(self) -> List[Dict[str, Any]]:
        """Create comprehensive extraction plan for all sources and targets"""
        extraction_plan = []
        
        # IndiaBix targets (5,000 questions)
        indiabix_targets = get_source_targets("indiabix")
        questions_per_indiabix_target = self.config.target_questions_per_source // len(indiabix_targets)
        
        for target in indiabix_targets:
            extraction_plan.append({
                "source": "indiabix",
                "target": target,
                "target_questions": min(questions_per_indiabix_target, target.expected_question_count),
                "priority": target.priority,
                "estimated_pages": questions_per_indiabix_target // self.config.questions_per_page_estimate
            })
        
        # GeeksforGeeks targets (5,000 questions)  
        geeksforgeeks_targets = get_source_targets("geeksforgeeks")
        questions_per_gfg_target = self.config.target_questions_per_source // len(geeksforgeeks_targets)
        
        for target in geeksforgeeks_targets:
            extraction_plan.append({
                "source": "geeksforgeeks",
                "target": target,
                "target_questions": min(questions_per_gfg_target, target.expected_question_count),
                "priority": target.priority,
                "estimated_pages": questions_per_gfg_target // self.config.questions_per_page_estimate
            })
        
        # Sort by priority
        extraction_plan.sort(key=lambda x: x["priority"])
        
        logger.info(f"📋 Created extraction plan with {len(extraction_plan)} targets")
        for plan_item in extraction_plan:
            logger.info(f"  - {plan_item['source']}: {plan_item['target'].category}/{plan_item['target'].subcategory} "
                       f"(target: {plan_item['target_questions']} questions)")
        
        return extraction_plan
    
    async def execute_extraction_plan(self, extraction_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the extraction plan with concurrent processing"""
        results = []
        self.is_running = True
        
        # Execute targets concurrently within limits
        concurrent_tasks = []
        
        for plan_item in extraction_plan:
            if len(concurrent_tasks) >= self.config.max_concurrent_extractors:
                # Wait for some tasks to complete
                completed_tasks = await asyncio.gather(*concurrent_tasks[:2])
                results.extend(completed_tasks)
                concurrent_tasks = concurrent_tasks[2:]
            
            # Create extraction task
            task = asyncio.create_task(
                self.extract_from_target(plan_item)
            )
            concurrent_tasks.append(task)
        
        # Wait for remaining tasks
        if concurrent_tasks:
            completed_tasks = await asyncio.gather(*concurrent_tasks)
            results.extend(completed_tasks)
        
        self.is_running = False
        return results
    
    async def extract_from_target(self, plan_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract questions from a specific target"""
        source_name = plan_item["source"]
        target = plan_item["target"]
        target_questions = plan_item["target_questions"]
        
        logger.info(f"🎯 Starting extraction from {source_name}: {target.category}/{target.subcategory}")
        
        # Update progress
        progress = self.progress_tracker[source_name]
        progress.category = f"{target.category}/{target.subcategory}"
        progress.current_url = target.target_url
        progress.status = "extracting"
        
        result = {
            "source": source_name,
            "target": target.category + "/" + target.subcategory,
            "target_questions": target_questions,
            "questions_extracted": 0,
            "success": False,
            "error": None,
            "execution_time": 0.0
        }
        
        start_time = datetime.now()
        
        try:
            # Get or create driver and extractor
            driver = self.driver_pool.get(source_name) or self.create_driver_for_source(source_name)
            extractor = self.extractor_pool.get(source_name) or self.create_extractor_for_source(source_name)
            
            if not driver or not extractor:
                result["error"] = "Failed to initialize driver or extractor"
                return result
            
            # Navigate to target URL
            navigation_result = driver.navigate_to_page(target.target_url)
            if not navigation_result.success:
                result["error"] = f"Navigation failed: {navigation_result.error_message}"
                return result
            
            # Extract questions from multiple pages
            total_extracted = 0
            current_page = 1
            consecutive_failures = 0
            
            while (total_extracted < target_questions and 
                   current_page <= self.config.max_pages_per_target and
                   consecutive_failures < self.config.max_consecutive_failures):
                
                # Update progress
                progress.current_page = current_page
                progress.last_update = datetime.now()
                
                # Apply rate limiting
                await self.apply_rate_limiting(source_name)
                
                try:
                    # Extract questions from current page
                    page_result = await self.extract_questions_from_page(
                        driver, extractor, target, current_page
                    )
                    
                    if page_result["success"]:
                        batch_questions = page_result["questions"]
                        total_extracted += len(batch_questions)
                        consecutive_failures = 0
                        
                        # Store questions in batch
                        await self.store_questions_batch(batch_questions)
                        
                        # Update progress
                        progress.questions_extracted += len(batch_questions)
                        self.stats.total_questions_extracted += len(batch_questions)
                        
                        logger.info(f"✅ Page {current_page}: extracted {len(batch_questions)} questions "
                                   f"({total_extracted}/{target_questions} total)")
                        
                        # Check if we have enough questions
                        if total_extracted >= target_questions:
                            break
                        
                        # Navigate to next page
                        has_next, next_url = await self.handle_pagination(driver, extractor, current_page)
                        if not has_next:
                            logger.info(f"📄 No more pages available for {target.category}/{target.subcategory}")
                            break
                        
                        current_page += 1
                    else:
                        consecutive_failures += 1
                        logger.warning(f"⚠️ Page extraction failed: {page_result.get('error', 'Unknown error')}")
                        
                        # Apply recovery delay
                        if consecutive_failures < self.config.max_consecutive_failures:
                            await asyncio.sleep(self.config.recovery_delay_seconds)
                        
                except Exception as e:
                    consecutive_failures += 1
                    logger.error(f"❌ Error extracting from page {current_page}: {e}")
                    
                    if consecutive_failures < self.config.max_consecutive_failures:
                        await asyncio.sleep(self.config.recovery_delay_seconds)
            
            # Update final results
            result["questions_extracted"] = total_extracted
            result["success"] = total_extracted > 0
            result["execution_time"] = (datetime.now() - start_time).total_seconds()
            
            # Update progress
            progress.status = "completed" if result["success"] else "failed"
            progress.success_rate = total_extracted / target_questions if target_questions > 0 else 0.0
            
            logger.info(f"🎉 Completed {source_name}: {target.category}/{target.subcategory} - "
                       f"extracted {total_extracted} questions")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Target extraction failed: {e}")
        
        return result
    
    async def extract_questions_from_page(self, driver: Any, extractor: Any, 
                                        target: Any, page_number: int) -> Dict[str, Any]:
        """Extract questions from a single page"""
        try:
            # Create extraction context
            from scraping.extractors.base_extractor import create_extraction_context
            context = create_extraction_context(
                target=target,
                page_url=driver._get_current_url() if hasattr(driver, '_get_current_url') else target.target_url,
                page_number=page_number
            )
            
            # Extract questions
            batch_result = extractor.extract_questions_from_page(driver.driver, context)
            
            if batch_result.successful_extractions > 0:
                # Convert extraction results to questions
                questions = []
                for extraction_result in batch_result.extraction_results:
                    if extraction_result.success and extraction_result.question_data:
                        questions.append(extraction_result.question_data.dict())
                
                return {
                    "success": True,
                    "questions": questions,
                    "total_processed": batch_result.total_processed,
                    "successful_extractions": batch_result.successful_extractions
                }
            else:
                return {
                    "success": False,
                    "error": f"No questions extracted from page {page_number}",
                    "errors": batch_result.errors
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Page extraction error: {str(e)}"
            }
    
    async def handle_pagination(self, driver: Any, extractor: Any, current_page: int) -> Tuple[bool, Optional[str]]:
        """Handle pagination navigation"""
        try:
            # For now, use simple page increment approach
            # In a full implementation, this would use the extractor's pagination handling
            next_page = current_page + 1
            
            # Check if next page exists (simple heuristic)
            current_url = driver._get_current_url() if hasattr(driver, '_get_current_url') else ""
            
            if "page=" in current_url:
                next_url = current_url.replace(f"page={current_page}", f"page={next_page}")
            else:
                next_url = f"{current_url}{'&' if '?' in current_url else '?'}page={next_page}"
            
            # Try to navigate to next page
            try:
                navigation_result = driver.navigate_to_page(next_url)
                return navigation_result.success, next_url if navigation_result.success else None
            except Exception:
                return False, None
            
        except Exception as e:
            logger.error(f"Pagination error: {e}")
            return False, None
    
    async def apply_rate_limiting(self, source_name: str):
        """Apply intelligent rate limiting"""
        try:
            rate_limiter = self.rate_limiters.get(source_name)
            if rate_limiter:
                delay = random.uniform(*self.config.request_delay_range)
                await asyncio.sleep(delay)
            else:
                # Default delay
                await asyncio.sleep(2.0)
        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
    
    async def store_questions_batch(self, questions: List[Dict[str, Any]]):
        """Store extracted questions in batches"""
        try:
            self.batch_storage_buffer.extend(questions)
            
            if len(self.batch_storage_buffer) >= self.config.storage_batch_size:
                # Store batch to database
                await self.flush_storage_buffer()
            
        except Exception as e:
            logger.error(f"Batch storage error: {e}")
    
    async def flush_storage_buffer(self):
        """Flush storage buffer to database"""
        try:
            if not self.batch_storage_buffer:
                return
            
            # In a real implementation, this would save to MongoDB
            # For now, store in memory and log
            batch_size = len(self.batch_storage_buffer)
            self.extracted_questions.extend(self.batch_storage_buffer)
            self.batch_storage_buffer.clear()
            
            self.stats.total_questions_stored += batch_size
            
            logger.info(f"💾 Stored batch of {batch_size} questions "
                       f"(total stored: {self.stats.total_questions_stored})")
            
        except Exception as e:
            logger.error(f"Storage flush error: {e}")
    
    async def monitor_progress(self):
        """Monitor and report progress in real-time"""
        try:
            while self.is_running:
                await asyncio.sleep(30)  # Report every 30 seconds
                
                total_extracted = sum(p.questions_extracted for p in self.progress_tracker.values())
                progress_percentage = (total_extracted / self.config.target_questions_total) * 100
                
                logger.info(f"📊 PROGRESS: {total_extracted}/{self.config.target_questions_total} questions "
                           f"({progress_percentage:.1f}%)")
                
                # Detailed progress per source
                for source_name, progress in self.progress_tracker.items():
                    if progress.questions_extracted > 0:
                        logger.info(f"  {source_name}: {progress.questions_extracted} questions "
                                   f"(page {progress.current_page}, {progress.status})")
        
        except asyncio.CancelledError:
            logger.info("📊 Progress monitoring stopped")
        except Exception as e:
            logger.error(f"Progress monitoring error: {e}")
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        end_time = datetime.now()
        total_time = (end_time - self.stats.start_time).total_seconds()
        
        return {
            "extraction_summary": {
                "total_questions_extracted": self.stats.total_questions_extracted,
                "total_questions_validated": self.stats.total_questions_validated,
                "total_questions_stored": self.stats.total_questions_stored,
                "target_achievement": (self.stats.total_questions_extracted / self.config.target_questions_total) * 100,
                "total_execution_time_seconds": total_time,
                "questions_per_minute": (self.stats.total_questions_extracted / (total_time / 60)) if total_time > 0 else 0
            },
            "source_breakdown": {
                source: progress.questions_extracted 
                for source, progress in self.progress_tracker.items()
            },
            "performance_metrics": {
                "avg_extraction_time": self.stats.avg_extraction_time_per_question,
                "overall_success_rate": self.stats.overall_success_rate,
                "pages_processed": self.stats.total_pages_processed
            },
            "timestamp": end_time.isoformat()
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Close all drivers
            for source_name, driver in self.driver_pool.items():
                try:
                    driver.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up driver for {source_name}: {e}")
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            # Final storage flush
            if self.batch_storage_buffer:
                asyncio.create_task(self.flush_storage_buffer())
            
            logger.info("🧹 High-volume scraper cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

async def run_high_volume_extraction(target_questions: int = 10000) -> Dict[str, Any]:
    """
    Main function to run high-volume question extraction
    
    Args:
        target_questions: Target number of questions to extract
        
    Returns:
        Dictionary with extraction results and statistics
    """
    config = HighVolumeScrapingConfig(target_questions_total=target_questions)
    scraper = HighVolumeScraper(config)
    
    try:
        # Run extraction
        results = await scraper.extract_questions_high_volume()
        
        # Cleanup
        scraper.cleanup()
        
        return results
        
    except Exception as e:
        logger.error(f"High-volume extraction failed: {e}")
        scraper.cleanup()
        return {"success": False, "error": str(e)}

def create_quick_extraction_test(source: str, max_questions: int = 50) -> Dict[str, Any]:
    """
    Create a quick test extraction for validation
    
    Args:
        source: Source name (indiabix/geeksforgeeks)
        max_questions: Maximum questions to extract for testing
        
    Returns:
        Test results
    """
    async def test_extraction():
        config = HighVolumeScrapingConfig(
            target_questions_total=max_questions,
            target_questions_per_source=max_questions,
            batch_size=10,
            max_concurrent_extractors=1
        )
        scraper = HighVolumeScraper(config)
        
        try:
            # Initialize for single source
            if not scraper.initialize_components():
                return {"success": False, "error": "Component initialization failed"}
            
            # Create simple plan
            targets = get_source_targets(source)
            if not targets:
                return {"success": False, "error": f"No targets found for {source}"}
            
            plan_item = {
                "source": source,
                "target": targets[0],  # Use first target
                "target_questions": max_questions,
                "priority": 1
            }
            
            # Execute extraction
            result = await scraper.extract_from_target(plan_item)
            
            scraper.cleanup()
            return result
            
        except Exception as e:
            scraper.cleanup()
            return {"success": False, "error": str(e)}
    
    return asyncio.run(test_extraction())