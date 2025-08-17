"""
Comprehensive Load Testing Framework for TASK 18: Performance Optimization & Scaling

This module provides advanced load testing capabilities including:
- Scalability testing for 1000+ questions processing
- Performance benchmarking with detailed metrics
- Resource utilization monitoring during load tests
- Bottleneck identification and analysis
- Stress testing with gradual load increase
"""

import asyncio
import logging
import time
import psutil
import aiohttp
import json
from typing import Dict, List, Any, Optional, Callable, Awaitable, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import statistics
import numpy as np
from enum import Enum
import matplotlib.pyplot as plt
import io
import base64

logger = logging.getLogger(__name__)

class LoadTestType(str, Enum):
    """Types of load tests"""
    BASELINE = "baseline"           # Single user baseline performance
    LOAD = "load"                  # Normal expected load
    STRESS = "stress"              # Beyond normal capacity
    SPIKE = "spike"                # Sudden traffic spikes
    VOLUME = "volume"              # Large data volume processing
    ENDURANCE = "endurance"        # Long-duration testing
    SCALABILITY = "scalability"    # Scaling to target capacity

class TestMetric(NamedTuple):
    """Individual test metric data point"""
    timestamp: float
    response_time: float
    success: bool
    status_code: Optional[int]
    error_message: Optional[str]
    memory_usage_mb: float
    cpu_usage_percent: float

