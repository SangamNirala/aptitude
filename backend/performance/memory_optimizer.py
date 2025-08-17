"""
Memory Optimization System for TASK 18: Performance Optimization & Scaling

This module provides comprehensive memory optimization features including:
- Intelligent caching strategies with LRU and TTL mechanisms
- Memory-efficient data structures for large datasets
- Garbage collection optimization and monitoring
- Memory pool management for object reuse
- Streaming data processing to minimize memory footprint
"""

import gc
import sys
import time
import weakref
import psutil
import logging
import asyncio
from typing import Dict, List, Any, Optional, TypeVar, Generic, Iterator, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict, deque
from functools import wraps, lru_cache
from contextlib import contextmanager, asynccontextmanager
import json
import pickle
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percent: float
    cache_size_mb: float
    gc_collections: int
    objects_tracked: int
    last_gc_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

class CacheStrategy:
    """Cache eviction strategies"""
    LRU = "lru"          # Least Recently Used
    LFU = "lfu"          # Least Frequently Used
    TTL = "ttl"          # Time To Live
    FIFO = "fifo"        # First In First Out
    ADAPTIVE = "adaptive" # Adaptive based on usage patterns

class MemoryEfficientCache(Generic[K, V]):
    """
    Memory-efficient cache with multiple eviction strategies and size limits
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 max_memory_mb: float = 100.0,
                 strategy: str = CacheStrategy.LRU,
                 ttl_seconds: Optional[float] = None):
        
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.strategy = strategy
        self.ttl_seconds = ttl_seconds
        
        # Storage structures
        self._data: OrderedDict[K, V] = OrderedDict()
        self._access_times: Dict[K, float] = {}
        self._access_counts: Dict[K, int] = defaultdict(int)
        self._expiry_times: Dict[K, float] = {}
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._current_memory_mb = 0.0
        
        # Thread safety
        self._lock = threading.RLock()
    
    def get(self, key: K) -> Optional[V]:
        """Get value from cache with strategy-aware access tracking"""
        with self._lock:
            # Check if key exists and not expired
            if key not in self._data:
                self._misses += 1
                return None
            
            # Check TTL expiration
            if self.ttl_seconds and key in self._expiry_times:
                if time.time() > self._expiry_times[key]:
                    self._remove_key(key)
                    self._misses += 1
                    return None
            
            # Update access tracking
            self._access_times[key] = time.time()
            self._access_counts[key] += 1
            
            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self._data.move_to_end(key)
            
            self._hits += 1
            return self._data[key]
    
    def put(self, key: K, value: V) -> bool:
        """Put value in cache with automatic eviction"""
        with self._lock:
            # Calculate estimated memory usage
            value_size = self._estimate_size(value)
            
            # Check if single item exceeds memory limit
            if value_size > self.max_memory_mb:
                logger.warning(f"Item size {value_size:.2f}MB exceeds cache limit {self.max_memory_mb}MB")
                return False
            
            # Remove existing key if updating
            if key in self._data:
                self._remove_key(key)
            
            # Ensure space available
            while (len(self._data) >= self.max_size or 
                   self._current_memory_mb + value_size > self.max_memory_mb):
                if not self._evict_one():
                    break  # No more items to evict
            
            # Add new item
            self._data[key] = value
            self._access_times[key] = time.time()
            self._access_counts[key] = 1
            
            if self.ttl_seconds:
                self._expiry_times[key] = time.time() + self.ttl_seconds
            
            self._current_memory_mb += value_size
            return True
    
    def _evict_one(self) -> bool:
        """Evict one item based on strategy"""
        if not self._data:
            return False
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first item in OrderedDict)
            key = next(iter(self._data))
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            key = min(self._access_counts.keys(), key=lambda k: self._access_counts[k])
        elif self.strategy == CacheStrategy.FIFO:
            # Remove first inserted (first in OrderedDict)
            key = next(iter(self._data))
        elif self.strategy == CacheStrategy.TTL:
            # Remove expired items first, then oldest
            current_time = time.time()
            expired_keys = [k for k, exp_time in self._expiry_times.items() 
                          if current_time > exp_time]
            if expired_keys:
                key = expired_keys[0]
            else:
                key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        else:  # ADAPTIVE
            # Combine recency and frequency
            current_time = time.time()
            scores = {}
            for k in self._data.keys():
                recency_score = current_time - self._access_times.get(k, 0)
                frequency_score = 1.0 / max(1, self._access_counts[k])
                scores[k] = recency_score + frequency_score
            key = max(scores.keys(), key=lambda k: scores[k])
        
        self._remove_key(key)
        self._evictions += 1
        return True
    
    def _remove_key(self, key: K):
        """Remove key and all associated metadata"""
        if key in self._data:
            value_size = self._estimate_size(self._data[key])
            del self._data[key]
            self._current_memory_mb -= value_size
        
        self._access_times.pop(key, None)
        self._access_counts.pop(key, None)
        self._expiry_times.pop(key, None)
    
    def _estimate_size(self, obj: Any) -> float:
        """Estimate memory size of object in MB"""
        try:
            if isinstance(obj, (str, int, float, bool)):
                return sys.getsizeof(obj) / (1024 * 1024)
            elif isinstance(obj, (list, tuple, dict, set)):
                size = sys.getsizeof(obj)
                if hasattr(obj, '__iter__'):
                    for item in obj:
                        size += sys.getsizeof(item)
                return size / (1024 * 1024)
            else:
                return sys.getsizeof(obj) / (1024 * 1024)
        except Exception:
            return 0.1  # Default estimate
    
    def clear(self):
        """Clear all cached data"""
        with self._lock:
            self._data.clear()
            self._access_times.clear()
            self._access_counts.clear()
            self._expiry_times.clear()
            self._current_memory_mb = 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "current_size": len(self._data),
                "max_size": self.max_size,
                "memory_usage_mb": self._current_memory_mb,
                "max_memory_mb": self.max_memory_mb,
                "memory_utilization": self._current_memory_mb / self.max_memory_mb,
                "strategy": self.strategy
            }

class MemoryPool(Generic[T]):
    """
    Memory pool for object reuse to reduce allocation overhead
    """
    
    def __init__(self, 
                 factory_func: callable,
                 max_size: int = 100,
                 reset_func: Optional[callable] = None):
        
        self.factory_func = factory_func
        self.max_size = max_size
        self.reset_func = reset_func
        
        self._pool: deque = deque()
        self._created_count = 0
        self._reused_count = 0
        
        self._lock = threading.Lock()
    
    def acquire(self) -> T:
        """Acquire object from pool or create new one"""
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self._reused_count += 1
                
                # Reset object if reset function provided
                if self.reset_func:
                    self.reset_func(obj)
                
                return obj
            else:
                obj = self.factory_func()
                self._created_count += 1
                return obj
    
    def release(self, obj: T):
        """Return object to pool for reuse"""
        with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            total_acquisitions = self._created_count + self._reused_count
            reuse_rate = self._reused_count / total_acquisitions if total_acquisitions > 0 else 0.0
            
            return {
                "pool_size": len(self._pool),
                "max_size": self.max_size,
                "created_count": self._created_count,
                "reused_count": self._reused_count,
                "reuse_rate": reuse_rate,
                "pool_utilization": len(self._pool) / self.max_size
            }

class StreamingProcessor:
    """
    Memory-efficient streaming data processor for large datasets
    """
    
    def __init__(self, chunk_size: int = 1000, max_memory_mb: float = 500.0):
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self._processed_items = 0
        self._memory_peaks = []
    
    async def process_stream(self, 
                           data_iterator: AsyncIterator[T], 
                           processor_func: callable,
                           output_handler: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process data stream in memory-efficient chunks
        """
        logger.info(f"🌊 Starting streaming processing with chunk size {self.chunk_size}")
        
        start_time = time.time()
        chunk_buffer = []
        total_processed = 0
        
        try:
            async for item in data_iterator:
                chunk_buffer.append(item)
                
                # Process chunk when buffer is full or memory pressure
                if (len(chunk_buffer) >= self.chunk_size or 
                    self._check_memory_pressure()):
                    
                    # Process current chunk
                    results = await self._process_chunk(chunk_buffer, processor_func)
                    
                    # Handle results
                    if output_handler:
                        await output_handler(results)
                    
                    total_processed += len(chunk_buffer)
                    chunk_buffer.clear()
                    
                    # Force garbage collection if memory usage is high
                    if self._check_memory_pressure():
                        gc.collect()
                    
                    # Brief pause for system breathing room
                    await asyncio.sleep(0.01)
            
            # Process remaining items in buffer
            if chunk_buffer:
                results = await self._process_chunk(chunk_buffer, processor_func)
                if output_handler:
                    await output_handler(results)
                total_processed += len(chunk_buffer)
        
        except Exception as e:
            logger.error(f"Streaming processing failed: {str(e)}")
            raise
        
        processing_time = time.time() - start_time
        self._processed_items += total_processed
        
        return {
            "total_processed": total_processed,
            "processing_time": processing_time,
            "throughput_per_second": total_processed / processing_time if processing_time > 0 else 0,
            "peak_memory_mb": max(self._memory_peaks) if self._memory_peaks else 0,
            "avg_memory_mb": sum(self._memory_peaks) / len(self._memory_peaks) if self._memory_peaks else 0
        }
    
    async def _process_chunk(self, chunk: List[T], processor_func: callable) -> List[Any]:
        """Process a single chunk of data"""
        # Monitor memory before processing
        memory_before = self._get_memory_usage()
        
        results = []
        for item in chunk:
            try:
                result = await processor_func(item) if asyncio.iscoroutinefunction(processor_func) else processor_func(item)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to process item: {str(e)}")
                continue
        
        # Monitor memory after processing
        memory_after = self._get_memory_usage()
        self._memory_peaks.append(memory_after)
        
        return results
    
    def _check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure"""
        memory_usage = self._get_memory_usage()
        return memory_usage > self.max_memory_mb
    
    def _get_memory_usage(self) -> float:
        """Get current process memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

