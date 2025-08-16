import logging
from typing import List, Dict, Optional, Any
import asyncio
from datetime import datetime
import json

# Import services directly to avoid circular imports
from ai_services.gemini_service import GeminiService
from ai_services.groq_service import GroqService  
from ai_services.huggingface_service import HuggingFaceService
from models.question_models import (
    EnhancedQuestion, AIQualityMetrics, QuestionMetadata, 
    AIExplanation, QuestionCategory, DifficultyLevel
)

logger = logging.getLogger(__name__)

class AICoordinator:
    """Orchestrates all AI services for enhanced question processing"""
    
    def __init__(self):
        try:
            self.gemini = GeminiService()
            self.groq = GroqService()
            self.huggingface = HuggingFaceService()
            logger.info("AICoordinator initialized with all services")
        except Exception as e:
            logger.error(f"Error initializing AICoordinator: {str(e)}")
            raise
    
    async def process_new_question_complete(self, question_data: Dict[str, Any]) -> EnhancedQuestion:
        """Complete AI processing pipeline for a new question"""
        try:
            question_text = question_data['question_text']
            options = question_data['options']
            correct_answer = question_data['correct_answer']
            
            logger.info(f"Starting complete AI processing for question: {question_text[:50]}...")
            
            # Run multiple AI analyses in parallel for speed
            tasks = [
                self._analyze_with_gemini(question_text, options, correct_answer),
                self._analyze_with_groq(question_text, options),
                self._analyze_with_huggingface(question_text, question_data.get('category', 'quantitative'))
            ]
            
            gemini_results, groq_results, hf_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions in results
            if isinstance(gemini_results, Exception):
                logger.error(f"Gemini analysis failed: {gemini_results}")
                gemini_results = self._get_default_gemini_results()
            
            if isinstance(groq_results, Exception):
                logger.error(f"Groq analysis failed: {groq_results}")
                groq_results = self._get_default_groq_results()
                
            if isinstance(hf_results, Exception):
                logger.error(f"HuggingFace analysis failed: {hf_results}")
                hf_results = self._get_default_hf_results()
            
            # Combine results into enhanced question
            enhanced_question = await self._combine_ai_results(
                question_data, gemini_results, groq_results, hf_results
            )
            
            logger.info(f"Complete AI processing finished for question with quality score: {enhanced_question.ai_metrics.quality_score}")
            return enhanced_question
            
        except Exception as e:
            logger.error(f"Error in complete question processing: {str(e)}")
            raise Exception(f"AI processing failed: {str(e)}")
    
    async def _analyze_with_gemini(self, question_text: str, options: List[str], correct_answer: str) -> Dict[str, Any]:
        """Analyze question using Gemini AI"""
        tasks = [
            self.gemini.assess_question_quality(question_text, options, correct_answer),
            self.gemini.generate_explanation(question_text, options, correct_answer, "aptitude")
        ]
        
        quality_assessment, explanation = await asyncio.gather(*tasks)
        
        return {
            "quality_assessment": quality_assessment,
            "explanation": explanation
        }
    
    async def _analyze_with_groq(self, question_text: str, options: List[str]) -> Dict[str, Any]:
        """Analyze question using Groq AI (fast processing)"""
        difficulty_result = await self.groq.assess_difficulty_instantly(question_text, options)
        
        return {
            "difficulty_assessment": difficulty_result
        }
    
    async def _analyze_with_huggingface(self, question_text: str, category: str) -> Dict[str, Any]:
        """Analyze question using HuggingFace models"""
        tasks = [
            self.huggingface.assess_text_quality(question_text),
            self.huggingface.classify_question_category(question_text),
            self.huggingface.extract_key_concepts(question_text, category)
        ]
        
        quality_metrics, category_classification, concepts = await asyncio.gather(*tasks)
        
        return {
            "quality_metrics": quality_metrics,
            "category_classification": category_classification,
            "concepts": concepts
        }
    
    async def _combine_ai_results(self, original_data: Dict[str, Any], gemini_results: Dict, groq_results: Dict, hf_results: Dict) -> EnhancedQuestion:
        """Combine all AI analysis results into an enhanced question"""
        
        # Extract quality metrics from all sources
        gemini_quality = gemini_results.get("quality_assessment", {})
        groq_difficulty = groq_results.get("difficulty_assessment", {})
        hf_quality = hf_results.get("quality_metrics", {})
        hf_category = hf_results.get("category_classification", {})
        
        # Calculate combined quality score (weighted average)
        quality_score = (
            gemini_quality.get("quality_score", 75) * 0.5 +  # Gemini weight: 50%
            hf_quality.get("overall_quality", 75) * 0.3 +     # HuggingFace weight: 30%
            (groq_difficulty.get("difficulty_score", 5) * 10) * 0.2  # Groq weight: 20%
        )
        
        # Create AI Quality Metrics
        ai_metrics = AIQualityMetrics(
            quality_score=min(100.0, quality_score),
            difficulty_score=groq_difficulty.get("difficulty_score", 5.0),
            relevance_score=gemini_quality.get("relevance_score", 85.0),
            clarity_score=gemini_quality.get("clarity_score", 80.0),
            assessed_by="ai_coordinator",
            assessment_date=datetime.utcnow()
        )
        
        # Create Question Metadata  
        metadata = QuestionMetadata(
            concepts=hf_results.get("concepts", ["general"]),
            company_patterns=[],  # Will be populated by company pattern analysis
            topics=[],  # Will be enhanced based on category
            subtopics=[],
            keywords=[],
            time_estimate=groq_difficulty.get("estimated_time_seconds", 60)
        )
        
        # Determine category and difficulty
        predicted_category = hf_category.get("predicted_category", original_data.get("category", "quantitative"))
        try:
            category = QuestionCategory(predicted_category)
        except ValueError:
            category = QuestionCategory.QUANTITATIVE
            
        difficulty_level = groq_difficulty.get("difficulty_level", "placement_ready")
        try:
            difficulty = DifficultyLevel(difficulty_level)
        except ValueError:
            difficulty = DifficultyLevel.PLACEMENT_READY
        
        # Create enhanced question
        enhanced_question = EnhancedQuestion(
            question_text=original_data["question_text"],
            options=original_data["options"],
            correct_answer=original_data["correct_answer"],
            category=category,
            difficulty=difficulty,
            ai_metrics=ai_metrics,
            metadata=metadata,
            ai_explanation=gemini_results.get("explanation"),
            source=original_data.get("source", "manual"),
            source_url=original_data.get("source_url"),
            is_verified=quality_score >= 80.0,  # Auto-verify high quality questions
            last_ai_processed=datetime.utcnow()
        )
        
        return enhanced_question
    
    async def generate_personalized_question_set(self, user_weak_areas: List[str], target_companies: List[str], count: int = 10) -> List[EnhancedQuestion]:
        """Generate personalized questions using AI coordination"""
        try:
            # Use Gemini for question generation
            generated_questions = await self.gemini.generate_personalized_questions(
                weak_areas=user_weak_areas,
                target_companies=target_companies, 
                count=count
            )
            
            # Process each generated question through AI pipeline
            enhanced_questions = []
            for question_data in generated_questions:
                try:
                    enhanced_question = await self.process_new_question_complete(question_data)
                    enhanced_questions.append(enhanced_question)
                except Exception as e:
                    logger.error(f"Error processing generated question: {str(e)}")
                    continue
            
            logger.info(f"Generated and processed {len(enhanced_questions)} personalized questions")
            return enhanced_questions
            
        except Exception as e:
            logger.error(f"Error generating personalized questions: {str(e)}")
            return []
    
    async def instant_feedback_response(self, question_text: str, user_answer: str, correct_answer: str) -> Dict[str, Any]:
        """Provide instant feedback using Groq's fast processing"""
        try:
            # Get instant feedback from Groq
            feedback = await self.groq.instant_answer_evaluation(question_text, user_answer, correct_answer)
            
            # Add additional context if wrong answer
            if not feedback.get("is_correct", False):
                # Get a helpful hint
                hint_result = await self.groq.generate_instant_hint(question_text)
                feedback["additional_hint"] = hint_result.get("hint", "")
                feedback["encouragement"] = hint_result.get("encouragement", "Keep trying!")
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error providing instant feedback: {str(e)}")
            return {
                "is_correct": user_answer.lower().strip() == correct_answer.lower().strip(),
                "feedback": "Keep practicing to improve your skills!",
                "quick_tip": "Review the concept and try again.",
                "confidence": 0.5
            }
    
    async def detect_duplicate_questions(self, new_question: str, existing_questions: List[Dict]) -> Dict[str, Any]:
        """Detect duplicates using HuggingFace similarity analysis"""
        return await self.huggingface.detect_duplicate_questions(new_question, existing_questions)
    
    async def bulk_process_questions(self, questions: List[Dict[str, Any]], batch_size: int = 5) -> List[EnhancedQuestion]:
        """Process multiple questions in batches for efficiency"""
        enhanced_questions = []
        
        # Process in batches to avoid overwhelming the APIs
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} questions")
            
            # Process batch in parallel
            batch_tasks = [self.process_new_question_complete(q) for q in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {result}")
                else:
                    enhanced_questions.append(result)
            
            # Small delay between batches to respect API rate limits
            await asyncio.sleep(1)
        
        logger.info(f"Bulk processing completed: {len(enhanced_questions)} questions processed")
        return enhanced_questions
    
    def _get_default_gemini_results(self) -> Dict[str, Any]:
        """Default results when Gemini fails"""
        return {
            "quality_assessment": {
                "quality_score": 75.0,
                "clarity_score": 75.0,
                "relevance_score": 75.0,
                "difficulty_score": 5.0
            },
            "explanation": None
        }
    
    def _get_default_groq_results(self) -> Dict[str, Any]:
        """Default results when Groq fails"""
        return {
            "difficulty_assessment": {
                "difficulty_score": 5.0,
                "difficulty_level": "placement_ready",
                "estimated_time_seconds": 60
            }
        }
    
    def _get_default_hf_results(self) -> Dict[str, Any]:
        """Default results when HuggingFace fails"""
        return {
            "quality_metrics": {"overall_quality": 75.0},
            "category_classification": {"predicted_category": "quantitative"},
            "concepts": ["general"]
        }
    
    async def analyze_user_performance(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive performance analysis using Gemini"""
        return await self.gemini.analyze_performance_data(user_data)
    
    async def get_real_time_study_insights(self, recent_attempts: List[Dict]) -> Dict[str, Any]:
        """Real-time performance insights using Groq"""
        return await self.groq.real_time_performance_feedback(recent_attempts)