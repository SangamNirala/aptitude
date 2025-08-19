"""
Enhanced Question Storage System for High-Volume Operations
Optimized storage system for handling 10,000+ questions with batch processing, 
duplicate detection, and comprehensive validation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
from collections import defaultdict
import hashlib
import json

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import os
from dotenv import load_dotenv

# Import models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.question_models import EnhancedQuestion
from models.scraping_models import RawExtractedQuestion, ProcessedScrapedQuestion

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

class HighVolumeStorageConfig:
    """Configuration for high-volume storage operations"""
    
    # Batch processing
    BATCH_SIZE = 50
    MAX_BATCH_WAIT_TIME = 30  # seconds
    MAX_CONCURRENT_BATCHES = 5
    
    # Duplicate detection
    ENABLE_DUPLICATE_DETECTION = True
    SIMILARITY_THRESHOLD = 0.85
    DUPLICATE_CHECK_BATCH_SIZE = 100
    
    # Performance optimization
    ENABLE_BULK_OPERATIONS = True
    INDEX_CREATION_ENABLED = True
    COMPRESSION_ENABLED = True
    
    # Quality control
    MINIMUM_QUALITY_SCORE = 70.0
    AUTO_VALIDATION_ENABLED = True
    STORAGE_VALIDATION_ENABLED = True

# =============================================================================
# HIGH-VOLUME STORAGE CLASS
# =============================================================================

class HighVolumeQuestionStorage:
    """
    Optimized storage system for handling large-scale question insertion with 
    duplicate detection, validation, and performance optimization
    """
    
    def __init__(self, config: HighVolumeStorageConfig = None):
        """Initialize high-volume storage system"""
        self.config = config or HighVolumeStorageConfig()
        
        # Database connection
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.questions_collection: Optional[AsyncIOMotorCollection] = None
        
        # Batch processing
        self.storage_queue = asyncio.Queue()
        self.batch_buffer = []
        self.batch_lock = asyncio.Lock()
        self.is_processing = False
        
        # Duplicate detection
        self.duplicate_detector = QuestionDuplicateDetector()
        self.question_hashes = set()  # For fast duplicate checking
        
        # Statistics
        self.storage_stats = {
            "total_processed": 0,
            "total_stored": 0,
            "total_duplicates": 0,
            "total_validation_failures": 0,
            "batches_processed": 0,
            "start_time": datetime.now(),
            "last_batch_time": None
        }
        
        logger.info("🗄️ HighVolumeQuestionStorage initialized")
    
    async def initialize_database(self) -> bool:
        """Initialize database connection and collections"""
        try:
            # Connect to MongoDB
            mongo_url = os.getenv('MONGO_URL')
            db_name = os.getenv('DB_NAME', 'test_database')
            
            if not mongo_url:
                raise ValueError("MONGO_URL not found in environment variables")
            
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            self.questions_collection = self.db.enhanced_questions
            
            # Create indexes for performance
            if self.config.INDEX_CREATION_ENABLED:
                await self._create_performance_indexes()
            
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def _create_performance_indexes(self):
        """Create indexes optimized for high-volume operations"""
        try:
            # Basic indexes
            await self.questions_collection.create_index([("category", 1), ("is_active", 1)])
            await self.questions_collection.create_index([("source", 1), ("created_at", -1)])
            await self.questions_collection.create_index([("ai_metrics.quality_score", -1)])
            
            # Duplicate detection indexes
            await self.questions_collection.create_index([("content_hash", 1)], unique=True, sparse=True)
            await self.questions_collection.create_index([("question_text_hash", 1)])
            
            # Compound indexes for filtering
            await self.questions_collection.create_index([
                ("category", 1), ("difficulty", 1), ("is_active", 1), ("ai_metrics.quality_score", -1)
            ])
            
            logger.info("🔗 Performance indexes created")
            
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def start_batch_processing(self):
        """Start batch processing for high-volume storage"""
        if self.is_processing:
            logger.warning("Batch processing already started")
            return
        
        self.is_processing = True
        
        # Start batch processor
        asyncio.create_task(self._batch_processor())
        
        logger.info("🚀 Batch processing started")
    
    async def stop_batch_processing(self):
        """Stop batch processing and flush remaining items"""
        self.is_processing = False
        
        # Process remaining items in buffer
        if self.batch_buffer:
            await self._process_batch(self.batch_buffer.copy())
            self.batch_buffer.clear()
        
        logger.info("⏹️ Batch processing stopped")
    
    async def store_questions_batch(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store batch of questions with validation and duplicate detection
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Storage results with statistics
        """
        try:
            logger.info(f"📦 Processing batch of {len(questions)} questions")
            
            if not self.questions_collection:
                raise RuntimeError("Database not initialized")
            
            # Process each question
            processed_questions = []
            duplicate_count = 0
            validation_failures = 0
            
            for question_data in questions:
                try:
                    # Validate question data
                    if self.config.AUTO_VALIDATION_ENABLED:
                        if not self._validate_question_data(question_data):
                            validation_failures += 1
                            continue
                    
                    # Check for duplicates
                    if self.config.ENABLE_DUPLICATE_DETECTION:
                        if await self._is_duplicate(question_data):
                            duplicate_count += 1
                            continue
                    
                    # Prepare for storage
                    enhanced_question = await self._prepare_question_for_storage(question_data)
                    processed_questions.append(enhanced_question)
                    
                except Exception as e:
                    logger.warning(f"Error processing question: {e}")
                    validation_failures += 1
            
            # Bulk insert processed questions
            stored_count = 0
            if processed_questions:
                try:
                    result = await self.questions_collection.insert_many(processed_questions, ordered=False)
                    stored_count = len(result.inserted_ids)
                    
                    logger.info(f"✅ Stored {stored_count} questions to database")
                    
                except Exception as e:
                    logger.error(f"Bulk insert failed: {e}")
                    # Fallback to individual inserts
                    stored_count = await self._fallback_individual_inserts(processed_questions)
            
            # Update statistics
            self.storage_stats["total_processed"] += len(questions)
            self.storage_stats["total_stored"] += stored_count
            self.storage_stats["total_duplicates"] += duplicate_count
            self.storage_stats["total_validation_failures"] += validation_failures
            self.storage_stats["batches_processed"] += 1
            self.storage_stats["last_batch_time"] = datetime.now()
            
            return {
                "success": True,
                "total_processed": len(questions),
                "stored": stored_count,
                "duplicates": duplicate_count,
                "validation_failures": validation_failures,
                "storage_stats": self.storage_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"❌ Batch storage failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_processed": len(questions),
                "stored": 0
            }
    
    async def _fallback_individual_inserts(self, questions: List[Dict[str, Any]]) -> int:
        """Fallback to individual inserts if bulk insert fails"""
        stored_count = 0
        
        for question in questions:
            try:
                await self.questions_collection.insert_one(question)
                stored_count += 1
            except Exception as e:
                logger.warning(f"Individual insert failed: {e}")
        
        return stored_count
    
    async def _batch_processor(self):
        """Background batch processor for queued items"""
        while self.is_processing:
            try:
                # Wait for items or timeout
                try:
                    item = await asyncio.wait_for(
                        self.storage_queue.get(), 
                        timeout=self.config.MAX_BATCH_WAIT_TIME
                    )
                    
                    async with self.batch_lock:
                        self.batch_buffer.append(item)
                        
                        # Process batch if full
                        if len(self.batch_buffer) >= self.config.BATCH_SIZE:
                            await self._process_batch(self.batch_buffer.copy())
                            self.batch_buffer.clear()
                
                except asyncio.TimeoutError:
                    # Process partial batch on timeout
                    async with self.batch_lock:
                        if self.batch_buffer:
                            await self._process_batch(self.batch_buffer.copy())
                            self.batch_buffer.clear()
            
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of questions"""
        if not batch:
            return
        
        try:
            result = await self.store_questions_batch(batch)
            
            if result["success"]:
                logger.info(f"✅ Batch processed: {result['stored']}/{len(batch)} questions stored")
            else:
                logger.error(f"❌ Batch processing failed: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
    
    async def _prepare_question_for_storage(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare question data for storage with enhancements"""
        try:
            # Generate unique ID
            question_id = str(uuid.uuid4())
            
            # Create content hash for duplicate detection
            content_hash = self._generate_content_hash(question_data)
            question_text_hash = self._generate_text_hash(question_data.get("raw_question_text", ""))
            
            # Create enhanced question structure
            enhanced_question = {
                "id": question_id,
                "question_text": question_data.get("raw_question_text", ""),
                "options": question_data.get("raw_options", []),
                "correct_answer": question_data.get("raw_correct_answer", ""),
                "explanation": question_data.get("raw_explanation", ""),
                
                # Categorization
                "category": question_data.get("detected_category", "general"),
                "difficulty": question_data.get("detected_difficulty", "medium"),
                "source": question_data.get("source_id", "unknown"),
                
                # AI metrics (with defaults)
                "ai_metrics": {
                    "quality_score": self._calculate_quality_score(question_data),
                    "clarity_score": 80.0,
                    "relevance_score": 85.0,
                    "difficulty_score": 75.0,
                    "engagement_score": 80.0,
                    "completeness_score": question_data.get("completeness_score", 85.0)
                },
                
                # Analytics
                "analytics": {
                    "total_attempts": 0,
                    "correct_attempts": 0,
                    "average_time_taken": 0.0,
                    "difficulty_rating": 0.0,
                    "last_attempted": None
                },
                
                # Metadata
                "metadata": {
                    "extraction_method": question_data.get("extraction_method", "unknown"),
                    "source_url": question_data.get("source_url", ""),
                    "page_number": question_data.get("page_number"),
                    "extraction_timestamp": question_data.get("extraction_timestamp", datetime.now()),
                    "concepts": self._extract_concepts(question_data),
                    "topics": self._extract_topics(question_data)
                },
                
                # Duplicate detection
                "content_hash": content_hash,
                "question_text_hash": question_text_hash,
                
                # Status
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            return enhanced_question
            
        except Exception as e:
            logger.error(f"Error preparing question for storage: {e}")
            raise
    
    def _validate_question_data(self, question_data: Dict[str, Any]) -> bool:
        """Validate question data before storage"""
        try:
            # Required fields
            question_text = question_data.get("raw_question_text", "")
            options = question_data.get("raw_options", [])
            
            # Basic validation
            if not question_text or len(question_text.strip()) < 10:
                return False
            
            if not options or len(options) < 2:
                return False
            
            # Quality threshold check
            quality_score = self._calculate_quality_score(question_data)
            if quality_score < self.config.MINIMUM_QUALITY_SCORE:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Validation error: {e}")
            return False
    
    async def _is_duplicate(self, question_data: Dict[str, Any]) -> bool:
        """Check if question is a duplicate"""
        try:
            # Generate hashes
            content_hash = self._generate_content_hash(question_data)
            text_hash = self._generate_text_hash(question_data.get("raw_question_text", ""))
            
            # Quick check against in-memory hashes
            if content_hash in self.question_hashes:
                return True
            
            # Database check
            existing = await self.questions_collection.find_one({
                "$or": [
                    {"content_hash": content_hash},
                    {"question_text_hash": text_hash}
                ]
            })
            
            if existing:
                return True
            
            # Add to in-memory cache
            self.question_hashes.add(content_hash)
            
            return False
            
        except Exception as e:
            logger.warning(f"Duplicate detection error: {e}")
            return False  # Default to not duplicate on error
    
    def _generate_content_hash(self, question_data: Dict[str, Any]) -> str:
        """Generate hash for complete question content"""
        try:
            content = {
                "question": question_data.get("raw_question_text", "").lower().strip(),
                "options": sorted([opt.lower().strip() for opt in question_data.get("raw_options", [])]),
                "answer": question_data.get("raw_correct_answer", "").lower().strip()
            }
            
            content_str = json.dumps(content, sort_keys=True)
            return hashlib.md5(content_str.encode()).hexdigest()
            
        except Exception as e:
            logger.warning(f"Content hash generation error: {e}")
            return str(uuid.uuid4())
    
    def _generate_text_hash(self, text: str) -> str:
        """Generate hash for question text only"""
        try:
            normalized_text = text.lower().strip()
            return hashlib.md5(normalized_text.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Text hash generation error: {e}")
            return str(uuid.uuid4())
    
    def _calculate_quality_score(self, question_data: Dict[str, Any]) -> float:
        """Calculate quality score for question"""
        try:
            score = 0.0
            
            # Question text quality (40%)
            question_text = question_data.get("raw_question_text", "")
            if question_text and len(question_text.strip()) > 20:
                score += 40.0
            
            # Options quality (30%)
            options = question_data.get("raw_options", [])
            if len(options) >= 4:
                score += 30.0
            elif len(options) >= 2:
                score += 20.0
            
            # Correct answer (20%)
            if question_data.get("raw_correct_answer"):
                score += 20.0
            
            # Explanation (10%)
            explanation = question_data.get("raw_explanation", "")
            if explanation and len(explanation.strip()) > 10:
                score += 10.0
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.warning(f"Quality score calculation error: {e}")
            return 75.0  # Default score
    
    def _extract_concepts(self, question_data: Dict[str, Any]) -> List[str]:
        """Extract concepts from question data"""
        concepts = []
        
        try:
            # Extract from category
            category = question_data.get("detected_category", "")
            if category:
                concepts.append(category)
            
            # Extract from question text (simple keyword extraction)
            question_text = question_data.get("raw_question_text", "").lower()
            
            concept_keywords = {
                "percentage": ["percentage", "percent", "%"],
                "profit_loss": ["profit", "loss", "selling", "cost price"],
                "time_work": ["work", "time", "complete", "days"],
                "speed_distance": ["speed", "distance", "time", "km/h"],
                "probability": ["probability", "chance", "random"],
                "geometry": ["area", "volume", "radius", "triangle", "circle"],
                "algebra": ["equation", "solve", "x", "y", "variable"]
            }
            
            for concept, keywords in concept_keywords.items():
                if any(keyword in question_text for keyword in keywords):
                    concepts.append(concept)
            
        except Exception as e:
            logger.warning(f"Concept extraction error: {e}")
        
        return list(set(concepts))  # Remove duplicates
    
    def _extract_topics(self, question_data: Dict[str, Any]) -> List[str]:
        """Extract topics from question data"""
        topics = []
        
        try:
            # Use detected category as primary topic
            category = question_data.get("detected_category")
            if category:
                topics.append(category)
            
            # Add source-specific topics
            source = question_data.get("source_id", "")
            if source:
                topics.append(f"source_{source}")
            
        except Exception as e:
            logger.warning(f"Topic extraction error: {e}")
        
        return topics
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        try:
            # Calculate rates
            elapsed_time = (datetime.now() - self.storage_stats["start_time"]).total_seconds()
            storage_rate = self.storage_stats["total_stored"] / (elapsed_time / 60) if elapsed_time > 0 else 0.0
            
            # Database statistics
            db_stats = await self.questions_collection.count_documents({})
            
            return {
                "processing_stats": self.storage_stats.copy(),
                "performance_metrics": {
                    "storage_rate_per_minute": storage_rate,
                    "success_rate": (self.storage_stats["total_stored"] / self.storage_stats["total_processed"]) * 100 if self.storage_stats["total_processed"] > 0 else 0.0,
                    "duplicate_rate": (self.storage_stats["total_duplicates"] / self.storage_stats["total_processed"]) * 100 if self.storage_stats["total_processed"] > 0 else 0.0
                },
                "database_stats": {
                    "total_questions_in_db": db_stats,
                    "collection_name": self.questions_collection.name
                },
                "system_status": "operational" if self.is_processing else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up storage system resources"""
        try:
            # Stop processing
            await self.stop_batch_processing()
            
            # Close database connection
            if self.client:
                self.client.close()
            
            logger.info("🧹 Storage system cleanup completed")
            
        except Exception as e:
            logger.error(f"Storage cleanup error: {e}")

# =============================================================================
# DUPLICATE DETECTION CLASS
# =============================================================================

class QuestionDuplicateDetector:
    """Advanced duplicate detection for questions"""
    
    def __init__(self):
        self.similarity_cache = {}
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two question texts"""
        try:
            # Simple similarity calculation (can be enhanced with ML models)
            text1_words = set(text1.lower().split())
            text2_words = set(text2.lower().split())
            
            intersection = text1_words.intersection(text2_words)
            union = text1_words.union(text2_words)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.warning(f"Similarity calculation error: {e}")
            return 0.0

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

async def create_high_volume_storage() -> HighVolumeQuestionStorage:
    """Create and initialize high-volume storage system"""
    storage = HighVolumeQuestionStorage()
    
    if await storage.initialize_database():
        await storage.start_batch_processing()
        return storage
    else:
        raise RuntimeError("Failed to initialize high-volume storage system")