class GarbageCollectionOptimizer:
    """
    Garbage collection optimization and monitoring system
    """
    
    def __init__(self):
        self.gc_stats = {
            "collections_count": [0, 0, 0],  # For each generation
            "collected_objects": [0, 0, 0],
            "uncollectable": [0, 0, 0],
            "last_collection_time": 0.0,
            "total_gc_time": 0.0
        }
        
        # Enable garbage collection debugging
        gc.set_debug(gc.DEBUG_STATS)
    
    def optimize_gc_settings(self):
        """Optimize garbage collection settings for performance"""
        # Get current thresholds
        current_thresholds = gc.get_threshold()
        logger.info(f"Current GC thresholds: {current_thresholds}")
        
        # Optimize thresholds for high-volume processing
        # Increase gen0 threshold to reduce frequent collections
        # Adjust gen1 and gen2 based on memory patterns
        optimized_thresholds = (
            current_thresholds[0] * 2,  # Double gen0 threshold
            current_thresholds[1] * 1.5,  # Increase gen1 threshold
            current_thresholds[2] * 1.2   # Slightly increase gen2 threshold
        )
        
        gc.set_threshold(*[int(t) for t in optimized_thresholds])
        logger.info(f"Optimized GC thresholds: {optimized_thresholds}")
    
    def force_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return statistics"""
        start_time = time.time()
        
        # Collect statistics before
        stats_before = gc.get_stats()
        
        # Force collection for all generations
        collected = []
        for generation in range(3):
            collected.append(gc.collect(generation))
        
        collection_time = time.time() - start_time
        
        # Update statistics
        self.gc_stats["last_collection_time"] = collection_time
        self.gc_stats["total_gc_time"] += collection_time
        
        stats_after = gc.get_stats()
        
        return {
            "collection_time": collection_time,
            "objects_collected": collected,
            "stats_before": stats_before,
            "stats_after": stats_after,
            "memory_freed_mb": self._calculate_memory_freed()
        }
    
    def _calculate_memory_freed(self) -> float:
        """Estimate memory freed by garbage collection"""
        # This is a rough estimate - in practice, you'd need more sophisticated tracking
        return 0.0  # Placeholder
    
    def get_gc_stats(self) -> Dict[str, Any]:
        """Get comprehensive garbage collection statistics"""
        current_stats = gc.get_stats()
        
        return {
            "gc_enabled": gc.isenabled(),
            "gc_thresholds": gc.get_threshold(),
            "gc_counts": gc.get_count(),
            "gc_stats": current_stats,
            "total_gc_time": self.gc_stats["total_gc_time"],
            "last_collection_time": self.gc_stats["last_collection_time"],
            "tracked_objects": len(gc.get_objects())
        }

class MemoryOptimizer:
    """
    Comprehensive memory optimization system
    """
    
    def __init__(self):
        self.caches: Dict[str, MemoryEfficientCache] = {}
        self.pools: Dict[str, MemoryPool] = {}
        self.gc_optimizer = GarbageCollectionOptimizer()
        self.streaming_processor = StreamingProcessor()
        
        # Memory monitoring
        self._memory_history = deque(maxlen=100)  # Keep last 100 readings
        self._monitoring_enabled = False
        self._monitoring_task = None
    
    def create_cache(self, 
                    name: str,
                    max_size: int = 1000,
                    max_memory_mb: float = 100.0,
                    strategy: str = CacheStrategy.LRU,
                    ttl_seconds: Optional[float] = None) -> MemoryEfficientCache:
        """Create a named cache with specified parameters"""
        cache = MemoryEfficientCache(
            max_size=max_size,
            max_memory_mb=max_memory_mb,
            strategy=strategy,
            ttl_seconds=ttl_seconds
        )
        self.caches[name] = cache
        return cache
    
    def create_pool(self, 
                   name: str,
                   factory_func: callable,
                   max_size: int = 100,
                   reset_func: Optional[callable] = None) -> MemoryPool:
        """Create a named object pool"""
        pool = MemoryPool(
            factory_func=factory_func,
            max_size=max_size,
            reset_func=reset_func
        )
        self.pools[name] = pool
        return pool
    
    def start_monitoring(self, interval_seconds: float = 10.0):
        """Start continuous memory monitoring"""
        if not self._monitoring_enabled:
            self._monitoring_enabled = True
            self._monitoring_task = asyncio.create_task(
                self._memory_monitoring_loop(interval_seconds)
            )
            logger.info(f"Memory monitoring started with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self._monitoring_enabled = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            logger.info("Memory monitoring stopped")
    
    async def _memory_monitoring_loop(self, interval: float):
        """Memory monitoring background task"""
        while self._monitoring_enabled:
            try:
                stats = self.get_memory_stats()
                self._memory_history.append(stats)
                
                # Check for memory pressure
                if stats.memory_percent > 90.0:
                    logger.warning(f"High memory usage detected: {stats.memory_percent:.1f}%")
                    await self._handle_memory_pressure()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {str(e)}")
                await asyncio.sleep(interval)
    
    async def _handle_memory_pressure(self):
        """Handle high memory usage situations"""
        logger.info("🧹 Handling memory pressure - triggering cleanup")
        
        # Clear least used caches
        for name, cache in self.caches.items():
            if cache.get_stats()["hit_rate"] < 0.1:  # Low hit rate
                cache.clear()
                logger.info(f"Cleared low-performing cache: {name}")
        
        # Force garbage collection
        gc_result = self.gc_optimizer.force_collection()
        logger.info(f"Forced GC completed in {gc_result['collection_time']:.3f}s")
    
    def get_memory_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics"""
        # System memory
        memory = psutil.virtual_memory()
        
        # Process memory
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Cache memory
        total_cache_size = sum(
            cache.get_stats()["memory_usage_mb"] 
            for cache in self.caches.values()
        )
        
        # GC statistics
        gc_stats = self.gc_optimizer.get_gc_stats()
        
        return MemoryStats(
            total_memory_mb=memory.total / (1024 * 1024),
            available_memory_mb=memory.available / (1024 * 1024),
            used_memory_mb=process_memory.rss / (1024 * 1024),
            memory_percent=memory.percent,
            cache_size_mb=total_cache_size,
            gc_collections=sum(gc_stats["gc_counts"]),
            objects_tracked=gc_stats["tracked_objects"],
            last_gc_time=gc_stats["last_collection_time"]
        )
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory optimization report"""
        memory_stats = self.get_memory_stats()
        gc_stats = self.gc_optimizer.get_gc_stats()
        
        # Cache statistics
        cache_stats = {
            name: cache.get_stats() 
            for name, cache in self.caches.items()
        }
        
        # Pool statistics
        pool_stats = {
            name: pool.get_stats() 
            for name, pool in self.pools.items()
        }
        
        # Memory trend analysis
        if len(self._memory_history) > 1:
            recent_usage = [stat.memory_percent for stat in list(self._memory_history)[-10:]]
            memory_trend = "increasing" if recent_usage[-1] > recent_usage[0] else "decreasing"
        else:
            memory_trend = "stable"
        
        return {
            "timestamp": datetime.utcnow(),
            "memory_statistics": {
                "total_memory_mb": memory_stats.total_memory_mb,
                "used_memory_mb": memory_stats.used_memory_mb,
                "memory_percent": memory_stats.memory_percent,
                "cache_size_mb": memory_stats.cache_size_mb
            },
            "cache_performance": cache_stats,
            "pool_performance": pool_stats,
            "garbage_collection": gc_stats,
            "memory_trend": memory_trend,
            "optimization_recommendations": self._generate_optimization_recommendations(memory_stats, cache_stats),
            "performance_score": self._calculate_memory_performance_score(memory_stats, cache_stats)
        }
    
    def _generate_optimization_recommendations(self, 
                                            memory_stats: MemoryStats, 
                                            cache_stats: Dict[str, Any]) -> List[str]:
        """Generate memory optimization recommendations"""
        recommendations = []
        
        # Memory usage recommendations
        if memory_stats.memory_percent > 80:
            recommendations.append("High memory usage detected - consider increasing cache eviction frequency")
        
        if memory_stats.cache_size_mb > 200:
            recommendations.append("Large cache footprint - review cache size limits")
        
        # Cache performance recommendations
        for name, stats in cache_stats.items():
            if stats["hit_rate"] < 0.3:
                recommendations.append(f"Cache '{name}' has low hit rate ({stats['hit_rate']:.2f}) - review caching strategy")
            
            if stats["memory_utilization"] > 0.9:
                recommendations.append(f"Cache '{name}' is near memory limit - consider increasing capacity")
        
        # GC recommendations
        if memory_stats.gc_collections > 1000:
            recommendations.append("High GC activity - optimize object allocation patterns")
        
        # General recommendations
        recommendations.extend([
            "Enable streaming processing for large datasets",
            "Use object pools for frequently created objects",
            "Monitor memory trends for proactive optimization"
        ])
        
        return recommendations
    
    def _calculate_memory_performance_score(self, 
                                          memory_stats: MemoryStats, 
                                          cache_stats: Dict[str, Any]) -> float:
        """Calculate overall memory performance score (0-100)"""
        score = 100.0
        
        # Deduct points for high memory usage
        if memory_stats.memory_percent > 90:
            score -= 30
        elif memory_stats.memory_percent > 80:
            score -= 15
        elif memory_stats.memory_percent > 70:
            score -= 5
        
        # Deduct points for poor cache performance
        if cache_stats:
            avg_hit_rate = sum(stats["hit_rate"] for stats in cache_stats.values()) / len(cache_stats)
            if avg_hit_rate < 0.3:
                score -= 20
            elif avg_hit_rate < 0.5:
                score -= 10
        
        # Deduct points for excessive GC activity
        if memory_stats.gc_collections > 1000:
            score -= 10
        
        return max(0.0, score)

# Factory function for easy initialization
def create_memory_optimizer() -> MemoryOptimizer:
    """Create and initialize memory optimizer"""
    optimizer = MemoryOptimizer()
    
    # Optimize GC settings
    optimizer.gc_optimizer.optimize_gc_settings()
    
    return optimizer

# Decorators for automatic memory optimization
def memory_efficient(cache_name: str = None, pool_name: str = None):
    """Decorator to add automatic memory optimization to functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Add memory monitoring around function execution
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                memory_delta = end_memory - start_memory
                
                if memory_delta > 10:  # More than 10MB increase
                    logger.debug(f"Function {func.__name__} used {memory_delta:.2f}MB memory")
                
                return result
                
            except Exception as e:
                logger.error(f"Memory-optimized function {func.__name__} failed: {str(e)}")
                raise
        
        return wrapper
    return decorator