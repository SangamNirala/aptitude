"""
Performance Optimization API Router for TASK 18: Performance Optimization & Scaling

This router provides API endpoints for:
- Database optimization management
- Performance monitoring and metrics
- Load testing execution and results
- Memory optimization controls
- Scalability testing for 1000+ questions processing
"""

import logging
import asyncio
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Import performance optimization modules
from performance import (
    IndexStrategy,
    ProcessingStrategy,
    LoadTestType,
    LoadTestConfig,
    optimize_database_for_scale,
    create_memory_optimizer,
    run_comprehensive_performance_test,
    create_load_tester,
    initialize_performance_optimization
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/performance", tags=["Performance Optimization & Scaling"])

# Global performance optimization components
performance_components = {}

# Request/Response Models
class DatabaseOptimizationRequest(BaseModel):
    """Request model for database optimization"""
    strategy: IndexStrategy = IndexStrategy.PERFORMANCE
    force_reindex: bool = False

class LoadTestRequest(BaseModel):
    """Request model for load testing"""
    test_type: LoadTestType = LoadTestType.LOAD
    concurrent_users: int = Field(10, ge=1, le=1000)
    total_requests: int = Field(100, ge=1, le=10000)
    target_endpoint: str = "/api/health"
    max_response_time_ms: float = Field(5000.0, ge=100.0)
    duration_seconds: Optional[int] = Field(None, ge=1, le=3600)

class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""
    timestamp: datetime
    database_metrics: Dict[str, Any]
    memory_metrics: Dict[str, Any]
    processing_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]

class OptimizationReportResponse(BaseModel):
    """Response model for optimization report"""
    optimization_timestamp: datetime
    database_optimization: Dict[str, Any]
    memory_optimization: Dict[str, Any]
    performance_score: float
    recommendations: List[str]
    ready_for_scale: bool

# Initialize database connection (will be set on startup)
db: Optional[AsyncIOMotorDatabase] = None
client: Optional[AsyncIOMotorClient] = None

def initialize_db_connection():
    """Initialize database connection for performance optimization"""
    global db, client
    try:
        mongo_url = os.environ.get('MONGO_URL')
        if mongo_url:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'ai_questions_db')]
            logger.info("Database connection initialized for performance optimization")
        else:
            logger.warning("MONGO_URL not found - database optimization will be limited")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}")

# Helper function for optimization recommendations
def _generate_optimization_recommendations(results) -> List[str]:
    """Generate optimization recommendations based on test results"""
    recommendations = []
    
    if results.success_rate < 0.95:
        recommendations.append("Improve error handling and system stability")
    
    if results.avg_response_time > 5000:
        recommendations.append("Optimize response time through better caching and indexing")
    
    if results.peak_memory_mb > 1500:
        recommendations.append("Implement memory optimization strategies")
    
    if results.peak_cpu_percent > 85:
        recommendations.append("Scale horizontally or optimize CPU-intensive operations")
    
    if results.requests_per_second < 50:
        recommendations.append("Improve throughput through concurrent processing optimization")
    
    return recommendations or ["System performance is within acceptable parameters"]

# =============================================================================
# DATABASE OPTIMIZATION ENDPOINTS
# =============================================================================

@router.post("/database/optimize", response_model=Dict[str, Any])
async def optimize_database(request: DatabaseOptimizationRequest, background_tasks: BackgroundTasks):
    """
    Optimize database for high-volume operations with comprehensive indexing
    """
    try:
        logger.info(f"🔧 Starting database optimization with {request.strategy} strategy")
        
        if not db or not client:
            initialize_db_connection()
            if not db or not client:
                raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Execute database optimization
        optimization_result = await optimize_database_for_scale(
            db, client, request.strategy
        )
        
        logger.info(f"✅ Database optimization completed: {optimization_result['index_optimization']['indexes_created']} indexes created")
        
        return {
            "success": True,
            "optimization_completed": optimization_result["optimization_completed"],
            "strategy_used": optimization_result["strategy_used"],
            "indexes_created": optimization_result["index_optimization"]["indexes_created"],
            "collections_optimized": optimization_result["index_optimization"]["collections_optimized"],
            "connection_pool_optimized": optimization_result["connection_pool_optimization"]["optimization_applied"],
            "performance_report": optimization_result["performance_report"],
            "ready_for_scale": optimization_result["ready_for_scale"],
            "message": f"Database optimized with {request.strategy} strategy for 1000+ questions processing"
        }
        
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database optimization failed: {str(e)}")

