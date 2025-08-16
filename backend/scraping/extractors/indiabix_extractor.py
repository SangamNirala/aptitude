"""
IndiaBix Content Extractor
Specialized extractor for IndiaBix question format with comprehensive extraction logic
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import uuid

# Import base extractor and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scraping.extractors.base_extractor import (
    BaseContentExtractor, ExtractionResult, BatchExtractionResult, 
    PageExtractionContext, create_extraction_context
)
from models.scraping_models import (
    RawExtractedQuestion, ProcessedScrapedQuestion, 
    ScrapingTarget, DataSourceConfig, ScrapingSourceType,
    ExtractionQuality, ContentExtractionMethod
)
from scraping.utils.content_validator import ContentValidator
from scraping.utils.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# =============================================================================
# INDIABIX EXTRACTOR CLASS
# =============================================================================

class IndiaBixExtractor(BaseContentExtractor):
    """
    Specialized content extractor for IndiaBix aptitude questions
    Handles IndiaBix-specific format, selectors, and pagination
    """
    
    def __init__(self, 
                 source_config: DataSourceConfig,
                 content_validator: Optional[ContentValidator] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize IndiaBix extractor
        
        Args:
            source_config: IndiaBix source configuration
            content_validator: Content validation utility
            performance_monitor: Performance monitoring utility
        """
        super().__init__(source_config, content_validator, performance_monitor)
        
        # IndiaBix-specific configuration
        self.indiabix_patterns = {
            "option_prefix": re.compile(r'^[A-Da-d][.)]\s*'),
            "question_number": re.compile(r'(?:Question|Q\.?)\s*(\d+)', re.IGNORECASE),
            "difficulty_indicator": re.compile(r'(Easy|Medium|Hard|Difficult)', re.IGNORECASE),
            "explanation_marker": re.compile(r'(?:Explanation|Solution|Answer)[:\s]*', re.IGNORECASE),
            "formula_pattern": re.compile(r'[A-Za-z]\s*=\s*[^,\n]+'),
            "numeric_answer": re.compile(r'\d+(?:\.\d+)?')
        }
        
        # IndiaBix question format detection rules
        self.format_rules = {
            "has_multiple_choice": ["table.bix-tbl-options", "div.bix-options"],
            "has_explanation": ["div.bix-ans-description", "div.explanation"],
            "has_formula": ["div.formula", "span.math"],
            "question_container": ["div.bix-div-container", "div.question-container"]
        }
        
        logger.info("IndiaBix extractor initialized with specialized patterns and rules")
    
    # =============================================================================
    # CORE EXTRACTION METHODS
    # =============================================================================
    
    def extract_question_from_element(self, question_element: Any, 
                                    extraction_context: PageExtractionContext) -> ExtractionResult:
        """
        Extract single question from IndiaBix question element
        
        Args:
            question_element: Web element containing question
            extraction_context: Context information for extraction
            
        Returns:
            ExtractionResult with extracted IndiaBix question data
        """
        start_time = datetime.now()
        
        try:
            with self.performance_monitor.monitor_operation("indiabix_question_extraction"):
                # Extract question components
                question_text = self._extract_question_text(question_element, extraction_context)
                options = self._extract_question_options(question_element, extraction_context)
                correct_answer = self._extract_correct_answer(question_element, extraction_context)
                explanation = self._extract_explanation(question_element, extraction_context)
                
                # Extract metadata
                metadata = self._extract_question_metadata(question_element, extraction_context)
                
                # Validate minimum requirements
                if not question_text or len(question_text.strip()) < 10:
                    return ExtractionResult(
                        success=False,
                        error_message="Question text too short or missing",
                        extraction_time=(datetime.now() - start_time).total_seconds(),
                        source_url=extraction_context.page_url
                    )
                
                # Create raw extracted question
                raw_question = RawExtractedQuestion(
                    question_id=str(uuid.uuid4()),
                    source_type=ScrapingSourceType.INDIABIX,
                    source_url=extraction_context.page_url,
                    category=extraction_context.category,
                    subcategory=extraction_context.subcategory,
                    question_text=question_text,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    difficulty_level=metadata.get("difficulty", "medium"),
                    tags=metadata.get("tags", []),
                    companies=metadata.get("companies", []),
                    extraction_timestamp=datetime.now(),
                    raw_html=self._get_element_html(question_element),
                    extraction_metadata={
                        "page_number": extraction_context.page_number,
                        "extractor": "IndiaBixExtractor",
                        "extraction_method": "selenium",
                        **metadata
                    }
                )
                
                extraction_time = (datetime.now() - start_time).total_seconds()
                
                return ExtractionResult(
                    success=True,
                    question_data=raw_question,
                    extraction_time=extraction_time,
                    source_url=extraction_context.page_url,
                    page_metadata=metadata
                )
        
        except Exception as e:
            logger.error(f"Error extracting IndiaBix question: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Extraction failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
    def extract_questions_from_page(self, page_source: Any,
                                  extraction_context: PageExtractionContext) -> BatchExtractionResult:
        """
        Extract all questions from IndiaBix page
        
        Args:
            page_source: Page source (Selenium driver)
            extraction_context: Context information for extraction
            
        Returns:
            BatchExtractionResult with all extracted questions from page
        """
        batch_start = datetime.now()
        extraction_results = []
        errors = []
        
        try:
            with self.performance_monitor.monitor_operation("indiabix_page_extraction"):
                # Find question containers
                question_containers = self._find_question_containers(page_source)
                
                if not question_containers:
                    logger.warning(f"No question containers found on page: {extraction_context.page_url}")
                    return self._create_empty_batch_result(batch_start, ["No question containers found"])
                
                logger.info(f"Found {len(question_containers)} question containers on IndiaBix page")
                
                # Extract each question
                for i, question_element in enumerate(question_containers):
                    try:
                        extraction_result = self.extract_question_from_element(
                            question_element, extraction_context
                        )
                        extraction_results.append(extraction_result)
                        
                        # Update statistics
                        self.update_extraction_statistics(extraction_result)
                        
                        if not extraction_result.success:
                            errors.append(f"Question {i+1}: {extraction_result.error_message}")
                    
                    except Exception as e:
                        error_msg = f"Error processing question {i+1}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                        # Create failed extraction result
                        extraction_results.append(ExtractionResult(
                            success=False,
                            error_message=error_msg,
                            source_url=extraction_context.page_url
                        ))
                
                batch_end = datetime.now()
                successful_count = sum(1 for r in extraction_results if r.success)
                
                return BatchExtractionResult(
                    total_processed=len(extraction_results),
                    successful_extractions=successful_count,
                    failed_extractions=len(extraction_results) - successful_count,
                    extraction_results=extraction_results,
                    batch_start_time=batch_start,
                    batch_end_time=batch_end,
                    total_batch_time=(batch_end - batch_start).total_seconds(),
                    errors=errors,
                    metadata={
                        "page_url": extraction_context.page_url,
                        "page_number": extraction_context.page_number,
                        "category": extraction_context.category,
                        "subcategory": extraction_context.subcategory,
                        "extractor": "IndiaBixExtractor",
                        "question_containers_found": len(question_containers)
                    }
                )
        
        except Exception as e:
            logger.error(f"Error in IndiaBix page extraction: {e}")
            return self._create_empty_batch_result(batch_start, [f"Page extraction failed: {str(e)}"])
    
    def detect_question_format(self, page_source: Any) -> Dict[str, Any]:
        """
        Analyze IndiaBix page structure and detect question format
        
        Args:
            page_source: Page source to analyze
            
        Returns:
            Dictionary with format detection results
        """
        format_info = {
            "source_type": "indiabix",
            "has_multiple_choice": False,
            "has_explanation": False,
            "has_formula": False,
            "question_count": 0,
            "pagination_type": "numbered",
            "selectors_found": {},
            "confidence_score": 0.0
        }
        
        try:
            # Check for IndiaBix-specific elements
            confidence_factors = []
            
            # Check for question containers
            for selector in self.format_rules["question_container"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["question_count"] = len(elements)
                    format_info["selectors_found"]["question_container"] = selector
                    confidence_factors.append(0.3)
                    break
            
            # Check for multiple choice options
            for selector in self.format_rules["has_multiple_choice"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_multiple_choice"] = True
                    format_info["selectors_found"]["options"] = selector
                    confidence_factors.append(0.25)
                    break
            
            # Check for explanations
            for selector in self.format_rules["has_explanation"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_explanation"] = True
                    format_info["selectors_found"]["explanation"] = selector
                    confidence_factors.append(0.2)
                    break
            
            # Check for IndiaBix-specific navigation
            pagination_selectors = [
                "div.bix-pagination",
                "a.bix-btn-next",
                "div.page-navigation"
            ]
            
            for selector in pagination_selectors:
                element = self._find_element(page_source, selector)
                if element:
                    format_info["selectors_found"]["pagination"] = selector
                    confidence_factors.append(0.15)
                    break
            
            # Check for IndiaBix branding/structure
            branding_selectors = [
                "div.bix-div-container",
                "table.bix-tbl-options",
                "div.bix-ans-description"
            ]
            
            branding_found = 0
            for selector in branding_selectors:
                if self._find_element(page_source, selector):
                    branding_found += 1
            
            if branding_found >= 2:
                confidence_factors.append(0.1)
            
            # Calculate confidence score
            format_info["confidence_score"] = min(sum(confidence_factors), 1.0)
            
            logger.info(f"IndiaBix format detection: {format_info['confidence_score']:.2f} confidence, "
                       f"{format_info['question_count']} questions found")
        
        except Exception as e:
            logger.error(f"Error in IndiaBix format detection: {e}")
            format_info["error"] = str(e)
        
        return format_info
    
    def handle_pagination(self, page_source: Any, 
                         current_page: int, extraction_context: PageExtractionContext) -> Tuple[bool, Optional[str]]:
        """
        Handle IndiaBix pagination navigation
        
        Args:
            page_source: Page source for navigation
            current_page: Current page number
            extraction_context: Context for navigation
            
        Returns:
            Tuple of (has_next_page, next_page_url)
        """
        try:
            # IndiaBix uses numbered pagination
            next_page_url = None
            has_next = False
            
            # Method 1: Look for "Next" button
            next_button_selectors = [
                "a.bix-btn-next",
                "a[title='Next']",
                "a.next-page",
                "div.bix-pagination a:contains('Next')"
            ]
            
            for selector in next_button_selectors:
                next_button = self._find_element(page_source, selector)
                if next_button:
                    # Check if button is enabled
                    if hasattr(next_button, 'get_attribute'):  # Selenium
                        href = next_button.get_attribute('href')
                        class_attr = next_button.get_attribute('class') or ""
                    else:  # Playwright
                        href = next_button.get_attribute('href')
                        class_attr = next_button.get_attribute('class') or ""
                    
                    if href and 'disabled' not in class_attr:
                        next_page_url = href
                        has_next = True
                        break
            
            # Method 2: Construct next page URL from pattern
            if not has_next and extraction_context.page_url:
                base_pattern = self.source_config.pagination_config.get("base_url_pattern", "")
                if base_pattern:
                    next_page_num = current_page + 1
                    try:
                        next_page_url = base_pattern.format(
                            base_url=self.base_url,
                            category=extraction_context.subcategory,
                            page=next_page_num
                        )
                        
                        # Check if we've reached max pages
                        max_pages = self.source_config.pagination_config.get("max_pages_per_category", 50)
                        if next_page_num <= max_pages:
                            has_next = True
                    except Exception as e:
                        logger.warning(f"Error constructing next page URL: {e}")
            
            # Method 3: Check page numbers in pagination
            if not has_next:
                page_number_selectors = [
                    "div.bix-pagination a",
                    "div.pagination a",
                    ".page-numbers a"
                ]
                
                for selector in page_number_selectors:
                    page_links = self._find_elements(page_source, selector)
                    if page_links:
                        # Look for page number higher than current
                        for link in page_links:
                            link_text = self.extract_text_from_element(link).strip()
                            if link_text.isdigit():
                                page_num = int(link_text)
                                if page_num == current_page + 1:
                                    if hasattr(link, 'get_attribute'):  # Selenium
                                        next_page_url = link.get_attribute('href')
                                    else:  # Playwright
                                        next_page_url = link.get_attribute('href')
                                    
                                    if next_page_url:
                                        has_next = True
                                        break
                        if has_next:
                            break
            
            logger.info(f"IndiaBix pagination: Current page {current_page}, "
                       f"Has next: {has_next}, Next URL: {next_page_url}")
            
            return has_next, next_page_url
        
        except Exception as e:
            logger.error(f"Error handling IndiaBix pagination: {e}")
            return False, None
    
    # =============================================================================
    # INDIABIX-SPECIFIC EXTRACTION METHODS
    # =============================================================================
    
    def _extract_question_text(self, question_element: Any, 
                             extraction_context: PageExtractionContext) -> str:
        """Extract question text from IndiaBix question element"""
        selectors = [
            extraction_context.selectors.get("question_text", ""),
            "div.bix-td-qtxt",
            "div.question-text",
            "div.bix-div-container p"
        ]
        
        for selector in selectors:
            if not selector:
                continue
                
            try:
                question_elem = self._find_element(question_element, selector)
                if question_elem:
                    question_text = self.extract_text_from_element(question_elem)
                    if question_text and len(question_text.strip()) > 5:
                        # Clean IndiaBix-specific formatting
                        question_text = self._clean_indiabix_question_text(question_text)
                        return question_text
            except Exception:
                continue
        
        return ""
    
    def _extract_question_options(self, question_element: Any, 
                                extraction_context: PageExtractionContext) -> List[str]:
        """Extract multiple choice options from IndiaBix question"""
        selectors = [
            extraction_context.selectors.get("options", ""),
            "table.bix-tbl-options td",
            "div.bix-options li",
            "div.options label"
        ]
        
        for selector in selectors:
            if not selector:
                continue
                
            try:
                option_elements = self._find_elements(question_element, selector)
                if option_elements and len(option_elements) >= 2:
                    options = []
                    for elem in option_elements:
                        option_text = self.extract_text_from_element(elem)
                        if option_text:
                            # Remove IndiaBix option prefixes
                            option_text = self.indiabix_patterns["option_prefix"].sub("", option_text).strip()
                            if option_text:  # Ensure not empty after cleaning
                                options.append(option_text)
                    
                    if len(options) >= 2:  # Valid options found
                        return options[:4]  # Limit to 4 options maximum
            except Exception:
                continue
        
        return []
    
    def _extract_correct_answer(self, question_element: Any, 
                              extraction_context: PageExtractionContext) -> Optional[str]:
        """Extract correct answer from IndiaBix question"""
        selectors = [
            extraction_context.selectors.get("answer", ""),
            extraction_context.selectors.get("correct_answer", ""),
            "div.bix-ans-description",
            "div.correct-answer",
            "div.solution"
        ]
        
        for selector in selectors:
            if not selector:
                continue
                
            try:
                answer_elem = self._find_element(question_element, selector)
                if answer_elem:
                    answer_text = self.extract_text_from_element(answer_elem)
                    if answer_text:
                        # Clean and extract answer
                        answer_text = self._clean_indiabix_answer_text(answer_text)
                        return answer_text
            except Exception:
                continue
        
        return None
    
    def _extract_explanation(self, question_element: Any, 
                           extraction_context: PageExtractionContext) -> Optional[str]:
        """Extract explanation/solution from IndiaBix question"""
        selectors = [
            extraction_context.selectors.get("explanation", ""),
            "div.bix-ans-description p",
            "div.explanation",
            "div.solution-text"
        ]
        
        for selector in selectors:
            if not selector:
                continue
                
            try:
                explanation_elem = self._find_element(question_element, selector)
                if explanation_elem:
                    explanation_text = self.extract_text_from_element(explanation_elem)
                    if explanation_text and len(explanation_text.strip()) > 10:
                        # Clean explanation text
                        explanation_text = self._clean_indiabix_explanation(explanation_text)
                        return explanation_text
            except Exception:
                continue
        
        return None
    
    def _extract_question_metadata(self, question_element: Any, 
                                 extraction_context: PageExtractionContext) -> Dict[str, Any]:
        """Extract metadata specific to IndiaBix questions"""
        metadata = {}
        
        try:
            # Extract difficulty level
            difficulty_selectors = [
                "div.bix-difficulty",
                "span.difficulty",
                "div.difficulty-level"
            ]
            
            for selector in difficulty_selectors:
                elem = self._find_element(question_element, selector)
                if elem:
                    difficulty_text = self.extract_text_from_element(elem)
                    if difficulty_text:
                        match = self.indiabix_patterns["difficulty_indicator"].search(difficulty_text)
                        if match:
                            metadata["difficulty"] = match.group(1).lower()
                            break
            
            # Extract question number if available
            question_number_selectors = [
                "div.bix-question-number",
                "span.question-num",
                "div.q-number"
            ]
            
            for selector in question_number_selectors:
                elem = self._find_element(question_element, selector)
                if elem:
                    number_text = self.extract_text_from_element(elem)
                    if number_text:
                        match = self.indiabix_patterns["question_number"].search(number_text)
                        if match:
                            metadata["question_number"] = int(match.group(1))
                            break
            
            # Check for formulas
            question_text = self._extract_question_text(question_element, extraction_context)
            if question_text:
                formulas = self.indiabix_patterns["formula_pattern"].findall(question_text)
                if formulas:
                    metadata["has_formula"] = True
                    metadata["formulas"] = formulas
            
            # Add IndiaBix-specific tags
            tags = ["indiabix", extraction_context.category]
            if extraction_context.subcategory:
                tags.append(extraction_context.subcategory)
            
            if metadata.get("has_formula"):
                tags.append("formula")
            
            metadata["tags"] = tags
        
        except Exception as e:
            logger.warning(f"Error extracting IndiaBix metadata: {e}")
        
        return metadata
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _find_question_containers(self, page_source: Any) -> List[Any]:
        """Find all question containers on IndiaBix page"""
        container_selectors = [
            "div.bix-div-container",
            "div.question-container",
            "div.quiz-question"
        ]
        
        for selector in container_selectors:
            containers = self._find_elements(page_source, selector)
            if containers:
                return containers
        
        return []
    
    def _clean_indiabix_question_text(self, text: str) -> str:
        """Clean IndiaBix-specific formatting from question text"""
        if not text:
            return ""
        
        # Remove question numbering
        text = self.indiabix_patterns["question_number"].sub("", text)
        
        # Clean common IndiaBix artifacts
        text = re.sub(r'^\s*Q\.\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*\d+\.\s*', '', text)
        
        return self.clean_text(text)
    
    def _clean_indiabix_answer_text(self, text: str) -> str:
        """Clean IndiaBix-specific formatting from answer text"""
        if not text:
            return ""
        
        # Remove answer markers
        text = self.indiabix_patterns["explanation_marker"].sub("", text)
        
        # Extract main answer if it's in a structured format
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Explanation:', 'Solution:', 'Answer:')):
                if len(line) > 5:  # Ensure it's substantial
                    return self.clean_text(line)
        
        return self.clean_text(text)
    
    def _clean_indiabix_explanation(self, text: str) -> str:
        """Clean IndiaBix-specific formatting from explanation text"""
        if not text:
            return ""
        
        # Remove explanation headers
        text = self.indiabix_patterns["explanation_marker"].sub("", text)
        
        return self.clean_text(text)
    
    def _get_element_html(self, element: Any) -> str:
        """Get HTML content of element for debugging"""
        try:
            if hasattr(element, 'get_attribute'):  # Selenium
                return element.get_attribute('outerHTML') or ""
            elif hasattr(element, 'outer_html'):  # Playwright
                return element.outer_html() or ""
        except Exception:
            return ""
        
        return ""
    
    def _create_empty_batch_result(self, start_time: datetime, errors: List[str]) -> BatchExtractionResult:
        """Create empty batch result for error cases"""
        end_time = datetime.now()
        return BatchExtractionResult(
            total_processed=0,
            successful_extractions=0,
            failed_extractions=0,
            extraction_results=[],
            batch_start_time=start_time,
            batch_end_time=end_time,
            total_batch_time=(end_time - start_time).total_seconds(),
            errors=errors,
            metadata={"extractor": "IndiaBixExtractor", "status": "failed"}
        )

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_indiabix_extractor(content_validator: Optional[ContentValidator] = None,
                             performance_monitor: Optional[PerformanceMonitor] = None) -> IndiaBixExtractor:
    """
    Create optimized IndiaBix extractor with proper configuration
    
    Args:
        content_validator: Optional content validator
        performance_monitor: Optional performance monitor
        
    Returns:
        Configured IndiaBixExtractor instance
    """
    from config.scraping_config import INDIABIX_CONFIG
    
    # Create specialized validator if none provided
    if content_validator is None:
        from scraping.utils.content_validator import create_indiabix_validator
        content_validator = create_indiabix_validator()
    
    # Create performance monitor if none provided
    if performance_monitor is None:
        from scraping.utils.performance_monitor import create_extraction_monitor
        performance_monitor = create_extraction_monitor()
    
    return IndiaBixExtractor(
        source_config=INDIABIX_CONFIG,
        content_validator=content_validator,
        performance_monitor=performance_monitor
    )

def extract_sample_indiabix_questions(driver: Any, 
                                    target: ScrapingTarget,
                                    max_questions: int = 10) -> BatchExtractionResult:
    """
    Convenience function to extract sample questions from IndiaBix
    
    Args:
        driver: Selenium or Playwright driver
        target: ScrapingTarget for IndiaBix
        max_questions: Maximum number of questions to extract
        
    Returns:
        BatchExtractionResult with extracted questions
    """
    extractor = create_indiabix_extractor()
    
    # Create extraction context
    context = create_extraction_context(
        target=target,
        page_url=target.target_url,
        page_number=1
    )
    
    try:
        # Navigate to target URL
        if hasattr(driver, 'get'):  # Selenium
            driver.get(target.target_url)
        elif hasattr(driver, 'goto'):  # Playwright
            driver.goto(target.target_url)
        
        # Extract questions
        batch_result = extractor.extract_questions_from_page(driver, context)
        
        # Limit to requested number
        if batch_result.successful_extractions > max_questions:
            batch_result.extraction_results = batch_result.extraction_results[:max_questions]
            batch_result.total_processed = max_questions
            batch_result.successful_extractions = min(batch_result.successful_extractions, max_questions)
        
        return batch_result
        
    except Exception as e:
        logger.error(f"Error extracting sample IndiaBix questions: {e}")
        return extractor._create_empty_batch_result(datetime.now(), [str(e)])