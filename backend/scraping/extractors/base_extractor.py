"""
Base Content Extractor Framework
Comprehensive extraction framework for all scraping sources
"""

import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Import models and utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.scraping_models import (
    RawExtractedQuestion, ProcessedScrapedQuestion, 
    ScrapingTarget, DataSourceConfig, ScrapingSourceType,
    ExtractionQuality, ContentExtractionMethod
)
from scraping.utils.content_validator import ContentValidator, ContentQualityScore
from scraping.utils.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# =============================================================================
# EXTRACTION RESULT CLASSES
# =============================================================================

@dataclass
class ExtractionResult:
    """Single question extraction result"""
    success: bool
    question_data: Optional[RawExtractedQuestion] = None
    error_message: Optional[str] = None
    extraction_time: Optional[float] = None
    source_url: Optional[str] = None
    page_metadata: Optional[Dict[str, Any]] = None

@dataclass
class BatchExtractionResult:
    """Multiple questions extraction result"""
    total_processed: int
    successful_extractions: int
    failed_extractions: int
    extraction_results: List[ExtractionResult]
    batch_start_time: datetime
    batch_end_time: datetime
    total_batch_time: float
    errors: List[str]
    metadata: Dict[str, Any]

@dataclass
class PageExtractionContext:
    """Context information for page extraction"""
    page_url: str
    page_number: int
    category: str
    subcategory: str
    expected_questions: int
    selectors: Dict[str, str]
    extraction_config: Dict[str, Any]

# =============================================================================
# BASE EXTRACTOR ABSTRACT CLASS
# =============================================================================

