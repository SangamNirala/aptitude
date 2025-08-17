"""
Performance Optimization & Scaling Module for TASK 18

This module provides comprehensive performance optimization features including:
- Database query optimization with intelligent indexing
- Concurrent processing improvements with adaptive algorithms  
- Memory usage optimization with intelligent caching
- Scalability testing framework for 1000+ questions processing
- Real-time performance monitoring and bottleneck detection
"""

from .database_optimizer import (
    DatabaseOptimizer, 
    IndexStrategy, 
    optimize_database_for_scale,
    create_database_optimizer
)

from .concurrent_processor import (
    ConcurrentProcessor,
    ProcessingStrategy,
    ProcessingMetrics,
    BatchProcessingConfig,
    ResourceMonitor,
    ConnectionPoolManager,
    create_optimized_processor,
    optimize_async_function
)

from .memory_optimizer import (
    MemoryOptimizer,
    MemoryEfficientCache,
    MemoryPool,
    StreamingProcessor,
    GarbageCollectionOptimizer,
    CacheStrategy,
    create_memory_optimizer,
    memory_efficient
)

from .load_tester import (
    LoadTestExecutor,
    LoadTestConfig,
    LoadTestResults,
    LoadTestType,
    test_1000_questions_processing,
    test_api_scalability,
    run_comprehensive_performance_test,
    create_load_tester
)

__version__ = "1.0.0"
__author__ = "AI-Enhanced Web Scraping System"

# Performance optimization factory function
async def initialize_performance_optimization(db, client, strategy=IndexStrategy.PERFORMANCE):
    """
    Initialize comprehensive performance optimization for the system
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Initializing TASK 18: Performance Optimization & Scaling")
    
    # Initialize database optimizer
    db_optimizer = await create_database_optimizer(db, client)
    db_results = await db_optimizer.initialize_comprehensive_indexes(strategy)
    
    # Initialize memory optimizer
    memory_optimizer = create_memory_optimizer()
    memory_optimizer.start_monitoring()
    
    # Create performance-optimized caches
    question_cache = memory_optimizer.create_cache(
        "enhanced_questions",
        max_size=2000,
        max_memory_mb=200.0,
        strategy=CacheStrategy.LRU,
        ttl_seconds=3600  # 1 hour TTL
    )
    
    scraping_cache = memory_optimizer.create_cache(
        "scraping_results", 
        max_size=1000,
        max_memory_mb=150.0,
        strategy=CacheStrategy.ADAPTIVE
    )
    
    # Create object pools for frequently used objects
    request_pool = memory_optimizer.create_pool(
        "api_requests",
        factory_func=dict,
        max_size=100
    )
    
    logger.info("✅ Performance optimization initialization completed")
    
    return {
        "database_optimizer": db_optimizer,
        "memory_optimizer": memory_optimizer, 
        "optimization_results": db_results,
        "caches": {
            "questions": question_cache,
            "scraping": scraping_cache
        },
        "pools": {
            "requests": request_pool
        }
    }

# Export key classes and functions
__all__ = [
    # Database optimization
    "DatabaseOptimizer",
    "IndexStrategy", 
    "optimize_database_for_scale",
    "create_database_optimizer",
    
    # Concurrent processing
    "ConcurrentProcessor",
    "ProcessingStrategy",
    "ProcessingMetrics",
    "BatchProcessingConfig",
    "ResourceMonitor",
    "ConnectionPoolManager",
    "create_optimized_processor",
    "optimize_async_function",
    
    # Memory optimization
    "MemoryOptimizer",
    "MemoryEfficientCache", 
    "MemoryPool",
    "StreamingProcessor",
    "GarbageCollectionOptimizer",
    "CacheStrategy",
    "create_memory_optimizer",
    "memory_efficient",
    
    # Load testing
    "LoadTestExecutor",
    "LoadTestConfig", 
    "LoadTestResults",
    "LoadTestType",
    "test_1000_questions_processing",
    "test_api_scalability", 
    "run_comprehensive_performance_test",
    "create_load_tester",
    
    # Main initialization
    "initialize_performance_optimization"
]