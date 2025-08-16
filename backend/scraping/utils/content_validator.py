"""
Content Validation Utilities
Comprehensive content validation and quality assessment for scraped data
"""

import re
import string
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import QualityGate from models
from models.scraping_models import QualityGate

logger = logging.getLogger(__name__)

# =============================================================================
# VALIDATION ENUMS AND CLASSES
# =============================================================================

class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ContentType(str, Enum):
    QUESTION_TEXT = "question_text"
    MULTIPLE_CHOICE = "multiple_choice"
    EXPLANATION = "explanation"
    CATEGORY = "category"
    DIFFICULTY = "difficulty"
    URL = "url"
    HTML_CONTENT = "html_content"

@dataclass
class ValidationRule:
    """Single validation rule configuration"""
    name: str
    description: str
    content_types: List[ContentType]
    severity: ValidationSeverity
    enabled: bool = True

@dataclass
class ValidationIssue:
    """Identified validation issue"""
    rule_name: str
    severity: ValidationSeverity
    message: str
    field_name: str
    content_preview: str = ""
    suggestion: Optional[str] = None

@dataclass
class ContentQualityScore:
    """Content quality assessment result"""
    overall_score: float  # 0-100
    completeness_score: float  # 0-100
    accuracy_score: float  # 0-100
    clarity_score: float  # 0-100
    
    issues: List[ValidationIssue]
    passed_validations: List[str]
    
    # Detailed metrics
    word_count: int
    sentence_count: int
    readability_score: float
    
    # Recommendation
    quality_gate: str  # approve, review, reject
    improvement_suggestions: List[str]

# =============================================================================
# CONTENT VALIDATOR CLASS
# =============================================================================

