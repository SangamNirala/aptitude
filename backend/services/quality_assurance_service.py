"""
Content Quality Assurance System
Multi-layered quality scoring, validation, and human review queue management
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
from dataclasses import dataclass
import json
import uuid

from models.scraping_models import (
    RawExtractedQuestion, ProcessedScrapedQuestion, QualityGate,
    ExtractionQuality, ScrapingJob, DataSourceConfig
)
from models.question_models import EnhancedQuestion, QuestionCategory, DifficultyLevel
from ai_services.ai_coordinator import AICoordinator

logger = logging.getLogger(__name__)

class QualityAssuranceLevel(str, Enum):
    """Quality assurance processing levels"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"

class ReviewPriority(str, Enum):
    """Priority levels for human review queue"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ValidationRule(str, Enum):
    """Content validation rule types"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CLARITY = "clarity"
    UNIQUENESS = "uniqueness"
    RELEVANCE = "relevance"
    FORMATTING = "formatting"
    LANGUAGE = "language"
    STRUCTURE = "structure"

@dataclass
class QualityThresholds:
    """Quality score thresholds for different gates"""
    auto_approve_threshold: float = 85.0
    auto_reject_threshold: float = 50.0
    human_review_min: float = 50.0
    human_review_max: float = 85.0
    clarity_threshold: float = 70.0
    relevance_threshold: float = 75.0
    completeness_threshold: float = 80.0

@dataclass
class ValidationRuleConfig:
    """Configuration for a validation rule"""
    rule_type: ValidationRule
    weight: float = 1.0
    threshold: float = 70.0
    is_required: bool = True
    error_penalty: float = 10.0
    description: str = ""

@dataclass
class QualityAssessmentResult:
    """Result of quality assessment"""
    overall_score: float
    dimension_scores: Dict[str, float]
    quality_gate: QualityGate
    validation_results: Dict[str, Any]
    recommendations: List[str]
    confidence_level: float
    processing_metadata: Dict[str, Any]

@dataclass
class HumanReviewItem:
    """Item in human review queue"""
    id: str
    question_id: str
    priority: ReviewPriority
    created_at: datetime
    assigned_to: Optional[str] = None
    review_category: str = "quality_check"
    quality_concerns: List[str] = None
    estimated_review_time: int = 300  # seconds
    context_data: Dict[str, Any] = None
    deadline: Optional[datetime] = None

class SourceReliabilityTracker:
    """Tracks and scores source reliability over time"""
    
    def __init__(self):
        self.source_metrics: Dict[str, Dict[str, Any]] = {}
        self.reliability_weights = {
            "quality_consistency": 0.25,
            "uptime_reliability": 0.20,
            "content_uniqueness": 0.20,
            "extraction_success_rate": 0.15,
            "processing_stability": 0.10,
            "duplicate_ratio": 0.10
        }
    
    def update_source_metrics(self, source_id: str, metrics: Dict[str, Any]):
        """Update metrics for a source"""
        if source_id not in self.source_metrics:
            self.source_metrics[source_id] = {
                "total_questions": 0,
                "quality_scores": [],
                "extraction_failures": 0,
                "processing_errors": 0,
                "duplicate_detections": 0,
                "last_updated": datetime.utcnow(),
                "reliability_trend": []
            }
        
        source_data = self.source_metrics[source_id]
        source_data.update(metrics)
        source_data["last_updated"] = datetime.utcnow()
    
    def calculate_reliability_score(self, source_id: str) -> Dict[str, Any]:
        """Calculate comprehensive reliability score for a source"""
        if source_id not in self.source_metrics:
            return {"reliability_score": 100.0, "confidence": 0.0, "assessment": "no_data"}
        
        metrics = self.source_metrics[source_id]
        
        # Quality Consistency (0-100)
        quality_scores = metrics.get("quality_scores", [])
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            quality_std = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
            quality_consistency = max(0, avg_quality - (quality_std * 2))  # Penalize inconsistency
        else:
            quality_consistency = 50.0
        
        # Extraction Success Rate
        total_attempts = metrics.get("total_questions", 0)
        extraction_failures = metrics.get("extraction_failures", 0)
        extraction_success_rate = ((total_attempts - extraction_failures) / max(1, total_attempts)) * 100
        
        # Processing Stability
        processing_errors = metrics.get("processing_errors", 0)
        processing_stability = max(0, 100 - (processing_errors / max(1, total_attempts) * 100))
        
        # Content Uniqueness (inverse of duplicate ratio)
        duplicate_detections = metrics.get("duplicate_detections", 0)
        content_uniqueness = max(0, 100 - (duplicate_detections / max(1, total_attempts) * 100))
        
        # Uptime Reliability (based on recent activity)
        uptime_reliability = 100.0  # Simplified - could integrate with monitoring
        
        # Calculate weighted score
        weighted_score = (
            quality_consistency * self.reliability_weights["quality_consistency"] +
            uptime_reliability * self.reliability_weights["uptime_reliability"] +
            content_uniqueness * self.reliability_weights["content_uniqueness"] +
            extraction_success_rate * self.reliability_weights["extraction_success_rate"] +
            processing_stability * self.reliability_weights["processing_stability"] +
            (100 - (duplicate_detections / max(1, total_attempts) * 100)) * self.reliability_weights["duplicate_ratio"]
        )
        
        # Calculate confidence based on data volume
        confidence = min(1.0, total_attempts / 100.0)  # Higher confidence with more data
        
        # Assessment category
        if weighted_score >= 90:
            assessment = "excellent"
        elif weighted_score >= 80:
            assessment = "good"
        elif weighted_score >= 70:
            assessment = "acceptable"
        elif weighted_score >= 60:
            assessment = "concerning"
        else:
            assessment = "poor"
        
        return {
            "reliability_score": weighted_score,
            "confidence": confidence,
            "assessment": assessment,
            "component_scores": {
                "quality_consistency": quality_consistency,
                "extraction_success_rate": extraction_success_rate,
                "processing_stability": processing_stability,
                "content_uniqueness": content_uniqueness,
                "uptime_reliability": uptime_reliability
            },
            "data_points": total_attempts,
            "last_updated": metrics["last_updated"].isoformat()
        }

