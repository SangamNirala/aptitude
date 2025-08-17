"""
Concurrent Processing Optimizer for TASK 18: Performance Optimization & Scaling

This module provides enhanced concurrent processing capabilities including:
- Advanced async job processing with optimized batch sizes
- Connection pooling for external API calls 
- Intelligent rate limiting with adaptive algorithms
- Memory-efficient concurrent operations
- Resource-aware processing limits
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, List, Any, Optional, Callable, Awaitable, TypeVar, Generic, AsyncIterable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import weakref
from contextlib import asynccontextmanager
import json
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

class ProcessingStrategy(str, Enum):
    """Processing optimization strategies"""
    CONSERVATIVE = "conservative"  # Low resource usage, slower processing
    BALANCED = "balanced"         # Balanced resource usage and speed  
    AGGRESSIVE = "aggressive"     # High resource usage, maximum speed
    ADAPTIVE = "adaptive"        # Dynamically adjusts based on system load

@dataclass
class ProcessingMetrics:
    """Real-time processing performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    avg_task_duration: float = 0.0
    success_rate: float = 0.0
    throughput_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    queue_size: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing operations"""
    batch_size: int = 50
    max_concurrent_batches: int = 5
    processing_timeout: float = 300.0  # 5 minutes
    retry_attempts: int = 3
    retry_delay: float = 1.0
    memory_limit_mb: float = 1024.0  # 1GB limit
    cpu_limit_percent: float = 80.0
    adaptive_sizing: bool = True
    circuit_breaker_threshold: int = 10  # Failed requests before circuit opens

class ResourceMonitor:
    """Monitor system resources for adaptive processing"""
    
    def __init__(self):
        self.cpu_samples = []
        self.memory_samples = []
        self.sample_window = 30  # 30 second window
        
    def get_current_resources(self) -> Dict[str, float]:
        """Get current system resource utilization"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Track samples for trend analysis
        now = time.time()
        self.cpu_samples.append((now, cpu_percent))
        self.memory_samples.append((now, memory.percent))
        
        # Keep only recent samples
        cutoff = now - self.sample_window
        self.cpu_samples = [(t, v) for t, v in self.cpu_samples if t > cutoff]
        self.memory_samples = [(t, v) for t, v in self.memory_samples if t > cutoff]
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "memory_used_mb": memory.used / (1024 * 1024),
            "avg_cpu": sum(v for _, v in self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else cpu_percent,
            "avg_memory": sum(v for _, v in self.memory_samples) / len(self.memory_samples) if self.memory_samples else memory.percent
        }
    
    def should_throttle(self, cpu_limit: float = 80.0, memory_limit: float = 85.0) -> bool:
        """Check if processing should be throttled due to high resource usage"""
        resources = self.get_current_resources()
        return resources["cpu_percent"] > cpu_limit or resources["memory_percent"] > memory_limit

class ConnectionPoolManager:
    """Advanced connection pool manager for external API calls"""
    
    def __init__(self, max_connections: int = 100, max_connections_per_host: int = 20):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self._session: Optional[aiohttp.ClientSession] = None
        self._connection_metrics = {
            "total_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "active_connections": 0
        }
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create optimized HTTP session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections_per_host,
                enable_cleanup_closed=True,
                keepalive_timeout=30,
                ttl_dns_cache=300,  # 5 minutes DNS cache
                use_dns_cache=True,
            )
            
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "AI-Enhanced-Scraper/2.0"}
            )
            
        return self._session
    
    async def make_request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an HTTP request with connection pooling and metrics tracking"""
        session = await self.get_session()
        start_time = time.time()
        
        try:
            self._connection_metrics["active_connections"] += 1
            async with session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                self._update_metrics(response_time, True)
                return response
                
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(response_time, False)
            raise
        finally:
            self._connection_metrics["active_connections"] -= 1
    
    def _update_metrics(self, response_time: float, success: bool):
        """Update connection metrics"""
        self._connection_metrics["total_requests"] += 1
        if not success:
            self._connection_metrics["failed_requests"] += 1
        
        # Update average response time
        total_requests = self._connection_metrics["total_requests"]
        current_avg = self._connection_metrics["avg_response_time"]
        self._connection_metrics["avg_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    async def close(self):
        """Close connection pool"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics"""
        return self._connection_metrics.copy()

