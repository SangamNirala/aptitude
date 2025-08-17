try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Transformers pipeline import failed: {e}")
    # Create mock pipeline function for compatibility
    def pipeline(*args, **kwargs):
        raise RuntimeError("Transformers pipeline not available due to import error")
    AutoTokenizer = None
    AutoModel = None
    TRANSFORMERS_AVAILABLE = False
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import os
import logging
from typing import List, Dict, Optional, Any, Tuple
import asyncio
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

logger = logging.getLogger(__name__)

class HuggingFaceService:
    def __init__(self):
        self.api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        if not self.api_token:
            raise ValueError("HUGGINGFACE_API_TOKEN environment variable is required")
        
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Initialize models for different tasks
        try:
            # For semantic similarity and duplicate detection
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # For text classification
            self.classifier = None  # Will be initialized when needed
            
            # For quality assessment
            self.quality_model_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            
            logger.info("HuggingFaceService initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing HuggingFace models: {str(e)}")
            # Initialize fallback models
            self.sentence_model = None
            self.classifier = None
    
    async def detect_duplicate_questions(self, new_question: str, existing_questions: List[Dict[str, Any]], threshold: float = 0.85) -> Dict[str, Any]:
        """Detect duplicate questions using semantic similarity"""
        try:
            if not self.sentence_model or not existing_questions:
                return {"is_duplicate": False, "similarity_scores": [], "most_similar": None}
            
            # Get embedding for new question
            new_embedding = await asyncio.to_thread(self.sentence_model.encode, [new_question])
            
            # Get embeddings for existing questions
            existing_texts = [q.get('question_text', '') for q in existing_questions]
            existing_embeddings = await asyncio.to_thread(self.sentence_model.encode, existing_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(new_embedding, existing_embeddings)[0]
            
            # Find highest similarity
            max_similarity = float(np.max(similarities))
            max_index = int(np.argmax(similarities))
            
            is_duplicate = max_similarity >= threshold
            
            result = {
                "is_duplicate": is_duplicate,
                "max_similarity": max_similarity,
                "similarity_threshold": threshold,
                "most_similar": existing_questions[max_index] if existing_questions else None,
                "similarity_scores": similarities.tolist(),
                "duplicate_count": int(np.sum(similarities >= threshold))
            }
            
            logger.info(f"Duplicate detection completed. Max similarity: {max_similarity:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in duplicate detection: {str(e)}")
            return {"is_duplicate": False, "error": str(e), "similarity_scores": []}
    
    async def assess_text_quality(self, text: str, context: str = "aptitude_question") -> Dict[str, float]:
        """Assess text quality using various metrics"""
        try:
            quality_metrics = {}
            
            # Basic readability metrics
            word_count = len(text.split())
            sentence_count = len([s for s in text.split('.') if s.strip()])
            
            # Calculate basic scores
            quality_metrics['word_count'] = word_count
            quality_metrics['sentence_count'] = sentence_count
            quality_metrics['avg_words_per_sentence'] = word_count / max(sentence_count, 1)
            
            # Length appropriateness (for aptitude questions)
            if context == "aptitude_question":
                if 10 <= word_count <= 50:
                    quality_metrics['length_score'] = 100.0
                elif 5 <= word_count <= 70:
                    quality_metrics['length_score'] = 80.0
                else:
                    quality_metrics['length_score'] = 60.0
            
            # Grammar and clarity (simplified assessment)
            grammar_score = await self._assess_grammar_simple(text)
            quality_metrics['grammar_score'] = grammar_score
            
            # Overall quality score
            overall_score = (
                quality_metrics.get('length_score', 70) * 0.3 +
                grammar_score * 0.4 +
                min(100, word_count * 2) * 0.3  # Completeness
            )
            
            quality_metrics['overall_quality'] = min(100.0, overall_score)
            
            logger.info(f"Text quality assessment completed. Overall score: {overall_score:.1f}")
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {str(e)}")
            return {"overall_quality": 75.0, "error": str(e)}
    
    async def _assess_grammar_simple(self, text: str) -> float:
        """Simple grammar assessment based on basic rules"""
        try:
            score = 100.0
            
            # Check for basic punctuation
            if not any(p in text for p in ['.', '?', '!']):
                score -= 20
            
            # Check for proper capitalization
            sentences = [s.strip() for s in text.replace('?', '.').replace('!', '.').split('.') if s.strip()]
            for sentence in sentences:
                if sentence and not sentence[0].isupper():
                    score -= 10
            
            # Check for excessive repetition
            words = text.lower().split()
            unique_words = set(words)
            if len(words) > 0 and len(unique_words) / len(words) < 0.5:
                score -= 15
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error in grammar assessment: {str(e)}")
            return 75.0
    
    async def classify_question_category(self, question_text: str) -> Dict[str, Any]:
        """Classify question into categories using text classification"""
        try:
            # Keywords-based classification (fallback method)
            category_keywords = {
                "quantitative": ["calculate", "percent", "profit", "loss", "time", "speed", "distance", "work", "average", "ratio", "proportion", "number", "mathematics", "arithmetic", "+", "-", "*", "/", "%"],
                "logical": ["logic", "pattern", "sequence", "arrange", "order", "relation", "blood", "family", "direction", "coding", "decoding", "puzzle", "reasoning"],
                "verbal": ["synonym", "antonym", "meaning", "vocabulary", "grammar", "sentence", "word", "language", "english", "comprehension", "passage", "reading"],
                "data_interpretation": ["chart", "graph", "table", "data", "statistics", "bar", "pie", "line", "percentage", "interpret", "analyze"]
            }
            
            question_lower = question_text.lower()
            category_scores = {}
            
            for category, keywords in category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in question_lower)
                category_scores[category] = score
            
            # Get the category with highest score
            predicted_category = max(category_scores, key=category_scores.get) if category_scores else "quantitative"
            confidence = category_scores[predicted_category] / max(sum(category_scores.values()), 1)
            
            result = {
                "predicted_category": predicted_category,
                "confidence": min(confidence * 0.8, 0.95),  # Cap confidence
                "category_scores": category_scores,
                "method": "keyword_based"
            }
            
            logger.info(f"Question classified as '{predicted_category}' with confidence {confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in category classification: {str(e)}")
            return {"predicted_category": "quantitative", "confidence": 0.5, "error": str(e)}
    
    async def extract_key_concepts(self, question_text: str, category: str) -> List[str]:
        """Extract key concepts from question text"""
        try:
            concepts = []
            text_lower = question_text.lower()
            
            # Category-specific concept extraction
            if category == "quantitative":
                quant_concepts = {
                    "percentage": ["percent", "%", "percentage"],
                    "profit_loss": ["profit", "loss", "selling", "cost", "sp", "cp"],
                    "time_speed_distance": ["time", "speed", "distance", "km/hr", "m/s"],
                    "time_work": ["work", "complete", "efficiency", "days", "hours"],
                    "ratio_proportion": ["ratio", "proportion", ":", "is to"],
                    "average": ["average", "mean"],
                    "simple_interest": ["interest", "principal", "rate", "SI"],
                    "compound_interest": ["compound", "CI", "amount"]
                }
            elif category == "logical":
                quant_concepts = {
                    "blood_relations": ["son", "daughter", "father", "mother", "brother", "sister", "uncle", "aunt"],
                    "direction_sense": ["north", "south", "east", "west", "left", "right", "direction"],
                    "coding_decoding": ["code", "coded", "decode", "language"],
                    "puzzles": ["arrange", "seating", "circular", "linear", "puzzle"],
                    "series": ["series", "sequence", "pattern", "next"]
                }
            elif category == "verbal":
                quant_concepts = {
                    "synonyms": ["synonym", "similar", "meaning"],
                    "antonyms": ["antonym", "opposite"],
                    "reading_comprehension": ["passage", "comprehension", "paragraph"],
                    "grammar": ["grammar", "error", "correction", "sentence"]
                }
            elif category == "data_interpretation":
                quant_concepts = {
                    "bar_chart": ["bar", "chart", "bar chart"],
                    "pie_chart": ["pie", "circle", "sector"],
                    "line_graph": ["line", "graph", "trend"],
                    "table": ["table", "row", "column"]
                }
            else:
                quant_concepts = {}
            
            # Extract matching concepts
            for concept, keywords in quant_concepts.items():
                if any(keyword in text_lower for keyword in keywords):
                    concepts.append(concept)
            
            # Add general concepts
            if any(word in text_lower for word in ["calculate", "find", "compute"]):
                concepts.append("calculation")
            
            if any(word in text_lower for word in ["compare", "greater", "less", "equal"]):
                concepts.append("comparison")
            
            logger.info(f"Extracted {len(concepts)} concepts: {concepts}")
            return concepts or ["general"]
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            return ["general"]
    
    async def generate_similarity_clusters(self, questions: List[Dict[str, Any]], threshold: float = 0.75) -> List[List[int]]:
        """Group similar questions into clusters"""
        try:
            if not self.sentence_model or len(questions) < 2:
                return [[i] for i in range(len(questions))]
            
            # Get question texts
            question_texts = [q.get('question_text', '') for q in questions]
            
            # Generate embeddings
            embeddings = await asyncio.to_thread(self.sentence_model.encode, question_texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Create clusters using simple threshold-based clustering
            clusters = []
            assigned = set()
            
            for i in range(len(questions)):
                if i in assigned:
                    continue
                
                cluster = [i]
                assigned.add(i)
                
                for j in range(i + 1, len(questions)):
                    if j not in assigned and similarity_matrix[i][j] >= threshold:
                        cluster.append(j)
                        assigned.add(j)
                
                clusters.append(cluster)
            
            logger.info(f"Generated {len(clusters)} similarity clusters from {len(questions)} questions")
            return clusters
            
        except Exception as e:
            logger.error(f"Error generating similarity clusters: {str(e)}")
            return [[i] for i in range(len(questions))]
    
    async def evaluate_answer_relevance(self, question: str, answer: str, context: str = "") -> float:
        """Evaluate how relevant an answer is to the question"""
        try:
            if not self.sentence_model:
                return 0.7  # Default relevance score
            
            # Create combined texts for embedding
            question_text = f"Question: {question} Context: {context}".strip()
            answer_text = f"Answer: {answer}".strip()
            
            # Generate embeddings
            embeddings = await asyncio.to_thread(
                self.sentence_model.encode, 
                [question_text, answer_text]
            )
            
            # Calculate similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            # Convert to relevance score (0-100)
            relevance_score = float(similarity * 100)
            
            logger.info(f"Answer relevance score: {relevance_score:.2f}")
            return min(100.0, max(0.0, relevance_score))
            
        except Exception as e:
            logger.error(f"Error evaluating answer relevance: {str(e)}")
            return 70.0  # Default score on error