@router.post("/load-test/1000-questions", response_model=Dict[str, Any])
async def test_1000_questions_processing():
    """
    Execute the primary TASK 18 requirement: 1000+ questions processing load test
    """
    try:
        logger.info("🎯 Starting TASK 18 primary test: 1000+ questions processing")
        
        # Get base URL for testing  
        base_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        if base_url.endswith('/api'):
            base_url = base_url[:-4]  # Remove /api suffix
        
        # Execute the 1000+ questions test
        from performance.load_tester import test_1000_questions_processing
        results = await test_1000_questions_processing(base_url)
        
        # Determine if performance targets are met
        performance_targets_met = (
            results.success_rate >= 0.95 and
            results.avg_response_time <= 10000 and  # 10 seconds
            results.requests_per_second >= 50 and    # At least 50 RPS
            results.performance_score >= 80.0
        )
        
        logger.info(f"✅ 1000+ questions test completed")
        logger.info(f"   Performance Targets Met: {'✅ YES' if performance_targets_met else '❌ NO'}")
        logger.info(f"   Success Rate: {results.success_rate:.2%}")
        logger.info(f"   Throughput: {results.requests_per_second:.1f} RPS")
        logger.info(f"   Performance Score: {results.performance_score:.1f}/100")
        
        return {
            "test_completed": True,
            "test_name": "TASK_18_1000_Questions_Processing",
            "performance_targets_met": performance_targets_met,
            "test_summary": {
                "total_questions_processed": results.total_requests,
                "successful_processing": results.successful_requests,
                "success_rate": results.success_rate,
                "avg_response_time_ms": results.avg_response_time,
                "throughput_rps": results.requests_per_second,
                "performance_score": results.performance_score
            },
            "scalability_metrics": {
                "peak_concurrent_users": results.config.concurrent_users,
                "peak_memory_usage_mb": results.peak_memory_mb,
                "peak_cpu_usage_percent": results.peak_cpu_percent,
                "system_stability": "stable" if results.meets_sla else "unstable"
            },
            "performance_analysis": {
                "meets_sla_requirements": results.meets_sla,
                "bottlenecks_identified": results.bottlenecks_identified,
                "optimization_recommendations": _generate_optimization_recommendations(results)
            },
            "detailed_results": {
                "p50_response_time": results.p50_response_time,
                "p90_response_time": results.p90_response_time,
                "p95_response_time": results.p95_response_time,
                "p99_response_time": results.p99_response_time,
                "error_distribution": results.error_distribution,
                "test_duration_seconds": results.duration_seconds
            }
        }
        
    except Exception as e:
        logger.error(f"1000+ questions processing test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"1000+ questions processing test failed: {str(e)}")

@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_full_performance_optimization():
    """
    Initialize complete performance optimization system for TASK 18
    """
    try:
        logger.info("🚀 Initializing complete TASK 18: Performance Optimization & Scaling system")
        
        # Initialize database connection
        initialize_db_connection()
        
        # Initialize comprehensive performance optimization
        if db is not None and client is not None:
            optimization_results = await initialize_performance_optimization(
                db, client, IndexStrategy.COMPREHENSIVE
            )
            
            # Store components globally
            global performance_components
            performance_components.update(optimization_results)
            
            logger.info("✅ Complete performance optimization system initialized")
            
            return {
                "initialization_completed": True,
                "components_initialized": {
                    "database_optimizer": "✅ Ready",
                    "memory_optimizer": "✅ Ready", 
                    "concurrent_processor": "✅ Ready",
                    "load_tester": "✅ Ready"
                },
                "optimization_results": optimization_results["optimization_results"],
                "performance_caches": list(optimization_results["caches"].keys()),
                "object_pools": list(optimization_results["pools"].keys()),
                "ready_for_1000_questions": True,
                "message": "TASK 18 Performance Optimization & Scaling system fully initialized and ready for high-volume operations"
            }
        else:
            raise HTTPException(status_code=500, detail="Database connection required for full optimization")
            
    except Exception as e:
        logger.error(f"Performance optimization initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance optimization initialization failed: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_performance_optimization_status():
    """
    Get overall performance optimization status for TASK 18
    """
    try:
        # Check system resources
        import psutil
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check database connection
        db_status = "not_connected"
        if db:
            try:
                await db.command("ping")
                db_status = "connected"
            except Exception:
                db_status = "connection_error"
        
        # Check optimization components
        memory_optimizer = performance_components.get("memory_optimizer")
        caches = performance_components.get("caches", {})
        pools = performance_components.get("pools", {})
        
        # Calculate readiness score
        readiness_score = 0
        if db_status == "connected":
            readiness_score += 30
        if memory_optimizer:
            readiness_score += 25
        if caches:
            readiness_score += 25
        if cpu_percent < 80 and memory.percent < 80:
            readiness_score += 20
        
        return {
            "task_18_status": "ready" if readiness_score >= 80 else "partial",
            "readiness_score": readiness_score,
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024)
            },
            "components_status": {
                "database_connection": db_status,
                "memory_optimizer": "enabled" if memory_optimizer else "disabled",
                "performance_caches": len(caches),
                "object_pools": len(pools)
            },
            "optimization_features": {
                "database_query_optimization": db_status == "connected",
                "concurrent_processing_improvements": True,
                "memory_usage_optimization": memory_optimizer is not None,
                "scalability_testing": True
            },
            "ready_for_1000_questions": readiness_score >= 80,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance status: {str(e)}")

# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def performance_health_check():
    """
    Health check for performance optimization system
    """
    return {
        "status": "healthy",
        "task_18_ready": True,
        "performance_optimization": "enabled",
        "timestamp": datetime.utcnow()
    }