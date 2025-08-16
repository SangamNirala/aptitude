import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import asyncio

from ..ai_services.ai_coordinator import AICoordinator
from ..models.question_models import QuestionCategory, DifficultyLevel, EnhancedQuestion

logger = logging.getLogger(__name__)

class CategorizationService:
    """Smart categorization and classification service using AI"""
    
    def __init__(self):
        self.ai_coordinator = AICoordinator()
        
        # Company-specific question patterns (learned from historical data)
        self.company_patterns = {
            "TCS": {
                "keywords": ["basic", "simple", "direct", "straightforward"],
                "difficulty_range": (3, 6),
                "common_topics": ["percentages", "profit_loss", "time_work", "averages"],
                "time_preference": "short",  # Prefer questions solvable in <60 seconds
                "complexity": "low"
            },
            "Infosys": {
                "keywords": ["logical", "reasoning", "pattern", "sequence"],
                "difficulty_range": (5, 8),
                "common_topics": ["puzzles", "blood_relations", "coding_decoding", "series"],
                "time_preference": "medium",  # 60-120 seconds
                "complexity": "medium"
            },
            "Wipro": {
                "keywords": ["balanced", "comprehensive", "analytical"],
                "difficulty_range": (4, 7),
                "common_topics": ["quantitative", "logical", "verbal", "data_interpretation"],
                "time_preference": "medium",
                "complexity": "medium"
            },
            "Cognizant": {
                "keywords": ["practical", "application", "real-world"],
                "difficulty_range": (4, 6),
                "common_topics": ["quantitative", "logical", "english"],
                "time_preference": "short",
                "complexity": "low-medium"
            }
        }
        
        # Topic difficulty mapping
        self.topic_difficulty_map = {
            # Easy topics (Foundation level)
            "percentages": 3.5,
            "averages": 3.0,
            "simple_interest": 3.5,
            "number_systems": 4.0,
            "synonyms_antonyms": 2.5,
            
            # Medium topics (Placement Ready level)  
            "profit_loss": 5.5,
            "time_work": 6.0,
            "time_speed_distance": 6.5,
            "blood_relations": 5.0,
            "direction_sense": 4.5,
            "coding_decoding": 5.5,
            "reading_comprehension": 6.0,
            "bar_charts": 5.5,
            "pie_charts": 5.0,
            
            # Hard topics (Campus Expert level)
            "permutations_combinations": 8.5,
            "probability": 8.0,
            "puzzles_seating": 7.5,
            "data_sufficiency": 7.0,
            "compound_interest": 7.0,
            "caselets": 8.0
        }
        
        logger.info("CategorizationService initialized with AI coordinator")
    
    async def categorize_question_smart(self, question_text: str, options: List[str], existing_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Smart categorization using multiple AI models"""
        try:
            logger.info(f"Smart categorization for question: {question_text[:50]}...")
            
            # Use HuggingFace for primary classification
            hf_result = await self.ai_coordinator.huggingface.classify_question_category(question_text)
            
            # Extract concepts
            predicted_category = hf_result.get("predicted_category", "quantitative")
            concepts = await self.ai_coordinator.huggingface.extract_key_concepts(question_text, predicted_category)
            
            # Assess difficulty using Groq
            groq_difficulty = await self.ai_coordinator.groq.assess_difficulty_instantly(question_text, options)
            
            # Determine company patterns
            company_matches = await self._identify_company_patterns(question_text, concepts, groq_difficulty.get("difficulty_score", 5))
            
            # Map to appropriate difficulty level
            difficulty_score = groq_difficulty.get("difficulty_score", 5)
            difficulty_level = self._map_difficulty_score_to_level(difficulty_score)
            
            # Enhanced metadata
            enhanced_metadata = {
                "category": predicted_category,
                "difficulty_level": difficulty_level,
                "difficulty_score": difficulty_score,
                "concepts": concepts,
                "company_patterns": company_matches,
                "topics": self._extract_detailed_topics(concepts, predicted_category),
                "subtopics": self._extract_subtopics(concepts),
                "time_estimate": groq_difficulty.get("estimated_time_seconds", 60),
                "classification_confidence": hf_result.get("confidence", 0.8),
                "keywords": self._extract_keywords(question_text),
                "complexity_level": self._assess_complexity_level(concepts, difficulty_score)
            }
            
            logger.info(f"Smart categorization completed - Category: {predicted_category}, Difficulty: {difficulty_level}")
            return enhanced_metadata
            
        except Exception as e:
            logger.error(f"Error in smart categorization: {str(e)}")
            return self._get_default_categorization()
    
    async def _identify_company_patterns(self, question_text: str, concepts: List[str], difficulty_score: float) -> List[str]:
        """Identify which company patterns this question matches"""
        try:
            matching_companies = []
            question_lower = question_text.lower()
            
            for company, pattern in self.company_patterns.items():
                match_score = 0
                
                # Check keyword matches
                keyword_matches = sum(1 for keyword in pattern["keywords"] if keyword in question_lower)
                match_score += keyword_matches * 2
                
                # Check difficulty range
                min_diff, max_diff = pattern["difficulty_range"]
                if min_diff <= difficulty_score <= max_diff:
                    match_score += 3
                
                # Check topic preferences
                topic_matches = sum(1 for topic in pattern["common_topics"] if any(concept in topic for concept in concepts))
                match_score += topic_matches * 2
                
                # If match score is high enough, include company
                if match_score >= 4:  # Threshold for pattern match
                    matching_companies.append(company)
            
            # If no specific matches, categorize as "General"
            if not matching_companies:
                matching_companies = ["General"]
            
            logger.info(f"Identified company patterns: {matching_companies}")
            return matching_companies
            
        except Exception as e:
            logger.error(f"Error identifying company patterns: {str(e)}")
            return ["General"]
    
    def _map_difficulty_score_to_level(self, difficulty_score: float) -> str:
        """Map numerical difficulty score to difficulty level"""
        if difficulty_score <= 4.0:
            return "foundation"
        elif difficulty_score <= 7.0:
            return "placement_ready"
        else:
            return "campus_expert"
    
    def _extract_detailed_topics(self, concepts: List[str], category: str) -> List[str]:
        """Extract detailed topics based on concepts and category"""
        topic_map = {
            "quantitative": {
                "percentage": "Percentages",
                "profit_loss": "Profit & Loss", 
                "time_work": "Time & Work",
                "time_speed_distance": "Time, Speed & Distance",
                "average": "Averages",
                "ratio_proportion": "Ratio & Proportion",
                "simple_interest": "Simple Interest",
                "compound_interest": "Compound Interest"
            },
            "logical": {
                "blood_relations": "Blood Relations",
                "direction_sense": "Direction Sense",
                "coding_decoding": "Coding-Decoding",
                "puzzles": "Puzzles & Seating Arrangement",
                "series": "Series & Pattern Recognition"
            },
            "verbal": {
                "synonyms": "Synonyms & Antonyms",
                "reading_comprehension": "Reading Comprehension",
                "grammar": "Error Spotting"
            },
            "data_interpretation": {
                "bar_chart": "Bar Graphs",
                "pie_chart": "Pie Charts",
                "line_graph": "Line Graphs",
                "table": "Tables"
            }
        }
        
        category_topics = topic_map.get(category, {})
        matched_topics = []
        
        for concept in concepts:
            for key, topic in category_topics.items():
                if key in concept:
                    matched_topics.append(topic)
        
        return list(set(matched_topics)) if matched_topics else [category.title()]
    
    def _extract_subtopics(self, concepts: List[str]) -> List[str]:
        """Extract granular subtopics"""
        subtopic_map = {
            "percentage": ["Basic Percentage", "Percentage Change", "Successive Percentage"],
            "profit_loss": ["Basic Profit Loss", "Discount", "Marked Price"],
            "time_work": ["Individual Work", "Combined Work", "Efficiency"],
            "blood_relations": ["Direct Relations", "Complex Relations", "Generation Gap"],
            "coding_decoding": ["Letter Coding", "Number Coding", "Symbol Coding"]
        }
        
        subtopics = []
        for concept in concepts:
            if concept in subtopic_map:
                subtopics.extend(subtopic_map[concept])
        
        return subtopics
    
    def _extract_keywords(self, question_text: str) -> List[str]:
        """Extract important keywords from question"""
        important_words = []
        question_lower = question_text.lower()
        
        # Mathematical keywords
        math_keywords = ["calculate", "find", "determine", "percent", "ratio", "average", "profit", "loss", "interest", "principal", "rate", "time", "speed", "distance", "work"]
        
        # Logical keywords
        logical_keywords = ["arrange", "order", "sequence", "pattern", "relation", "direction", "code", "decode"]
        
        # Common question words
        question_words = ["what", "which", "how", "when", "where", "who"]
        
        all_keywords = math_keywords + logical_keywords + question_words
        
        for keyword in all_keywords:
            if keyword in question_lower:
                important_words.append(keyword)
        
        return list(set(important_words))
    
    def _assess_complexity_level(self, concepts: List[str], difficulty_score: float) -> str:
        """Assess overall complexity level"""
        if difficulty_score <= 3:
            return "simple"
        elif difficulty_score <= 6:
            return "moderate"  
        elif difficulty_score <= 8:
            return "complex"
        else:
            return "advanced"
    
    def _get_default_categorization(self) -> Dict[str, Any]:
        """Default categorization when AI fails"""
        return {
            "category": "quantitative",
            "difficulty_level": "placement_ready",
            "difficulty_score": 5.0,
            "concepts": ["general"],
            "company_patterns": ["General"],
            "topics": ["General Aptitude"],
            "subtopics": [],
            "time_estimate": 60,
            "classification_confidence": 0.5,
            "keywords": [],
            "complexity_level": "moderate"
        }
    
    async def batch_categorize_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize multiple questions efficiently"""
        try:
            logger.info(f"Starting batch categorization for {len(questions)} questions")
            
            # Process in smaller batches to avoid API rate limits
            batch_size = 10
            categorized_results = []
            
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i + batch_size]
                
                # Create tasks for parallel processing
                tasks = []
                for question in batch:
                    task = self.categorize_question_smart(
                        question.get("question_text", ""),
                        question.get("options", []),
                        question.get("metadata")
                    )
                    tasks.append(task)
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error categorizing question {i+j}: {result}")
                        categorized_results.append(self._get_default_categorization())
                    else:
                        categorized_results.append(result)
                
                # Brief pause between batches
                await asyncio.sleep(0.5)
            
            logger.info(f"Batch categorization completed: {len(categorized_results)} questions processed")
            return categorized_results
            
        except Exception as e:
            logger.error(f"Error in batch categorization: {str(e)}")
            return [self._get_default_categorization() for _ in questions]
    
    async def suggest_optimal_difficulty_progression(self, user_performance: Dict[str, Any]) -> List[str]:
        """Suggest optimal difficulty progression for user"""
        try:
            current_accuracy = user_performance.get("overall_accuracy", 0)
            weak_areas = user_performance.get("weak_areas", [])
            
            suggestions = []
            
            if current_accuracy < 60:
                suggestions.append("foundation")
                suggestions.append("Focus on basic concepts and easy questions")
            elif current_accuracy < 80:
                suggestions.append("placement_ready") 
                suggestions.append("Mix of medium difficulty questions with concept reinforcement")
            else:
                suggestions.append("campus_expert")
                suggestions.append("Challenge with advanced questions and time optimization")
            
            # Add specific weak area suggestions
            for weak_area in weak_areas[:3]:  # Top 3 weak areas
                if weak_area in self.topic_difficulty_map:
                    topic_difficulty = self.topic_difficulty_map[weak_area]
                    suggested_level = self._map_difficulty_score_to_level(topic_difficulty)
                    suggestions.append(f"Practice {weak_area} at {suggested_level} level")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting difficulty progression: {str(e)}")
            return ["placement_ready", "Continue with standard difficulty questions"]