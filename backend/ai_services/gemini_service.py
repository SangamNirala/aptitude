import google.generativeai as genai
import os
import json
import logging
from typing import List, Dict, Optional, Any
import asyncio
from ..models.question_models import AIExplanation, QuestionCategory, DifficultyLevel

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("GeminiService initialized successfully")
    
    async def generate_question(self, category: str, difficulty: str, topic: str, company_pattern: str = "") -> Dict[str, Any]:
        """Generate a high-quality aptitude question using Gemini AI"""
        try:
            prompt = f"""
            Generate a high-quality {category} aptitude question for {difficulty} level students preparing for placement tests.
            
            Requirements:
            - Topic: {topic}
            - Company Pattern: {company_pattern if company_pattern else "General placement pattern"}
            - Difficulty: {difficulty}
            - Must have 4 multiple choice options
            - Only one correct answer
            - Question should be practical and test real understanding
            
            Return response in this exact JSON format:
            {{
                "question_text": "Your question here",
                "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                "correct_answer": "A) Option 1",
                "concepts": ["concept1", "concept2"],
                "time_estimate": 60,
                "company_patterns": ["{company_pattern}"],
                "difficulty_justification": "Why this is {difficulty} level"
            }}
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            # Clean and parse JSON response
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]  # Remove ```json and ```
            elif content.startswith('```'):
                content = content[3:-3]  # Remove ``` 
            
            result = json.loads(content)
            
            # Validate required fields
            required_fields = ['question_text', 'options', 'correct_answer']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"Successfully generated {category} question for {difficulty} level")
            return result
            
        except Exception as e:
            logger.error(f"Error generating question with Gemini: {str(e)}")
            raise Exception(f"Question generation failed: {str(e)}")
    
    async def generate_explanation(self, question: str, options: List[str], correct_answer: str, category: str) -> AIExplanation:
        """Generate detailed explanation for a question using Gemini AI"""
        try:
            prompt = f"""
            Generate a comprehensive explanation for this {category} aptitude question:
            
            Question: {question}
            Options: {', '.join(options)}
            Correct Answer: {correct_answer}
            
            Provide explanation in this JSON format:
            {{
                "step_by_step": "Detailed step-by-step solution with clear reasoning",
                "key_concept": "Main concept or formula used",
                "alternative_methods": ["method1", "method2"],
                "tips_and_tricks": ["tip1", "tip2", "tip3"],
                "common_errors": ["error1", "error2"]
            }}
            
            Make sure explanations are:
            - Clear and easy to understand
            - Include formulas and calculations where needed
            - Provide shortcuts and time-saving tips
            - Highlight common mistakes students make
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            # Clean and parse JSON response
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            explanation_data = json.loads(content)
            
            # Create AIExplanation object
            explanation = AIExplanation(
                step_by_step=explanation_data.get('step_by_step', ''),
                key_concept=explanation_data.get('key_concept', ''),
                alternative_methods=explanation_data.get('alternative_methods', []),
                tips_and_tricks=explanation_data.get('tips_and_tricks', []),
                common_errors=explanation_data.get('common_errors', []),
                generated_by="gemini",
                confidence_score=0.95
            )
            
            logger.info(f"Generated explanation for {category} question")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation with Gemini: {str(e)}")
            raise Exception(f"Explanation generation failed: {str(e)}")
    
    async def assess_question_quality(self, question: str, options: List[str], correct_answer: str) -> Dict[str, float]:
        """Assess question quality using Gemini AI"""
        try:
            prompt = f"""
            Assess the quality of this aptitude question and provide scores (0-100):
            
            Question: {question}
            Options: {', '.join(options)}
            Correct Answer: {correct_answer}
            
            Evaluate and return scores in this JSON format:
            {{
                "quality_score": 85,
                "clarity_score": 90,
                "relevance_score": 88,
                "difficulty_score": 6.5,
                "reasoning": "Brief explanation of the assessment"
            }}
            
            Consider:
            - Question clarity and unambiguity
            - Relevance for placement preparation  
            - Appropriate difficulty level
            - Quality of options (no obviously wrong/silly choices)
            - Practical applicability
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            
            logger.info("Completed question quality assessment")
            return result
            
        except Exception as e:
            logger.error(f"Error assessing question quality: {str(e)}")
            # Return default scores if assessment fails
            return {
                "quality_score": 75.0,
                "clarity_score": 75.0,
                "relevance_score": 75.0,
                "difficulty_score": 5.0,
                "reasoning": "Assessment unavailable"
            }
    
    async def generate_personalized_questions(self, weak_areas: List[str], target_companies: List[str], count: int = 10) -> List[Dict[str, Any]]:
        """Generate personalized questions based on user's weak areas"""
        try:
            weak_areas_text = ', '.join(weak_areas)
            companies_text = ', '.join(target_companies) if target_companies else "General placement"
            
            prompt = f"""
            Generate {count} personalized aptitude questions targeting these weak areas: {weak_areas_text}
            Target companies: {companies_text}
            
            Focus on:
            - Common question patterns from these companies
            - Progressive difficulty to help improve weak areas
            - Practical, placement-relevant problems
            
            Return as JSON array with this format for each question:
            {{
                "question_text": "Question here",
                "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                "correct_answer": "A) Option 1", 
                "category": "quantitative/logical/verbal/data_interpretation",
                "difficulty": "foundation/placement_ready/campus_expert",
                "target_weak_area": "specific weak area this addresses",
                "company_relevance": ["company1", "company2"]
            }}
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            questions = json.loads(content)
            
            logger.info(f"Generated {len(questions)} personalized questions")
            return questions if isinstance(questions, list) else [questions]
            
        except Exception as e:
            logger.error(f"Error generating personalized questions: {str(e)}")
            return []
    
    async def analyze_performance_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user performance and provide AI insights"""
        try:
            prompt = f"""
            Analyze this student's performance data and provide insights:
            
            Performance Data: {json.dumps(user_data, indent=2)}
            
            Return analysis in this JSON format:
            {{
                "weak_areas": [
                    {{"topic": "topic_name", "priority": "high/medium/low", "suggestion": "specific advice"}}
                ],
                "strong_areas": ["area1", "area2"],
                "study_recommendations": ["recommendation1", "recommendation2"],
                "predicted_readiness": {{
                    "TCS": {{"probability": 85, "timeline_days": 21}},
                    "Infosys": {{"probability": 67, "timeline_days": 35}}
                }},
                "personalized_study_plan": {{
                    "daily_target": 25,
                    "focus_areas": ["area1", "area2"],
                    "estimated_improvement_days": 28
                }}
            }}
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            analysis = json.loads(content)
            
            logger.info("Completed performance analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing performance data: {str(e)}")
            return {"error": "Performance analysis unavailable"}