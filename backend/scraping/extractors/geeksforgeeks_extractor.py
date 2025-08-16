"""
GeeksforGeeks Content Extractor
Specialized extractor for GeeksforGeeks question format with dynamic content handling
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import uuid
import asyncio

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

class GeeksforGeeksExtractor(BaseContentExtractor):
    """
    Specialized content extractor for GeeksforGeeks questions
    Handles dynamic content, JavaScript rendering, and multiple question formats
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
            "code_block": re.compile(r'```[\w]*\n(.*?)\n```', re.DOTALL),
            "inline_code": re.compile(r'`([^`]+)`'),
            "complexity_pattern": re.compile(r'(?:Time|Space)\s*Complexity[:\s]*O\([^)]+\)', re.IGNORECASE),
            "approach_marker": re.compile(r'(?:Approach|Algorithm|Solution)[:\s]*', re.IGNORECASE),
            "example_pattern": re.compile(r'Example\s*\d*[:\s]*', re.IGNORECASE),
            "input_output": re.compile(r'(?:Input|Output)[:\s]*(.+?)(?=(?:Input|Output|Example|\n\n|$))', re.DOTALL | re.IGNORECASE),
            "difficulty_levels": re.compile(r'(Easy|Medium|Hard|Basic|School)', re.IGNORECASE)
        }
        
        # GeeksforGeeks question format types
        self.gfg_formats = {
            "multiple_choice": ["div.mcq-question", "ul.mcq-options"],
            "coding_problem": ["div.problem-statement", "div.code-editor"],
            "theory_question": ["div.article-content", "div.question-content"],
            "practice_problem": ["div.practice-question", "div.problem-description"]
        }
        
        # Dynamic content selectors
        self.dynamic_selectors = {
            "lazy_images": "img[data-src], img[loading='lazy']",
            "ajax_content": "div[data-ajax], section[data-lazy]",
            "infinite_scroll": "div.infinite-scroll-container",
            "load_more_button": "button.load-more, a.load-more",
            "dynamic_tabs": "div.tab-content[data-tab]"
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
                # Detect question format first
                question_format = self._detect_element_format(question_element)
                
                # Extract based on format
                if question_format == "multiple_choice":
                    return self._extract_mcq_question(question_element, extraction_context, start_time)
                elif question_format == "coding_problem":
                    return self._extract_coding_problem(question_element, extraction_context, start_time)
                elif question_format == "theory_question":
                    return self._extract_theory_question(question_element, extraction_context, start_time)
                else:
                    return self._extract_generic_question(question_element, extraction_context, start_time)
        
        except Exception as e:
            logger.error(f"Error extracting GeeksforGeeks question: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Extraction failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
    def extract_questions_from_page(self, page_source: Any,
                                  extraction_context: PageExtractionContext) -> BatchExtractionResult:
        """
        Extract all questions from GeeksforGeeks page with dynamic content handling
        
        Args:
            page_source: Page source (Playwright page preferred for dynamic content)
            extraction_context: Context information for extraction
            
        Returns:
            BatchExtractionResult with all extracted questions from page
        """
        batch_start = datetime.now()
        extraction_results = []
        errors = []
        
        try:
            with self.performance_monitor.monitor_operation("gfg_page_extraction"):
                # Handle dynamic content loading
                if self._is_playwright_page(page_source):
                    asyncio.create_task(self._handle_dynamic_content(page_source))
                
                # Wait for content to load
                self._wait_for_content_load(page_source)
                
                # Find question containers
                question_containers = self._find_gfg_question_containers(page_source)
                
                if not question_containers:
                    logger.warning(f"No question containers found on GeeksforGeeks page: {extraction_context.page_url}")
                    return self._create_empty_batch_result(batch_start, ["No question containers found"])
                
                logger.info(f"Found {len(question_containers)} question containers on GeeksforGeeks page")
                
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
                        error_msg = f"Error processing GeeksforGeeks question {i+1}: {str(e)}"
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
                        "extractor": "GeeksforGeeksExtractor",
                        "question_containers_found": len(question_containers),
                        "dynamic_content_handled": True
                    }
                )
        
        except Exception as e:
            logger.error(f"Error in GeeksforGeeks page extraction: {e}")
            return self._create_empty_batch_result(batch_start, [f"Page extraction failed: {str(e)}"])
    
    def detect_question_format(self, page_source: Any) -> Dict[str, Any]:
        """
        Analyze GeeksforGeeks page structure and detect question format
        
        Args:
            page_source: Page source to analyze
            
        Returns:
            Dictionary with format detection results
        """
        format_info = {
            "source_type": "geeksforgeeks",
            "primary_format": "unknown",
            "has_code_snippets": False,
            "has_multiple_choice": False,
            "has_examples": False,
            "question_count": 0,
            "dynamic_content": False,
            "pagination_type": "infinite_scroll",
            "selectors_found": {},
            "confidence_score": 0.0
        }
        
        try:
            confidence_factors = []
            
            # Check for GeeksforGeeks branding/structure
            gfg_indicators = [
                "header.gfg-header",
                "div.gfg-content",
                "nav.gfg-navigation",
                "footer.gfg-footer"
            ]
            
            gfg_branding = 0
            for selector in gfg_indicators:
                if self._find_element(page_source, selector):
                    gfg_branding += 1
            
            if gfg_branding >= 1:
                confidence_factors.append(0.2)
            
            # Check for question formats
            question_types = []
            
            # Multiple choice questions
            mcq_selectors = ["div.mcq-question", "ul.mcq-options", "div.quiz-container"]
            for selector in mcq_selectors:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_multiple_choice"] = True
                    question_types.append("multiple_choice")
                    confidence_factors.append(0.15)
                    break
            
            # Coding problems
            code_selectors = ["div.problem-statement", "pre.code", "div.code-editor", "textarea.code-input"]
            for selector in code_selectors:
                elements = self._find_elements(page_source, selector)
                if elements:
                    format_info["has_code_snippets"] = True
                    question_types.append("coding_problem")
                    confidence_factors.append(0.2)
                    break
            
            # Theory/Article questions
            theory_selectors = ["div.article-content", "div.question-content", "section.problem-description"]
            for selector in theory_selectors:
                elements = self._find_elements(page_source, selector)
                if elements:
                    question_types.append("theory_question")
                    confidence_factors.append(0.1)
                    break
            
            # Practice problems
            practice_selectors = ["div.practice-question", "div.problem-container"]
            for selector in practice_selectors:
                elements = self._find_elements(page_source, selector)
                if elements:
                    question_types.append("practice_problem")
                    confidence_factors.append(0.15)
                    break
            
            # Determine primary format
            if question_types:
                format_info["primary_format"] = question_types[0]
                format_info["question_count"] = len(self._find_gfg_question_containers(page_source))
            
            # Check for examples
            example_indicators = ["div.example", "h3:contains('Example')", "h4:contains('Example')"]
            for selector in example_indicators:
                if self._find_element(page_source, selector):
                    format_info["has_examples"] = True
                    confidence_factors.append(0.1)
                    break
            
            # Check for dynamic content
            dynamic_indicators = [
                self.dynamic_selectors["lazy_images"],
                self.dynamic_selectors["ajax_content"],
                self.dynamic_selectors["infinite_scroll"]
            ]
            
            for selector in dynamic_indicators:
                if self._find_element(page_source, selector):
                    format_info["dynamic_content"] = True
                    confidence_factors.append(0.1)
                    break
            
            # Calculate confidence score
            format_info["confidence_score"] = min(sum(confidence_factors), 1.0)
            
            logger.info(f"GeeksforGeeks format detection: {format_info['confidence_score']:.2f} confidence, "
                       f"Primary format: {format_info['primary_format']}, "
                       f"{format_info['question_count']} questions found")
        
        except Exception as e:
            logger.error(f"Error in GeeksforGeeks format detection: {e}")
            format_info["error"] = str(e)
        
        return format_info
    
    def handle_pagination(self, page_source: Any, 
                         current_page: int, extraction_context: PageExtractionContext) -> Tuple[bool, Optional[str]]:
        """
        Handle GeeksforGeeks pagination (typically infinite scroll or load more)
        
        Args:
            page_source: Page source for navigation
            current_page: Current page number
            extraction_context: Context for navigation
            
        Returns:
            Tuple of (has_next_page, next_page_url)
        """
        try:
            has_next = False
            next_page_url = None
            
            # Method 1: Check for "Load More" button
            load_more_selectors = [
                "button.load-more",
                "a.load-more",
                "div.load-more-container button",
                "button[data-action='load-more']"
            ]
            
            for selector in load_more_selectors:
                load_button = self._find_element(page_source, selector)
                if load_button:
                    # Check if button is visible and enabled
                    is_visible = self._is_element_visible(load_button)
                    is_enabled = not self._is_element_disabled(load_button)
                    
                    if is_visible and is_enabled:
                        has_next = True
                        # For load more buttons, we typically trigger them rather than navigate
                        break
            
            # Method 2: Check for infinite scroll capability
            if not has_next:
                scroll_container = self._find_element(page_source, self.dynamic_selectors["infinite_scroll"])
                if scroll_container:
                    # Check if we can scroll more
                    if self._can_scroll_more(page_source):
                        has_next = True
            
            # Method 3: Check for traditional pagination
            if not has_next:
                pagination_selectors = [
                    "nav.pagination a.next",
                    "div.pagination a:contains('Next')",
                    "a.next-page"
                ]
                
                for selector in pagination_selectors:
                    next_link = self._find_element(page_source, selector)
                    if next_link:
                        if hasattr(next_link, 'get_attribute'):  # Selenium
                            href = next_link.get_attribute('href')
                        else:  # Playwright
                            href = next_link.get_attribute('href')
                        
                        if href:
                            next_page_url = href
                            has_next = True
                            break
            
            # Method 4: Check for "end of content" indicators
            if has_next:
                end_indicators = [
                    "div.no-more-content",
                    "p.end-of-results",
                    "div.end-of-list"
                ]
                
                for selector in end_indicators:
                    end_element = self._find_element(page_source, selector)
                    if end_element and self._is_element_visible(end_element):
                        has_next = False
                        break
            
            logger.info(f"GeeksforGeeks pagination: Current page {current_page}, "
                       f"Has next: {has_next}, Next URL: {next_page_url}")
            
            return has_next, next_page_url
        
        except Exception as e:
            logger.error(f"Error handling GeeksforGeeks pagination: {e}")
            return False, None
    
    # =============================================================================
    # FORMAT-SPECIFIC EXTRACTION METHODS
    # =============================================================================
    
    def _extract_mcq_question(self, question_element: Any, 
                            extraction_context: PageExtractionContext,
                            start_time: datetime) -> ExtractionResult:
        """Extract multiple choice question from GeeksforGeeks"""
        try:
            # Extract question text
            question_text = self._extract_gfg_question_text(question_element, "mcq")
            
            # Extract options
            options = self._extract_gfg_options(question_element)
            
            # Extract correct answer
            correct_answer = self._extract_gfg_correct_answer(question_element, "mcq")
            
            # Extract explanation
            explanation = self._extract_gfg_explanation(question_element)
            
            # Extract metadata
            metadata = self._extract_gfg_metadata(question_element, extraction_context)
            metadata["question_type"] = "multiple_choice"
            
            return self._create_extraction_result(
                question_text, options, correct_answer, explanation, 
                metadata, extraction_context, start_time
            )
        
        except Exception as e:
            logger.error(f"Error extracting GeeksforGeeks MCQ: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"MCQ extraction failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
    def _extract_coding_problem(self, question_element: Any,
                              extraction_context: PageExtractionContext,
                              start_time: datetime) -> ExtractionResult:
        """Extract coding problem from GeeksforGeeks"""
        try:
            # Extract problem statement
            question_text = self._extract_gfg_question_text(question_element, "coding")
            
            # Extract examples and test cases
            examples = self._extract_code_examples(question_element)
            
            # Extract constraints and complexity
            constraints = self._extract_constraints(question_element)
            
            # Extract code snippets if available
            code_snippets = self._extract_code_snippets(question_element)
            
            # Build comprehensive question text
            full_question = question_text
            if examples:
                full_question += "\n\nExamples:\n" + "\n".join(examples)
            if constraints:
                full_question += "\n\nConstraints:\n" + constraints
            
            # Extract metadata
            metadata = self._extract_gfg_metadata(question_element, extraction_context)
            metadata.update({
                "question_type": "coding_problem",
                "has_code_snippets": bool(code_snippets),
                "code_snippets": code_snippets,
                "examples_count": len(examples)
            })
            
            return self._create_extraction_result(
                full_question, [], None, None,  # Coding problems don't have traditional options
                metadata, extraction_context, start_time
            )
        
        except Exception as e:
            logger.error(f"Error extracting GeeksforGeeks coding problem: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Coding problem extraction failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
    def _extract_theory_question(self, question_element: Any,
                               extraction_context: PageExtractionContext,
                               start_time: datetime) -> ExtractionResult:
        """Extract theory/article question from GeeksforGeeks"""
        try:
            # Extract question/article text
            question_text = self._extract_gfg_question_text(question_element, "theory")
            
            # Extract key concepts
            key_concepts = self._extract_key_concepts(question_element)
            
            # Extract explanations/solutions
            explanation = self._extract_gfg_explanation(question_element)
            
            # Extract metadata
            metadata = self._extract_gfg_metadata(question_element, extraction_context)
            metadata.update({
                "question_type": "theory_question",
                "key_concepts": key_concepts
            })
            
            return self._create_extraction_result(
                question_text, [], None, explanation,
                metadata, extraction_context, start_time
            )
        
        except Exception as e:
            logger.error(f"Error extracting GeeksforGeeks theory question: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Theory question extraction failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
    def _extract_generic_question(self, question_element: Any,
                                extraction_context: PageExtractionContext,
                                start_time: datetime) -> ExtractionResult:
        """Extract generic question when format is unclear"""
        try:
            # Extract basic question text
            question_text = self._extract_gfg_question_text(question_element, "generic")
            
            # Try to extract any available options
            options = self._extract_gfg_options(question_element)
            
            # Try to extract answer/solution
            correct_answer = self._extract_gfg_correct_answer(question_element, "generic")
            explanation = self._extract_gfg_explanation(question_element)
            
            # Extract metadata
            metadata = self._extract_gfg_metadata(question_element, extraction_context)
            metadata["question_type"] = "generic"
            
            return self._create_extraction_result(
                question_text, options, correct_answer, explanation,
                metadata, extraction_context, start_time
            )
        
        except Exception as e:
            logger.error(f"Error extracting generic GeeksforGeeks question: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Generic extraction failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _detect_element_format(self, element: Any) -> str:
        """Detect the format of a question element"""
        try:
            # Check for MCQ indicators
            mcq_indicators = ["div.mcq-question", "ul.mcq-options", "input[type='radio']"]
            for selector in mcq_indicators:
                if self._find_element(element, selector):
                    return "multiple_choice"
            
            # Check for coding problem indicators
            code_indicators = ["pre.code", "div.code-editor", "textarea.code-input", "div.problem-statement"]
            for selector in code_indicators:
                if self._find_element(element, selector):
                    return "coding_problem"
            
            # Check for theory/article indicators
            theory_indicators = ["div.article-content", "section.content", "div.theory-content"]
            for selector in theory_indicators:
                if self._find_element(element, selector):
                    return "theory_question"
            
            return "generic"
        
        except Exception:
            return "generic"
    
    def _extract_gfg_question_text(self, element: Any, question_type: str) -> str:
        """Extract question text based on GeeksforGeeks format"""
        selectors = {
            "mcq": ["div.mcq-question p", "div.question-text", "div.problem-statement"],
            "coding": ["div.problem-statement", "div.problem-description", "section.problem-content"],
            "theory": ["div.article-content p", "div.theory-text", "section.content"],
            "generic": ["p", "div.content", "div.text-content"]
        }
        
        for selector in selectors.get(question_type, selectors["generic"]):
            try:
                elem = self._find_element(element, selector)
                if elem:
                    text = self.extract_text_from_element(elem)
                    if text and len(text.strip()) > 10:
                        return self._clean_gfg_question_text(text)
            except Exception:
                continue
        
        return ""
    
    def _extract_gfg_options(self, element: Any) -> List[str]:
        """Extract options from GeeksforGeeks question"""
        option_selectors = [
            "ul.mcq-options li",
            "div.options label",
            "ol.option-list li",
            "div.choice-container div"
        ]
        
        for selector in option_selectors:
            try:
                option_elements = self._find_elements(element, selector)
                if option_elements and len(option_elements) >= 2:
                    options = []
                    for elem in option_elements:
                        option_text = self.extract_text_from_element(elem)
                        if option_text:
                            # Clean option text
                            option_text = re.sub(r'^[A-Za-z0-9]+[.)]\s*', '', option_text).strip()
                            if option_text:
                                options.append(option_text)
                    
                    if len(options) >= 2:
                        return options[:4]  # Limit to 4 options
            except Exception:
                continue
        
        return []
    
    def _extract_gfg_correct_answer(self, element: Any, question_type: str) -> Optional[str]:
        """Extract correct answer from GeeksforGeeks question"""
        answer_selectors = [
            "div.correct-answer",
            "div.solution",
            "div.answer-explanation",
            "span.answer",
            "p.correct-option"
        ]
        
        for selector in answer_selectors:
            try:
                answer_elem = self._find_element(element, selector)
                if answer_elem:
                    answer_text = self.extract_text_from_element(answer_elem)
                    if answer_text:
                        return self._clean_gfg_answer_text(answer_text)
            except Exception:
                continue
        
        return None
    
    def _extract_gfg_explanation(self, element: Any) -> Optional[str]:
        """Extract explanation from GeeksforGeeks question"""
        explanation_selectors = [
            "div.solution-approach",
            "div.explanation",
            "div.answer-explanation",
            "section.solution",
            "div.approach-content"
        ]
        
        for selector in explanation_selectors:
            try:
                explanation_elem = self._find_element(element, selector)
                if explanation_elem:
                    explanation_text = self.extract_text_from_element(explanation_elem)
                    if explanation_text and len(explanation_text.strip()) > 15:
                        return self._clean_gfg_explanation(explanation_text)
            except Exception:
                continue
        
        return None
    
    def _extract_gfg_metadata(self, element: Any, context: PageExtractionContext) -> Dict[str, Any]:
        """Extract GeeksforGeeks-specific metadata"""
        metadata = {}
        
        try:
            # Extract difficulty
            difficulty_selectors = ["span.difficulty", "div.difficulty-level", "badge.difficulty"]
            for selector in difficulty_selectors:
                elem = self._find_element(element, selector)
                if elem:
                    difficulty = self.extract_text_from_element(elem)
                    if difficulty:
                        match = self.gfg_patterns["difficulty_levels"].search(difficulty)
                        if match:
                            metadata["difficulty"] = match.group(1).lower()
                            break
            
            # Extract company tags
            company_selectors = ["div.company-tags a", "span.company-tag", "div.tags .company"]
            companies = []
            for selector in company_selectors:
                elements = self._find_elements(element, selector)
                for elem in elements:
                    company = self.extract_text_from_element(elem)
                    if company:
                        companies.append(company)
            
            if companies:
                metadata["companies"] = companies
            
            # Extract topic tags
            topic_selectors = ["div.topic-tags a", "span.topic", "div.tags .topic"]
            topics = []
            for selector in topic_selectors:
                elements = self._find_elements(element, selector)
                for elem in elements:
                    topic = self.extract_text_from_element(elem)
                    if topic:
                        topics.append(topic)
            
            if topics:
                metadata["topics"] = topics
            
            # Extract complexity information
            text_content = self._get_element_text_content(element)
            complexity_matches = self.gfg_patterns["complexity_pattern"].findall(text_content)
            if complexity_matches:
                metadata["complexity_analysis"] = complexity_matches
            
            # Add GeeksforGeeks-specific tags
            tags = ["geeksforgeeks", context.category]
            if context.subcategory:
                tags.append(context.subcategory)
            
            metadata["tags"] = tags
        
        except Exception as e:
            logger.warning(f"Error extracting GeeksforGeeks metadata: {e}")
        
        return metadata
    
    def _extract_code_examples(self, element: Any) -> List[str]:
        """Extract code examples from GeeksforGeeks coding problems"""
        examples = []
        
        try:
            # Look for example sections
            example_selectors = [
                "div.example",
                "section.example",
                "div[class*='example']"
            ]
            
            for selector in example_selectors:
                example_elements = self._find_elements(element, selector)
                for elem in example_elements:
                    example_text = self.extract_text_from_element(elem)
                    if example_text:
                        examples.append(example_text)
            
            # Extract input/output patterns
            text_content = self._get_element_text_content(element)
            io_matches = self.gfg_patterns["input_output"].findall(text_content)
            examples.extend(io_matches)
        
        except Exception as e:
            logger.warning(f"Error extracting code examples: {e}")
        
        return examples
    
    def _extract_constraints(self, element: Any) -> str:
        """Extract constraints from coding problems"""
        try:
            constraint_selectors = [
                "div.constraints",
                "section.constraints", 
                "div[class*='constraint']"
            ]
            
            for selector in constraint_selectors:
                elem = self._find_element(element, selector)
                if elem:
                    return self.extract_text_from_element(elem)
        
        except Exception as e:
            logger.warning(f"Error extracting constraints: {e}")
        
        return ""
    
    def _extract_code_snippets(self, element: Any) -> List[Dict[str, str]]:
        """Extract code snippets with language information"""
        snippets = []
        
        try:
            # Look for code blocks
            code_selectors = [
                "pre code",
                "div.code-block",
                "textarea.code-input"
            ]
            
            for selector in code_selectors:
                code_elements = self._find_elements(element, selector)
                for elem in code_elements:
                    code_text = self.extract_text_from_element(elem)
                    if code_text:
                        # Try to detect language
                        language = self._detect_code_language(elem, code_text)
                        snippets.append({
                            "code": code_text,
                            "language": language
                        })
        
        except Exception as e:
            logger.warning(f"Error extracting code snippets: {e}")
        
        return snippets
    
    def _extract_key_concepts(self, element: Any) -> List[str]:
        """Extract key concepts from theory questions"""
        concepts = []
        
        try:
            # Look for emphasized text, headings, etc.
            concept_selectors = [
                "strong",
                "b",
                "em",
                "h3",
                "h4",
                "span.highlight"
            ]
            
            for selector in concept_selectors:
                concept_elements = self._find_elements(element, selector)
                for elem in concept_elements:
                    concept = self.extract_text_from_element(elem)
                    if concept and len(concept) < 100:  # Filter out long text
                        concepts.append(concept)
        
        except Exception as e:
            logger.warning(f"Error extracting key concepts: {e}")
        
        return concepts
    
    async def _handle_dynamic_content(self, page_source: Any):
        """Handle dynamic content loading on GeeksforGeeks pages"""
        try:
            if not self._is_playwright_page(page_source):
                return
            
            # Wait for lazy-loaded images
            await page_source.wait_for_selector(self.dynamic_selectors["lazy_images"], timeout=5000)
            
            # Handle infinite scroll
            scroll_container = await page_source.query_selector(self.dynamic_selectors["infinite_scroll"])
            if scroll_container:
                # Scroll to trigger content loading
                await page_source.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page_source.wait_for_timeout(2000)
            
            # Click load more if available
            load_more_button = await page_source.query_selector(self.dynamic_selectors["load_more_button"])
            if load_more_button:
                await load_more_button.click()
                await page_source.wait_for_timeout(3000)
        
        except Exception as e:
            logger.warning(f"Error handling dynamic content: {e}")
    
    def _wait_for_content_load(self, page_source: Any):
        """Wait for content to fully load"""
        try:
            if self._is_playwright_page(page_source):
                # Playwright - wait for network idle
                page_source.wait_for_load_state("networkidle", timeout=10000)
            else:
                # Selenium - wait for specific elements
                import time
                time.sleep(3)  # Basic wait for Selenium
        
        except Exception as e:
            logger.warning(f"Error waiting for content load: {e}")
    
    def _find_gfg_question_containers(self, page_source: Any) -> List[Any]:
        """Find question containers on GeeksforGeeks page"""
        container_selectors = [
            "div.problem-container",
            "div.question-container", 
            "div.mcq-container",
            "article.problem",
            "section.question"
        ]
        
        for selector in container_selectors:
            containers = self._find_elements(page_source, selector)
            if containers:
                return containers
        
        return []
    
    # Additional helper methods for dynamic content and UI interactions...
    
    def _is_playwright_page(self, page_source: Any) -> bool:
        """Check if page_source is a Playwright page"""
        return hasattr(page_source, 'goto') and hasattr(page_source, 'query_selector')
    
    def _is_element_visible(self, element: Any) -> bool:
        """Check if element is visible"""
        try:
            if hasattr(element, 'is_displayed'):  # Selenium
                return element.is_displayed()
            elif hasattr(element, 'is_visible'):  # Playwright
                return element.is_visible()
        except Exception:
            pass
        return True
    
    def _is_element_disabled(self, element: Any) -> bool:
        """Check if element is disabled"""
        try:
            if hasattr(element, 'get_attribute'):  # Selenium
                disabled = element.get_attribute('disabled')
                return disabled is not None
            elif hasattr(element, 'get_attribute'):  # Playwright
                disabled = element.get_attribute('disabled')
                return disabled is not None
        except Exception:
            pass
        return False
    
    def _can_scroll_more(self, page_source: Any) -> bool:
        """Check if page can scroll more"""
        try:
            if self._is_playwright_page(page_source):
                # Check scroll position vs total height
                scroll_info = page_source.evaluate("""
                    () => {
                        const scrollTop = window.pageYOffset;
                        const scrollHeight = document.body.scrollHeight;
                        const clientHeight = window.innerHeight;
                        return {
                            canScrollMore: scrollTop + clientHeight < scrollHeight - 100
                        };
                    }
                """)
                return scroll_info.get("canScrollMore", False)
        except Exception:
            pass
        return False
    
    def _detect_code_language(self, element: Any, code_text: str) -> str:
        """Detect programming language from code element or content"""
        try:
            # Check element classes for language hints
            if hasattr(element, 'get_attribute'):
                class_attr = element.get_attribute('class') or ""
                
                # Common language class patterns
                language_patterns = {
                    'python': ['python', 'py'],
                    'java': ['java'],
                    'cpp': ['cpp', 'c++', 'cxx'],
                    'c': ['language-c'],
                    'javascript': ['js', 'javascript'],
                    'html': ['html'],
                    'css': ['css']
                }
                
                for lang, patterns in language_patterns.items():
                    if any(pattern in class_attr.lower() for pattern in patterns):
                        return lang
            
            # Analyze code content for language indicators
            if 'def ' in code_text or 'import ' in code_text:
                return 'python'
            elif 'public class' in code_text or 'System.out' in code_text:
                return 'java'
            elif '#include' in code_text or 'cout <<' in code_text:
                return 'cpp'
            elif 'function' in code_text or 'var ' in code_text:
                return 'javascript'
        
        except Exception:
            pass
        
        return 'unknown'
    
    def _get_element_text_content(self, element: Any) -> str:
        """Get all text content from element"""
        try:
            if hasattr(element, 'text'):  # Selenium
                return element.text
            elif hasattr(element, 'text_content'):  # Playwright
                return element.text_content()
        except Exception:
            pass
        return ""
    
    def _clean_gfg_question_text(self, text: str) -> str:
        """Clean GeeksforGeeks-specific formatting"""
        if not text:
            return ""
        
        # Remove common GfG artifacts
        text = self.gfg_patterns["approach_marker"].sub("", text)
        text = self.gfg_patterns["example_pattern"].sub("Example: ", text)
        
        return self.clean_text(text)
    
    def _clean_gfg_answer_text(self, text: str) -> str:
        """Clean GeeksforGeeks answer text"""
        if not text:
            return ""
        
        # Remove answer prefixes
        text = re.sub(r'^(?:Answer|Correct Answer|Solution)[:\s]*', '', text, flags=re.IGNORECASE)
        
        return self.clean_text(text)
    
    def _clean_gfg_explanation(self, text: str) -> str:
        """Clean GeeksforGeeks explanation text"""
        if not text:
            return ""
        
        # Remove explanation headers
        text = self.gfg_patterns["approach_marker"].sub("", text)
        
        return self.clean_text(text)
    
    def _create_extraction_result(self, question_text: str, options: List[str],
                                correct_answer: Optional[str], explanation: Optional[str],
                                metadata: Dict[str, Any], extraction_context: PageExtractionContext,
                                start_time: datetime) -> ExtractionResult:
        """Create standardized extraction result"""
        try:
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
                source_type=ScrapingSourceType.GEEKSFORGEEKS,
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
                raw_html="",  # Could be enhanced to capture HTML
                extraction_metadata={
                    "page_number": extraction_context.page_number,
                    "extractor": "GeeksforGeeksExtractor",
                    "extraction_method": "playwright",
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
            logger.error(f"Error creating extraction result: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Result creation failed: {str(e)}",
                extraction_time=(datetime.now() - start_time).total_seconds(),
                source_url=extraction_context.page_url
            )
    
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
            metadata={"extractor": "GeeksforGeeksExtractor", "status": "failed"}
        )

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_geeksforgeeks_extractor(content_validator: Optional[ContentValidator] = None,
                                 performance_monitor: Optional[PerformanceMonitor] = None) -> GeeksforGeeksExtractor:
    """
    Create optimized GeeksforGeeks extractor with proper configuration
    
    Args:
        content_validator: Optional content validator
        performance_monitor: Optional performance monitor
        
    Returns:
        Configured GeeksforGeeksExtractor instance
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
    
    return GeeksforGeeksExtractor(
        source_config=GEEKSFORGEEKS_CONFIG,
        content_validator=content_validator,
        performance_monitor=performance_monitor
    )

def extract_sample_gfg_questions(page_source: Any,
                               target: ScrapingTarget,
                               max_questions: int = 10) -> BatchExtractionResult:
    """
    Convenience function to extract sample questions from GeeksforGeeks
    
    Args:
        page_source: Playwright page or Selenium driver
        target: ScrapingTarget for GeeksforGeeks
        max_questions: Maximum number of questions to extract
        
    Returns:
        BatchExtractionResult with extracted questions
    """
    extractor = create_geeksforgeeks_extractor()
    
    # Create extraction context
    context = create_extraction_context(
        target=target,
        page_url=target.target_url,
        page_number=1
    )
    
    try:
        # Navigate to target URL
        if hasattr(page_source, 'get'):  # Selenium
            page_source.get(target.target_url)
        elif hasattr(page_source, 'goto'):  # Playwright
            page_source.goto(target.target_url)
        
        # Extract questions
        batch_result = extractor.extract_questions_from_page(page_source, context)
        
        # Limit to requested number
        if batch_result.successful_extractions > max_questions:
            batch_result.extraction_results = batch_result.extraction_results[:max_questions]
            batch_result.total_processed = max_questions
            batch_result.successful_extractions = min(batch_result.successful_extractions, max_questions)
        
        return batch_result
        
    except Exception as e:
        logger.error(f"Error extracting sample GeeksforGeeks questions: {e}")
        return extractor._create_empty_batch_result(datetime.now(), [str(e)])