@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios"""
    test_name: str
    test_type: LoadTestType
    target_url: str
    
    # Load characteristics
    concurrent_users: int = 10
    total_requests: int = 100
    duration_seconds: Optional[int] = None
    ramp_up_seconds: int = 0
    ramp_down_seconds: int = 0
    
    # Request configuration
    request_method: str = "POST"
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_payload: Optional[Dict[str, Any]] = None
    
    # Performance thresholds
    max_response_time_ms: float = 5000.0
    min_success_rate: float = 0.95
    max_error_rate: float = 0.05
    
    # Resource limits
    max_memory_mb: float = 2048.0
    max_cpu_percent: float = 80.0
    
    # Advanced options
    think_time_ms: int = 0
    data_variation: bool = False  # Vary request data
    connection_pooling: bool = True

@dataclass
class LoadTestResults:
    """Comprehensive load test results"""
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Performance metrics
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    
    # Response time statistics
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Throughput metrics
    requests_per_second: float
    peak_rps: float
    
    # Resource utilization
    avg_memory_mb: float
    peak_memory_mb: float
    avg_cpu_percent: float
    peak_cpu_percent: float
    
    # Error analysis
    error_distribution: Dict[str, int]
    bottlenecks_identified: List[str]
    
    # Performance score
    performance_score: float
    meets_sla: bool
    
    # Raw data for detailed analysis
    metrics: List[TestMetric]

class LoadTestExecutor:
    """
    Advanced load testing executor with comprehensive metrics collection
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self._resource_monitor_task: Optional[asyncio.Task] = None
        self._resource_samples: List[Dict[str, float]] = []
        
    async def execute_load_test(self, config: LoadTestConfig) -> LoadTestResults:
        """Execute a comprehensive load test"""
        logger.info(f"🚀 Starting load test: {config.test_name}")
        logger.info(f"   Type: {config.test_type}")
        logger.info(f"   Users: {config.concurrent_users}")
        logger.info(f"   Requests: {config.total_requests}")
        
        start_time = datetime.utcnow()
        
        # Initialize session with connection pooling
        await self._initialize_session(config)
        
        # Start resource monitoring
        self._start_resource_monitoring()
        
        try:
            # Execute the test based on type
            if config.test_type == LoadTestType.SCALABILITY:
                metrics = await self._execute_scalability_test(config)
            elif config.test_type == LoadTestType.STRESS:
                metrics = await self._execute_stress_test(config)
            elif config.test_type == LoadTestType.SPIKE:
                metrics = await self._execute_spike_test(config)
            elif config.test_type == LoadTestType.ENDURANCE:
                metrics = await self._execute_endurance_test(config)
            else:
                metrics = await self._execute_standard_load_test(config)
            
            end_time = datetime.utcnow()
            
            # Stop resource monitoring
            self._stop_resource_monitoring()
            
            # Analyze results
            results = self._analyze_results(config, metrics, start_time, end_time)
            
            logger.info(f"✅ Load test completed: {results.success_rate:.2%} success rate")
            logger.info(f"   Avg Response Time: {results.avg_response_time:.0f}ms")
            logger.info(f"   Throughput: {results.requests_per_second:.1f} RPS")
            logger.info(f"   Performance Score: {results.performance_score:.1f}/100")
            
            return results
            
        finally:
            await self._cleanup_session()
    
    async def _initialize_session(self, config: LoadTestConfig):
        """Initialize HTTP session with optimized settings"""
        connector = aiohttp.TCPConnector(
            limit=config.concurrent_users * 2,  # Allow extra connections
            limit_per_host=config.concurrent_users * 2,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        ) if config.connection_pooling else None
        
        timeout = aiohttp.ClientTimeout(total=config.max_response_time_ms / 1000)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=config.request_headers
        )
    
    async def _execute_standard_load_test(self, config: LoadTestConfig) -> List[TestMetric]:
        """Execute standard load test with concurrent users"""
        metrics = []
        
        # Calculate requests per user
        requests_per_user = config.total_requests // config.concurrent_users
        remaining_requests = config.total_requests % config.concurrent_users
        
        # Create tasks for concurrent users
        tasks = []
        for user_id in range(config.concurrent_users):
            user_requests = requests_per_user + (1 if user_id < remaining_requests else 0)
            task = asyncio.create_task(
                self._simulate_user(user_id, user_requests, config, metrics)
            )
            tasks.append(task)
            
            # Ramp up delay
            if config.ramp_up_seconds > 0:
                ramp_delay = config.ramp_up_seconds / config.concurrent_users
                await asyncio.sleep(ramp_delay)
        
        # Wait for all users to complete
        await asyncio.gather(*tasks)
        
        return metrics
    
    async def _execute_scalability_test(self, config: LoadTestConfig) -> List[TestMetric]:
        """Execute scalability test with gradual user increase"""
        metrics = []
        max_users = config.concurrent_users
        
        # Test with increasing user load: 1, 5, 10, 20, 50, etc.
        user_levels = [1, 5, 10, 20, 50, 100, 200, 500, 1000]
        user_levels = [level for level in user_levels if level <= max_users]
        user_levels.append(max_users)  # Ensure we test the target level
        
        for user_count in user_levels:
            logger.info(f"📈 Scaling test: {user_count} concurrent users")
            
            # Configure for this user level
            level_config = LoadTestConfig(
                test_name=f"{config.test_name}_scale_{user_count}",
                test_type=LoadTestType.LOAD,
                target_url=config.target_url,
                concurrent_users=user_count,
                total_requests=user_count * 10,  # 10 requests per user
                request_method=config.request_method,
                request_headers=config.request_headers,
                request_payload=config.request_payload,
                max_response_time_ms=config.max_response_time_ms
            )
            
            # Execute this level
            level_metrics = await self._execute_standard_load_test(level_config)
            metrics.extend(level_metrics)
            
            # Brief pause between levels
            await asyncio.sleep(2)
        
        return metrics
    
    async def _execute_stress_test(self, config: LoadTestConfig) -> List[TestMetric]:
        """Execute stress test pushing beyond normal limits"""
        metrics = []
        
        # Stress test phases: normal -> 2x -> 3x -> 5x load
        stress_multipliers = [1, 2, 3, 5]
        
        for multiplier in stress_multipliers:
            stressed_users = config.concurrent_users * multiplier
            logger.info(f"💪 Stress test phase: {multiplier}x load ({stressed_users} users)")
            
            phase_config = LoadTestConfig(
                test_name=f"{config.test_name}_stress_{multiplier}x",
                test_type=LoadTestType.LOAD,
                target_url=config.target_url,
                concurrent_users=stressed_users,
                total_requests=stressed_users * 5,
                request_method=config.request_method,
                request_headers=config.request_headers,
                request_payload=config.request_payload,
                max_response_time_ms=config.max_response_time_ms * 2  # Allow longer response times
            )
            
            phase_metrics = await self._execute_standard_load_test(phase_config)
            metrics.extend(phase_metrics)
            
            # Recovery pause between phases
            await asyncio.sleep(5)
        
        return metrics
    
    async def _execute_spike_test(self, config: LoadTestConfig) -> List[TestMetric]:
        """Execute spike test with sudden traffic increase"""
        metrics = []
        
        # Normal load phase
        logger.info("📊 Spike test: Normal load phase")
        normal_metrics = await self._execute_standard_load_test(config)
        metrics.extend(normal_metrics)
        
        await asyncio.sleep(2)
        
        # Spike phase - 10x users for short duration
        spike_users = config.concurrent_users * 10
        logger.info(f"⚡ Spike test: Traffic spike ({spike_users} users)")
        
        spike_config = LoadTestConfig(
            test_name=f"{config.test_name}_spike",
            test_type=LoadTestType.LOAD,
            target_url=config.target_url,
            concurrent_users=spike_users,
            total_requests=spike_users * 2,  # Shorter burst
            request_method=config.request_method,
            request_headers=config.request_headers,
            request_payload=config.request_payload,
            max_response_time_ms=config.max_response_time_ms * 3
        )
        
        spike_metrics = await self._execute_standard_load_test(spike_config)
        metrics.extend(spike_metrics)
        
        await asyncio.sleep(2)
        
        # Recovery phase - back to normal
        logger.info("📉 Spike test: Recovery phase")
        recovery_metrics = await self._execute_standard_load_test(config)
        metrics.extend(recovery_metrics)
        
        return metrics
    
    async def _execute_endurance_test(self, config: LoadTestConfig) -> List[TestMetric]:
        """Execute endurance test for sustained load"""
        metrics = []
        duration = config.duration_seconds or 300  # 5 minutes default
        
        logger.info(f"🕒 Endurance test: {duration} seconds sustained load")
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Execute batch of requests
            batch_metrics = await self._execute_standard_load_test(
                LoadTestConfig(
                    test_name=f"{config.test_name}_endurance_batch",
                    test_type=LoadTestType.LOAD,
                    target_url=config.target_url,
                    concurrent_users=config.concurrent_users,
                    total_requests=config.concurrent_users * 5,  # Smaller batches
                    request_method=config.request_method,
                    request_headers=config.request_headers,
                    request_payload=config.request_payload
                )
            )
            metrics.extend(batch_metrics)
            
            # Brief pause between batches
            await asyncio.sleep(1)
        
        return metrics
    
    async def _simulate_user(self, 
                           user_id: int, 
                           request_count: int, 
                           config: LoadTestConfig, 
                           metrics: List[TestMetric]):
        """Simulate individual user making requests"""
        for request_num in range(request_count):
            try:
                # Vary request data if configured
                payload = self._generate_request_payload(config, user_id, request_num)
                
                # Make request with timing
                metric = await self._make_timed_request(config, payload)
                metrics.append(metric)
                
                # Think time between requests
                if config.think_time_ms > 0:
                    await asyncio.sleep(config.think_time_ms / 1000)
                    
            except Exception as e:
                logger.warning(f"User {user_id} request {request_num} failed: {str(e)}")
                # Record failed request
                metrics.append(TestMetric(
                    timestamp=time.time(),
                    response_time=0.0,
                    success=False,
                    status_code=None,
                    error_message=str(e),
                    memory_usage_mb=self._get_memory_usage(),
                    cpu_usage_percent=self._get_cpu_usage()
                ))
    
    async def _make_timed_request(self, config: LoadTestConfig, payload: Dict[str, Any]) -> TestMetric:
        """Make a single timed request and collect metrics"""
        start_time = time.time()
        memory_before = self._get_memory_usage()
        cpu_before = self._get_cpu_usage()
        
        try:
            async with self.session.request(
                config.request_method,
                config.target_url,
                json=payload
            ) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                success = response.status < 400
                
                return TestMetric(
                    timestamp=start_time,
                    response_time=response_time,
                    success=success,
                    status_code=response.status,
                    error_message=None if success else f"HTTP {response.status}",
                    memory_usage_mb=self._get_memory_usage(),
                    cpu_usage_percent=self._get_cpu_usage()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestMetric(
                timestamp=start_time,
                response_time=response_time,
                success=False,
                status_code=None,
                error_message=str(e),
                memory_usage_mb=self._get_memory_usage(),
                cpu_usage_percent=self._get_cpu_usage()
            )
    
    def _generate_request_payload(self, config: LoadTestConfig, user_id: int, request_num: int) -> Dict[str, Any]:
        """Generate request payload with optional variation"""
        base_payload = config.request_payload or {}
        
        if not config.data_variation:
            return base_payload
        
        # Add variation for load testing
        varied_payload = base_payload.copy()
        varied_payload.update({
            "user_id": user_id,
            "request_num": request_num,
            "timestamp": time.time(),
            "test_data": f"load_test_{user_id}_{request_num}"
        })
        
        return varied_payload
    
    def _start_resource_monitoring(self):
        """Start background resource monitoring"""
        self._resource_samples.clear()
        self._resource_monitor_task = asyncio.create_task(self._monitor_resources())
    
    def _stop_resource_monitoring(self):
        """Stop resource monitoring"""
        if self._resource_monitor_task:
            self._resource_monitor_task.cancel()
    
    async def _monitor_resources(self):
        """Background resource monitoring task"""
        while True:
            try:
                sample = {
                    "timestamp": time.time(),
                    "memory_mb": self._get_memory_usage(),
                    "cpu_percent": self._get_cpu_usage()
                }
                self._resource_samples.append(sample)
                await asyncio.sleep(1)  # Sample every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Resource monitoring error: {str(e)}")
                await asyncio.sleep(1)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return psutil.Process().memory_info().rss / (1024 * 1024)
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=None)
    
    def _analyze_results(self, 
                        config: LoadTestConfig, 
                        metrics: List[TestMetric], 
                        start_time: datetime, 
                        end_time: datetime) -> LoadTestResults:
        """Analyze test results and generate comprehensive report"""
        
        # Basic statistics
        total_requests = len(metrics)
        successful_requests = sum(1 for m in metrics if m.success)
        failed_requests = total_requests - successful_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Response time statistics
        response_times = [m.response_time for m in metrics if m.success]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = np.percentile(response_times, 50)
            p90_response_time = np.percentile(response_times, 90)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50_response_time = p90_response_time = p95_response_time = p99_response_time = 0
        
        # Throughput calculation
        duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration if duration > 0 else 0
        
        # Calculate peak RPS (using 1-second windows)
        if metrics:
            time_windows = {}
            for metric in metrics:
                window = int(metric.timestamp)
                time_windows[window] = time_windows.get(window, 0) + 1
            peak_rps = max(time_windows.values()) if time_windows else 0
        else:
            peak_rps = 0
        
        # Resource utilization
        memory_values = [m.memory_usage_mb for m in metrics]
        cpu_values = [m.cpu_usage_percent for m in metrics]
        
        avg_memory_mb = statistics.mean(memory_values) if memory_values else 0
        peak_memory_mb = max(memory_values) if memory_values else 0
        avg_cpu_percent = statistics.mean(cpu_values) if cpu_values else 0
        peak_cpu_percent = max(cpu_values) if cpu_values else 0
        
        # Error analysis
        error_distribution = {}
        for metric in metrics:
            if not metric.success and metric.error_message:
                error_distribution[metric.error_message] = error_distribution.get(metric.error_message, 0) + 1
        
        # Bottleneck identification
        bottlenecks = self._identify_bottlenecks(config, metrics, avg_response_time, peak_memory_mb, peak_cpu_percent)
        
        # Performance scoring
        performance_score = self._calculate_performance_score(
            config, success_rate, avg_response_time, requests_per_second, peak_memory_mb, peak_cpu_percent
        )
        
        # SLA compliance check
        meets_sla = (
            success_rate >= config.min_success_rate and
            avg_response_time <= config.max_response_time_ms and
            peak_memory_mb <= config.max_memory_mb and
            peak_cpu_percent <= config.max_cpu_percent
        )
        
        return LoadTestResults(
            config=config,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p90_response_time=p90_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            peak_rps=peak_rps,
            avg_memory_mb=avg_memory_mb,
            peak_memory_mb=peak_memory_mb,
            avg_cpu_percent=avg_cpu_percent,
            peak_cpu_percent=peak_cpu_percent,
            error_distribution=error_distribution,
            bottlenecks_identified=bottlenecks,
            performance_score=performance_score,
            meets_sla=meets_sla,
            metrics=metrics
        )
    
    def _identify_bottlenecks(self, 
                            config: LoadTestConfig, 
                            metrics: List[TestMetric], 
                            avg_response_time: float,
                            peak_memory_mb: float,
                            peak_cpu_percent: float) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Response time bottlenecks
        if avg_response_time > config.max_response_time_ms * 0.8:
            bottlenecks.append("High response times indicate processing bottleneck")
        
        # Memory bottlenecks
        if peak_memory_mb > config.max_memory_mb * 0.9:
            bottlenecks.append("High memory usage indicates memory pressure")
        
        # CPU bottlenecks
        if peak_cpu_percent > config.max_cpu_percent * 0.9:
            bottlenecks.append("High CPU usage indicates processing bottleneck")
        
        # Error rate bottlenecks
        failed_count = sum(1 for m in metrics if not m.success)
        if failed_count > len(metrics) * 0.1:  # More than 10% failures
            bottlenecks.append("High error rate indicates system overload")
        
        # Response time variance (indicates inconsistent performance)
        successful_times = [m.response_time for m in metrics if m.success]
        if successful_times and len(successful_times) > 1:
            std_dev = statistics.stdev(successful_times)
            if std_dev > avg_response_time * 0.5:  # High variance
                bottlenecks.append("High response time variance indicates system instability")
        
        return bottlenecks
    
    def _calculate_performance_score(self, 
                                   config: LoadTestConfig,
                                   success_rate: float,
                                   avg_response_time: float,
                                   requests_per_second: float,
                                   peak_memory_mb: float,
                                   peak_cpu_percent: float) -> float:
        """Calculate overall performance score (0-100)"""
        score = 100.0
        
        # Success rate impact (40% of score)
        success_score = success_rate * 40
        
        # Response time impact (30% of score)
        response_score = max(0, 30 - (avg_response_time / config.max_response_time_ms) * 30)
        
        # Resource utilization impact (20% of score)
        memory_score = max(0, 10 - (peak_memory_mb / config.max_memory_mb) * 10)
        cpu_score = max(0, 10 - (peak_cpu_percent / config.max_cpu_percent) * 10)
        
        # Throughput impact (10% of score)
        # This is more subjective - higher is better up to a reasonable limit
        throughput_score = min(10, requests_per_second / 10)  # 1 point per 10 RPS
        
        total_score = success_score + response_score + memory_score + cpu_score + throughput_score
        return min(100.0, max(0.0, total_score))
    
    async def _cleanup_session(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()

# Specialized load testing scenarios for question processing

async def test_1000_questions_processing(base_url: str) -> LoadTestResults:
    """
    Test processing 1000+ questions as required by TASK 18
    """
    logger.info("🎯 Starting 1000+ questions processing load test")
    
    config = LoadTestConfig(
        test_name="1000_Questions_Processing",
        test_type=LoadTestType.VOLUME,
        target_url=f"{base_url}/api/scraping/jobs",
        concurrent_users=50,  # 50 concurrent users
        total_requests=1000,  # 1000 questions
        request_method="POST",
        request_headers={"Content-Type": "application/json"},
        request_payload={
            "job_name": "Load_Test_Job",
            "source_names": ["indiabix"],
            "max_questions_per_source": 20,
            "quality_threshold": 75.0,
            "target_categories": ["quantitative"],
            "enable_ai_processing": True,
            "priority_level": 1
        },
        max_response_time_ms=10000.0,  # 10 seconds max
        min_success_rate=0.95,
        max_memory_mb=2048.0,
        max_cpu_percent=85.0,
        data_variation=True
    )
    
    executor = LoadTestExecutor(base_url)
    return await executor.execute_load_test(config)

async def test_api_scalability(base_url: str) -> LoadTestResults:
    """
    Test API scalability from 1 to 1000 concurrent users
    """
    logger.info("📈 Starting API scalability test")
    
    config = LoadTestConfig(
        test_name="API_Scalability",
        test_type=LoadTestType.SCALABILITY,
        target_url=f"{base_url}/api/health",
        concurrent_users=1000,  # Scale up to 1000 users
        total_requests=10000,   # Total 10k requests across all levels
        request_method="GET",
        max_response_time_ms=2000.0,
        min_success_rate=0.98,
        connection_pooling=True
    )
    
    executor = LoadTestExecutor(base_url)
    return await executor.execute_load_test(config)

async def run_comprehensive_performance_test(base_url: str) -> Dict[str, LoadTestResults]:
    """
    Run comprehensive performance test suite for TASK 18
    """
    logger.info("🚀 Starting comprehensive performance test suite for TASK 18")
    
    test_results = {}
    
    # Test 1: 1000+ questions processing (primary requirement)
    logger.info("\n" + "="*60)
    logger.info("TEST 1: 1000+ Questions Processing")
    logger.info("="*60)
    test_results["1000_questions"] = await test_1000_questions_processing(base_url)
    
    # Test 2: API scalability
    logger.info("\n" + "="*60)
    logger.info("TEST 2: API Scalability")
    logger.info("="*60)
    test_results["api_scalability"] = await test_api_scalability(base_url)
    
    # Test 3: Stress testing
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Stress Testing")
    logger.info("="*60)
    stress_config = LoadTestConfig(
        test_name="Stress_Test",
        test_type=LoadTestType.STRESS,
        target_url=f"{base_url}/api/scraping/system-status",
        concurrent_users=100,
        total_requests=2000,
        request_method="GET",
        max_response_time_ms=5000.0
    )
    executor = LoadTestExecutor(base_url)
    test_results["stress_test"] = await executor.execute_load_test(stress_config)
    
    # Generate comprehensive report
    logger.info("\n" + "="*60)
    logger.info("COMPREHENSIVE TEST RESULTS SUMMARY")
    logger.info("="*60)
    
    for test_name, result in test_results.items():
        logger.info(f"\n{test_name.upper()}:")
        logger.info(f"  ✅ Success Rate: {result.success_rate:.2%}")
        logger.info(f"  ⏱️  Avg Response Time: {result.avg_response_time:.0f}ms")
        logger.info(f"  🚀 Throughput: {result.requests_per_second:.1f} RPS")
        logger.info(f"  📊 Performance Score: {result.performance_score:.1f}/100")
        logger.info(f"  🎯 Meets SLA: {'✅ YES' if result.meets_sla else '❌ NO'}")
        
        if result.bottlenecks_identified:
            logger.info(f"  ⚠️  Bottlenecks: {', '.join(result.bottlenecks_identified)}")
    
    return test_results

# Factory function for easy load testing
def create_load_tester(base_url: str) -> LoadTestExecutor:
    """Create load test executor"""
    return LoadTestExecutor(base_url)