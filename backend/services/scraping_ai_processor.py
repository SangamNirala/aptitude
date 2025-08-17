"""
AI Content Processing Pipeline for Scraped Questions
Integrates existing AI coordinator with scraped content processing
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from dataclasses import asdict

from ai_services.ai_coordinator import AICoordinator
from models.scraping_models import (
    RawExtractedQuestion, ProcessedScrapedQuestion, QualityGate,
    ExtractionQuality, ScrapingJobStatus
)
from models.question_models import EnhancedQuestion, QuestionCategory, DifficultyLevel

logger = logging.getLogger(__name__)

class ScrapingAIProcessor:
    """
    AI Content Processing Pipeline for Scraped Questions
    
    Integrates existing AI coordinator with scraped content to:
    1. Process raw scraped questions through AI pipeline
    2. Apply quality assessment and gating
    3. Standardize content format
    4. Batch process for efficiency
    """
    
    def __init__(self):
        """Initialize the AI processor with existing AI coordinator"""
        try:
            self.ai_coordinator = AICoordinator()
            self.processing_stats = {
                "total_processed": 0,
                "auto_approved": 0,
                "auto_rejected": 0,
                "human_review_required": 0,
                "failed_processing": 0,
                "avg_processing_time": 0.0
            }
            logger.info("ScrapingAIProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ScrapingAIProcessor: {str(e)}")
            raise

    async def process_raw_question(self, raw_question: RawExtractedQuestion) -> ProcessedScrapedQuestion:
        """
        Process a single raw scraped question through the AI pipeline
        
        Args:
            raw_question: Raw extracted question data
            
        Returns:
            ProcessedScrapedQuestion with AI analysis and quality assessment
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing raw question {raw_question.id} from source {raw_question.source_id}")
            
            # Prepare question data for AI coordinator
            question_data = self._prepare_question_for_ai(raw_question)
            
            # Process through existing AI coordinator pipeline
            enhanced_question = await self.ai_coordinator.process_new_question_complete(question_data)
            
            # Apply quality assessment and gating
            quality_gate_result, quality_reasons = self._apply_quality_gates(enhanced_question)
            
            # Create processed question record
            processed_question = ProcessedScrapedQuestion(
                raw_question_id=raw_question.id,
                enhanced_question_id=enhanced_question.id if hasattr(enhanced_question, 'id') else None,
                quality_gate_result=quality_gate_result,
                quality_score=enhanced_question.ai_metrics.quality_score,
                quality_reasons=quality_reasons,
                processing_timestamp=datetime.utcnow(),
                processing_duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                ai_metadata={
                    "difficulty_score": enhanced_question.ai_metrics.difficulty_score,
                    "relevance_score": enhanced_question.ai_metrics.relevance_score,
                    "clarity_score": enhanced_question.ai_metrics.clarity_score,
                    "concepts": enhanced_question.metadata.concepts,
                    "estimated_time": enhanced_question.metadata.time_estimate
                }
            )
            
            # Update processing statistics
            self._update_processing_stats(quality_gate_result, (datetime.utcnow() - start_time).total_seconds())
            
            logger.info(f"Successfully processed question {raw_question.id}: Quality={quality_gate_result.value}, Score={enhanced_question.ai_metrics.quality_score:.1f}")
            
            return processed_question, enhanced_question
            
        except Exception as e:
            logger.error(f"Error processing raw question {raw_question.id}: {str(e)}")
            
            # Create failed processing record
            failed_processed = ProcessedScrapedQuestion(
                raw_question_id=raw_question.id,
                quality_gate_result=QualityGate.AUTO_REJECT,
                quality_score=0.0,
                quality_reasons=[f"Processing failed: {str(e)}"],
                processing_timestamp=datetime.utcnow(),
                processing_duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
            
            self._update_processing_stats(QualityGate.AUTO_REJECT, (datetime.utcnow() - start_time).total_seconds())
            return failed_processed, None

    async def batch_process_questions(
        self, 
        raw_questions: List[RawExtractedQuestion], 
        batch_size: int = 5,
        quality_threshold: float = 75.0
    ) -> Dict[str, Any]:
        """
        Process multiple raw questions in batches for efficiency
        
        Args:
            raw_questions: List of raw extracted questions
            batch_size: Number of questions to process concurrently
            quality_threshold: Minimum quality score for auto-approval
            
        Returns:
            Processing results with statistics and processed questions
        """
        logger.info(f"Starting batch processing of {len(raw_questions)} questions (batch_size={batch_size})")
        
        processed_questions = []
        enhanced_questions = []
        batch_stats = {
            "total_questions": len(raw_questions),
            "processed_successfully": 0,
            "failed_processing": 0,
            "auto_approved": 0,
            "auto_rejected": 0,
            "human_review_required": 0,
            "avg_quality_score": 0.0,
            "processing_start": datetime.utcnow(),
            "processing_end": None,
            "total_duration_seconds": 0.0
        }
        
        try:
            # Process in batches to manage resources and API rate limits
            for i in range(0, len(raw_questions), batch_size):
                batch = raw_questions[i:i + batch_size]
                batch_number = (i // batch_size) + 1
                total_batches = (len(raw_questions) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_number}/{total_batches} with {len(batch)} questions")
                
                # Process batch concurrently
                batch_tasks = [self.process_raw_question(question) for question in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing exception: {result}")
                        batch_stats["failed_processing"] += 1
                    else:
                        processed_question, enhanced_question = result
                        processed_questions.append(processed_question)
                        if enhanced_question:
                            enhanced_questions.append(enhanced_question)
                        batch_stats["processed_successfully"] += 1
                
                # Small delay between batches to respect API rate limits
                await asyncio.sleep(1.0)
            
            # Calculate final statistics
            batch_stats["processing_end"] = datetime.utcnow()
            batch_stats["total_duration_seconds"] = (batch_stats["processing_end"] - batch_stats["processing_start"]).total_seconds()
            
            # Quality distribution statistics
            quality_scores = [pq.quality_score for pq in processed_questions if pq.quality_score > 0]
            batch_stats["avg_quality_score"] = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Gate distribution
            for pq in processed_questions:
                if pq.quality_gate_result == QualityGate.AUTO_APPROVE:
                    batch_stats["auto_approved"] += 1
                elif pq.quality_gate_result == QualityGate.AUTO_REJECT:
                    batch_stats["auto_rejected"] += 1
                elif pq.quality_gate_result == QualityGate.HUMAN_REVIEW:
                    batch_stats["human_review_required"] += 1
            
            logger.info(f"Batch processing completed: {batch_stats['processed_successfully']}/{batch_stats['total_questions']} successful")
            
            return {
                "status": "completed",
                "processed_questions": processed_questions,
                "enhanced_questions": enhanced_questions,
                "statistics": batch_stats,
                "processing_summary": self._generate_processing_summary(batch_stats)
            }
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            batch_stats["processing_end"] = datetime.utcnow()
            batch_stats["total_duration_seconds"] = (batch_stats["processing_end"] - batch_stats["processing_start"]).total_seconds()
            
            return {
                "status": "failed",
                "error": str(e),
                "processed_questions": processed_questions,
                "enhanced_questions": enhanced_questions,
                "statistics": batch_stats
            }

    async def standardize_content_format(self, enhanced_question: EnhancedQuestion) -> Dict[str, Any]:
        """
        Standardize content format for consistency across sources
        
        Args:
            enhanced_question: AI-processed question
            
        Returns:
            Standardized question format
        """
        try:
            # Apply standardization rules
            standardized = {
                "id": enhanced_question.id if hasattr(enhanced_question, 'id') else None,
                "question_text": self._clean_and_standardize_text(enhanced_question.question_text),
                "options": [self._clean_and_standardize_text(opt) for opt in enhanced_question.options],
                "correct_answer": self._clean_and_standardize_text(enhanced_question.correct_answer),
                "category": enhanced_question.category.value,
                "difficulty": enhanced_question.difficulty.value,
                "source": enhanced_question.source,
                "quality_metrics": {
                    "overall_score": enhanced_question.ai_metrics.quality_score,
                    "difficulty_score": enhanced_question.ai_metrics.difficulty_score,
                    "relevance_score": enhanced_question.ai_metrics.relevance_score,
                    "clarity_score": enhanced_question.ai_metrics.clarity_score
                },
                "metadata": {
                    "concepts": enhanced_question.metadata.concepts,
                    "estimated_time_seconds": enhanced_question.metadata.time_estimate,
                    "keywords": enhanced_question.metadata.keywords,
                    "topics": enhanced_question.metadata.topics
                },
                "ai_explanation": enhanced_question.ai_explanation.explanation if enhanced_question.ai_explanation else None,
                "is_verified": enhanced_question.is_verified,
                "processed_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Standardized question format for {standardized.get('id', 'unknown')}")
            return standardized
            
        except Exception as e:
            logger.error(f"Error standardizing content format: {str(e)}")
            return {"error": f"Standardization failed: {str(e)}"}

    async def quality_workflow_orchestrator(
        self, 
        raw_questions: List[RawExtractedQuestion],
        auto_approve_threshold: float = 85.0,
        auto_reject_threshold: float = 50.0
    ) -> Dict[str, Any]:
        """
        Complete quality workflow orchestration
        
        Args:
            raw_questions: Raw scraped questions
            auto_approve_threshold: Quality score threshold for auto-approval
            auto_reject_threshold: Quality score threshold for auto-rejection
            
        Returns:
            Complete workflow results with quality-gated outputs
        """
        logger.info(f"Starting quality workflow for {len(raw_questions)} questions")
        
        # Step 1: Batch process questions through AI pipeline
        processing_results = await self.batch_process_questions(raw_questions)
        
        if processing_results["status"] == "failed":
            return processing_results
        
        processed_questions = processing_results["processed_questions"]
        enhanced_questions = processing_results["enhanced_questions"]
        
        # Step 2: Apply quality gating and categorize results
        quality_categories = {
            "auto_approved": [],
            "auto_rejected": [], 
            "human_review_required": [],
            "processing_failed": []
        }
        
        for pq in processed_questions:
            if pq.quality_gate_result == QualityGate.AUTO_APPROVE:
                quality_categories["auto_approved"].append(pq)
            elif pq.quality_gate_result == QualityGate.AUTO_REJECT:
                quality_categories["auto_rejected"].append(pq)
            elif pq.quality_gate_result == QualityGate.HUMAN_REVIEW:
                quality_categories["human_review_required"].append(pq)
            else:
                quality_categories["processing_failed"].append(pq)
        
        # Step 3: Standardize approved content
        standardized_questions = []
        for enhanced_question in enhanced_questions:
            if enhanced_question.ai_metrics.quality_score >= auto_approve_threshold:
                standardized = await self.standardize_content_format(enhanced_question)
                standardized_questions.append(standardized)
        
        # Step 4: Generate comprehensive workflow summary
        workflow_summary = {
            "total_input_questions": len(raw_questions),
            "processing_statistics": processing_results["statistics"],
            "quality_distribution": {
                "auto_approved": len(quality_categories["auto_approved"]),
                "auto_rejected": len(quality_categories["auto_rejected"]),
                "human_review_required": len(quality_categories["human_review_required"]),
                "processing_failed": len(quality_categories["processing_failed"])
            },
            "output_counts": {
                "standardized_questions": len(standardized_questions),
                "ready_for_database": len([q for q in standardized_questions if q.get("quality_metrics", {}).get("overall_score", 0) >= auto_approve_threshold])
            },
            "workflow_completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Quality workflow completed: {workflow_summary['output_counts']['ready_for_database']} questions ready for database")
        
        return {
            "status": "completed",
            "workflow_summary": workflow_summary,
            "quality_categories": quality_categories,
            "standardized_questions": standardized_questions,
            "processing_details": processing_results
        }

    def _prepare_question_for_ai(self, raw_question: RawExtractedQuestion) -> Dict[str, Any]:
        """Prepare raw question data for AI coordinator processing"""
        return {
            "question_text": raw_question.raw_question_text,
            "options": raw_question.raw_options,
            "correct_answer": raw_question.raw_correct_answer,
            "category": raw_question.detected_category or "quantitative",
            "source": f"scraped_{raw_question.source_id}",
            "source_url": raw_question.source_url,
            "extraction_metadata": {
                "extraction_method": raw_question.extraction_method.value,
                "extraction_confidence": raw_question.extraction_confidence,
                "completeness_score": raw_question.completeness_score,
                "page_number": raw_question.page_number
            }
        }

    def _apply_quality_gates(self, enhanced_question: EnhancedQuestion) -> Tuple[QualityGate, List[str]]:
        """Apply quality gate logic based on AI assessment"""
        quality_score = enhanced_question.ai_metrics.quality_score
        clarity_score = enhanced_question.ai_metrics.clarity_score
        relevance_score = enhanced_question.ai_metrics.relevance_score
        
        reasons = []
        
        # Auto-approve criteria (high quality)
        if (quality_score >= 85.0 and 
            clarity_score >= 80.0 and 
            relevance_score >= 85.0 and 
            len(enhanced_question.options) >= 2):
            reasons.append(f"High quality scores: overall={quality_score:.1f}, clarity={clarity_score:.1f}, relevance={relevance_score:.1f}")
            return QualityGate.AUTO_APPROVE, reasons
        
        # Auto-reject criteria (low quality)
        if (quality_score < 50.0 or 
            clarity_score < 40.0 or 
            len(enhanced_question.question_text.strip()) < 10 or
            len(enhanced_question.options) < 2):
            reasons.append(f"Low quality: overall={quality_score:.1f}, clarity={clarity_score:.1f}, options_count={len(enhanced_question.options)}")
            return QualityGate.AUTO_REJECT, reasons
        
        # Human review required (medium quality)
        reasons.append(f"Medium quality requiring review: overall={quality_score:.1f}, clarity={clarity_score:.1f}")
        return QualityGate.HUMAN_REVIEW, reasons

    def _clean_and_standardize_text(self, text: str) -> str:
        """Clean and standardize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Remove common artifacts from scraping
        artifacts = ["<br>", "<BR>", "&nbsp;", "\\n", "\\r", "\\t"]
        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, " ")
        
        # Standardize common patterns
        cleaned = cleaned.replace(" .", ".")
        cleaned = cleaned.replace(" ,", ",")
        cleaned = cleaned.replace(" ?", "?")
        cleaned = cleaned.replace(" !", "!")
        
        return cleaned.strip()

    def _update_processing_stats(self, gate_result: QualityGate, processing_time: float):
        """Update internal processing statistics"""
        self.processing_stats["total_processed"] += 1
        
        if gate_result == QualityGate.AUTO_APPROVE:
            self.processing_stats["auto_approved"] += 1
        elif gate_result == QualityGate.AUTO_REJECT:
            self.processing_stats["auto_rejected"] += 1
        elif gate_result == QualityGate.HUMAN_REVIEW:
            self.processing_stats["human_review_required"] += 1
        else:
            self.processing_stats["failed_processing"] += 1
        
        # Update average processing time
        total_time = (self.processing_stats["avg_processing_time"] * (self.processing_stats["total_processed"] - 1)) + processing_time
        self.processing_stats["avg_processing_time"] = total_time / self.processing_stats["total_processed"]

    def _generate_processing_summary(self, batch_stats: Dict[str, Any]) -> str:
        """Generate human-readable processing summary"""
        return (
            f"Processed {batch_stats['processed_successfully']}/{batch_stats['total_questions']} questions "
            f"in {batch_stats['total_duration_seconds']:.1f}s. "
            f"Quality distribution: {batch_stats['auto_approved']} approved, "
            f"{batch_stats['human_review_required']} need review, "
            f"{batch_stats['auto_rejected']} rejected. "
            f"Average quality score: {batch_stats['avg_quality_score']:.1f}"
        )

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return {
            "processing_stats": self.processing_stats.copy(),
            "success_rate": (
                self.processing_stats["auto_approved"] / 
                max(1, self.processing_stats["total_processed"])
            ) * 100.0 if self.processing_stats["total_processed"] > 0 else 0.0,
            "quality_gate_distribution": {
                "auto_approved_percentage": (
                    self.processing_stats["auto_approved"] / 
                    max(1, self.processing_stats["total_processed"])
                ) * 100.0,
                "human_review_percentage": (
                    self.processing_stats["human_review_required"] / 
                    max(1, self.processing_stats["total_processed"])
                ) * 100.0,
                "auto_rejected_percentage": (
                    self.processing_stats["auto_rejected"] / 
                    max(1, self.processing_stats["total_processed"])
                ) * 100.0
            }
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_scraping_ai_processor() -> ScrapingAIProcessor:
    """Factory function to create ScrapingAIProcessor instance"""
    return ScrapingAIProcessor()

async def process_scraped_questions_batch(
    raw_questions: List[RawExtractedQuestion],
    batch_size: int = 5,
    quality_threshold: float = 75.0
) -> Dict[str, Any]:
    """
    Convenience function for batch processing scraped questions
    
    Args:
        raw_questions: List of raw extracted questions
        batch_size: Batch size for processing
        quality_threshold: Quality threshold for gating
        
    Returns:
        Processing results
    """
    processor = create_scraping_ai_processor()
    return await processor.batch_process_questions(raw_questions, batch_size, quality_threshold)

async def run_complete_ai_workflow(
    raw_questions: List[RawExtractedQuestion],
    auto_approve_threshold: float = 85.0,
    auto_reject_threshold: float = 50.0
) -> Dict[str, Any]:
    """
    Run complete AI processing workflow for scraped content
    
    Args:
        raw_questions: Raw scraped questions
        auto_approve_threshold: Threshold for auto-approval
        auto_reject_threshold: Threshold for auto-rejection
        
    Returns:
        Complete workflow results
    """
    processor = create_scraping_ai_processor()
    return await processor.quality_workflow_orchestrator(
        raw_questions, 
        auto_approve_threshold, 
        auto_reject_threshold
    )