class ContentQualityAssuranceService:
    """
    Comprehensive Content Quality Assurance System
    
    Features:
    1. Multi-layered quality scoring and validation
    2. Quality gate implementation (auto-approve/reject/review)
    3. Source reliability scoring and tracking
    4. Content validation rules engine
    5. Human review queue management
    6. Quality trend analysis and recommendations
    """
    
    def __init__(self, 
                 quality_level: QualityAssuranceLevel = QualityAssuranceLevel.STANDARD,
                 custom_thresholds: Optional[QualityThresholds] = None):
        """
        Initialize Quality Assurance Service
        
        Args:
            quality_level: Level of quality assurance to apply
            custom_thresholds: Custom quality thresholds (optional)
        """
        try:
            self.ai_coordinator = AICoordinator()
            self.quality_level = quality_level
            self.thresholds = custom_thresholds or self._get_default_thresholds(quality_level)
            
            # Initialize components
            self.source_reliability_tracker = SourceReliabilityTracker()
            self.human_review_queue: List[HumanReviewItem] = []
            self.validation_rules = self._initialize_validation_rules()
            
            # Statistics tracking
            self.qa_stats = {
                "total_assessments": 0,
                "auto_approved": 0,
                "auto_rejected": 0,
                "human_review_required": 0,
                "avg_processing_time": 0.0,
                "quality_distribution": {},
                "rule_violations": {},
                "source_reliability_trends": {}
            }
            
            logger.info(f"ContentQualityAssuranceService initialized with {quality_level.value} level")
            
        except Exception as e:
            logger.error(f"Error initializing ContentQualityAssuranceService: {str(e)}")
            raise
    
    async def comprehensive_quality_assessment(self, 
                                             question_data: Dict[str, Any],
                                             context: Optional[Dict[str, Any]] = None) -> QualityAssessmentResult:
        """
        Perform comprehensive quality assessment on a question
        
        Args:
            question_data: Question data to assess
            context: Additional context for assessment
            
        Returns:
            Comprehensive quality assessment result
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Starting comprehensive quality assessment for question: {question_data.get('id', 'unknown')}")
            
            # Step 1: Run all validation rules
            validation_results = await self._run_validation_rules(question_data, context)
            
            # Step 2: Calculate dimension scores
            dimension_scores = await self._calculate_dimension_scores(question_data, validation_results)
            
            # Step 3: Determine overall quality score
            overall_score = self._calculate_overall_quality_score(dimension_scores, validation_results)
            
            # Step 4: Apply quality gate logic
            quality_gate = self._determine_quality_gate(overall_score, dimension_scores, validation_results)
            
            # Step 5: Generate recommendations
            recommendations = self._generate_quality_recommendations(dimension_scores, validation_results)
            
            # Step 6: Calculate confidence level
            confidence_level = self._calculate_confidence_level(validation_results, context)
            
            # Step 7: Prepare processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            processing_metadata = {
                "processing_time_seconds": processing_time,
                "quality_level_used": self.quality_level.value,
                "validation_rules_applied": len(self.validation_rules),
                "thresholds_used": {
                    "auto_approve": self.thresholds.auto_approve_threshold,
                    "auto_reject": self.thresholds.auto_reject_threshold
                },
                "assessment_timestamp": datetime.utcnow().isoformat()
            }
            
            # Create assessment result
            assessment_result = QualityAssessmentResult(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                quality_gate=quality_gate,
                validation_results=validation_results,
                recommendations=recommendations,
                confidence_level=confidence_level,
                processing_metadata=processing_metadata
            )
            
            # Update statistics
            self._update_qa_statistics(assessment_result)
            
            # Handle human review queue if needed
            if quality_gate == QualityGate.HUMAN_REVIEW:
                await self._add_to_human_review_queue(question_data, assessment_result, context)
            
            logger.debug(f"Quality assessment completed: Score={overall_score:.1f}, Gate={quality_gate.value}")
            
            return assessment_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive quality assessment: {str(e)}")
            
            # Return failure result
            return QualityAssessmentResult(
                overall_score=0.0,
                dimension_scores={"error": 0.0},
                quality_gate=QualityGate.AUTO_REJECT,
                validation_results={"error": str(e)},
                recommendations=[f"Assessment failed: {str(e)}"],
                confidence_level=0.0,
                processing_metadata={"error": True, "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()}
            )
    
    async def batch_quality_assessment(self, 
                                     questions: List[Dict[str, Any]], 
                                     batch_size: int = 10) -> Dict[str, Any]:
        """
        Perform batch quality assessment on multiple questions
        
        Args:
            questions: List of questions to assess
            batch_size: Number of questions to process concurrently
            
        Returns:
            Batch assessment results with statistics
        """
        logger.info(f"Starting batch quality assessment for {len(questions)} questions")
        
        start_time = datetime.utcnow()
        assessment_results = []
        batch_stats = {
            "total_questions": len(questions),
            "processed_successfully": 0,
            "failed_assessments": 0,
            "quality_distribution": {
                "auto_approved": 0,
                "auto_rejected": 0,
                "human_review_required": 0
            },
            "avg_quality_score": 0.0,
            "processing_start": start_time,
            "processing_end": None,
            "total_duration_seconds": 0.0
        }
        
        try:
            # Process in batches for resource management
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i + batch_size]
                batch_number = (i // batch_size) + 1
                total_batches = (len(questions) + batch_size - 1) // batch_size
                
                logger.info(f"Processing quality assessment batch {batch_number}/{total_batches} with {len(batch)} questions")
                
                # Process batch concurrently
                batch_tasks = [self.comprehensive_quality_assessment(question) for question in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch assessment exception: {result}")
                        batch_stats["failed_assessments"] += 1
                    else:
                        assessment_results.append(result)
                        batch_stats["processed_successfully"] += 1
                        
                        # Update quality distribution
                        gate = result.quality_gate
                        if gate == QualityGate.AUTO_APPROVE:
                            batch_stats["quality_distribution"]["auto_approved"] += 1
                        elif gate == QualityGate.AUTO_REJECT:
                            batch_stats["quality_distribution"]["auto_rejected"] += 1
                        elif gate == QualityGate.HUMAN_REVIEW:
                            batch_stats["quality_distribution"]["human_review_required"] += 1
                
                # Small delay between batches
                await asyncio.sleep(0.5)
            
            # Calculate final statistics
            batch_stats["processing_end"] = datetime.utcnow()
            batch_stats["total_duration_seconds"] = (batch_stats["processing_end"] - batch_stats["processing_start"]).total_seconds()
            
            # Average quality score
            quality_scores = [r.overall_score for r in assessment_results if r.overall_score > 0]
            batch_stats["avg_quality_score"] = statistics.mean(quality_scores) if quality_scores else 0.0
            
            logger.info(f"Batch quality assessment completed: {batch_stats['processed_successfully']}/{batch_stats['total_questions']} successful")
            
            return {
                "status": "completed",
                "assessment_results": assessment_results,
                "batch_statistics": batch_stats,
                "quality_summary": self._generate_batch_quality_summary(batch_stats, assessment_results)
            }
            
        except Exception as e:
            logger.error(f"Error in batch quality assessment: {str(e)}")
            batch_stats["processing_end"] = datetime.utcnow()
            batch_stats["total_duration_seconds"] = (batch_stats["processing_end"] - batch_stats["processing_start"]).total_seconds()
            
            return {
                "status": "failed",
                "error": str(e),
                "assessment_results": assessment_results,
                "batch_statistics": batch_stats
            }
    
    async def update_source_reliability(self, source_id: str, 
                                      quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update reliability metrics for a source
        
        Args:
            source_id: ID of the source to update
            quality_data: Quality and performance data for the source
            
        Returns:
            Updated reliability assessment
        """
        try:
            logger.debug(f"Updating source reliability for: {source_id}")
            
            # Update source metrics
            self.source_reliability_tracker.update_source_metrics(source_id, quality_data)
            
            # Calculate new reliability score
            reliability_assessment = self.source_reliability_tracker.calculate_reliability_score(source_id)
            
            # Update QA statistics
            self.qa_stats["source_reliability_trends"][source_id] = {
                "reliability_score": reliability_assessment["reliability_score"],
                "assessment": reliability_assessment["assessment"],
                "updated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Source reliability updated for {source_id}: {reliability_assessment['reliability_score']:.1f} ({reliability_assessment['assessment']})")
            
            return reliability_assessment
            
        except Exception as e:
            logger.error(f"Error updating source reliability: {str(e)}")
            return {"error": str(e)}
    
    async def manage_human_review_queue(self, 
                                      action: str = "get_queue",
                                      item_id: Optional[str] = None,
                                      reviewer_id: Optional[str] = None,
                                      review_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Manage human review queue operations
        
        Args:
            action: Action to perform (get_queue, assign, complete, prioritize)
            item_id: ID of review item (for specific actions)
            reviewer_id: ID of reviewer (for assignment)
            review_data: Review completion data
            
        Returns:
            Queue management result
        """
        try:
            logger.debug(f"Managing human review queue: action={action}")
            
            if action == "get_queue":
                return await self._get_review_queue_status()
            
            elif action == "assign" and item_id and reviewer_id:
                return await self._assign_review_item(item_id, reviewer_id)
            
            elif action == "complete" and item_id and review_data:
                return await self._complete_review_item(item_id, review_data)
            
            elif action == "prioritize":
                return await self._prioritize_review_queue()
            
            elif action == "get_stats":
                return self._get_review_queue_statistics()
            
            else:
                return {"error": "Invalid action or missing parameters"}
        
        except Exception as e:
            logger.error(f"Error in human review queue management: {str(e)}")
            return {"error": str(e)}
    
    def get_quality_assurance_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive QA dashboard data
        
        Returns:
            Dashboard data with statistics and insights
        """
        try:
            # Current queue status
            queue_stats = self._get_review_queue_statistics()
            
            # Source reliability overview
            source_reliability = {}
            for source_id in self.source_reliability_tracker.source_metrics:
                reliability_assessment = self.source_reliability_tracker.calculate_reliability_score(source_id)
                source_reliability[source_id] = reliability_assessment
            
            # Quality trends
            quality_trends = self._analyze_quality_trends()
            
            # System recommendations
            system_recommendations = self._generate_system_recommendations()
            
            dashboard_data = {
                "qa_statistics": self.qa_stats.copy(),
                "quality_thresholds": {
                    "auto_approve": self.thresholds.auto_approve_threshold,
                    "auto_reject": self.thresholds.auto_reject_threshold,
                    "human_review_min": self.thresholds.human_review_min,
                    "human_review_max": self.thresholds.human_review_max
                },
                "human_review_queue": queue_stats,
                "source_reliability": source_reliability,
                "quality_trends": quality_trends,
                "system_recommendations": system_recommendations,
                "system_health": {
                    "total_sources_monitored": len(self.source_reliability_tracker.source_metrics),
                    "avg_processing_time": self.qa_stats["avg_processing_time"],
                    "quality_assurance_level": self.quality_level.value
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating QA dashboard: {str(e)}")
            return {"error": str(e)}
    
    # Helper Methods
    
    def _get_default_thresholds(self, quality_level: QualityAssuranceLevel) -> QualityThresholds:
        """Get default quality thresholds based on quality level"""
        
        if quality_level == QualityAssuranceLevel.BASIC:
            return QualityThresholds(
                auto_approve_threshold=75.0,
                auto_reject_threshold=40.0,
                clarity_threshold=60.0,
                relevance_threshold=65.0,
                completeness_threshold=70.0
            )
        elif quality_level == QualityAssuranceLevel.STRICT:
            return QualityThresholds(
                auto_approve_threshold=90.0,
                auto_reject_threshold=60.0,
                clarity_threshold=80.0,
                relevance_threshold=85.0,
                completeness_threshold=85.0
            )
        else:  # STANDARD
            return QualityThresholds()
    
    def _initialize_validation_rules(self) -> List[ValidationRuleConfig]:
        """Initialize validation rules based on quality level"""
        
        base_rules = [
            ValidationRuleConfig(
                rule_type=ValidationRule.COMPLETENESS,
                weight=1.5,
                threshold=self.thresholds.completeness_threshold,
                description="Check if question has all required components"
            ),
            ValidationRuleConfig(
                rule_type=ValidationRule.CLARITY,
                weight=1.3,
                threshold=self.thresholds.clarity_threshold,
                description="Assess question clarity and readability"
            ),
            ValidationRuleConfig(
                rule_type=ValidationRule.RELEVANCE,
                weight=1.2,
                threshold=self.thresholds.relevance_threshold,
                description="Check question relevance to category"
            ),
            ValidationRuleConfig(
                rule_type=ValidationRule.FORMATTING,
                weight=1.0,
                threshold=70.0,
                description="Validate question formatting and structure"
            ),
            ValidationRuleConfig(
                rule_type=ValidationRule.LANGUAGE,
                weight=0.8,
                threshold=75.0,
                description="Check language quality and grammar"
            )
        ]
        
        if self.quality_level in [QualityAssuranceLevel.STANDARD, QualityAssuranceLevel.STRICT]:
            base_rules.extend([
                ValidationRuleConfig(
                    rule_type=ValidationRule.ACCURACY,
                    weight=1.4,
                    threshold=80.0,
                    description="Verify factual accuracy of content"
                ),
                ValidationRuleConfig(
                    rule_type=ValidationRule.UNIQUENESS,
                    weight=1.1,
                    threshold=75.0,
                    description="Check for uniqueness and originality"
                )
            ])
        
        if self.quality_level == QualityAssuranceLevel.STRICT:
            base_rules.append(
                ValidationRuleConfig(
                    rule_type=ValidationRule.STRUCTURE,
                    weight=1.0,
                    threshold=85.0,
                    description="Validate advanced question structure"
                )
            )
        
        return base_rules
    
    async def _run_validation_rules(self, 
                                  question_data: Dict[str, Any], 
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run all validation rules on question data"""
        
        validation_results = {
            "rule_scores": {},
            "rule_violations": [],
            "passed_rules": [],
            "total_rules_applied": len(self.validation_rules)
        }
        
        for rule in self.validation_rules:
            try:
                score = await self._apply_validation_rule(rule, question_data, context)
                validation_results["rule_scores"][rule.rule_type.value] = {
                    "score": score,
                    "threshold": rule.threshold,
                    "weight": rule.weight,
                    "passed": score >= rule.threshold
                }
                
                if score >= rule.threshold:
                    validation_results["passed_rules"].append(rule.rule_type.value)
                else:
                    validation_results["rule_violations"].append({
                        "rule": rule.rule_type.value,
                        "score": score,
                        "threshold": rule.threshold,
                        "description": rule.description
                    })
                    
            except Exception as e:
                logger.warning(f"Error applying validation rule {rule.rule_type.value}: {str(e)}")
                validation_results["rule_violations"].append({
                    "rule": rule.rule_type.value,
                    "error": str(e)
                })
        
        return validation_results
    
    async def _apply_validation_rule(self, 
                                   rule: ValidationRuleConfig, 
                                   question_data: Dict[str, Any],
                                   context: Optional[Dict[str, Any]] = None) -> float:
        """Apply a specific validation rule and return score"""
        
        if rule.rule_type == ValidationRule.COMPLETENESS:
            return self._validate_completeness(question_data)
        
        elif rule.rule_type == ValidationRule.CLARITY:
            return await self._validate_clarity(question_data)
        
        elif rule.rule_type == ValidationRule.RELEVANCE:
            return await self._validate_relevance(question_data, context)
        
        elif rule.rule_type == ValidationRule.FORMATTING:
            return self._validate_formatting(question_data)
        
        elif rule.rule_type == ValidationRule.LANGUAGE:
            return self._validate_language_quality(question_data)
        
        elif rule.rule_type == ValidationRule.ACCURACY:
            return await self._validate_accuracy(question_data)
        
        elif rule.rule_type == ValidationRule.UNIQUENESS:
            return await self._validate_uniqueness(question_data, context)
        
        elif rule.rule_type == ValidationRule.STRUCTURE:
            return self._validate_structure(question_data)
        
        else:
            return 50.0  # Default score for unknown rules
    
    def _validate_completeness(self, question_data: Dict[str, Any]) -> float:
        """Validate question completeness"""
        score = 0.0
        max_score = 100.0
        
        # Check question text
        question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
        if question_text and len(question_text.strip()) > 10:
            score += 30.0
        
        # Check options
        options = question_data.get("options", question_data.get("raw_options", []))
        if options and len(options) >= 2:
            score += 25.0
            if len(options) >= 4:  # Prefer 4+ options
                score += 10.0
        
        # Check correct answer
        correct_answer = question_data.get("correct_answer", question_data.get("raw_correct_answer"))
        if correct_answer:
            score += 20.0
        
        # Check category/classification
        category = question_data.get("category", question_data.get("detected_category"))
        if category:
            score += 10.0
        
        # Check explanation (bonus)
        explanation = question_data.get("explanation", question_data.get("raw_explanation"))
        if explanation:
            score += 5.0
        
        return min(score, max_score)
    
    async def _validate_clarity(self, question_data: Dict[str, Any]) -> float:
        """Validate question clarity using AI assessment"""
        try:
            question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
            
            if not question_text:
                return 0.0
            
            # Basic clarity checks
            score = 50.0  # Base score
            
            # Length check (not too short or too long)
            word_count = len(question_text.split())
            if 10 <= word_count <= 100:
                score += 15.0
            elif word_count > 5:
                score += 5.0
            
            # Check for clear question structure
            if any(marker in question_text.lower() for marker in ["?", "which", "what", "how", "why", "find", "calculate"]):
                score += 10.0
            
            # Check for excessive technical jargon (simplified)
            technical_terms = len([word for word in question_text.split() if len(word) > 12])
            if technical_terms / max(1, word_count) < 0.2:  # Less than 20% long technical terms
                score += 10.0
            
            # Check for proper grammar indicators (simplified)
            if question_text[0].isupper() and question_text.endswith(("?", ".")):
                score += 5.0
            
            # Check readability (simplified - could use AI for more sophisticated analysis)
            sentences = question_text.split(".")
            avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
            if avg_sentence_length < 25:  # Reasonable sentence length
                score += 10.0
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.warning(f"Error in clarity validation: {str(e)}")
            return 50.0
    
    async def _validate_relevance(self, question_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> float:
        """Validate question relevance to its category"""
        try:
            category = question_data.get("category", question_data.get("detected_category", ""))
            question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
            
            if not category or not question_text:
                return 50.0
            
            # Basic relevance scoring (could be enhanced with AI)
            score = 60.0  # Base score
            
            # Check for category-specific keywords
            category_keywords = {
                "quantitative": ["number", "calculate", "percentage", "ratio", "average", "sum", "difference", "multiply"],
                "logical": ["pattern", "sequence", "logic", "reasoning", "conclusion", "if", "then", "because"],
                "verbal": ["meaning", "synonym", "antonym", "sentence", "grammar", "vocabulary", "reading"],
                "general": ["knowledge", "fact", "information", "about", "related", "concerning"]
            }
            
            relevant_keywords = category_keywords.get(category.lower(), [])
            found_keywords = sum(1 for keyword in relevant_keywords if keyword.lower() in question_text.lower())
            
            if found_keywords > 0:
                score += min(30.0, found_keywords * 10.0)  # Up to 30 points for keywords
            
            # Check if answer format matches category expectations
            options = question_data.get("options", [])
            if category.lower() == "quantitative" and options:
                numeric_options = sum(1 for opt in options if any(char.isdigit() for char in str(opt)))
                if numeric_options > 0:
                    score += 10.0
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.warning(f"Error in relevance validation: {str(e)}")
            return 50.0
    
    def _validate_formatting(self, question_data: Dict[str, Any]) -> float:
        """Validate question formatting and structure"""
        score = 0.0
        
        question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
        options = question_data.get("options", question_data.get("raw_options", []))
        
        # Question text formatting
        if question_text:
            # Check capitalization
            if question_text[0].isupper():
                score += 10.0
            
            # Check ending punctuation
            if question_text.rstrip().endswith(("?", ".", ":")):
                score += 10.0
            
            # Check for excessive whitespace or formatting issues
            if len(question_text.split()) == len(question_text.strip().split()):
                score += 10.0
            
            # Check for HTML artifacts
            if not any(artifact in question_text for artifact in ["<", ">", "&nbsp;", "\\n", "\\r"]):
                score += 15.0
        
        # Options formatting
        if options:
            valid_options = [opt for opt in options if opt and len(str(opt).strip()) > 0]
            if len(valid_options) == len(options):  # All options are valid
                score += 20.0
            
            # Check for consistent option formatting
            option_lengths = [len(str(opt).strip()) for opt in valid_options]
            if option_lengths and max(option_lengths) / max(1, min(option_lengths)) < 5:  # Reasonable length variation
                score += 15.0
        
        # Overall structure
        if question_text and options:
            score += 20.0  # Bonus for having both components
        
        return min(score, 100.0)
    
    def _validate_language_quality(self, question_data: Dict[str, Any]) -> float:
        """Validate language quality and grammar (simplified)"""
        score = 60.0  # Base score
        
        question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
        
        if not question_text:
            return 0.0
        
        # Basic language quality checks
        text = question_text.lower()
        
        # Check for repeated words (potential error)
        words = text.split()
        unique_words = set(words)
        if len(unique_words) / max(1, len(words)) > 0.7:  # At least 70% unique words
            score += 15.0
        
        # Check for basic sentence structure
        if any(word in words for word in ["the", "a", "an", "is", "are", "was", "were"]):
            score += 10.0
        
        # Check for excessive ALL CAPS (indicates poor formatting)
        if sum(1 for c in question_text if c.isupper()) / max(1, len(question_text)) < 0.3:
            score += 10.0
        
        # Check spelling (simplified - look for common misspellings)
        common_misspellings = ["recieve", "seperate", "occured", "definately", "accomodate"]
        if not any(misspelling in text for misspelling in common_misspellings):
            score += 5.0
        
        return min(score, 100.0)
    
    async def _validate_accuracy(self, question_data: Dict[str, Any]) -> float:
        """Validate factual accuracy (simplified - would need domain-specific knowledge)"""
        try:
            # This is a simplified accuracy check
            # In production, would use domain-specific fact checking
            
            score = 70.0  # Base assumption of reasonable accuracy
            
            question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
            correct_answer = question_data.get("correct_answer", question_data.get("raw_correct_answer"))
            options = question_data.get("options", question_data.get("raw_options", []))
            
            # Basic consistency checks
            if correct_answer and options:
                # Check if correct answer is among options
                correct_in_options = any(str(correct_answer).lower().strip() in str(opt).lower().strip() 
                                       for opt in options)
                if correct_in_options:
                    score += 20.0
                else:
                    score -= 30.0  # Major penalty for inconsistency
            
            # Check for obviously incorrect patterns (simplified)
            problematic_patterns = ["always never", "impossible possible", "100% 0%"]
            if not any(pattern in question_text.lower() for pattern in problematic_patterns):
                score += 10.0
            
            return max(0.0, min(score, 100.0))
            
        except Exception as e:
            logger.warning(f"Error in accuracy validation: {str(e)}")
            return 70.0
    
    async def _validate_uniqueness(self, question_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> float:
        """Validate content uniqueness (simplified)"""
        try:
            # This would typically use the duplicate detection service
            # For now, implement basic uniqueness checks
            
            question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
            
            if not question_text:
                return 0.0
            
            # Basic uniqueness score
            score = 80.0
            
            # Check for generic/template questions
            generic_patterns = ["fill in the blank", "choose the correct option", "select the right answer"]
            if any(pattern in question_text.lower() for pattern in generic_patterns):
                score -= 20.0
            
            # Check for overly short questions (likely not unique)
            if len(question_text.split()) < 5:
                score -= 15.0
            
            # Check for unique content indicators
            if any(indicator in question_text.lower() for indicator in ["specific", "particular", "given", "following"]):
                score += 10.0
            
            return max(0.0, min(score, 100.0))
            
        except Exception as e:
            logger.warning(f"Error in uniqueness validation: {str(e)}")
            return 50.0
    
    def _validate_structure(self, question_data: Dict[str, Any]) -> float:
        """Validate advanced question structure"""
        score = 0.0
        
        question_text = question_data.get("question_text", question_data.get("raw_question_text", ""))
        options = question_data.get("options", question_data.get("raw_options", []))
        correct_answer = question_data.get("correct_answer", question_data.get("raw_correct_answer"))
        explanation = question_data.get("explanation", question_data.get("raw_explanation"))
        
        # Question structure components
        components_present = 0
        
        if question_text and len(question_text.strip()) > 15:
            components_present += 1
            score += 25.0
        
        if options and len(options) >= 3:
            components_present += 1
            score += 25.0
        
        if correct_answer:
            components_present += 1
            score += 25.0
        
        if explanation:
            components_present += 1
            score += 15.0
        
        # Bonus for complete structure
        if components_present >= 3:
            score += 10.0
        
        return min(score, 100.0)
    
    async def _calculate_dimension_scores(self, 
                                        question_data: Dict[str, Any], 
                                        validation_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality dimension scores"""
        
        rule_scores = validation_results.get("rule_scores", {})
        
        # Map validation rules to quality dimensions
        dimension_scores = {
            "completeness": 0.0,
            "clarity": 0.0,
            "relevance": 0.0,
            "accuracy": 0.0,
            "formatting": 0.0,
            "language_quality": 0.0,
            "structure": 0.0,
            "uniqueness": 0.0
        }
        
        # Direct mapping from validation rules
        for rule_name, rule_result in rule_scores.items():
            if rule_name in dimension_scores:
                dimension_scores[rule_name] = rule_result["score"]
        
        # Calculate composite dimensions
        if "completeness" not in rule_scores and "structure" in rule_scores:
            dimension_scores["completeness"] = rule_scores["structure"]["score"]
        
        return dimension_scores
    
    def _calculate_overall_quality_score(self, 
                                       dimension_scores: Dict[str, float], 
                                       validation_results: Dict[str, Any]) -> float:
        """Calculate overall quality score using weighted dimensions"""
        
        # Dimension weights based on quality level
        weights = {
            "completeness": 0.20,
            "clarity": 0.18,
            "relevance": 0.15,
            "accuracy": 0.15,
            "formatting": 0.10,
            "language_quality": 0.10,
            "structure": 0.07,
            "uniqueness": 0.05
        }
        
        # Calculate weighted score
        weighted_score = 0.0
        total_weight = 0.0
        
        for dimension, score in dimension_scores.items():
            if score > 0 and dimension in weights:
                weighted_score += score * weights[dimension]
                total_weight += weights[dimension]
        
        if total_weight == 0:
            return 0.0
        
        overall_score = weighted_score / total_weight
        
        # Apply penalties for rule violations
        violations = validation_results.get("rule_violations", [])
        for violation in violations:
            penalty = 5.0  # Base penalty per violation
            overall_score = max(0.0, overall_score - penalty)
        
        return min(100.0, overall_score)
    
    def _determine_quality_gate(self, 
                              overall_score: float, 
                              dimension_scores: Dict[str, float], 
                              validation_results: Dict[str, Any]) -> QualityGate:
        """Determine quality gate based on scores and thresholds"""
        
        # Check for automatic rejection conditions
        critical_violations = [
            v for v in validation_results.get("rule_violations", []) 
            if v.get("rule") in ["completeness", "accuracy"]
        ]
        
        if critical_violations or overall_score < self.thresholds.auto_reject_threshold:
            return QualityGate.AUTO_REJECT
        
        # Check for automatic approval
        if (overall_score >= self.thresholds.auto_approve_threshold and 
            dimension_scores.get("completeness", 0) >= self.thresholds.completeness_threshold and
            dimension_scores.get("clarity", 0) >= self.thresholds.clarity_threshold):
            return QualityGate.AUTO_APPROVE
        
        # Everything else goes to human review
        return QualityGate.HUMAN_REVIEW
    
    def _generate_quality_recommendations(self, 
                                        dimension_scores: Dict[str, float], 
                                        validation_results: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations"""
        
        recommendations = []
        
        # Dimension-based recommendations
        for dimension, score in dimension_scores.items():
            if score < 70.0:
                if dimension == "completeness":
                    recommendations.append("Ensure question includes all required components: question text, options, and correct answer")
                elif dimension == "clarity":
                    recommendations.append("Improve question clarity by simplifying language and structure")
                elif dimension == "relevance":
                    recommendations.append("Review question relevance to the assigned category")
                elif dimension == "formatting":
                    recommendations.append("Fix formatting issues such as capitalization and punctuation")
                elif dimension == "accuracy":
                    recommendations.append("Verify factual accuracy and answer consistency")
        
        # Violation-based recommendations
        violations = validation_results.get("rule_violations", [])
        for violation in violations:
            rule = violation.get("rule")
            if rule == "language_quality":
                recommendations.append("Review language quality and grammar")
            elif rule == "uniqueness":
                recommendations.append("Ensure content is unique and not duplicated")
        
        if not recommendations:
            recommendations.append("Quality appears acceptable - consider minor formatting improvements")
        
        return recommendations
    
    def _calculate_confidence_level(self, 
                                  validation_results: Dict[str, Any], 
                                  context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate confidence level for the assessment"""
        
        # Base confidence
        confidence = 0.8
        
        # Adjust based on validation completeness
        total_rules = validation_results.get("total_rules_applied", 1)
        successful_rules = len(validation_results.get("rule_scores", {}))
        
        rule_completion_rate = successful_rules / max(1, total_rules)
        confidence *= rule_completion_rate
        
        # Adjust based on data completeness
        if context and context.get("source_reliability"):
            source_confidence = context["source_reliability"] / 100.0
            confidence = (confidence + source_confidence) / 2
        
        # Penalize if many validation errors occurred
        if len(validation_results.get("rule_violations", [])) > total_rules * 0.5:
            confidence *= 0.7
        
        return max(0.1, min(1.0, confidence))
    
    async def _add_to_human_review_queue(self, 
                                       question_data: Dict[str, Any], 
                                       assessment_result: QualityAssessmentResult, 
                                       context: Optional[Dict[str, Any]] = None):
        """Add item to human review queue"""
        
        # Determine priority
        priority = ReviewPriority.MEDIUM
        
        if assessment_result.overall_score < 60.0:
            priority = ReviewPriority.HIGH
        elif assessment_result.overall_score > 80.0:
            priority = ReviewPriority.LOW
        
        # Check for critical issues
        critical_violations = [
            v for v in assessment_result.validation_results.get("rule_violations", []) 
            if v.get("rule") in ["accuracy", "completeness"]
        ]
        if critical_violations:
            priority = ReviewPriority.CRITICAL
        
        # Create review item
        review_item = HumanReviewItem(
            id=str(uuid.uuid4()),
            question_id=question_data.get("id", str(uuid.uuid4())),
            priority=priority,
            created_at=datetime.utcnow(),
            quality_concerns=assessment_result.recommendations,
            context_data={
                "overall_score": assessment_result.overall_score,
                "dimension_scores": assessment_result.dimension_scores,
                "validation_violations": assessment_result.validation_results.get("rule_violations", []),
                "source": question_data.get("source", "unknown")
            },
            deadline=datetime.utcnow() + timedelta(hours=24)  # Default 24-hour deadline
        )
        
        self.human_review_queue.append(review_item)
        
        logger.info(f"Added question {review_item.question_id} to human review queue with {priority.value} priority")
    
    async def _get_review_queue_status(self) -> Dict[str, Any]:
        """Get current human review queue status"""
        
        queue_stats = {
            "total_items": len(self.human_review_queue),
            "priority_distribution": {},
            "assigned_items": 0,
            "overdue_items": 0,
            "avg_wait_time_hours": 0.0,
            "oldest_item_age_hours": 0.0
        }
        
        if not self.human_review_queue:
            return queue_stats
        
        # Calculate statistics
        now = datetime.utcnow()
        wait_times = []
        
        for item in self.human_review_queue:
            # Priority distribution
            priority = item.priority.value
            queue_stats["priority_distribution"][priority] = queue_stats["priority_distribution"].get(priority, 0) + 1
            
            # Assignment tracking
            if item.assigned_to:
                queue_stats["assigned_items"] += 1
            
            # Overdue tracking
            if item.deadline and now > item.deadline:
                queue_stats["overdue_items"] += 1
            
            # Wait time calculation
            wait_time_hours = (now - item.created_at).total_seconds() / 3600
            wait_times.append(wait_time_hours)
        
        # Calculate averages
        if wait_times:
            queue_stats["avg_wait_time_hours"] = statistics.mean(wait_times)
            queue_stats["oldest_item_age_hours"] = max(wait_times)
        
        return queue_stats
    
    async def _assign_review_item(self, item_id: str, reviewer_id: str) -> Dict[str, Any]:
        """Assign a review item to a reviewer"""
        
        for item in self.human_review_queue:
            if item.id == item_id:
                item.assigned_to = reviewer_id
                return {
                    "status": "assigned",
                    "item_id": item_id,
                    "reviewer_id": reviewer_id,
                    "assigned_at": datetime.utcnow().isoformat()
                }
        
        return {"error": "Review item not found"}
    
    async def _complete_review_item(self, item_id: str, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a human review item"""
        
        for i, item in enumerate(self.human_review_queue):
            if item.id == item_id:
                # Remove from queue
                completed_item = self.human_review_queue.pop(i)
                
                # Log completion
                completion_data = {
                    "item_id": item_id,
                    "question_id": completed_item.question_id,
                    "reviewer_id": completed_item.assigned_to,
                    "review_decision": review_data.get("decision", "unknown"),
                    "review_notes": review_data.get("notes", ""),
                    "review_time_hours": (datetime.utcnow() - completed_item.created_at).total_seconds() / 3600,
                    "completed_at": datetime.utcnow().isoformat()
                }
                
                return {
                    "status": "completed",
                    "completion_data": completion_data
                }
        
        return {"error": "Review item not found"}
    
    async def _prioritize_review_queue(self) -> Dict[str, Any]:
        """Prioritize and reorganize the review queue"""
        
        # Sort queue by priority and age
        priority_order = {
            ReviewPriority.CRITICAL: 0,
            ReviewPriority.HIGH: 1,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 3
        }
        
        self.human_review_queue.sort(
            key=lambda item: (priority_order[item.priority], item.created_at)
        )
        
        return {
            "status": "prioritized",
            "queue_length": len(self.human_review_queue),
            "prioritized_at": datetime.utcnow().isoformat()
        }
    
    def _get_review_queue_statistics(self) -> Dict[str, Any]:
        """Get detailed review queue statistics"""
        
        stats = {
            "queue_length": len(self.human_review_queue),
            "priority_breakdown": {},
            "assignment_status": {"assigned": 0, "unassigned": 0},
            "overdue_count": 0,
            "avg_queue_time_hours": 0.0
        }
        
        if not self.human_review_queue:
            return stats
        
        now = datetime.utcnow()
        queue_times = []
        
        for item in self.human_review_queue:
            # Priority breakdown
            priority = item.priority.value
            stats["priority_breakdown"][priority] = stats["priority_breakdown"].get(priority, 0) + 1
            
            # Assignment status
            if item.assigned_to:
                stats["assignment_status"]["assigned"] += 1
            else:
                stats["assignment_status"]["unassigned"] += 1
            
            # Overdue tracking
            if item.deadline and now > item.deadline:
                stats["overdue_count"] += 1
            
            # Queue time
            queue_time = (now - item.created_at).total_seconds() / 3600
            queue_times.append(queue_time)
        
        if queue_times:
            stats["avg_queue_time_hours"] = statistics.mean(queue_times)
        
        return stats
    
    def _analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        
        # This would typically analyze historical data
        # For now, return current state analysis
        
        total_assessments = self.qa_stats["total_assessments"]
        
        if total_assessments == 0:
            return {"trend": "no_data", "analysis": "No assessments completed yet"}
        
        # Calculate approval rates
        approval_rate = (self.qa_stats["auto_approved"] / total_assessments) * 100
        rejection_rate = (self.qa_stats["auto_rejected"] / total_assessments) * 100
        review_rate = (self.qa_stats["human_review_required"] / total_assessments) * 100
        
        # Determine trend
        if approval_rate > 70:
            trend = "improving"
            analysis = f"High approval rate ({approval_rate:.1f}%) indicates good quality content"
        elif rejection_rate > 40:
            trend = "declining"
            analysis = f"High rejection rate ({rejection_rate:.1f}%) indicates quality concerns"
        else:
            trend = "stable"
            analysis = f"Balanced quality distribution with {review_rate:.1f}% requiring human review"
        
        return {
            "trend": trend,
            "analysis": analysis,
            "approval_rate": approval_rate,
            "rejection_rate": rejection_rate,
            "human_review_rate": review_rate,
            "total_assessments": total_assessments
        }
    
    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-level recommendations for quality improvement"""
        
        recommendations = []
        
        # Analyze approval rates
        total = self.qa_stats["total_assessments"]
        if total > 0:
            rejection_rate = (self.qa_stats["auto_rejected"] / total) * 100
            review_rate = (self.qa_stats["human_review_required"] / total) * 100
            
            if rejection_rate > 30:
                recommendations.append(
                    f"High rejection rate ({rejection_rate:.1f}%). Consider reviewing source quality "
                    "and extraction processes."
                )
            
            if review_rate > 50:
                recommendations.append(
                    f"High human review rate ({review_rate:.1f}%). Consider adjusting quality thresholds "
                    "or improving automated assessment."
                )
        
        # Review queue recommendations
        queue_length = len(self.human_review_queue)
        if queue_length > 50:
            recommendations.append(
                f"Large review queue ({queue_length} items). Consider increasing reviewer capacity "
                "or adjusting quality gates."
            )
        
        # Processing time recommendations
        if self.qa_stats["avg_processing_time"] > 5.0:
            recommendations.append(
                f"Slow processing time ({self.qa_stats['avg_processing_time']:.2f}s). "
                "Consider optimizing validation rules or using batch processing."
            )
        
        # Source reliability recommendations
        poor_sources = [
            source_id for source_id, trend in self.qa_stats["source_reliability_trends"].items()
            if trend.get("reliability_score", 100) < 70
        ]
        
        if poor_sources:
            recommendations.append(
                f"Sources with poor reliability detected: {', '.join(poor_sources)}. "
                "Review source configurations and extraction methods."
            )
        
        if not recommendations:
            recommendations.append("Quality assurance system operating optimally.")
        
        return recommendations
    
    def _update_qa_statistics(self, assessment_result: QualityAssessmentResult):
        """Update internal QA statistics"""
        
        self.qa_stats["total_assessments"] += 1
        
        gate = assessment_result.quality_gate
        if gate == QualityGate.AUTO_APPROVE:
            self.qa_stats["auto_approved"] += 1
        elif gate == QualityGate.AUTO_REJECT:
            self.qa_stats["auto_rejected"] += 1
        elif gate == QualityGate.HUMAN_REVIEW:
            self.qa_stats["human_review_required"] += 1
        
        # Update average processing time
        processing_time = assessment_result.processing_metadata.get("processing_time_seconds", 0.0)
        total_time = (self.qa_stats["avg_processing_time"] * (self.qa_stats["total_assessments"] - 1)) + processing_time
        self.qa_stats["avg_processing_time"] = total_time / self.qa_stats["total_assessments"]
        
        # Update quality distribution
        score_range = self._get_score_range(assessment_result.overall_score)
        self.qa_stats["quality_distribution"][score_range] = self.qa_stats["quality_distribution"].get(score_range, 0) + 1
        
        # Update rule violations
        violations = assessment_result.validation_results.get("rule_violations", [])
        for violation in violations:
            rule_name = violation.get("rule", "unknown")
            self.qa_stats["rule_violations"][rule_name] = self.qa_stats["rule_violations"].get(rule_name, 0) + 1
    
    def _get_score_range(self, score: float) -> str:
        """Get score range category for statistics"""
        if score >= 90:
            return "excellent_90+"
        elif score >= 80:
            return "good_80-90"
        elif score >= 70:
            return "acceptable_70-80"
        elif score >= 60:
            return "poor_60-70"
        else:
            return "very_poor_<60"
    
    def _generate_batch_quality_summary(self, 
                                      batch_stats: Dict[str, Any], 
                                      assessment_results: List[QualityAssessmentResult]) -> str:
        """Generate human-readable batch quality summary"""
        
        total = batch_stats["total_questions"]
        successful = batch_stats["processed_successfully"]
        avg_score = batch_stats["avg_quality_score"]
        
        distribution = batch_stats["quality_distribution"]
        approved = distribution["auto_approved"]
        rejected = distribution["auto_rejected"]
        review = distribution["human_review_required"]
        
        return (
            f"Processed {successful}/{total} questions with average quality score {avg_score:.1f}. "
            f"Results: {approved} auto-approved ({(approved/max(1,successful))*100:.1f}%), "
            f"{review} require human review ({(review/max(1,successful))*100:.1f}%), "
            f"{rejected} auto-rejected ({(rejected/max(1,successful))*100:.1f}%)."
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_quality_assurance_service(quality_level: QualityAssuranceLevel = QualityAssuranceLevel.STANDARD) -> ContentQualityAssuranceService:
    """Factory function to create quality assurance service"""
    return ContentQualityAssuranceService(quality_level=quality_level)

async def assess_question_quality(question_data: Dict[str, Any], 
                                quality_level: QualityAssuranceLevel = QualityAssuranceLevel.STANDARD) -> QualityAssessmentResult:
    """Convenience function for single question quality assessment"""
    service = create_quality_assurance_service(quality_level)
    return await service.comprehensive_quality_assessment(question_data)

async def batch_assess_quality(questions: List[Dict[str, Any]], 
                             quality_level: QualityAssuranceLevel = QualityAssuranceLevel.STANDARD) -> Dict[str, Any]:
    """Convenience function for batch quality assessment"""
    service = create_quality_assurance_service(quality_level)
    return await service.batch_quality_assessment(questions)