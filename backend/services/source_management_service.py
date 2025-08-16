"""
Source Management Service
Manages scraping data sources, configurations, and source reliability
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.scraping_models import (
    DataSourceConfig, ScrapingTarget, SourceReliabilityReport,
    ScrapingSourceType, ContentExtractionMethod, ScrapingJobStatus
)
from ..config.scraping_config import (
    get_source_config, get_source_targets, get_quality_thresholds,
    get_anti_detection_config, SOURCE_PRIORITY_CONFIG
)

logger = logging.getLogger(__name__)

class SourceManagementService:
    """Service for managing scraping data sources and configurations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sources_collection = db.scraping_sources
        self.targets_collection = db.scraping_targets
        self.reliability_collection = db.source_reliability
        
    # =============================================================================
    # SOURCE CONFIGURATION MANAGEMENT
    # =============================================================================
    
    async def initialize_default_sources(self) -> Dict[str, str]:
        """Initialize default source configurations in database"""
        try:
            results = {}
            
            # Initialize IndiaBix source
            indiabix_config = get_source_config("indiabix")
            indiabix_id = await self._create_or_update_source(indiabix_config)
            results["indiabix"] = indiabix_id
            
            # Initialize GeeksforGeeks source  
            geeksforgeeks_config = get_source_config("geeksforgeeks")
            geeksforgeeks_id = await self._create_or_update_source(geeksforgeeks_config)
            results["geeksforgeeks"] = geeksforgeeks_id
            
            # Initialize targets for each source
            await self._initialize_source_targets("indiabix", indiabix_id)
            await self._initialize_source_targets("geeksforgeeks", geeksforgeeks_id)
            
            logger.info(f"✅ Initialized default sources: {list(results.keys())}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize default sources: {str(e)}")
            raise
    
    async def _create_or_update_source(self, config: DataSourceConfig) -> str:
        """Create or update a source configuration"""
        try:
            # Check if source exists
            existing_source = await self.sources_collection.find_one({"name": config.name})
            
            config_dict = config.dict()
            config_dict["updated_at"] = datetime.utcnow()
            
            if existing_source:
                # Update existing source
                await self.sources_collection.update_one(
                    {"_id": existing_source["_id"]},
                    {"$set": config_dict}
                )
                source_id = existing_source["id"]
                logger.info(f"Updated source: {config.name}")
            else:
                # Create new source
                await self.sources_collection.insert_one(config_dict)
                source_id = config.id
                logger.info(f"Created new source: {config.name}")
                
            return source_id
            
        except Exception as e:
            logger.error(f"Failed to create/update source {config.name}: {str(e)}")
            raise
    
    async def _initialize_source_targets(self, source_name: str, source_id: str):
        """Initialize targets for a specific source"""
        try:
            targets = get_source_targets(source_name)
            
            for target in targets:
                target.source_id = source_id
                target_dict = target.dict()
                
                # Check if target exists
                existing_target = await self.targets_collection.find_one({
                    "source_id": source_id,
                    "category": target.category,
                    "subcategory": target.subcategory
                })
                
                if not existing_target:
                    await self.targets_collection.insert_one(target_dict)
                    logger.debug(f"Created target: {target.category}/{target.subcategory}")
                else:
                    # Update existing target
                    await self.targets_collection.update_one(
                        {"_id": existing_target["_id"]},
                        {"$set": target_dict}
                    )
                    
            logger.info(f"Initialized {len(targets)} targets for {source_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize targets for {source_name}: {str(e)}")
            raise
    
    # =============================================================================
    # SOURCE RETRIEVAL & MANAGEMENT
    # =============================================================================
    
    async def get_all_sources(self) -> List[DataSourceConfig]:
        """Get all configured scraping sources"""
        try:
            sources_cursor = self.sources_collection.find({"is_active": True})
            sources = []
            
            async for source_doc in sources_cursor:
                source = DataSourceConfig(**source_doc)
                sources.append(source)
                
            logger.info(f"Retrieved {len(sources)} active sources")
            return sources
            
        except Exception as e:
            logger.error(f"Failed to get sources: {str(e)}")
            return []
    
    async def get_source_by_name(self, name: str) -> Optional[DataSourceConfig]:
        """Get source configuration by name"""
        try:
            source_doc = await self.sources_collection.find_one({
                "name": name,
                "is_active": True
            })
            
            if source_doc:
                return DataSourceConfig(**source_doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get source {name}: {str(e)}")
            return None
    
    async def get_source_targets(self, source_id: str, category: Optional[str] = None) -> List[ScrapingTarget]:
        """Get targets for a specific source, optionally filtered by category"""
        try:
            query = {"source_id": source_id, "is_active": True}
            if category:
                query["category"] = category
                
            targets_cursor = self.targets_collection.find(query).sort("priority", 1)
            targets = []
            
            async for target_doc in targets_cursor:
                target = ScrapingTarget(**target_doc)
                targets.append(target)
                
            logger.info(f"Retrieved {len(targets)} targets for source {source_id}")
            return targets
            
        except Exception as e:
            logger.error(f"Failed to get targets for source {source_id}: {str(e)}")
            return []
    
    async def get_high_priority_targets(self, limit: int = 10) -> List[ScrapingTarget]:
        """Get highest priority targets across all sources"""
        try:
            targets_cursor = self.targets_collection.find({
                "is_active": True,
                "priority": {"$lte": 2}
            }).sort("priority", 1).limit(limit)
            
            targets = []
            async for target_doc in targets_cursor:
                target = ScrapingTarget(**target_doc)
                targets.append(target)
                
            return targets
            
        except Exception as e:
            logger.error(f"Failed to get high priority targets: {str(e)}")
            return []
    
    # =============================================================================
    # SOURCE RELIABILITY & MONITORING
    # =============================================================================
    
    async def update_source_reliability(self, source_id: str, job_result: Dict[str, Any]):
        """Update source reliability based on scraping job results"""
        try:
            source = await self.sources_collection.find_one({"id": source_id})
            if not source:
                logger.warning(f"Source {source_id} not found for reliability update")
                return
            
            # Calculate new reliability metrics
            success_rate = job_result.get("success_rate", 0.0)
            questions_extracted = job_result.get("questions_extracted", 0)
            avg_quality = job_result.get("avg_quality_score", 0.0)
            
            # Update source statistics
            current_success_rate = source.get("success_rate", 0.0)
            current_question_count = source.get("total_questions_scraped", 0)
            current_quality = source.get("avg_quality_score", 0.0)
            
            # Weighted average for reliability score
            new_reliability = (current_success_rate * 0.7 + success_rate * 0.3)
            new_question_count = current_question_count + questions_extracted
            new_avg_quality = ((current_quality * current_question_count + 
                              avg_quality * questions_extracted) / 
                             max(new_question_count, 1))
            
            # Update source
            await self.sources_collection.update_one(
                {"id": source_id},
                {
                    "$set": {
                        "success_rate": success_rate,
                        "total_questions_scraped": new_question_count,
                        "avg_quality_score": new_avg_quality,
                        "reliability_score": new_reliability,
                        "last_scraped": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Updated reliability for source {source_id}: {new_reliability:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to update source reliability: {str(e)}")
    
    async def generate_reliability_report(self, source_id: str) -> Optional[SourceReliabilityReport]:
        """Generate comprehensive reliability report for a source"""
        try:
            source = await self.sources_collection.find_one({"id": source_id})
            if not source:
                return None
            
            # Get recent job history (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # This would need to query scraping jobs collection (implemented in later tasks)
            # For now, we'll use the source data
            
            report = SourceReliabilityReport(
                source_id=source_id,
                source_name=source.get("name", "Unknown"),
                reliability_score=source.get("reliability_score", 0.0),
                uptime_percentage=95.0,  # Placeholder - would calculate from job history
                avg_response_time=2.5,   # Placeholder
                total_questions_scraped=source.get("total_questions_scraped", 0),
                avg_quality_score=source.get("avg_quality_score", 0.0),
                success_rate=source.get("success_rate", 0.0),
                last_successful_scrape=source.get("last_scraped")
            )
            
            # Add trend analysis (simplified)
            if source.get("success_rate", 0.0) > 0.8:
                report.quality_trend = "stable"
            elif source.get("success_rate", 0.0) > 0.6:
                report.quality_trend = "declining"
            else:
                report.quality_trend = "poor"
                report.recommended_actions.append("Review source configuration")
                report.recommended_actions.append("Check for site structure changes")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate reliability report: {str(e)}")
            return None
    
    # =============================================================================
    # SOURCE HEALTH MONITORING
    # =============================================================================
    
    async def check_source_health(self, source_id: str) -> Dict[str, Any]:
        """Check the health status of a specific source"""
        try:
            source = await self.sources_collection.find_one({"id": source_id})
            if not source:
                return {"status": "not_found", "message": f"Source {source_id} not found"}
            
            health_status = {
                "source_id": source_id,
                "source_name": source.get("name", "Unknown"),
                "status": "healthy",
                "checks": [],
                "warnings": [],
                "last_checked": datetime.utcnow()
            }
            
            # Check if source is active
            if not source.get("is_active", False):
                health_status["status"] = "inactive"
                health_status["warnings"].append("Source is marked as inactive")
            
            # Check last scrape time
            last_scraped = source.get("last_scraped")
            if last_scraped:
                time_since_last_scrape = datetime.utcnow() - last_scraped
                if time_since_last_scrape > timedelta(days=7):
                    health_status["warnings"].append("No successful scrape in over 7 days")
            else:
                health_status["warnings"].append("Source has never been scraped")
            
            # Check success rate
            success_rate = source.get("success_rate", 0.0)
            if success_rate < 0.5:
                health_status["status"] = "degraded"
                health_status["warnings"].append(f"Low success rate: {success_rate:.1%}")
            
            # Check reliability score
            reliability = source.get("reliability_score", 0.0)
            if reliability < 70.0:
                health_status["status"] = "degraded" 
                health_status["warnings"].append(f"Low reliability score: {reliability:.1f}")
            
            health_status["checks"] = [
                f"Active: {source.get('is_active', False)}",
                f"Success Rate: {success_rate:.1%}",
                f"Reliability: {reliability:.1f}",
                f"Total Questions: {source.get('total_questions_scraped', 0)}",
                f"Avg Quality: {source.get('avg_quality_score', 0.0):.1f}"
            ]
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to check source health: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def check_all_sources_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all sources"""
        try:
            sources = await self.get_all_sources()
            health_reports = {}
            
            for source in sources:
                health_report = await self.check_source_health(source.id)
                health_reports[source.name] = health_report
            
            return health_reports
            
        except Exception as e:
            logger.error(f"Failed to check all sources health: {str(e)}")
            return {}
    
    # =============================================================================
    # SOURCE CONFIGURATION UPDATES
    # =============================================================================
    
    async def update_source_config(self, source_id: str, updates: Dict[str, Any]) -> bool:
        """Update source configuration"""
        try:
            # Validate updates
            allowed_updates = {
                "rate_limit_delay", "max_concurrent_requests", "is_active",
                "selectors", "pagination_config"
            }
            
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
            filtered_updates["updated_at"] = datetime.utcnow()
            
            result = await self.sources_collection.update_one(
                {"id": source_id},
                {"$set": filtered_updates}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated source {source_id} configuration")
            else:
                logger.warning(f"No updates applied to source {source_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to update source config: {str(e)}")
            return False
    
    async def toggle_source_status(self, source_id: str, active: bool) -> bool:
        """Enable or disable a source"""
        try:
            result = await self.sources_collection.update_one(
                {"id": source_id},
                {
                    "$set": {
                        "is_active": active,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            status = "enabled" if active else "disabled"
            
            if success:
                logger.info(f"Source {source_id} {status}")
            else:
                logger.warning(f"Failed to {status.lower()} source {source_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to toggle source status: {str(e)}")
            return False
    
    # =============================================================================
    # TARGET MANAGEMENT
    # =============================================================================
    
    async def update_target_progress(self, target_id: str, progress_data: Dict[str, Any]):
        """Update target scraping progress"""
        try:
            progress_updates = {
                "last_scraped_page": progress_data.get("last_page", 0),
                "questions_extracted": progress_data.get("questions_count", 0),
                "updated_at": datetime.utcnow()
            }
            
            if "total_pages" in progress_data:
                progress_updates["total_pages"] = progress_data["total_pages"]
            
            await self.targets_collection.update_one(
                {"id": target_id},
                {"$set": progress_updates}
            )
            
            logger.debug(f"Updated target {target_id} progress")
            
        except Exception as e:
            logger.error(f"Failed to update target progress: {str(e)}")
    
    async def get_target_statistics(self) -> Dict[str, Any]:
        """Get statistics about all targets"""
        try:
            pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "total_questions": {"$sum": "$questions_extracted"},
                    "avg_priority": {"$avg": "$priority"}
                }}
            ]
            
            stats_cursor = self.targets_collection.aggregate(pipeline)
            category_stats = {}
            
            async for stat in stats_cursor:
                category_stats[stat["_id"]] = {
                    "target_count": stat["count"],
                    "questions_extracted": stat["total_questions"],
                    "avg_priority": round(stat["avg_priority"], 1)
                }
            
            # Overall statistics
            total_targets = await self.targets_collection.count_documents({"is_active": True})
            total_questions = sum(stats["questions_extracted"] for stats in category_stats.values())
            
            return {
                "total_active_targets": total_targets,
                "total_questions_extracted": total_questions,
                "categories": category_stats,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get target statistics: {str(e)}")
            return {}
    
    # =============================================================================
    # DATABASE INDEXES & OPTIMIZATION
    # =============================================================================
    
    async def create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Source indexes
            await self.sources_collection.create_index([("name", 1)], unique=True)
            await self.sources_collection.create_index([("source_type", 1), ("is_active", 1)])
            await self.sources_collection.create_index([("reliability_score", -1)])
            
            # Target indexes
            await self.targets_collection.create_index([("source_id", 1), ("category", 1)])
            await self.targets_collection.create_index([("priority", 1), ("is_active", 1)])
            await self.targets_collection.create_index([("questions_extracted", -1)])
            
            # Reliability indexes
            await self.reliability_collection.create_index([("source_id", 1), ("generated_at", -1)])
            
            logger.info("✅ Created database indexes for source management")
            
        except Exception as e:
            logger.warning(f"Index creation warning: {str(e)}")

# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================

async def initialize_source_management(db: AsyncIOMotorDatabase) -> SourceManagementService:
    """Initialize source management service with default configurations"""
    service = SourceManagementService(db)
    
    # Create indexes
    await service.create_indexes()
    
    # Initialize default sources
    await service.initialize_default_sources()
    
    logger.info("✅ Source management service initialized successfully")
    return service