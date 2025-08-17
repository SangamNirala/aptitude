"""
Advanced Duplicate Detection System for Scraped Questions
Sophisticated duplicate detection using HuggingFace semantic similarity
"""

import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import json
from dataclasses import asdict
from collections import defaultdict
import hashlib

from ai_services.huggingface_service import HuggingFaceService
from models.scraping_models import RawExtractedQuestion, ProcessedScrapedQuestion
from models.question_models import EnhancedQuestion

logger = logging.getLogger(__name__)

class DuplicateCluster:
    """Represents a cluster of duplicate/similar questions"""
    
    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self.questions: List[Dict[str, Any]] = []
        self.similarity_matrix: np.ndarray = None
        self.representative_question: Optional[Dict[str, Any]] = None
        self.cluster_quality_score: float = 0.0
        self.creation_timestamp = datetime.utcnow()
        
    def add_question(self, question: Dict[str, Any], similarity_score: float = 1.0):
        """Add a question to the cluster"""
        question_data = {
            **question,
            "cluster_similarity_score": similarity_score,
            "added_to_cluster_at": datetime.utcnow()
        }
        self.questions.append(question_data)
        
        # Update representative if this question has higher quality
        if (not self.representative_question or 
            question.get("quality_score", 0) > self.representative_question.get("quality_score", 0)):
            self.representative_question = question_data
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics"""
        return {
            "cluster_id": self.cluster_id,
            "question_count": len(self.questions),
            "sources": list(set(q.get("source", "unknown") for q in self.questions)),
            "avg_quality_score": np.mean([q.get("quality_score", 0) for q in self.questions]),
            "quality_range": {
                "min": min([q.get("quality_score", 0) for q in self.questions]) if self.questions else 0,
                "max": max([q.get("quality_score", 0) for q in self.questions]) if self.questions else 0
            },
            "representative_question_id": self.representative_question.get("id") if self.representative_question else None,
            "creation_timestamp": self.creation_timestamp.isoformat()
        }

class AdvancedDuplicateDetector:
    """
    Advanced Duplicate Detection System
    
    Features:
    1. Semantic similarity analysis using HuggingFace models
    2. Cross-source duplicate detection
    3. Intelligent clustering and management
    4. Performance-optimized similarity search
    5. Multi-level similarity thresholds
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.85,
                 clustering_threshold: float = 0.75,
                 cross_source_threshold: float = 0.90):
        """
        Initialize duplicate detector
        
        Args:
            similarity_threshold: Primary threshold for duplicate detection
            clustering_threshold: Threshold for grouping similar questions
            cross_source_threshold: Higher threshold for cross-source duplicates
        """
        try:
            self.huggingface_service = HuggingFaceService()
            self.similarity_threshold = similarity_threshold
            self.clustering_threshold = clustering_threshold
            self.cross_source_threshold = cross_source_threshold
            
            # Cache for embeddings to improve performance
            self.embedding_cache: Dict[str, np.ndarray] = {}
            self.question_index: Dict[str, Dict[str, Any]] = {}
            
            # Cluster management
            self.clusters: Dict[str, DuplicateCluster] = {}
            self.question_to_cluster: Dict[str, str] = {}
            
            # Performance tracking
            self.detection_stats = {
                "total_questions_processed": 0,
                "duplicates_detected": 0,
                "clusters_created": 0,
                "cross_source_duplicates": 0,
                "avg_processing_time": 0.0,
                "cache_hits": 0,
                "cache_misses": 0
            }
            
            logger.info("AdvancedDuplicateDetector initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AdvancedDuplicateDetector: {str(e)}")
            raise

    async def detect_duplicates_single(self, 
                                     new_question: Dict[str, Any], 
                                     existing_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect duplicates for a single question against existing questions
        
        Args:
            new_question: Question to check for duplicates
            existing_questions: List of existing questions to compare against
            
        Returns:
            Duplicate detection results with similarity analysis
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Detecting duplicates for question: {new_question.get('id', 'unknown')}")
            
            if not existing_questions:
                return {
                    "is_duplicate": False,
                    "similarity_scores": [],
                    "most_similar": None,
                    "duplicate_cluster_id": None,
                    "detection_confidence": 1.0
                }
            
            # Get question text for comparison
            new_text = self._extract_question_text(new_question)
            existing_texts = [self._extract_question_text(q) for q in existing_questions]
            
            # Use HuggingFace service for similarity detection
            similarity_result = await self.huggingface_service.detect_duplicate_questions(
                new_text, 
                [{"question_text": text} for text in existing_texts],
                threshold=self.similarity_threshold
            )
            
            # Enhanced analysis with multiple thresholds
            similarity_scores = similarity_result.get("similarity_scores", [])
            
            if not similarity_scores:
                return {
                    "is_duplicate": False,
                    "similarity_scores": [],
                    "most_similar": None,
                    "duplicate_cluster_id": None,
                    "detection_confidence": 1.0
                }
            
            max_similarity = max(similarity_scores)
            max_index = similarity_scores.index(max_similarity)
            most_similar_question = existing_questions[max_index]
            
            # Multi-level duplicate detection
            detection_results = self._analyze_similarity_levels(
                new_question, 
                most_similar_question, 
                max_similarity,
                similarity_scores
            )
            
            # Check for cross-source duplicates (stricter threshold)
            is_cross_source = (new_question.get("source") != most_similar_question.get("source"))
            if is_cross_source and max_similarity >= self.cross_source_threshold:
                detection_results["cross_source_duplicate"] = True
                self.detection_stats["cross_source_duplicates"] += 1
            
            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_detection_stats(detection_results["is_duplicate"], processing_time)
            
            logger.debug(f"Duplicate detection completed: {detection_results['is_duplicate']} (similarity: {max_similarity:.3f})")
            
            return detection_results
            
        except Exception as e:
            logger.error(f"Error in duplicate detection: {str(e)}")
            return {
                "is_duplicate": False,
                "error": str(e),
                "similarity_scores": [],
                "detection_confidence": 0.0
            }

    async def batch_duplicate_detection(self, 
                                      questions: List[Dict[str, Any]],
                                      batch_size: int = 50) -> Dict[str, Any]:
        """
        Perform batch duplicate detection across a set of questions
        
        Args:
            questions: List of questions to analyze for duplicates
            batch_size: Size of batches for processing
            
        Returns:
            Comprehensive duplicate analysis results
        """
        logger.info(f"Starting batch duplicate detection for {len(questions)} questions")
        
        start_time = datetime.utcnow()
        duplicate_pairs = []
        similarity_matrix = None
        
        try:
            # Generate similarity clusters using HuggingFace
            clusters = await self.huggingface_service.generate_similarity_clusters(
                questions, 
                threshold=self.clustering_threshold
            )
            
            # Process clusters and identify duplicates
            batch_results = {
                "total_questions": len(questions),
                "clusters": [],
                "duplicate_pairs": [],
                "similarity_statistics": {},
                "processing_time_seconds": 0.0,
                "questions_with_duplicates": 0,
                "unique_questions": 0
            }
            
            questions_with_duplicates = set()
            
            for cluster_indices in clusters:
                if len(cluster_indices) > 1:
                    # This cluster has multiple questions (potential duplicates)
                    cluster_questions = [questions[i] for i in cluster_indices]
                    
                    # Perform detailed similarity analysis within cluster
                    cluster_analysis = await self._analyze_cluster_similarities(cluster_questions)
                    
                    # Create cluster object
                    cluster_id = f"cluster_{hashlib.md5(str(cluster_indices).encode()).hexdigest()[:8]}"
                    duplicate_cluster = DuplicateCluster(cluster_id)
                    
                    for i, question in enumerate(cluster_questions):
                        duplicate_cluster.add_question(question, cluster_analysis["similarities"][i])
                        questions_with_duplicates.add(question.get("id"))
                    
                    self.clusters[cluster_id] = duplicate_cluster
                    
                    # Add to results
                    batch_results["clusters"].append({
                        "cluster_id": cluster_id,
                        "question_count": len(cluster_questions),
                        "question_ids": [q.get("id") for q in cluster_questions],
                        "avg_similarity": cluster_analysis["avg_similarity"],
                        "representative_question": cluster_analysis["representative"],
                        "cluster_stats": duplicate_cluster.get_cluster_stats()
                    })
                    
                    # Identify explicit duplicate pairs within cluster
                    for i in range(len(cluster_questions)):
                        for j in range(i + 1, len(cluster_questions)):
                            similarity = cluster_analysis["pairwise_similarities"].get(f"{i}-{j}", 0.0)
                            if similarity >= self.similarity_threshold:
                                duplicate_pairs.append({
                                    "question1": cluster_questions[i],
                                    "question2": cluster_questions[j],
                                    "similarity_score": similarity,
                                    "is_cross_source": (cluster_questions[i].get("source") != cluster_questions[j].get("source"))
                                })
            
            batch_results["duplicate_pairs"] = duplicate_pairs
            batch_results["questions_with_duplicates"] = len(questions_with_duplicates)
            batch_results["unique_questions"] = len(questions) - len(questions_with_duplicates)
            batch_results["processing_time_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate similarity statistics
            if duplicate_pairs:
                similarities = [pair["similarity_score"] for pair in duplicate_pairs]
                batch_results["similarity_statistics"] = {
                    "mean_similarity": float(np.mean(similarities)),
                    "std_similarity": float(np.std(similarities)),
                    "min_similarity": float(np.min(similarities)),
                    "max_similarity": float(np.max(similarities)),
                    "median_similarity": float(np.median(similarities))
                }
            
            logger.info(f"Batch duplicate detection completed: {len(duplicate_pairs)} duplicate pairs found in {len(clusters)} clusters")
            
            return {
                "status": "completed",
                "results": batch_results,
                "clusters_created": len([c for c in clusters if len(c) > 1]),
                "processing_summary": self._generate_batch_summary(batch_results)
            }
            
        except Exception as e:
            logger.error(f"Error in batch duplicate detection: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()
            }

    async def cross_source_duplicate_analysis(self, 
                                            source_questions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Specialized analysis for cross-source duplicates
        
        Args:
            source_questions: Dictionary mapping source_id -> list of questions
            
        Returns:
            Cross-source duplicate analysis results
        """
        logger.info(f"Starting cross-source duplicate analysis across {len(source_questions)} sources")
        
        cross_source_duplicates = []
        source_similarity_matrix = {}
        
        try:
            source_names = list(source_questions.keys())
            
            # Compare questions across different sources
            for i, source1 in enumerate(source_names):
                for j, source2 in enumerate(source_names[i+1:], i+1):
                    logger.info(f"Comparing {source1} vs {source2}")
                    
                    questions1 = source_questions[source1]
                    questions2 = source_questions[source2]
                    
                    # Find duplicates between these two sources
                    source_pair_duplicates = await self._find_duplicates_between_sources(
                        questions1, questions2, source1, source2
                    )
                    
                    cross_source_duplicates.extend(source_pair_duplicates)
                    
                    # Store similarity statistics between sources
                    source_similarity_matrix[f"{source1}-{source2}"] = {
                        "duplicate_count": len(source_pair_duplicates),
                        "total_comparisons": len(questions1) * len(questions2),
                        "duplicate_rate": len(source_pair_duplicates) / max(1, len(questions1) * len(questions2))
                    }
            
            # Analyze cross-source patterns
            analysis_results = {
                "total_cross_source_duplicates": len(cross_source_duplicates),
                "source_pair_analysis": source_similarity_matrix,
                "duplicate_details": cross_source_duplicates,
                "source_reliability_scores": self._calculate_source_reliability_scores(
                    source_questions, cross_source_duplicates
                ),
                "recommendations": self._generate_source_recommendations(
                    source_similarity_matrix, cross_source_duplicates
                )
            }
            
            logger.info(f"Cross-source analysis completed: {len(cross_source_duplicates)} duplicates found")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in cross-source duplicate analysis: {str(e)}")
            return {"error": str(e), "cross_source_duplicates": cross_source_duplicates}

    async def optimize_similarity_search(self, 
                                       query_question: Dict[str, Any],
                                       candidate_pool: List[Dict[str, Any]],
                                       top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Performance-optimized similarity search for large question pools
        
        Args:
            query_question: Question to find similarities for
            candidate_pool: Large pool of candidate questions
            top_k: Number of top similar questions to return
            
        Returns:
            Top-k most similar questions with scores
        """
        try:
            logger.debug(f"Optimized similarity search in pool of {len(candidate_pool)} questions")
            
            # Use embedding cache for performance
            query_text = self._extract_question_text(query_question)
            query_embedding = await self._get_cached_embedding(query_text)
            
            # Batch process candidate embeddings
            candidate_embeddings = await self._batch_get_embeddings(candidate_pool)
            
            # Calculate similarities using vectorized operations
            similarities = np.dot(candidate_embeddings, query_embedding.reshape(-1, 1)).flatten()
            
            # Get top-k indices
            top_k_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_k_indices = top_k_indices[np.argsort(similarities[top_k_indices])[::-1]]
            
            # Prepare results
            top_similar = []
            for idx in top_k_indices:
                if idx < len(candidate_pool):
                    result = {
                        "question": candidate_pool[idx],
                        "similarity_score": float(similarities[idx]),
                        "rank": len(top_similar) + 1
                    }
                    top_similar.append(result)
            
            logger.debug(f"Found {len(top_similar)} similar questions (top similarity: {top_similar[0]['similarity_score']:.3f})")
            return top_similar
            
        except Exception as e:
            logger.error(f"Error in optimized similarity search: {str(e)}")
            return []

    def get_duplicate_management_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for duplicate management
        
        Returns:
            Dashboard data with statistics and management information
        """
        try:
            cluster_stats = []
            for cluster_id, cluster in self.clusters.items():
                cluster_stats.append(cluster.get_cluster_stats())
            
            dashboard_data = {
                "detection_statistics": self.detection_stats.copy(),
                "cluster_overview": {
                    "total_clusters": len(self.clusters),
                    "total_questions_in_clusters": sum(len(c.questions) for c in self.clusters.values()),
                    "avg_questions_per_cluster": (
                        sum(len(c.questions) for c in self.clusters.values()) / 
                        max(1, len(self.clusters))
                    )
                },
                "cluster_details": cluster_stats,
                "performance_metrics": {
                    "cache_hit_rate": (
                        self.detection_stats["cache_hits"] / 
                        max(1, self.detection_stats["cache_hits"] + self.detection_stats["cache_misses"])
                    ) * 100.0,
                    "avg_processing_time": self.detection_stats["avg_processing_time"],
                    "questions_per_second": (
                        1.0 / max(0.001, self.detection_stats["avg_processing_time"])
                    )
                },
                "system_recommendations": self._generate_system_recommendations()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating duplicate management dashboard: {str(e)}")
            return {"error": str(e)}

    # Helper Methods
    
    def _extract_question_text(self, question: Dict[str, Any]) -> str:
        """Extract question text from question dictionary"""
        return question.get("question_text", question.get("raw_question_text", ""))

    def _analyze_similarity_levels(self, 
                                 question1: Dict[str, Any], 
                                 question2: Dict[str, Any], 
                                 similarity_score: float,
                                 all_scores: List[float]) -> Dict[str, Any]:
        """Analyze similarity at multiple levels"""
        
        # Determine duplicate status based on thresholds
        is_duplicate = similarity_score >= self.similarity_threshold
        is_similar = similarity_score >= self.clustering_threshold
        
        # Calculate confidence based on score distribution
        confidence = min(1.0, similarity_score / self.similarity_threshold)
        
        # Check for exact text match
        text1 = self._extract_question_text(question1).lower().strip()
        text2 = self._extract_question_text(question2).lower().strip()
        is_exact_match = text1 == text2
        
        return {
            "is_duplicate": is_duplicate,
            "is_similar": is_similar,
            "is_exact_match": is_exact_match,
            "similarity_score": similarity_score,
            "detection_confidence": confidence,
            "similarity_level": self._categorize_similarity(similarity_score),
            "most_similar": question2,
            "similarity_scores": all_scores,
            "duplicate_cluster_id": self.question_to_cluster.get(question2.get("id"))
        }

    def _categorize_similarity(self, score: float) -> str:
        """Categorize similarity score into levels"""
        if score >= 0.95:
            return "identical"
        elif score >= 0.85:
            return "duplicate"
        elif score >= 0.75:
            return "very_similar"
        elif score >= 0.60:
            return "similar"
        elif score >= 0.40:
            return "somewhat_similar"
        else:
            return "different"

    async def _analyze_cluster_similarities(self, cluster_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze similarities within a cluster of questions"""
        
        if len(cluster_questions) <= 1:
            return {
                "similarities": [1.0],
                "avg_similarity": 1.0,
                "pairwise_similarities": {},
                "representative": cluster_questions[0] if cluster_questions else None
            }
        
        # Calculate pairwise similarities
        pairwise_similarities = {}
        similarities = []
        
        for i in range(len(cluster_questions)):
            for j in range(i + 1, len(cluster_questions)):
                text1 = self._extract_question_text(cluster_questions[i])
                text2 = self._extract_question_text(cluster_questions[j])
                
                # Use HuggingFace for similarity calculation
                result = await self.huggingface_service.detect_duplicate_questions(
                    text1, [{"question_text": text2}], threshold=0.5
                )
                similarity = result.get("similarity_scores", [0.0])[0]
                
                pairwise_similarities[f"{i}-{j}"] = similarity
                similarities.append(similarity)
        
        # Find representative question (highest average similarity or quality)
        representative = max(cluster_questions, 
                           key=lambda q: q.get("quality_score", 0))
        
        return {
            "similarities": [1.0] * len(cluster_questions),  # Individual similarities to cluster
            "avg_similarity": np.mean(similarities) if similarities else 1.0,
            "pairwise_similarities": pairwise_similarities,
            "representative": representative
        }

    async def _find_duplicates_between_sources(self, 
                                             questions1: List[Dict[str, Any]], 
                                             questions2: List[Dict[str, Any]],
                                             source1: str, 
                                             source2: str) -> List[Dict[str, Any]]:
        """Find duplicates between two specific sources"""
        
        duplicates = []
        
        for q1 in questions1:
            text1 = self._extract_question_text(q1)
            
            # Compare against all questions in source2
            texts2 = [self._extract_question_text(q) for q in questions2]
            
            if texts2:
                result = await self.huggingface_service.detect_duplicate_questions(
                    text1, 
                    [{"question_text": text} for text in texts2],
                    threshold=self.cross_source_threshold
                )
                
                similarity_scores = result.get("similarity_scores", [])
                
                for i, score in enumerate(similarity_scores):
                    if score >= self.cross_source_threshold:
                        duplicates.append({
                            "question1": q1,
                            "question2": questions2[i],
                            "source1": source1,
                            "source2": source2,
                            "similarity_score": score,
                            "detection_timestamp": datetime.utcnow().isoformat()
                        })
        
        return duplicates

    async def _get_cached_embedding(self, text: str) -> np.ndarray:
        """Get embedding from cache or compute and cache"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.embedding_cache:
            self.detection_stats["cache_hits"] += 1
            return self.embedding_cache[text_hash]
        
        self.detection_stats["cache_misses"] += 1
        
        # Compute embedding using HuggingFace service
        if hasattr(self.huggingface_service, 'sentence_model') and self.huggingface_service.sentence_model:
            embedding = await asyncio.to_thread(
                self.huggingface_service.sentence_model.encode, 
                [text]
            )
            embedding = embedding[0]  # Get single embedding
        else:
            # Fallback to simple vector
            embedding = np.random.random(384)  # MiniLM embedding size
        
        # Cache for future use (with size limit)
        if len(self.embedding_cache) < 10000:  # Limit cache size
            self.embedding_cache[text_hash] = embedding
        
        return embedding

    async def _batch_get_embeddings(self, questions: List[Dict[str, Any]]) -> np.ndarray:
        """Get embeddings for batch of questions"""
        texts = [self._extract_question_text(q) for q in questions]
        
        if hasattr(self.huggingface_service, 'sentence_model') and self.huggingface_service.sentence_model:
            embeddings = await asyncio.to_thread(
                self.huggingface_service.sentence_model.encode, 
                texts
            )
        else:
            # Fallback embeddings
            embeddings = np.random.random((len(texts), 384))
        
        return embeddings

    def _calculate_source_reliability_scores(self, 
                                           source_questions: Dict[str, List[Dict[str, Any]]], 
                                           cross_source_duplicates: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate reliability scores for each source"""
        
        source_scores = {}
        
        for source_id, questions in source_questions.items():
            # Count duplicates involving this source
            duplicate_count = sum(
                1 for dup in cross_source_duplicates 
                if dup["source1"] == source_id or dup["source2"] == source_id
            )
            
            # Calculate reliability (lower duplicates = higher reliability)
            total_questions = len(questions)
            if total_questions > 0:
                duplicate_rate = duplicate_count / total_questions
                reliability_score = max(0.0, 1.0 - (duplicate_rate * 2))  # Scale factor
            else:
                reliability_score = 1.0
            
            source_scores[source_id] = reliability_score * 100.0  # Convert to percentage
        
        return source_scores

    def _generate_source_recommendations(self, 
                                       similarity_matrix: Dict[str, Dict[str, Any]], 
                                       duplicates: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on source analysis"""
        
        recommendations = []
        
        # Find sources with high duplicate rates
        high_duplicate_pairs = [
            pair for pair, stats in similarity_matrix.items() 
            if stats["duplicate_rate"] > 0.1  # 10% duplicate rate threshold
        ]
        
        if high_duplicate_pairs:
            recommendations.append(
                f"High duplicate rates detected between sources: {', '.join(high_duplicate_pairs)}. "
                "Consider adjusting scraping targets or implementing source-specific deduplication."
            )
        
        # Check for sources with many duplicates
        source_duplicate_counts = defaultdict(int)
        for dup in duplicates:
            source_duplicate_counts[dup["source1"]] += 1
            source_duplicate_counts[dup["source2"]] += 1
        
        problematic_sources = [
            source for source, count in source_duplicate_counts.items() 
            if count > 5  # More than 5 duplicates
        ]
        
        if problematic_sources:
            recommendations.append(
                f"Sources with high duplicate content: {', '.join(problematic_sources)}. "
                "Consider reviewing scraping configuration or source quality."
            )
        
        if not recommendations:
            recommendations.append("No significant duplicate issues detected across sources.")
        
        return recommendations

    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-level recommendations"""
        
        recommendations = []
        stats = self.detection_stats
        
        # Performance recommendations
        cache_hit_rate = (stats["cache_hits"] / max(1, stats["cache_hits"] + stats["cache_misses"])) * 100
        if cache_hit_rate < 50:
            recommendations.append(
                f"Low cache hit rate ({cache_hit_rate:.1f}%). Consider increasing cache size or "
                "implementing persistent embedding storage."
            )
        
        # Duplicate rate recommendations
        if stats["total_questions_processed"] > 0:
            duplicate_rate = (stats["duplicates_detected"] / stats["total_questions_processed"]) * 100
            if duplicate_rate > 20:
                recommendations.append(
                    f"High duplicate rate ({duplicate_rate:.1f}%). Consider adjusting similarity "
                    "thresholds or improving source diversity."
                )
        
        # Processing speed recommendations
        if stats["avg_processing_time"] > 2.0:
            recommendations.append(
                f"Slow processing speed ({stats['avg_processing_time']:.2f}s per question). "
                "Consider optimizing batch sizes or using GPU acceleration."
            )
        
        if not recommendations:
            recommendations.append("System performance is optimal.")
        
        return recommendations

    def _update_detection_stats(self, is_duplicate: bool, processing_time: float):
        """Update detection statistics"""
        self.detection_stats["total_questions_processed"] += 1
        
        if is_duplicate:
            self.detection_stats["duplicates_detected"] += 1
        
        # Update average processing time
        total_time = (self.detection_stats["avg_processing_time"] * 
                     (self.detection_stats["total_questions_processed"] - 1)) + processing_time
        self.detection_stats["avg_processing_time"] = total_time / self.detection_stats["total_questions_processed"]

    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> str:
        """Generate human-readable batch processing summary"""
        return (
            f"Processed {batch_results['total_questions']} questions in "
            f"{batch_results['processing_time_seconds']:.1f}s. "
            f"Found {len(batch_results['duplicate_pairs'])} duplicate pairs across "
            f"{len(batch_results['clusters'])} clusters. "
            f"{batch_results['unique_questions']} questions are unique."
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_duplicate_detector(similarity_threshold: float = 0.85) -> AdvancedDuplicateDetector:
    """Factory function to create duplicate detector"""
    return AdvancedDuplicateDetector(similarity_threshold=similarity_threshold)

async def detect_duplicates_in_batch(questions: List[Dict[str, Any]], 
                                   threshold: float = 0.85) -> Dict[str, Any]:
    """Convenience function for batch duplicate detection"""
    detector = create_duplicate_detector(threshold)
    return await detector.batch_duplicate_detection(questions)

async def find_cross_source_duplicates(source_questions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Convenience function for cross-source duplicate analysis"""
    detector = create_duplicate_detector()
    return await detector.cross_source_duplicate_analysis(source_questions)