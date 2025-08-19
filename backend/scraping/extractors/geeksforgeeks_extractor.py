"""
GeeksforGeeks Content Extractor
Specialized extractor for GeeksforGeeks question format with dynamic content handling
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
# GEEKSFORGEEKS EXTRACTOR CLASS
# =============================================================================

class GeeksForGeeksExtractor(BaseContentExtractor):
    """
    Specialized content extractor for GeeksforGeeks questions
    Handles dynamic content, infinite scroll, and multiple question formats
    """
    
    def __init__(self, 
                 source_config: DataSourceConfig,
                 content_validator: Optional[ContentValidator] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize GeeksforGeeks extractor
        
        Args:
            source_config: GeeksforGeeks source configuration
            content_validator: Content validation utility
            performance_monitor: Performance monitoring utility
        """
        super().__init__(source_config, content_validator, performance_monitor)
        
        # GeeksforGeeks-specific patterns
        self.gfg_patterns = {
            "option_pattern": re.compile(r'^[A-Da-d][.)]\s*'),
            "code_block": re.compile(r'```[\s\S]*?```|<code>[\s\S]*?</code>'),
            "difficulty_levels": re.compile(r'(Easy|Medium|Hard|School|Basic)', re.IGNORECASE),
            "company_tags": re.compile(r'(Amazon|Google|Microsoft|Facebook|Apple|Netflix)', re.IGNORECASE),
            "topic_extraction": re.compile(r'(Array|String|Tree|Graph|DP|Dynamic Programming)', re.IGNORECASE),
            "numeric_answer": re.compile(r'\d+(?:\.\d+)?'),
            "formula_pattern": re.compile(r'O\([^)]+\)|[A-Za-z]\s*=\s*[^,\n]+')
        }
        
        # GeeksforGeeks question format detection
        self.format_rules = {
            "has_code": ["pre", "code", ".highlight"],
            "has_multiple_choice": [".mcq-options", ".options", "input[type='radio']"],
            "has_explanation": [".solution-approach", ".article-content", ".explanation"],
            "is_programming": [".problem-statement", ".code-editor", ".language-selection"],
            "question_containers": [".problem-container", ".mcq-container", ".quiz-question", ".practice-problem"]
        }
        
        logger.info("GeeksforGeeks extractor initialized with dynamic content handling")
    
    # =============================================================================
    # CORE EXTRACTION METHODS
    # =============================================================================
    
    def extract_question_from_element(self, question_element: Any, 
                                    extraction_context: PageExtractionContext) -> ExtractionResult:
        """
        Extract single question from GeeksforGeeks question element
        
        Args:
            question_element: Web element containing question
            extraction_context: Context information for extraction
            
        Returns:
            ExtractionResult with extracted GeeksforGeeks question data
        """
        start_time = datetime.now()
        
        try:
            with self.performance_monitor.monitor_operation("gfg_question_extraction"):
                # Extract question components
                question_text = self._extract_question_text(question_element, extraction_context)
                options = self._extract_question_options(question_element, extraction_context)
                correct_answer = self._extract_correct_answer(question_element, extraction_context)
                explanation = self._extract_explanation(question_element, extraction_context)
                metadata = self._extract_question_metadata(question_element, extraction_context)
                
                # Validate extracted data
                if not question_text or len(question_text.strip()) < 10:
                    return ExtractionResult(
                        success=False,
                        error_message="Question text too short or missing",
                        extraction_time=(datetime.now() - start_time).total_seconds()
                    )
                
                if len(options) < 2:
                    return ExtractionResult(
                        success=False,
                        error_message="Insufficient options found",
                        extraction_time=(datetime.now() - start_time).total_seconds()
                    )
                
                # Create RawExtractedQuestion
                raw_question = RawExtractedQuestion(
                    source_id=extraction_context.extraction_config.get("source_id", "geeksforgeeks"),
                    source_url=extraction_context.page_url,
                    job_id=extraction_context.extraction_config.get("job_id", str(uuid.uuid4())),
                    raw_question_text=question_text,
                    raw_options=options,
                    raw_correct_answer=correct_answer,
                    raw_explanation=explanation,
                    page_number=extraction_context.page_number,
                    extraction_method=ContentExtractionMethod.SELENIUM,
                    detected_category=extraction_context.category,
                    detected_difficulty=metadata.get("difficulty"),
                    extraction_confidence=0.8,  # GeeksforGeeks generally has good structure
                    completeness_score=self._calculate_completeness_score(question_text, options, correct_answer, explanation)
                )
                
                extraction_time = (datetime.now() - start_time).total_seconds()
                
                # Update statistics
                self.update_extraction_statistics(ExtractionResult(
                    success=True,
                    question_data=raw_question,
                    extraction_time=extraction_time
                ))
                
                return ExtractionResult(
                    success=True,
                    question_data=raw_question,
                    extraction_time=extraction_time,
                    source_url=extraction_context.page_url,
                    page_metadata=metadata
                )
        
        except Exception as e:
            extraction_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"GeeksforGeeks question extraction failed: {e}")
            
            return ExtractionResult(
                success=False,
                error_message=str(e),
                extraction_time=extraction_time
            )
    
    def extract_questions_from_page(self, page_source: Any,
                                  extraction_context: PageExtractionContext) -> BatchExtractionResult:
        """
        Extract all questions from GeeksforGeeks page
        
        Args:
            page_source: Page source (Selenium driver)
            extraction_context: Context information for extraction
            
        Returns:
            BatchExtractionResult with all extracted questions
        """
        start_time = datetime.now()
        extraction_results = []
        errors = []
        
        try:
            with self.performance_monitor.monitor_operation("gfg_batch_extraction"):
                # Wait for dynamic content to load
                self._wait_for_dynamic_content(page_source)
                
                # Find question containers
                question_containers = self._find_question_containers(page_source)
                
                if not question_containers:
                    errors.append("No question containers found on GeeksforGeeks page")
                    return self._create_empty_batch_result(start_time, errors)
                
                logger.info(f"Found {len(question_containers)} question containers on GeeksforGeeks page")
                
                # Extract from each container
                for i, container in enumerate(question_containers):
                    try:
                        # Update extraction context for current question
                        context_copy = PageExtractionContext(
                            page_url=extraction_context.page_url,
                            page_number=extraction_context.page_number,
                            category=extraction_context.category,
                            subcategory=extraction_context.subcategory,
                            expected_questions=extraction_context.expected_questions,
                            selectors=extraction_context.selectors,
                            extraction_config={
                                **extraction_context.extraction_config,
                                "question_index": i,
                                "source_id": "geeksforgeeks"
                            }
                        )
                        
                        # Extract question
                        result = self.extract_question_from_element(container, context_copy)
                        extraction_results.append(result)
                        
                        if result.success:
                            logger.debug(f"✅ GeeksforGeeks question {i+1} extracted successfully")
                        else:
                            logger.warning(f"⚠️ GeeksforGeeks question {i+1} extraction failed: {result.error_message}")
                            errors.append(f"Question {i+1}: {result.error_message}")
                    
                    except Exception as e:
                        error_msg = f"Error extracting GeeksforGeeks question {i+1}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        
                        extraction_results.append(ExtractionResult(
                            success=False,
                            error_message=str(e)
                        ))
                
                end_time = datetime.now()
                successful = sum(1 for r in extraction_results if r.success)
                failed = len(extraction_results) - successful
                
                return BatchExtractionResult(
                    total_processed=len(extraction_results),
                    successful_extractions=successful,
                    failed_extractions=failed,
                    extraction_results=extraction_results,
                    batch_start_time=start_time,
                    batch_end_time=end_time,
                    total_batch_time=(end_time - start_time).total_seconds(),
                    errors=errors,
                    metadata={
                        "extractor": "GeeksForGeeksExtractor",
                        "page_url": extraction_context.page_url,
                        "question_containers_found": len(question_containers)
                    }
                )
        
        except Exception as e:
            errors.append(f"Batch extraction error: {str(e)}")
            logger.error(f"GeeksforGeeks batch extraction failed: {e}")
            return self._create_empty_batch_result(start_time, errors)
    
    def detect_question_format(self, page_source: Any) -> Dict[str, Any]:
        """Analyze GeeksforGeeks page structure and detect question format"""
        format_info = {
            "has_multiple_choice": False,
            "has_code_blocks": False,
            "has_programming_problems": False,
            "has_explanations": False,
            "question_count_estimate": 0,
            "detected_categories": [],
            "page_type": "unknown"
        }
        
        try:
            # Check for multiple choice questions
            for selector in self.format_rules["has_multiple_choice"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_multiple_choice"] = True
                    break
            
            # Check for code blocks
            for selector in self.format_rules["has_code"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_code_blocks"] = True
                    break
            
            # Check for programming problems
            for selector in self.format_rules["is_programming"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_programming_problems"] = True
                    break
            
            # Check for explanations
            for selector in self.format_rules["has_explanation"]:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_explanations"] = True
                    break
            
            # Estimate question count
            question_containers = self._find_question_containers(page_source)
            format_info["question_count_estimate"] = len(question_containers)
            
            # Determine page type
            if format_info["has_multiple_choice"]:
                format_info["page_type"] = "multiple_choice_quiz"
            elif format_info["has_programming_problems"]:
                format_info["page_type"] = "programming_practice"
            else:
                format_info["page_type"] = "article_with_questions"
            
            logger.info(f"GeeksforGeeks format detected: {format_info['page_type']} "
                       f"with {format_info['question_count_estimate']} questions")
        
        except Exception as e:
            logger.error(f"GeeksforGeeks format detection failed: {e}")
        
        return format_info
    
    def handle_pagination(self, page_source: Any, 
                         current_page: int, extraction_context: PageExtractionContext) -> Tuple[bool, Optional[str]]:
        """Handle GeeksforGeeks pagination (often infinite scroll)"""
        try:
            # Check for traditional pagination first
            pagination_selectors = [
                "div.pagination a",
                "nav.pagination a", 
                ".pagination-nav a",
                "a.next-problem",
                "button.load-more"
            ]
            
            has_next = False
            next_page_url = None
            
            for selector in pagination_selectors:
                try:
                    pagination_elements = self._find_elements(page_source, selector)
                    
                    if pagination_elements:
                        for element in pagination_elements:
                            text = self.extract_text_from_element(element).lower()
                            
                            # Look for "next" or page numbers
                            if ("next" in text or ">" in text or 
                                str(current_page + 1) in text):
                                
                                # Get URL
                                if hasattr(element, 'get_attribute'):  # Selenium
                                    next_page_url = element.get_attribute('href')
                                else:  # Playwright
                                    next_page_url = element.get_attribute('href')
                                
                                if next_page_url:
                                    has_next = True
                                    break
                        
                        if has_next:
                            break
                
                except Exception:
                    continue
            
            # If no traditional pagination, try infinite scroll
            if not has_next:
                has_next = self._handle_infinite_scroll(page_source)
            
            logger.info(f"GeeksforGeeks pagination: Current page {current_page}, "
                       f"Has next: {has_next}, Next URL: {next_page_url}")
            
            return has_next, next_page_url
        
        except Exception as e:
            logger.error(f"Error handling GeeksforGeeks pagination: {e}")
            return False, None
    
    # =============================================================================
    # GEEKSFORGEEKS-SPECIFIC EXTRACTION METHODS
    # =============================================================================
    
    def _wait_for_dynamic_content(self, page_source: Any):
        """Wait for dynamic content to load on GeeksforGeeks"""
        try:
            import time
            
            # Wait for common loading indicators to disappear
            loading_selectors = [
                ".spinner",
                ".loading",
                ".loader",
                "[data-loading='true']"
            ]
            
            max_wait_time = 10  # seconds
            wait_interval = 0.5
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                loading_found = False
                
                for selector in loading_selectors:
                    elements = self._find_elements(page_source, selector)
                    if elements:
                        loading_found = True
                        break
                
                if not loading_found:
                    break
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            # Additional wait for content stabilization
            time.sleep(1.0)
            
        except Exception as e:
            logger.warning(f"Error waiting for dynamic content: {e}")
    
    def _extract_question_text(self, question_element: Any, 
                             extraction_context: PageExtractionContext) -> str:
        """Extract question text from GeeksforGeeks question element"""
        selectors = [
            extraction_context.selectors.get("question_text", ""),
            "div.problem-statement",
            "div.question-text",
            "div.problemStatement p",
            "div.quiz-question .question",
            "p.question-content"
        ]
        
        for selector in selectors:
            if not selector:
                continue
                
            try:
                question_elem = self._find_element(question_element, selector)
                if question_elem:
                    question_text = self.extract_text_from_element(question_elem)
                    if question_text and len(question_text.strip()) > 5:
                        # Clean GeeksforGeeks-specific formatting
                        question_text = self._clean_gfg_question_text(question_text)
                        return question_text
            except Exception:
                continue
        
        return ""
    
    def _extract_question_options(self, question_element: Any, 
                                extraction_context: PageExtractionContext) -> List[str]:
        """Extract multiple choice options from GeeksforGeeks question"""
        selectors = [
            extraction_context.selectors.get("options", ""),
            "div.options label",
            "ul.mcq-options li",
            ".quiz-options label",
            "div.option-text"
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
                            # Remove GeeksforGeeks option prefixes
                            option_text = self.gfg_patterns["option_pattern"].sub("", option_text).strip()
                            if option_text:  # Ensure not empty after cleaning
                                options.append(option_text)
                    
                    if len(options) >= 2:  # Valid options found
                        return options[:4]  # Limit to 4 options maximum
            except Exception:
                continue
        
        return []
    
    def _extract_correct_answer(self, question_element: Any, 
                              extraction_context: PageExtractionContext) -> Optional[str]:
        """Extract correct answer from GeeksforGeeks question"""
        selectors = [
            extraction_context.selectors.get("answer", ""),
            extraction_context.selectors.get("correct_answer", ""),
            "div.solution-approach",
            "div.correct-answer",
            ".answer-content",
            ".solution"
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
                        answer_text = self._clean_gfg_answer_text(answer_text)
                        return answer_text
            except Exception:
                continue
        
        return None
    
    def _extract_explanation(self, question_element: Any, 
                           extraction_context: PageExtractionContext) -> Optional[str]:
        """Extract explanation/solution from GeeksforGeeks question"""
        selectors = [
            extraction_context.selectors.get("explanation", ""),
            "div.solution-explanation",
            "div.article-content",
            ".explanation-text",
            ".solution-approach p"
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
                        explanation_text = self._clean_gfg_explanation(explanation_text)
                        return explanation_text
            except Exception:
                continue
        
        return None
    
    def _extract_question_metadata(self, question_element: Any, 
                                 extraction_context: PageExtractionContext) -> Dict[str, Any]:
        """Extract metadata specific to GeeksforGeeks questions"""
        metadata = {}
        
        try:
            # Extract difficulty level
            difficulty_selectors = [
                "span.difficulty",
                "div.difficulty-level",
                ".problem-difficulty"
            ]
            
            for selector in difficulty_selectors:
                elem = self._find_element(question_element, selector)
                if elem:
                    difficulty_text = self.extract_text_from_element(elem)
                    if difficulty_text:
                        match = self.gfg_patterns["difficulty_levels"].search(difficulty_text)
                        if match:
                            metadata["difficulty"] = match.group(1).lower()
                            break
            
            # Extract company tags
            company_selectors = [
                "div.company-tags span",
                ".company-tag",
                "a.company"
            ]
            
            companies = []
            for selector in company_selectors:
                elements = self._find_elements(question_element, selector)
                for elem in elements:
                    company_text = self.extract_text_from_element(elem)
                    if company_text:
                        companies.append(company_text)
            
            if companies:
                metadata["companies"] = companies
            
            # Extract topic tags
            topic_selectors = [
                "div.topic-tags a",
                ".topic",
                "span.tag"
            ]
            
            topics = []
            for selector in topic_selectors:
                elements = self._find_elements(question_element, selector)
                for elem in elements:
                    topic_text = self.extract_text_from_element(elem)
                    if topic_text:
                        topics.append(topic_text)
            
            if topics:
                metadata["topics"] = topics
            
            # Check for code content
            question_text = self._extract_question_text(question_element, extraction_context)
            if question_text:
                has_code = bool(self.gfg_patterns["code_block"].search(question_text))
                metadata["has_code"] = has_code
            
            # Add GeeksforGeeks-specific tags
            tags = ["geeksforgeeks", extraction_context.category]
            if extraction_context.subcategory:
                tags.append(extraction_context.subcategory)
            
            if metadata.get("has_code"):
                tags.append("programming")
            
            metadata["tags"] = tags
        
        except Exception as e:
            logger.warning(f"Error extracting GeeksforGeeks metadata: {e}")
        
        return metadata
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _find_question_containers(self, page_source: Any) -> List[Any]:
        """Find all question containers on GeeksforGeeks page"""
        container_selectors = [
            "div.problem-container",
            "div.mcq-container", 
            "div.quiz-question",
            "div.practice-problem",
            ".question-wrapper"
        ]
        
        for selector in container_selectors:
            containers = self._find_elements(page_source, selector)
            if containers:
                return containers
        
        return []
    
    def _handle_infinite_scroll(self, page_source: Any) -> bool:
        """Handle infinite scroll for GeeksforGeeks"""
        try:
            # Execute scroll to trigger loading
            if hasattr(page_source, 'execute_script'):  # Selenium
                page_source.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                import time
                time.sleep(2)  # Wait for content to load
                
                # Check if new content appeared
                current_height = page_source.execute_script("return document.body.scrollHeight")
                
                # Scroll again and check if height changed
                time.sleep(1)
                page_source.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = page_source.execute_script("return document.body.scrollHeight")
                
                return new_height > current_height
            
            return False
            
        except Exception as e:
            logger.warning(f"Infinite scroll handling failed: {e}")
            return False
    
    def _clean_gfg_question_text(self, text: str) -> str:
        """Clean GeeksforGeeks-specific formatting from question text"""
        if not text:
            return ""
        
        # Remove common GeeksforGeeks artifacts
        text = re.sub(r'^\s*Question\s*\d+[.:]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*Q\d+[.:]\s*', '', text)
        
        return self.clean_text(text)
    
    def _clean_gfg_answer_text(self, text: str) -> str:
        """Clean GeeksforGeeks-specific formatting from answer text"""
        if not text:
            return ""
        
        # Remove answer markers
        text = re.sub(r'(?:Answer|Solution|Correct Answer)[:\s]*', '', text, flags=re.IGNORECASE)
        
        return self.clean_text(text)
    
    def _clean_gfg_explanation(self, text: str) -> str:
        """Clean GeeksforGeeks-specific formatting from explanation text"""
        if not text:
            return ""
        
        # Remove explanation headers
        text = re.sub(r'(?:Explanation|Solution|Approach)[:\s]*', '', text, flags=re.IGNORECASE)
        
        return self.clean_text(text)
    
    def _calculate_completeness_score(self, question_text: str, options: List[str], 
                                    correct_answer: Optional[str], explanation: Optional[str]) -> float:
        """Calculate completeness score for GeeksforGeeks question"""
        score = 0.0
        
        # Question text (40% of score)
        if question_text and len(question_text.strip()) > 10:
            score += 40.0
        
        # Options (30% of score)
        if len(options) >= 2:
            score += 30.0 * (len(options) / 4.0)  # Full score for 4 options
        
        # Correct answer (20% of score)
        if correct_answer:
            score += 20.0
        
        # Explanation (10% of score)
        if explanation and len(explanation.strip()) > 20:
            score += 10.0
        
        return min(score, 100.0)
    
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
            metadata={"extractor": "GeeksForGeeksExtractor", "status": "failed"}
        )

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_geeksforgeeks_extractor(content_validator: Optional[ContentValidator] = None,
                                 performance_monitor: Optional[PerformanceMonitor] = None) -> GeeksForGeeksExtractor:
    """
    Create optimized GeeksforGeeks extractor with proper configuration
    
    Args:
        content_validator: Optional content validator
        performance_monitor: Optional performance monitor
        
    Returns:
        Configured GeeksForGeeksExtractor instance
    """
    from config.scraping_config import GEEKSFORGEEKS_CONFIG
    
    # Create specialized validator if none provided
    if content_validator is None:
        from scraping.utils.content_validator import create_geeksforgeeks_validator
        content_validator = create_geeksforgeeks_validator()
    
    # Create performance monitor if none provided
    if performance_monitor is None:
        from scraping.utils.performance_monitor import create_extraction_monitor
        performance_monitor = create_extraction_monitor()
    
    return GeeksForGeeksExtractor(
        source_config=GEEKSFORGEEKS_CONFIG,
        content_validator=content_validator,
        performance_monitor=performance_monitor
    )