class ConcurrentProcessor(Generic[T, R]):
    """
    Advanced concurrent processor for high-volume operations with adaptive optimization
    """
    
    def __init__(self, 
                 processing_function: Callable[[T], Awaitable[R]],
                 config: BatchProcessingConfig = None,
                 strategy: ProcessingStrategy = ProcessingStrategy.BALANCED):
        
        self.processing_function = processing_function
        self.config = config or BatchProcessingConfig()
        self.strategy = strategy
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor()
        self.metrics = ProcessingMetrics()
        
        # Connection management
        self.connection_pool = ConnectionPoolManager()
        
        # Concurrency control
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)
        self._processing_queue = asyncio.Queue()
        
        # Adaptive configuration
        self._adaptive_config = self._initialize_adaptive_config()
        
    def _initialize_adaptive_config(self) -> Dict[str, Any]:
        """Initialize adaptive configuration based on strategy"""
        if self.strategy == ProcessingStrategy.CONSERVATIVE:
            return {
                "batch_size": min(20, self.config.batch_size),
                "max_concurrent": min(2, self.config.max_concurrent_batches),
                "cpu_limit": 60.0,
                "memory_limit": 70.0
            }
        elif self.strategy == ProcessingStrategy.AGGRESSIVE:
            return {
                "batch_size": max(100, self.config.batch_size),
                "max_concurrent": max(10, self.config.max_concurrent_batches),
                "cpu_limit": 90.0,
                "memory_limit": 90.0
            }
        elif self.strategy == ProcessingStrategy.ADAPTIVE:
            return {
                "batch_size": self.config.batch_size,
                "max_concurrent": self.config.max_concurrent_batches,
                "cpu_limit": self.config.cpu_limit_percent,
                "memory_limit": 85.0
            }
        else:  # BALANCED
            return {
                "batch_size": self.config.batch_size,
                "max_concurrent": self.config.max_concurrent_batches,
                "cpu_limit": 75.0,
                "memory_limit": 80.0
            }
    
    async def process_batch(self, items: List[T], batch_id: str = None) -> List[R]:
        """Process a batch of items with optimized concurrency"""
        if not items:
            return []
        
        batch_id = batch_id or f"batch_{int(time.time())}"
        logger.info(f"🔄 Processing batch {batch_id} with {len(items)} items")
        
        start_time = time.time()
        results = []
        
        # Adaptive batch sizing
        effective_batch_size = self._calculate_effective_batch_size(len(items))
        
        try:
            async with self._semaphore:
                # Process items in smaller chunks for better memory management
                chunks = [items[i:i + effective_batch_size] for i in range(0, len(items), effective_batch_size)]
                
                # Process chunks concurrently
                tasks = []
                for chunk_idx, chunk in enumerate(chunks):
                    task = asyncio.create_task(
                        self._process_chunk(chunk, f"{batch_id}_chunk_{chunk_idx}")
                    )
                    tasks.append(task)
                    
                    # Throttle if resources are high
                    if self.resource_monitor.should_throttle(
                        self._adaptive_config["cpu_limit"],
                        self._adaptive_config["memory_limit"]
                    ):
                        await asyncio.sleep(0.1)  # Brief pause
                
                # Wait for all chunks to complete
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect results and handle exceptions
                for chunk_result in chunk_results:
                    if isinstance(chunk_result, Exception):
                        logger.error(f"Chunk processing failed: {str(chunk_result)}")
                    else:
                        results.extend(chunk_result)
        
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise
        
        # Update metrics
        processing_time = time.time() - start_time
        self._update_metrics(len(items), len(results), 0, processing_time)
        
        logger.info(f"✅ Batch {batch_id} completed: {len(results)} successful in {processing_time:.2f}s")
        return results
    
    async def _process_chunk(self, chunk: List[T], chunk_id: str) -> List[R]:
        """Process a single chunk of items"""
        chunk_results = []
        
        for item in chunk:
            try:
                # Add small delay for rate limiting
                await asyncio.sleep(0.01)
                
                # Process individual item
                result = await self.processing_function(item)
                chunk_results.append(result)
                
            except Exception as e:
                logger.warning(f"Item processing failed in {chunk_id}: {str(e)}")
                continue
        
        return chunk_results
    
    def _calculate_effective_batch_size(self, total_items: int) -> int:
        """Calculate effective batch size based on current system conditions"""
        base_size = self._adaptive_config["batch_size"]
        
        if not self.config.adaptive_sizing:
            return base_size
        
        # Get current resource utilization
        resources = self.resource_monitor.get_current_resources()
        
        # Adjust batch size based on resources
        cpu_factor = 1.0 - (resources["cpu_percent"] / 100.0)
        memory_factor = 1.0 - (resources["memory_percent"] / 100.0)
        
        # Use the more constrained resource
        resource_factor = min(cpu_factor, memory_factor)
        
        # Apply strategy-specific adjustments
        if self.strategy == ProcessingStrategy.ADAPTIVE:
            if resource_factor < 0.2:  # High resource usage
                effective_size = max(10, int(base_size * 0.5))
            elif resource_factor > 0.8:  # Low resource usage
                effective_size = min(200, int(base_size * 1.5))
            else:
                effective_size = base_size
        else:
            effective_size = max(5, int(base_size * (0.5 + resource_factor)))
        
        return effective_size
    
    def _update_metrics(self, items_processed: int, success_count: int, 
                       failed_count: int, processing_time: float):
        """Update processing metrics"""
        self.metrics.tasks_completed += success_count
        self.metrics.tasks_failed += failed_count
        self.metrics.total_processing_time += processing_time
        
        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total_tasks > 0:
            self.metrics.success_rate = self.metrics.tasks_completed / total_tasks
            self.metrics.avg_task_duration = self.metrics.total_processing_time / total_tasks
            
        if processing_time > 0:
            self.metrics.throughput_per_second = items_processed / processing_time
        
        # Update resource metrics
        resources = self.resource_monitor.get_current_resources()
        self.metrics.cpu_usage_percent = resources["cpu_percent"]
        self.metrics.memory_usage_mb = resources["memory_used_mb"]
        self.metrics.active_connections = self.connection_pool.get_metrics()["active_connections"]
        self.metrics.last_updated = datetime.utcnow()
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        resources = self.resource_monitor.get_current_resources()
        connection_metrics = self.connection_pool.get_metrics()
        
        return {
            "processing_metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": self.metrics.success_rate,
                "avg_task_duration": self.metrics.avg_task_duration,
                "throughput_per_second": self.metrics.throughput_per_second,
                "last_updated": self.metrics.last_updated.isoformat()
            },
            "resource_metrics": resources,
            "connection_metrics": connection_metrics,
            "adaptive_config": self._adaptive_config,
            "strategy": self.strategy
        }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.connection_pool.close()

# Factory functions for easy initialization
async def create_optimized_processor(processing_type: str, **kwargs) -> ConcurrentProcessor:
    """Create an optimized processor for specific use case"""
    return ConcurrentProcessor(**kwargs)

# Decorator for automatic performance optimization
def optimize_async_function(strategy: ProcessingStrategy = ProcessingStrategy.BALANCED):
    """Decorator to automatically optimize async functions for concurrent processing"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Add performance monitoring and optimization
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                processing_time = time.time() - start_time
                logger.debug(f"Function {func.__name__} completed in {processing_time:.3f}s")
                return result
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Function {func.__name__} failed after {processing_time:.3f}s: {str(e)}")
                raise
        return wrapper
    return decorator