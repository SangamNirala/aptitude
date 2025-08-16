from groq import Groq
import os
import json
import logging
from typing import List, Dict, Optional, Any
import asyncio
import time

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Initialize Groq client without proxy settings to avoid conflicts
        try:
            self.client = Groq(api_key=self.api_key)
        except TypeError as e:
            if "proxies" in str(e):
                # Handle proxy parameter issue by creating client without proxy settings
                import httpx
                http_client = httpx.Client()
                self.client = Groq(api_key=self.api_key, http_client=http_client)
            else:
                raise e
        
        self.model = "llama-3.1-8b-instant"  # Ultra-fast model for real-time features
        logger.info("GroqService initialized successfully")
    
    async def instant_answer_evaluation(self, question: str, user_answer: str, correct_answer: str) -> Dict[str, Any]:
        """Ultra-fast answer evaluation and feedback using Groq"""
        try:
            start_time = time.time()
            
            prompt = f"""
            Evaluate this answer instantly and provide brief feedback:
            
            Question: {question}
            Student Answer: {user_answer}
            Correct Answer: {correct_answer}
            
            Return JSON format:
            {{
                "is_correct": true/false,
                "feedback": "Brief encouraging feedback (max 50 words)",
                "quick_tip": "One-line tip or hint (max 25 words)",
                "confidence": 0.95
            }}
            
            Be encouraging and constructive. Keep it short for speed.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            
            # Add processing time
            result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Instant evaluation completed in {result['response_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error in instant evaluation: {str(e)}")
            return {
                "is_correct": user_answer.lower().strip() == correct_answer.lower().strip(),
                "feedback": "Keep practicing! Every attempt makes you stronger.",
                "quick_tip": "Review the concept and try similar questions.",
                "confidence": 0.5,
                "response_time_ms": 0
            }
    
    async def generate_instant_hint(self, question: str, user_progress: str = "") -> Dict[str, Any]:
        """Generate contextual hints instantly using Groq's fast inference"""
        try:
            start_time = time.time()
            
            prompt = f"""
            Provide a helpful hint for this question. Be encouraging and guide without giving the answer away:
            
            Question: {question}
            User Progress: {user_progress if user_progress else "User is stuck"}
            
            Return JSON:
            {{
                "hint": "Helpful hint without revealing answer (max 40 words)",
                "encouragement": "Motivating message (max 20 words)",
                "next_step": "What to think about next (max 15 words)"
            }}
            
            Keep hints progressive - guide their thinking process.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Instant hint generated in {result['response_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error generating hint: {str(e)}")
            return {
                "hint": "Break down the problem into smaller steps and identify the key information.",
                "encouragement": "You've got this! Take your time.",
                "next_step": "Look for patterns or formulas that apply here.",
                "response_time_ms": 0
            }
    
    async def assess_difficulty_instantly(self, question: str, options: List[str]) -> Dict[str, Any]:
        """Instantly assess question difficulty using Groq's fast processing"""
        try:
            start_time = time.time()
            
            prompt = f"""
            Quickly assess the difficulty of this aptitude question:
            
            Question: {question}
            Options: {', '.join(options)}
            
            Return JSON:
            {{
                "difficulty_score": 6.5,
                "difficulty_level": "placement_ready",
                "reasoning": "Brief reason for this difficulty (max 30 words)",
                "estimated_time_seconds": 75
            }}
            
            Difficulty scale: 1-3 (foundation), 4-7 (placement_ready), 8-10 (campus_expert)
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Difficulty assessed in {result['response_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error assessing difficulty: {str(e)}")
            return {
                "difficulty_score": 5.0,
                "difficulty_level": "placement_ready",
                "reasoning": "Standard placement level question",
                "estimated_time_seconds": 60,
                "response_time_ms": 0
            }
    
    async def real_time_performance_feedback(self, recent_attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provide real-time performance feedback based on recent attempts"""
        try:
            start_time = time.time()
            
            attempts_summary = []
            for attempt in recent_attempts[-10:]:  # Last 10 attempts
                attempts_summary.append({
                    "correct": attempt.get('is_correct', False),
                    "time": attempt.get('time_taken_seconds', 0),
                    "topic": attempt.get('topic', 'unknown')
                })
            
            prompt = f"""
            Analyze these recent question attempts and provide instant performance feedback:
            
            Recent Attempts: {json.dumps(attempts_summary)}
            
            Return JSON:
            {{
                "current_streak": "positive/negative/neutral",
                "performance_trend": "improving/declining/stable", 
                "immediate_suggestion": "What to focus on next (max 25 words)",
                "motivation_message": "Encouraging message (max 20 words)",
                "accuracy_percentage": 85.0
            }}
            
            Be encouraging and actionable. Focus on immediate next steps.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.2,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Real-time feedback generated in {result['response_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error generating performance feedback: {str(e)}")
            return {
                "current_streak": "neutral",
                "performance_trend": "stable",
                "immediate_suggestion": "Keep practicing consistently to improve your skills.",
                "motivation_message": "Great effort! You're making progress.",
                "accuracy_percentage": 70.0,
                "response_time_ms": 0
            }
    
    async def adaptive_difficulty_suggestion(self, user_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal difficulty level based on performance"""
        try:
            start_time = time.time()
            
            prompt = f"""
            Suggest optimal difficulty adjustment based on performance:
            
            Current Performance: {json.dumps(user_performance)}
            
            Return JSON:
            {{
                "recommended_difficulty": "foundation/placement_ready/campus_expert",
                "adjustment_reason": "Brief explanation (max 30 words)",
                "confidence_level": 0.85,
                "next_question_type": "easier/same/harder"
            }}
            
            Consider accuracy, consistency, and improvement trends.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Difficulty suggestion generated in {result['response_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error generating difficulty suggestion: {str(e)}")
            return {
                "recommended_difficulty": "placement_ready",
                "adjustment_reason": "Continue with current level",
                "confidence_level": 0.7,
                "next_question_type": "same",
                "response_time_ms": 0
            }
    
    async def quick_concept_explanation(self, concept: str, difficulty_level: str = "placement_ready") -> Dict[str, Any]:
        """Provide quick concept explanations for immediate learning"""
        try:
            start_time = time.time()
            
            prompt = f"""
            Explain this concept quickly and clearly for {difficulty_level} students:
            
            Concept: {concept}
            Level: {difficulty_level}
            
            Return JSON:
            {{
                "simple_explanation": "Clear explanation in simple terms (max 50 words)",
                "key_formula": "Main formula or rule (if applicable)",
                "quick_example": "One-line example (max 20 words)",
                "memory_tip": "Easy way to remember (max 15 words)"
            }}
            
            Make it practical and easy to understand quickly.
            """
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.2,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"Quick explanation generated in {result['response_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error generating concept explanation: {str(e)}")
            return {
                "simple_explanation": f"Key concept in {concept} - practice with examples to master it.",
                "key_formula": "See reference materials for formulas",
                "quick_example": "Apply step by step",
                "memory_tip": "Practice makes perfect",
                "response_time_ms": 0
            }