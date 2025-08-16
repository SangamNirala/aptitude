"""
Rate Limiter with Exponential Backoff
Comprehensive rate limiting system for ethical web scraping
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import math

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

class BackoffStrategy(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"
    CUSTOM = "custom"

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float = 0.5  # Base rate limit
    requests_per_minute: int = 20
    requests_per_hour: int = 500
    burst_allowance: int = 3  # Allow small bursts
    
    # Backoff configuration
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay: float = 2.0
    max_delay: float = 300.0  # 5 minutes max delay
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1  # Add randomness to delays
    
    # Recovery configuration
    success_threshold: int = 5  # Consecutive successes to reset backoff
    failure_threshold: int = 3  # Failures to trigger backoff
    recovery_rate: float = 0.5  # How fast to recover from backoff

@dataclass
class RequestRecord:
    """Record of a single request"""
    timestamp: datetime
    success: bool
    response_time: float
    status_code: Optional[int] = None
    delay_applied: float = 0.0
    backoff_level: int = 0

class RateLimiterState(str, Enum):
    NORMAL = "normal"
    BACKING_OFF = "backing_off"
    RECOVERING = "recovering"
    PAUSED = "paused"

# =============================================================================
# BASE RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Basic rate limiter with configurable limits
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.request_history: List[RequestRecord] = []
        self.state = RateLimiterState.NORMAL
        
        # Internal tracking
        self._last_request_time = 0.0
        self._burst_count = 0
        self._consecutive_successes = 0
        self._consecutive_failures = 0
        
        logger.info(f"🚦 RateLimiter initialized: {self.config.requests_per_second} RPS")
    
    async def acquire(self) -> float:
        """
        Acquire permission to make a request
        Returns the delay that was applied
        """
        
        current_time = time.time()
        
        # Check if we need to wait
        required_delay = self._calculate_delay(current_time)
        
        if required_delay > 0:
            logger.debug(f"⏳ Rate limiting: waiting {required_delay:.2f} seconds")
            await asyncio.sleep(required_delay)
        
        self._last_request_time = time.time()
        return required_delay
    
    def _calculate_delay(self, current_time: float) -> float:
        """Calculate required delay based on rate limits"""
        
        # Basic rate limiting (requests per second)
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.config.requests_per_second
        
        if time_since_last < min_interval:
            return min_interval - time_since_last
        
        # Check burst allowance
        if self._is_burst_allowed():
            return 0.0
        
        # Check rate limits over different time windows
        minute_delay = self._check_minute_limit(current_time)
        hour_delay = self._check_hour_limit(current_time)
        
        return max(0.0, minute_delay, hour_delay)
    
    def _is_burst_allowed(self) -> bool:
        """Check if burst is allowed"""
        
        if self._burst_count < self.config.burst_allowance:
            self._burst_count += 1
            return True
        
        return False
    
    def _check_minute_limit(self, current_time: float) -> float:
        """Check requests per minute limit"""
        
        minute_ago = current_time - 60
        recent_requests = [
            r for r in self.request_history 
            if r.timestamp.timestamp() > minute_ago
        ]
        
        if len(recent_requests) >= self.config.requests_per_minute:
            # Calculate when we can make the next request
            oldest_request = min(recent_requests, key=lambda x: x.timestamp.timestamp())
            return 60 - (current_time - oldest_request.timestamp.timestamp())
        
        return 0.0
    
    def _check_hour_limit(self, current_time: float) -> float:
        """Check requests per hour limit"""
        
        hour_ago = current_time - 3600
        recent_requests = [
            r for r in self.request_history 
            if r.timestamp.timestamp() > hour_ago
        ]
        
        if len(recent_requests) >= self.config.requests_per_hour:
            # Calculate when we can make the next request
            oldest_request = min(recent_requests, key=lambda x: x.timestamp.timestamp())
            return 3600 - (current_time - oldest_request.timestamp.timestamp())
        
        return 0.0
    
    def record_request(self, success: bool, response_time: float, status_code: Optional[int] = None):
        """Record the result of a request"""
        
        record = RequestRecord(
            timestamp=datetime.utcnow(),
            success=success,
            response_time=response_time,
            status_code=status_code
        )
        
        self.request_history.append(record)
        
        # Update burst counter
        if success:
            self._burst_count = max(0, self._burst_count - 1)
        
        # Maintain history size (keep last 1000 requests)
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
        
        logger.debug(f"📝 Request recorded: {'✅' if success else '❌'} ({status_code}) - {response_time:.2f}s")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        
        if not self.request_history:
            return {"total_requests": 0}
        
        recent_hour = [
            r for r in self.request_history 
            if datetime.utcnow() - r.timestamp < timedelta(hours=1)
        ]
        
        recent_minute = [
            r for r in recent_hour
            if datetime.utcnow() - r.timestamp < timedelta(minutes=1)
        ]
        
        return {
            "total_requests": len(self.request_history),
            "requests_last_hour": len(recent_hour),
            "requests_last_minute": len(recent_minute),
            "success_rate": sum(1 for r in self.request_history if r.success) / len(self.request_history),
            "avg_response_time": sum(r.response_time for r in self.request_history) / len(self.request_history),
            "current_state": self.state.value
        }

# =============================================================================
# EXPONENTIAL BACKOFF RATE LIMITER
# =============================================================================

class ExponentialBackoffLimiter(RateLimiter):
    """
    Advanced rate limiter with exponential backoff on failures
    """
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        
        # Backoff state
        self.backoff_level = 0
        self.max_backoff_level = 10
        self.last_backoff_time = 0.0
        
        # Recovery tracking
        self._consecutive_successes = 0
        self._consecutive_failures = 0
        
        logger.info(f"📈 ExponentialBackoffLimiter initialized with {config.backoff_strategy.value} strategy")
    
    async def acquire(self) -> float:
        """Acquire with backoff consideration"""
        
        # Check if we're in backoff period
        backoff_delay = self._calculate_backoff_delay()
        
        # Get regular rate limit delay
        regular_delay = await super().acquire()
        
        # Apply the maximum of both delays
        total_delay = max(backoff_delay, regular_delay)
        
        if backoff_delay > 0:
            logger.info(f"⏳ Backoff delay: {backoff_delay:.2f}s (level {self.backoff_level})")
            await asyncio.sleep(backoff_delay)
        
        return total_delay
    
    def _calculate_backoff_delay(self) -> float:
        """Calculate exponential backoff delay"""
        
        if self.backoff_level == 0:
            return 0.0
        
        # Calculate delay based on strategy
        if self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * self.backoff_level
        
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** self.backoff_level)
        
        elif self.config.backoff_strategy == BackoffStrategy.FIBONACCI:
            delay = self.config.base_delay * self._fibonacci(self.backoff_level)
        
        else:  # CUSTOM or fallback
            delay = self.config.base_delay * (1.5 ** self.backoff_level)
        
        # Apply jitter to avoid thundering herd
        jitter = random.uniform(-self.config.jitter_factor, self.config.jitter_factor)
        delay = delay * (1 + jitter)
        
        # Ensure delay is within bounds
        return min(max(0.0, delay), self.config.max_delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate fibonacci number efficiently"""
        if n <= 1:
            return 1
        
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def record_request(self, success: bool, response_time: float, status_code: Optional[int] = None):
        """Record request and update backoff state"""
        
        # Call parent to record the request
        super().record_request(success, response_time, status_code)
        
        # Update backoff state based on success/failure
        if success:
            self._handle_success()
        else:
            self._handle_failure(status_code)
        
        # Update internal state
        self._update_state()
    
    def _handle_success(self):
        """Handle successful request"""
        
        self._consecutive_successes += 1
        self._consecutive_failures = 0
        
        # Recovery logic
        if (self.backoff_level > 0 and 
            self._consecutive_successes >= self.config.success_threshold):
            
            # Reduce backoff level
            old_level = self.backoff_level
            self.backoff_level = max(0, int(self.backoff_level * self.config.recovery_rate))
            
            if self.backoff_level != old_level:
                logger.info(f"📉 Backoff recovery: level {old_level} → {self.backoff_level}")
                self._consecutive_successes = 0  # Reset counter
    
    def _handle_failure(self, status_code: Optional[int]):
        """Handle failed request"""
        
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        
        # Determine if this failure should trigger backoff
        should_backoff = self._should_trigger_backoff(status_code)
        
        if (should_backoff and 
            self._consecutive_failures >= self.config.failure_threshold):
            
            # Increase backoff level
            old_level = self.backoff_level
            self.backoff_level = min(self.max_backoff_level, self.backoff_level + 1)
            
            if self.backoff_level != old_level:
                logger.warning(f"📈 Backoff triggered: level {old_level} → {self.backoff_level} (failures: {self._consecutive_failures})")
                self._consecutive_failures = 0  # Reset counter
                self.last_backoff_time = time.time()
    
    def _should_trigger_backoff(self, status_code: Optional[int]) -> bool:
        """Determine if status code should trigger backoff"""
        
        if status_code is None:
            return True  # Network errors trigger backoff
        
        # Status codes that indicate we should back off
        backoff_codes = {
            429,  # Too Many Requests
            503,  # Service Unavailable
            502,  # Bad Gateway
            504,  # Gateway Timeout
            403,  # Forbidden (might be rate limiting)
            408,  # Request Timeout
        }
        
        return status_code in backoff_codes
    
    def _update_state(self):
        """Update the current state of the rate limiter"""
        
        if self.backoff_level == 0:
            self.state = RateLimiterState.NORMAL
        elif self._consecutive_successes > 0 and self.backoff_level > 0:
            self.state = RateLimiterState.RECOVERING
        else:
            self.state = RateLimiterState.BACKING_OFF
    
    def force_backoff(self, level: int = None):
        """Manually trigger backoff (e.g., when detection is suspected)"""
        
        old_level = self.backoff_level
        self.backoff_level = min(self.max_backoff_level, level or (self.backoff_level + 2))
        
        logger.warning(f"🚨 Forced backoff: level {old_level} → {self.backoff_level}")
        self._update_state()
    
    def reset_backoff(self):
        """Reset backoff state"""
        
        old_level = self.backoff_level
        self.backoff_level = 0
        self._consecutive_successes = 0
        self._consecutive_failures = 0
        
        logger.info(f"🔄 Backoff reset: level {old_level} → 0")
        self._update_state()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics including backoff information"""
        
        stats = super().get_statistics()
        
        # Add backoff-specific stats
        stats.update({
            "backoff_level": self.backoff_level,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures,
            "current_backoff_delay": self._calculate_backoff_delay(),
            "time_since_last_backoff": time.time() - self.last_backoff_time if self.last_backoff_time > 0 else None
        })
        
        return stats

# =============================================================================
# ADAPTIVE RATE LIMITER
# =============================================================================

class AdaptiveRateLimiter(ExponentialBackoffLimiter):
    """
    Adaptive rate limiter that adjusts based on server response patterns
    """
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        
        # Adaptive parameters
        self.base_requests_per_second = config.requests_per_second if config else 0.5
        self.adaptive_factor = 1.0
        self.adaptation_history = []
        self.performance_window = 50  # Number of requests to consider for adaptation
        
        logger.info(f"🤖 AdaptiveRateLimiter initialized")
    
    def record_request(self, success: bool, response_time: float, status_code: Optional[int] = None):
        """Record request and adapt rate based on performance"""
        
        # Call parent to handle backoff logic
        super().record_request(success, response_time, status_code)
        
        # Add to adaptation history
        self.adaptation_history.append({
            "timestamp": datetime.utcnow(),
            "success": success,
            "response_time": response_time,
            "status_code": status_code
        })
        
        # Maintain adaptation history size
        if len(self.adaptation_history) > self.performance_window:
            self.adaptation_history = self.adaptation_history[-self.performance_window:]
        
        # Adapt rate if we have enough data
        if len(self.adaptation_history) >= 10:
            self._adapt_rate()
    
    def _adapt_rate(self):
        """Adapt request rate based on recent performance"""
        
        if len(self.adaptation_history) < 10:
            return
        
        recent_requests = self.adaptation_history[-20:]  # Last 20 requests
        
        # Calculate performance metrics
        success_rate = sum(1 for r in recent_requests if r["success"]) / len(recent_requests)
        avg_response_time = sum(r["response_time"] for r in recent_requests) / len(recent_requests)
        
        # Count rate limit indicators
        rate_limit_responses = sum(
            1 for r in recent_requests 
            if r["status_code"] in [429, 503, 502] or not r["success"]
        )
        rate_limit_ratio = rate_limit_responses / len(recent_requests)
        
        # Adaptation logic
        old_factor = self.adaptive_factor
        
        if rate_limit_ratio > 0.3:
            # Too many rate limits - slow down significantly
            self.adaptive_factor = max(0.3, self.adaptive_factor * 0.7)
        elif rate_limit_ratio > 0.1:
            # Some rate limits - slow down moderately
            self.adaptive_factor = max(0.5, self.adaptive_factor * 0.8)
        elif success_rate > 0.95 and avg_response_time < 2.0:
            # High success rate and fast responses - can speed up slightly
            self.adaptive_factor = min(2.0, self.adaptive_factor * 1.05)
        elif success_rate > 0.9:
            # Good success rate - maintain or slight increase
            self.adaptive_factor = min(1.5, self.adaptive_factor * 1.02)
        
        # Update the effective rate
        self.config.requests_per_second = self.base_requests_per_second * self.adaptive_factor
        
        if abs(self.adaptive_factor - old_factor) > 0.1:
            logger.info(f"📊 Rate adapted: factor {old_factor:.2f} → {self.adaptive_factor:.2f} "
                       f"(RPS: {self.config.requests_per_second:.3f})")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics including adaptation info"""
        
        stats = super().get_statistics()
        
        # Add adaptation-specific stats
        stats.update({
            "adaptive_factor": self.adaptive_factor,
            "effective_rps": self.config.requests_per_second,
            "base_rps": self.base_requests_per_second,
            "adaptation_data_points": len(self.adaptation_history)
        })
        
        return stats

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_rate_limiter(limiter_type: str = "exponential", 
                       source_config: Optional[Dict[str, Any]] = None) -> RateLimiter:
    """Factory function to create appropriate rate limiter"""
    
    # Create configuration from source config
    config = RateLimitConfig()
    
    if source_config:
        # Apply source-specific configuration
        if "requests_per_second" in source_config:
            config.requests_per_second = source_config["requests_per_second"]
        if "requests_per_minute" in source_config:
            config.requests_per_minute = source_config["requests_per_minute"]
        if "base_delay" in source_config:
            config.base_delay = source_config["base_delay"]
        if "max_delay" in source_config:
            config.max_delay = source_config["max_delay"]
    
    # Create appropriate limiter type
    if limiter_type == "basic":
        return RateLimiter(config)
    elif limiter_type == "adaptive":
        return AdaptiveRateLimiter(config)
    else:  # default to exponential
        return ExponentialBackoffLimiter(config)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

class RateLimiterManager:
    """Manager for multiple rate limiters (e.g., per-domain)"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
    
    def get_limiter(self, key: str, limiter_type: str = "exponential", 
                   config: Optional[Dict[str, Any]] = None) -> RateLimiter:
        """Get or create rate limiter for a specific key"""
        
        if key not in self.limiters:
            self.limiters[key] = create_rate_limiter(limiter_type, config)
        
        return self.limiters[key]
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all managed limiters"""
        
        return {key: limiter.get_statistics() for key, limiter in self.limiters.items()}