class ContentValidator:
    """
    Comprehensive content validation and quality assessment system
    """
    
    def __init__(self, source_name: str = "general", custom_rules: List[ValidationRule] = None):
        """
        Initialize content validator
        
        Args:
            source_name: Name of the scraping source for specialized rules
            custom_rules: Additional custom validation rules
        """
        self.source_name = source_name
        self.validation_rules = self._load_default_rules()
        
        if custom_rules:
            self.validation_rules.extend(custom_rules)
        
        # Quality thresholds
        self.quality_thresholds = {
            "auto_approve": 85.0,
            "auto_reject": 40.0,
            "min_word_count": 10,
            "max_word_count": 1000,
            "min_options_count": 2,
            "max_options_count": 10
        }
        
        logger.info(f"📋 ContentValidator initialized for {source_name} with {len(self.validation_rules)} rules")
    
    def _load_default_rules(self) -> List[ValidationRule]:
        """Load default validation rules"""
        return [
            # Content Completeness Rules
            ValidationRule(
                name="empty_content_check",
                description="Check for empty or whitespace-only content",
                content_types=[ContentType.QUESTION_TEXT, ContentType.MULTIPLE_CHOICE, ContentType.EXPLANATION],
                severity=ValidationSeverity.CRITICAL
            ),
            ValidationRule(
                name="minimum_length_check",
                description="Ensure content meets minimum length requirements",
                content_types=[ContentType.QUESTION_TEXT, ContentType.EXPLANATION],
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="maximum_length_check",
                description="Ensure content doesn't exceed maximum length",
                content_types=[ContentType.QUESTION_TEXT, ContentType.EXPLANATION],
                severity=ValidationSeverity.WARNING
            ),
            
            # Format Validation Rules
            ValidationRule(
                name="html_tag_cleanup",
                description="Check for residual HTML tags in plain text",
                content_types=[ContentType.QUESTION_TEXT, ContentType.MULTIPLE_CHOICE, ContentType.EXPLANATION],
                severity=ValidationSeverity.WARNING
            ),
            ValidationRule(
                name="encoding_issues",
                description="Check for encoding issues and special characters",
                content_types=[ContentType.QUESTION_TEXT, ContentType.MULTIPLE_CHOICE, ContentType.EXPLANATION],
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="malformed_options",
                description="Validate multiple choice options format",
                content_types=[ContentType.MULTIPLE_CHOICE],
                severity=ValidationSeverity.ERROR
            ),
            
            # Content Quality Rules
            ValidationRule(
                name="readability_check",
                description="Assess content readability and clarity",
                content_types=[ContentType.QUESTION_TEXT, ContentType.EXPLANATION],
                severity=ValidationSeverity.INFO
            ),
            ValidationRule(
                name="grammar_basic_check",
                description="Basic grammar and punctuation validation",
                content_types=[ContentType.QUESTION_TEXT, ContentType.EXPLANATION],
                severity=ValidationSeverity.WARNING
            ),
            ValidationRule(
                name="duplicate_content_check",
                description="Check for duplicate sentences or repetitive content",
                content_types=[ContentType.QUESTION_TEXT, ContentType.EXPLANATION],
                severity=ValidationSeverity.WARNING
            ),
            
            # Structure Validation Rules
            ValidationRule(
                name="question_format_validation",
                description="Validate question structure and format",
                content_types=[ContentType.QUESTION_TEXT],
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="answer_consistency_check",
                description="Check answer consistency with question type",
                content_types=[ContentType.MULTIPLE_CHOICE],
                severity=ValidationSeverity.ERROR
            ),
            
            # URL and Source Validation
            ValidationRule(
                name="url_validity_check",
                description="Validate URL format and accessibility",
                content_types=[ContentType.URL],
                severity=ValidationSeverity.WARNING
            )
        ]
    
    def validate_content(self, content_data: Dict[str, Any], 
                        content_types: Dict[str, ContentType] = None) -> ContentQualityScore:
        """
        Validate content and generate quality score
        
        Args:
            content_data: Dictionary of content fields to validate
            content_types: Mapping of field names to content types
            
        Returns:
            ContentQualityScore with validation results
        """
        logger.debug(f"🔍 Validating content with {len(content_data)} fields")
        
        issues = []
        passed_validations = []
        
        # Auto-detect content types if not provided
        if not content_types:
            content_types = self._auto_detect_content_types(content_data)
        
        # Run validation rules
        for rule in self.validation_rules:
            if not rule.enabled:
                continue
            
            # Check which fields this rule applies to
            applicable_fields = [
                field_name for field_name, field_content_type in content_types.items()
                if field_content_type in rule.content_types and field_name in content_data
            ]
            
            if not applicable_fields:
                continue
            
            # Run rule on applicable fields
            rule_issues = self._execute_validation_rule(rule, content_data, applicable_fields)
            
            if rule_issues:
                issues.extend(rule_issues)
            else:
                passed_validations.append(rule.name)
        
        # Calculate quality scores
        completeness_score = self._calculate_completeness_score(content_data, issues)
        accuracy_score = self._calculate_accuracy_score(content_data, issues)
        clarity_score = self._calculate_clarity_score(content_data, issues)
        
        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.4 +
            accuracy_score * 0.35 +
            clarity_score * 0.25
        )
        
        # Content analysis
        text_content = self._extract_text_content(content_data)
        word_count = len(text_content.split()) if text_content else 0
        sentence_count = len([s for s in text_content.split('.') if s.strip()]) if text_content else 0
        readability_score = self._calculate_readability(text_content)
        
        # Determine quality gate
        quality_gate = self._determine_quality_gate(overall_score, issues)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(issues, content_data)
        
        result = ContentQualityScore(
            overall_score=round(overall_score, 2),
            completeness_score=round(completeness_score, 2),
            accuracy_score=round(accuracy_score, 2),
            clarity_score=round(clarity_score, 2),
            issues=issues,
            passed_validations=passed_validations,
            word_count=word_count,
            sentence_count=sentence_count,
            readability_score=round(readability_score, 2),
            quality_gate=quality_gate,
            improvement_suggestions=improvement_suggestions
        )
        
        logger.info(f"✅ Validation complete: Score={overall_score:.1f}, Gate={quality_gate}, Issues={len(issues)}")
        
        return result
    
    def _auto_detect_content_types(self, content_data: Dict[str, Any]) -> Dict[str, ContentType]:
        """Auto-detect content types based on field names"""
        content_types = {}
        
        for field_name, content in content_data.items():
            field_lower = field_name.lower()
            
            if any(keyword in field_lower for keyword in ['question', 'text', 'problem']):
                content_types[field_name] = ContentType.QUESTION_TEXT
            elif any(keyword in field_lower for keyword in ['option', 'choice', 'answer']):
                content_types[field_name] = ContentType.MULTIPLE_CHOICE
            elif any(keyword in field_lower for keyword in ['explanation', 'solution', 'hint']):
                content_types[field_name] = ContentType.EXPLANATION
            elif any(keyword in field_lower for keyword in ['category', 'topic', 'subject']):
                content_types[field_name] = ContentType.CATEGORY
            elif any(keyword in field_lower for keyword in ['difficulty', 'level']):
                content_types[field_name] = ContentType.DIFFICULTY
            elif any(keyword in field_lower for keyword in ['url', 'link', 'href']):
                content_types[field_name] = ContentType.URL
            elif 'html' in field_lower:
                content_types[field_name] = ContentType.HTML_CONTENT
            else:
                # Default to question text for unknown fields
                content_types[field_name] = ContentType.QUESTION_TEXT
        
        return content_types
    
    def _execute_validation_rule(self, rule: ValidationRule, content_data: Dict[str, Any], 
                                applicable_fields: List[str]) -> List[ValidationIssue]:
        """Execute a specific validation rule"""
        issues = []
        
        try:
            # Route to specific validation method
            method_name = f"_validate_{rule.name}"
            if hasattr(self, method_name):
                validation_method = getattr(self, method_name)
                rule_issues = validation_method(content_data, applicable_fields)
                if rule_issues:
                    issues.extend(rule_issues)
            else:
                logger.warning(f"Validation method not found: {method_name}")
        
        except Exception as e:
            logger.error(f"Error executing validation rule {rule.name}: {e}")
            # Create an issue for the validation error itself
            issues.append(ValidationIssue(
                rule_name=rule.name,
                severity=ValidationSeverity.ERROR,
                message=f"Validation rule execution failed: {e}",
                field_name="validation_system"
            ))
        
        return issues
    
    # =============================================================================
    # SPECIFIC VALIDATION METHODS
    # =============================================================================
    
    def _validate_empty_content_check(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Check for empty or whitespace-only content"""
        issues = []
        
        for field_name in fields:
            content = content_data.get(field_name, "")
            
            if not content or not str(content).strip():
                issues.append(ValidationIssue(
                    rule_name="empty_content_check",
                    severity=ValidationSeverity.CRITICAL,
                    message="Content is empty or contains only whitespace",
                    field_name=field_name,
                    suggestion="Ensure content is properly extracted and not empty"
                ))
        
        return issues
    
    def _validate_minimum_length_check(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Check minimum content length requirements"""
        issues = []
        min_lengths = {
            "question": 10,
            "explanation": 20,
            "default": 5
        }
        
        for field_name in fields:
            content = str(content_data.get(field_name, "")).strip()
            
            # Determine minimum length based on field type
            min_length = min_lengths.get("default", 5)
            for key, length in min_lengths.items():
                if key in field_name.lower():
                    min_length = length
                    break
            
            if len(content) < min_length:
                issues.append(ValidationIssue(
                    rule_name="minimum_length_check",
                    severity=ValidationSeverity.ERROR,
                    message=f"Content too short: {len(content)} characters (minimum: {min_length})",
                    field_name=field_name,
                    content_preview=content[:50] + "..." if len(content) > 50 else content,
                    suggestion=f"Content should be at least {min_length} characters long"
                ))
        
        return issues
    
    def _validate_maximum_length_check(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Check maximum content length limits"""
        issues = []
        max_lengths = {
            "question": 2000,
            "explanation": 5000,
            "option": 500,
            "default": 1000
        }
        
        for field_name in fields:
            content = str(content_data.get(field_name, "")).strip()
            
            # Determine maximum length based on field type
            max_length = max_lengths.get("default", 1000)
            for key, length in max_lengths.items():
                if key in field_name.lower():
                    max_length = length
                    break
            
            if len(content) > max_length:
                issues.append(ValidationIssue(
                    rule_name="maximum_length_check",
                    severity=ValidationSeverity.WARNING,
                    message=f"Content too long: {len(content)} characters (maximum: {max_length})",
                    field_name=field_name,
                    content_preview=content[:100] + "...",
                    suggestion=f"Consider truncating content to under {max_length} characters"
                ))
        
        return issues
    
    def _validate_html_tag_cleanup(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Check for residual HTML tags"""
        issues = []
        html_pattern = re.compile(r'<[^>]+>')
        
        for field_name in fields:
            content = str(content_data.get(field_name, ""))
            
            html_matches = html_pattern.findall(content)
            if html_matches:
                issues.append(ValidationIssue(
                    rule_name="html_tag_cleanup",
                    severity=ValidationSeverity.WARNING,
                    message=f"Found {len(html_matches)} HTML tags in content",
                    field_name=field_name,
                    content_preview=", ".join(html_matches[:3]) + ("..." if len(html_matches) > 3 else ""),
                    suggestion="Clean HTML tags from plain text content"
                ))
        
        return issues
    
    def _validate_encoding_issues(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Check for encoding issues and problematic characters"""
        issues = []
        
        # Common encoding issue patterns
        problematic_patterns = [
            (r'â€™', 'Encoding issue: apostrophe'),
            (r'â€œ|â€\x9d', 'Encoding issue: quotes'),
            (r'â€¢', 'Encoding issue: bullet point'),
            (r'\ufffd', 'Unicode replacement character'),
            (r'[^\x00-\x7F\u00A0-\uFFFF]', 'Invalid Unicode characters')
        ]
        
        for field_name in fields:
            content = str(content_data.get(field_name, ""))
            
            for pattern, description in problematic_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    issues.append(ValidationIssue(
                        rule_name="encoding_issues",
                        severity=ValidationSeverity.ERROR,
                        message=f"{description}: Found {len(matches)} instances",
                        field_name=field_name,
                        content_preview=", ".join(matches[:3]) + ("..." if len(matches) > 3 else ""),
                        suggestion="Fix encoding issues during extraction"
                    ))
        
        return issues
    
    def _validate_malformed_options(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Validate multiple choice options format"""
        issues = []
        
        for field_name in fields:
            content = content_data.get(field_name)
            
            # Handle different option formats
            if isinstance(content, list):
                options = content
            elif isinstance(content, str):
                # Try to parse options from string
                options = [opt.strip() for opt in content.split('\n') if opt.strip()]
                if len(options) <= 1:
                    # Try other separators
                    for sep in [';', '|', ',']:
                        options = [opt.strip() for opt in content.split(sep) if opt.strip()]
                        if len(options) > 1:
                            break
            else:
                options = []
            
            # Validate options
            if len(options) < 2:
                issues.append(ValidationIssue(
                    rule_name="malformed_options",
                    severity=ValidationSeverity.ERROR,
                    message=f"Insufficient options: Found {len(options)}, minimum 2 required",
                    field_name=field_name,
                    suggestion="Ensure at least 2 options are extracted"
                ))
            elif len(options) > 10:
                issues.append(ValidationIssue(
                    rule_name="malformed_options",
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many options: Found {len(options)}, maximum 10 recommended",
                    field_name=field_name,
                    suggestion="Review if all extracted items are actually options"
                ))
            
            # Check for duplicate options
            if len(options) != len(set(options)):
                issues.append(ValidationIssue(
                    rule_name="malformed_options",
                    severity=ValidationSeverity.WARNING,
                    message="Duplicate options detected",
                    field_name=field_name,
                    suggestion="Remove duplicate options"
                ))
        
        return issues
    
    def _validate_question_format_validation(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Validate question structure and format"""
        issues = []
        
        for field_name in fields:
            content = str(content_data.get(field_name, "")).strip()
            
            # Check if content looks like a question
            question_indicators = ['?', 'what', 'which', 'how', 'why', 'where', 'when', 'who']
            has_question_marker = any(indicator in content.lower() for indicator in question_indicators)
            
            if not has_question_marker and len(content) > 20:  # Only flag longer content
                issues.append(ValidationIssue(
                    rule_name="question_format_validation",
                    severity=ValidationSeverity.WARNING,
                    message="Content doesn't appear to be a properly formatted question",
                    field_name=field_name,
                    content_preview=content[:100] + "..." if len(content) > 100 else content,
                    suggestion="Verify this is actually a question or add question formatting"
                ))
        
        return issues
    
    def _validate_readability_check(self, content_data: Dict[str, Any], fields: List[str]) -> List[ValidationIssue]:
        """Basic readability assessment"""
        issues = []
        
        for field_name in fields:
            content = str(content_data.get(field_name, "")).strip()
            
            if not content:
                continue
            
            # Calculate readability metrics
            words = content.split()
            sentences = [s for s in content.split('.') if s.strip()]
            
            if not sentences:
                continue
            
            avg_words_per_sentence = len(words) / len(sentences)
            avg_chars_per_word = sum(len(word) for word in words) / len(words) if words else 0
            
            # Flag potential readability issues
            if avg_words_per_sentence > 25:
                issues.append(ValidationIssue(
                    rule_name="readability_check",
                    severity=ValidationSeverity.INFO,
                    message=f"Long sentences detected: {avg_words_per_sentence:.1f} words per sentence on average",
                    field_name=field_name,
                    suggestion="Consider breaking long sentences for better readability"
                ))
            
            if avg_chars_per_word > 8:
                issues.append(ValidationIssue(
                    rule_name="readability_check",
                    severity=ValidationSeverity.INFO,
                    message=f"Complex vocabulary detected: {avg_chars_per_word:.1f} characters per word on average",
                    field_name=field_name,
                    suggestion="Consider using simpler vocabulary for better accessibility"
                ))
        
        return issues
    
    # =============================================================================
    # SCORE CALCULATION METHODS
    # =============================================================================
    
    def _calculate_completeness_score(self, content_data: Dict[str, Any], issues: List[ValidationIssue]) -> float:
        """Calculate content completeness score"""
        # Base score
        score = 100.0
        
        # Penalize based on critical and error issues
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 25
            elif issue.severity == ValidationSeverity.ERROR:
                score -= 15
        
        # Bonus for having comprehensive content
        field_count = len([v for v in content_data.values() if v and str(v).strip()])
        if field_count >= 4:  # question, options, answer, explanation
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _calculate_accuracy_score(self, content_data: Dict[str, Any], issues: List[ValidationIssue]) -> float:
        """Calculate content accuracy score"""
        score = 100.0
        
        # Penalize based on validation issues
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 20
            elif issue.severity == ValidationSeverity.ERROR:
                score -= 10
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 5
        
        return max(0.0, min(100.0, score))
    
    def _calculate_clarity_score(self, content_data: Dict[str, Any], issues: List[ValidationIssue]) -> float:
        """Calculate content clarity score"""
        score = 100.0
        
        # Penalize based on readability and format issues
        readability_issues = [i for i in issues if 'readability' in i.rule_name or 'format' in i.rule_name]
        score -= len(readability_issues) * 5
        
        # Check for clear, well-structured content
        text_content = self._extract_text_content(content_data)
        if text_content:
            # Bonus for proper punctuation
            if text_content.count('.') >= 1 and text_content.count('?') >= 1:
                score += 5
        
        return max(0.0, min(100.0, score))
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate basic readability score"""
        if not text or not text.strip():
            return 0.0
        
        words = text.split()
        sentences = [s for s in text.split('.') if s.strip()]
        
        if not words or not sentences:
            return 50.0  # Neutral score for very short text
        
        # Simple readability approximation
        avg_words_per_sentence = len(words) / len(sentences)
        avg_chars_per_word = sum(len(word) for word in words) / len(words)
        
        # Score based on complexity (lower complexity = higher readability)
        readability = 100 - (avg_words_per_sentence * 2) - (avg_chars_per_word * 3)
        
        return max(0.0, min(100.0, readability))
    
    def _extract_text_content(self, content_data: Dict[str, Any]) -> str:
        """Extract all text content for analysis"""
        text_parts = []
        
        for field_name, content in content_data.items():
            if content and str(content).strip():
                if isinstance(content, list):
                    text_parts.extend(str(item) for item in content if item)
                else:
                    text_parts.append(str(content))
        
        return " ".join(text_parts)
    
    def _determine_quality_gate(self, overall_score: float, issues: List[ValidationIssue]) -> str:
        """Determine quality gate based on score and issues"""
        # Check for critical issues
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            return "reject"
        
        # Score-based gating
        if overall_score >= self.quality_thresholds["auto_approve"]:
            return "approve"
        elif overall_score <= self.quality_thresholds["auto_reject"]:
            return "reject"
        else:
            return "review"
    
    def _generate_improvement_suggestions(self, issues: List[ValidationIssue], 
                                       content_data: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on issues"""
        suggestions = []
        
        # Collect unique suggestions from issues
        issue_suggestions = [issue.suggestion for issue in issues if issue.suggestion]
        suggestions.extend(list(set(issue_suggestions)))
        
        # Add general improvement suggestions
        text_content = self._extract_text_content(content_data)
        if text_content:
            word_count = len(text_content.split())
            if word_count < 20:
                suggestions.append("Add more detailed content to improve comprehensiveness")
            elif word_count > 500:
                suggestions.append("Consider condensing content for better readability")
        
        return suggestions[:5]  # Limit to top 5 suggestions

# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

def create_indiabix_validator() -> ContentValidator:
    """Create validator optimized for IndiaBix content"""
    custom_rules = [
        ValidationRule(
            name="indiabix_specific_format",
            description="IndiaBix-specific format validation",
            content_types=[ContentType.QUESTION_TEXT],
            severity=ValidationSeverity.WARNING
        )
    ]
    
    validator = ContentValidator("indiabix", custom_rules)
    
    # Adjust thresholds for IndiaBix
    validator.quality_thresholds.update({
        "auto_approve": 80.0,
        "auto_reject": 35.0,
        "min_word_count": 8
    })
    
    return validator

def create_geeksforgeeks_validator() -> ContentValidator:
    """Create validator optimized for GeeksforGeeks content"""
    custom_rules = [
        ValidationRule(
            name="code_snippet_validation",
            description="Validate code snippets in content",
            content_types=[ContentType.QUESTION_TEXT, ContentType.EXPLANATION],
            severity=ValidationSeverity.INFO
        )
    ]
    
    validator = ContentValidator("geeksforgeeks", custom_rules)
    
    # Adjust thresholds for GeeksforGeeks
    validator.quality_thresholds.update({
        "auto_approve": 75.0,
        "auto_reject": 40.0,
        "min_word_count": 12
    })
    
    return validator

def validate_extracted_question(question_data: Dict[str, Any], source: str = "general") -> ContentQualityScore:
    """
    Convenience function to validate a complete extracted question
    
    Args:
        question_data: Dictionary containing question fields
        source: Source name for specialized validation
        
    Returns:
        ContentQualityScore with validation results
    """
    if source.lower() == "indiabix":
        validator = create_indiabix_validator()
    elif source.lower() == "geeksforgeeks":
        validator = create_geeksforgeeks_validator()
    else:
        validator = ContentValidator(source)
    
    return validator.validate_content(question_data)