class BaseContentExtractor(ABC):
    """
    Abstract base class for all content extractors
    Provides common functionality and enforces implementation requirements
    """
    
    def __init__(self, 
                 source_config: DataSourceConfig,
                 content_validator: Optional[ContentValidator] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize base extractor with configuration and utilities
        
        Args:
            source_config: Source-specific configuration
            content_validator: Content validation utility
            performance_monitor: Performance monitoring utility
        """
        self.source_config = source_config
        self.source_name = source_config.name.lower()
        self.source_type = source_config.source_type
        self.base_url = source_config.base_url
        self.selectors = source_config.selectors
        self.extraction_method = source_config.extraction_method
        
        # Initialize utilities
        self.validator = content_validator or ContentValidator(self.source_name)
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        
        # Extraction statistics
        self.extraction_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_extraction_time": 0.0,
            "last_extraction_time": None
        }
        
        logger.info(f"Initialized {self.__class__.__name__} for {self.source_name}")
    
    # =============================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # =============================================================================
    
    @abstractmethod
    def extract_question_from_element(self, question_element: Any, 
                                    extraction_context: PageExtractionContext) -> ExtractionResult:
        """
        Extract a single question from a web element
        
        Args:
            question_element: Web element containing question (Selenium WebElement or Playwright ElementHandle)
            extraction_context: Context information for extraction
            
        Returns:
            ExtractionResult with extracted question data
        """
        pass
    
    @abstractmethod
    def extract_questions_from_page(self, page_source: Any,
                                  extraction_context: PageExtractionContext) -> BatchExtractionResult:
        """
        Extract all questions from a single page
        
        Args:
            page_source: Page source (Selenium driver or Playwright page)
            extraction_context: Context information for extraction
            
        Returns:
            BatchExtractionResult with all extracted questions from page
        """
        pass
    
    @abstractmethod
    def detect_question_format(self, page_source: Any) -> Dict[str, Any]:
        """
        Analyze page structure and detect question format
        
        Args:
            page_source: Page source to analyze
            
        Returns:
            Dictionary with format detection results
        """
        pass
    
    @abstractmethod
    def handle_pagination(self, page_source: Any, 
                         current_page: int, extraction_context: PageExtractionContext) -> Tuple[bool, Optional[str]]:
        """
        Handle pagination navigation
        
        Args:
            page_source: Page source for navigation
            current_page: Current page number
            extraction_context: Context for navigation
            
        Returns:
            Tuple of (has_next_page, next_page_url)
        """
        pass
    
    # =============================================================================
    # COMMON EXTRACTION UTILITIES
    # =============================================================================
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&#8217;': "'",
            '&#8220;': '"',
            '&#8221;': '"'
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text.strip()
    
    def extract_text_from_element(self, element: Any, method: str = "text") -> str:
        """
        Extract text from web element with error handling
        
        Args:
            element: Web element
            method: Extraction method ("text", "innerHTML", "textContent")
            
        Returns:
            Cleaned extracted text
        """
        try:
            if element is None:
                return ""
            
            # Handle different element types
            if hasattr(element, 'text'):  # Selenium WebElement
                raw_text = element.text if method == "text" else element.get_attribute('innerHTML')
            elif hasattr(element, 'text_content'):  # Playwright ElementHandle
                if method == "text":
                    raw_text = element.text_content()
                elif method == "innerHTML":
                    raw_text = element.inner_html()
                else:
                    raw_text = element.text_content()
            else:
                raw_text = str(element)
            
            return self.clean_text(raw_text or "")
            
        except Exception as e:
            logger.warning(f"Error extracting text from element: {e}")
            return ""
    
    def extract_options_from_elements(self, option_elements: List[Any]) -> List[str]:
        """Extract and clean option text from multiple elements"""
        options = []
        
        for element in option_elements:
            option_text = self.extract_text_from_element(element)
            if option_text:
                # Remove option labels like "A)", "1.", etc.
                option_text = re.sub(r'^[A-Za-z0-9]+[.)]\s*', '', option_text)
                options.append(option_text)
        
        return options
    
    def detect_correct_answer(self, question_element: Any, 
                            extraction_context: PageExtractionContext) -> Optional[str]:
        """
        Detect correct answer from question context
        
        Args:
            question_element: Question container element
            extraction_context: Extraction context
            
        Returns:
            Correct answer text or None
        """
        try:
            answer_selectors = [
                extraction_context.selectors.get("correct_answer", ""),
                extraction_context.selectors.get("answer", ""),
                "div.correct-answer",
                "div.solution",
                "div.answer"
            ]
            
            for selector in answer_selectors:
                if not selector:
                    continue
                    
                try:
                    # Handle different driver types
                    if hasattr(question_element, 'find_element'):  # Selenium
                        from selenium.webdriver.common.by import By
                        answer_element = question_element.find_element(By.CSS_SELECTOR, selector)
                    elif hasattr(question_element, 'query_selector'):  # Playwright
                        answer_element = question_element.query_selector(selector)
                    else:
                        continue
                    
                    if answer_element:
                        answer_text = self.extract_text_from_element(answer_element)
                        if answer_text:
                            return answer_text
                            
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting correct answer: {e}")
            return None
    
    def extract_metadata_from_page(self, page_source: Any) -> Dict[str, Any]:
        """Extract metadata from page (difficulty, tags, etc.)"""
        metadata = {}
        
        try:
            # Extract difficulty if available
            difficulty_selectors = [
                self.selectors.get("difficulty_indicator", ""),
                self.selectors.get("difficulty_badge", ""),
                "div.difficulty",
                "span.difficulty",
                ".difficulty-level"
            ]
            
            for selector in difficulty_selectors:
                if selector:
                    try:
                        difficulty_element = self._find_element(page_source, selector)
                        if difficulty_element:
                            metadata["difficulty"] = self.extract_text_from_element(difficulty_element)
                            break
                    except Exception:
                        continue
            
            # Extract company tags if available
            company_selectors = [
                self.selectors.get("company_tags", ""),
                "div.company-tags",
                ".company-tag"
            ]
            
            for selector in company_selectors:
                if selector:
                    try:
                        company_elements = self._find_elements(page_source, selector)
                        if company_elements:
                            metadata["companies"] = [
                                self.extract_text_from_element(elem) 
                                for elem in company_elements
                            ]
                            break
                    except Exception:
                        continue
            
            # Extract topic tags if available
            topic_selectors = [
                self.selectors.get("topic_tags", ""),
                "div.topic-tags",
                ".topic"
            ]
            
            for selector in topic_selectors:
                if selector:
                    try:
                        topic_elements = self._find_elements(page_source, selector)
                        if topic_elements:
                            metadata["topics"] = [
                                self.extract_text_from_element(elem) 
                                for elem in topic_elements
                            ]
                            break
                    except Exception:
                        continue
        
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _find_element(self, page_source: Any, selector: str) -> Any:
        """Find single element with unified interface"""
        try:
            if hasattr(page_source, 'find_element'):  # Selenium
                from selenium.webdriver.common.by import By
                return page_source.find_element(By.CSS_SELECTOR, selector)
            elif hasattr(page_source, 'query_selector'):  # Playwright
                return page_source.query_selector(selector)
        except Exception:
            return None
    
    def _find_elements(self, page_source: Any, selector: str) -> List[Any]:
        """Find multiple elements with unified interface"""
        try:
            if hasattr(page_source, 'find_elements'):  # Selenium
                from selenium.webdriver.common.by import By
                return page_source.find_elements(By.CSS_SELECTOR, selector)
            elif hasattr(page_source, 'query_selector_all'):  # Playwright
                return page_source.query_selector_all(selector)
        except Exception:
            return []
    
    # =============================================================================
    # VALIDATION AND QUALITY ASSESSMENT
    # =============================================================================
    
    def validate_extracted_question(self, question_data: RawExtractedQuestion) -> ContentQualityScore:
        """Validate extracted question using content validator"""
        try:
            question_dict = question_data.dict()
            return self.validator.validate_content(question_dict)
        except Exception as e:
            logger.error(f"Error validating question: {e}")
            # Return default quality score
            from scraping.utils.content_validator import ContentQualityScore, ValidationIssue, ValidationSeverity
            return ContentQualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                clarity_score=0.0,
                validation_issues=[ValidationIssue(
                    rule_name="validation_error",
                    severity=ValidationSeverity.ERROR,
                    message=f"Validation failed: {e}",
                    field_name="general"
                )],
                improvement_suggestions=["Fix validation error"],
                validation_timestamp=datetime.now()
            )
    
    def assess_extraction_quality(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """Assess overall extraction quality"""
        quality_assessment = {
            "extraction_successful": extraction_result.success,
            "has_question_data": extraction_result.question_data is not None,
            "extraction_time": extraction_result.extraction_time or 0.0,
            "quality_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        if extraction_result.question_data:
            # Validate content
            validation_result = self.validate_extracted_question(extraction_result.question_data)
            quality_assessment["quality_score"] = validation_result.overall_score
            quality_assessment["issues"] = [issue.message for issue in validation_result.validation_issues]
            quality_assessment["recommendations"] = validation_result.improvement_suggestions
        
        return quality_assessment
    
    # =============================================================================
    # STATISTICS AND MONITORING
    # =============================================================================
    
    def update_extraction_statistics(self, extraction_result: ExtractionResult):
        """Update extraction statistics"""
        self.extraction_stats["total_processed"] += 1
        
        if extraction_result.success:
            self.extraction_stats["successful_extractions"] += 1
        else:
            self.extraction_stats["failed_extractions"] += 1
        
        if extraction_result.extraction_time:
            # Update average extraction time
            total_time = (self.extraction_stats["average_extraction_time"] * 
                         (self.extraction_stats["total_processed"] - 1) + 
                         extraction_result.extraction_time)
            self.extraction_stats["average_extraction_time"] = total_time / self.extraction_stats["total_processed"]
        
        self.extraction_stats["last_extraction_time"] = datetime.now()
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get current extraction statistics"""
        stats = self.extraction_stats.copy()
        
        if stats["total_processed"] > 0:
            stats["success_rate"] = stats["successful_extractions"] / stats["total_processed"]
            stats["failure_rate"] = stats["failed_extractions"] / stats["total_processed"]
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset extraction statistics"""
        self.extraction_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_extraction_time": 0.0,
            "last_extraction_time": None
        }

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_extraction_context(target: ScrapingTarget, 
                            page_url: str, 
                            page_number: int,
                            additional_config: Optional[Dict[str, Any]] = None) -> PageExtractionContext:
    """
    Create extraction context from scraping target
    
    Args:
        target: ScrapingTarget configuration
        page_url: Current page URL
        page_number: Current page number
        additional_config: Additional configuration parameters
        
    Returns:
        PageExtractionContext for extraction operations
    """
    return PageExtractionContext(
        page_url=page_url,
        page_number=page_number,
        category=target.category,
        subcategory=target.subcategory,
        expected_questions=target.expected_question_count,
        selectors=target.question_selectors,
        extraction_config=additional_config or {}
    )

def merge_batch_results(batch_results: List[BatchExtractionResult]) -> BatchExtractionResult:
    """
    Merge multiple batch extraction results into one
    
    Args:
        batch_results: List of batch results to merge
        
    Returns:
        Merged BatchExtractionResult
    """
    if not batch_results:
        return BatchExtractionResult(
            total_processed=0,
            successful_extractions=0,
            failed_extractions=0,
            extraction_results=[],
            batch_start_time=datetime.now(),
            batch_end_time=datetime.now(),
            total_batch_time=0.0,
            errors=[],
            metadata={}
        )
    
    merged_results = []
    all_errors = []
    total_processed = 0
    successful = 0
    failed = 0
    
    for batch in batch_results:
        merged_results.extend(batch.extraction_results)
        all_errors.extend(batch.errors)
        total_processed += batch.total_processed
        successful += batch.successful_extractions
        failed += batch.failed_extractions
    
    earliest_start = min(batch.batch_start_time for batch in batch_results)
    latest_end = max(batch.batch_end_time for batch in batch_results)
    
    return BatchExtractionResult(
        total_processed=total_processed,
        successful_extractions=successful,
        failed_extractions=failed,
        extraction_results=merged_results,
        batch_start_time=earliest_start,
        batch_end_time=latest_end,
        total_batch_time=(latest_end - earliest_start).total_seconds(),
        errors=all_errors,
        metadata={
            "merged_batches": len(batch_results),
            "merge_timestamp": datetime.now()
        }
    )