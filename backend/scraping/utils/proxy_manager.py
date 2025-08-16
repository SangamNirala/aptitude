"""
Proxy Manager
Comprehensive proxy management system for web scraping with health monitoring
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import json
import time

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

class ProxyType(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    FAILED = "failed"
    BANNED = "banned"

@dataclass
class ProxyConfig:
    """Configuration for a proxy server"""
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Performance metrics
    response_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    
    # Status and metadata
    status: ProxyStatus = ProxyStatus.INACTIVE
    country: Optional[str] = None
    city: Optional[str] = None
    anonymity_level: str = "unknown"  # transparent, anonymous, elite
    
    # Performance tracking
    avg_response_time: float = 0.0
    reliability_score: float = 0.0
    ban_count: int = 0
    consecutive_failures: int = 0
    
    def __post_init__(self):
        self.id = f"{self.host}:{self.port}"
    
    @property
    def url(self) -> str:
        """Get proxy URL for requests"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

@dataclass
class ProxyTestResult:
    """Result of a proxy test"""
    proxy_id: str
    success: bool
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    test_url: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

# =============================================================================
# PROXY MANAGER
# =============================================================================

class ProxyManager:
    """
    Comprehensive proxy management system with health monitoring and rotation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.proxies: Dict[str, ProxyConfig] = {}
        self.active_proxies: List[ProxyConfig] = []
        
        # Test configuration
        self.test_urls = [
            "http://httpbin.org/ip",
            "https://api.ipify.org?format=json", 
            "http://icanhazip.com",
            "https://ipinfo.io/json"
        ]
        self.test_timeout = 10.0
        self.test_interval = timedelta(minutes=15)
        
        # Rotation settings
        self.rotation_strategy = self.config.get("rotation_strategy", "round_robin")  # round_robin, random, performance
        self.current_index = 0
        self.max_failures_before_ban = self.config.get("max_failures_before_ban", 5)
        
        # Performance tracking
        self.proxy_usage_history = []
        self.test_results_history = []
        
        logger.info(f"🔄 ProxyManager initialized with {self.rotation_strategy} rotation")
    
    # =============================================================================
    # PROXY MANAGEMENT
    # =============================================================================
    
    def add_proxy(self, host: str, port: int, proxy_type: ProxyType = ProxyType.HTTP,
                  username: str = None, password: str = None, **kwargs) -> ProxyConfig:
        """Add a proxy to the manager"""
        
        proxy = ProxyConfig(
            host=host,
            port=port, 
            proxy_type=proxy_type,
            username=username,
            password=password,
            **kwargs
        )
        
        self.proxies[proxy.id] = proxy
        logger.info(f"➕ Added proxy: {proxy.id}")
        
        return proxy
    
    def add_proxy_list(self, proxy_list: List[Dict[str, Any]]):
        """Add multiple proxies from a list"""
        
        for proxy_data in proxy_list:
            try:
                self.add_proxy(**proxy_data)
            except Exception as e:
                logger.error(f"❌ Failed to add proxy {proxy_data}: {str(e)}")
    
    def remove_proxy(self, proxy_id: str) -> bool:
        """Remove a proxy from the manager"""
        
        if proxy_id in self.proxies:
            proxy = self.proxies[proxy_id]
            
            # Remove from active list if present
            self.active_proxies = [p for p in self.active_proxies if p.id != proxy_id]
            
            del self.proxies[proxy_id]
            logger.info(f"🗑️ Removed proxy: {proxy_id}")
            return True
        
        return False
    
    def get_proxy_by_id(self, proxy_id: str) -> Optional[ProxyConfig]:
        """Get proxy by ID"""
        return self.proxies.get(proxy_id)
    
    # =============================================================================
    # PROXY TESTING
    # =============================================================================
    
    async def test_proxy(self, proxy: ProxyConfig, test_url: str = None) -> ProxyTestResult:
        """Test a single proxy"""
        
        proxy.status = ProxyStatus.TESTING
        test_url = test_url or random.choice(self.test_urls)
        
        start_time = time.time()
        
        try:
            # Create proxy connector
            connector = aiohttp.TCPConnector()
            
            # Configure proxy settings for aiohttp
            proxy_url = proxy.url
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.test_timeout)
            ) as session:
                
                async with session.get(test_url, proxy=proxy_url) as response:
                    response_time = time.time() - start_time
                    
                    # Test passed if we get any valid HTTP response
                    success = response.status < 400
                    
                    result = ProxyTestResult(
                        proxy_id=proxy.id,
                        success=success,
                        response_time=response_time,
                        status_code=response.status,
                        test_url=test_url
                    )
                    
                    await self._update_proxy_metrics(proxy, result)
                    return result
        
        except Exception as e:
            response_time = time.time() - start_time
            
            result = ProxyTestResult(
                proxy_id=proxy.id,
                success=False,
                response_time=response_time,
                error_message=str(e),
                test_url=test_url
            )
            
            await self._update_proxy_metrics(proxy, result)
            return result
    
    async def test_all_proxies(self) -> List[ProxyTestResult]:
        """Test all proxies concurrently"""
        
        logger.info(f"🧪 Testing {len(self.proxies)} proxies...")
        
        # Create test tasks
        test_tasks = [
            self.test_proxy(proxy) for proxy in self.proxies.values()
        ]
        
        # Run tests concurrently with some limits to avoid overwhelming
        batch_size = 10
        results = []
        
        for i in range(0, len(test_tasks), batch_size):
            batch = test_tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, ProxyTestResult):
                    results.append(result)
                else:
                    logger.error(f"❌ Proxy test failed: {str(result)}")
        
        # Update active proxy list
        await self._update_active_proxies()
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ Proxy testing complete: {success_count}/{len(results)} passed")
        
        return results
    
    async def _update_proxy_metrics(self, proxy: ProxyConfig, result: ProxyTestResult):
        """Update proxy performance metrics"""
        
        proxy.last_tested = datetime.utcnow()
        proxy.response_time = result.response_time
        
        if result.success:
            proxy.success_count += 1
            proxy.consecutive_failures = 0
            proxy.status = ProxyStatus.ACTIVE
            
            # Update average response time
            if proxy.avg_response_time == 0:
                proxy.avg_response_time = result.response_time
            else:
                proxy.avg_response_time = (proxy.avg_response_time * 0.7 + result.response_time * 0.3)
        
        else:
            proxy.failure_count += 1
            proxy.consecutive_failures += 1
            
            # Mark as failed or banned based on failure pattern
            if proxy.consecutive_failures >= self.max_failures_before_ban:
                proxy.status = ProxyStatus.BANNED
                proxy.ban_count += 1
            else:
                proxy.status = ProxyStatus.FAILED
        
        # Update reliability score (0-100)
        total_tests = proxy.success_count + proxy.failure_count
        if total_tests > 0:
            base_reliability = (proxy.success_count / total_tests) * 100
            
            # Penalize high response times
            speed_penalty = min(20, proxy.avg_response_time * 2)  # Up to 20% penalty
            
            # Penalize recent failures
            recency_penalty = min(15, proxy.consecutive_failures * 5)  # Up to 15% penalty
            
            proxy.reliability_score = max(0, base_reliability - speed_penalty - recency_penalty)
        
        # Store test result
        self.test_results_history.append(result)
        
        # Maintain history size
        if len(self.test_results_history) > 1000:
            self.test_results_history = self.test_results_history[-1000:]
    
    async def _update_active_proxies(self):
        """Update the list of active proxies"""
        
        # Get proxies that are currently working
        active_proxies = [
            proxy for proxy in self.proxies.values()
            if proxy.status == ProxyStatus.ACTIVE and proxy.reliability_score > 30
        ]
        
        # Sort by performance (reliability score and response time)
        active_proxies.sort(key=lambda p: (p.reliability_score, -p.avg_response_time), reverse=True)
        
        self.active_proxies = active_proxies
        logger.debug(f"📊 Active proxies updated: {len(active_proxies)} available")
    
    # =============================================================================
    # PROXY SELECTION AND ROTATION
    # =============================================================================
    
    def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get the next proxy based on rotation strategy"""
        
        if not self.active_proxies:
            logger.warning("⚠️ No active proxies available")
            return None
        
        if self.rotation_strategy == "round_robin":
            proxy = self._get_round_robin_proxy()
        elif self.rotation_strategy == "random":
            proxy = self._get_random_proxy()
        elif self.rotation_strategy == "performance":
            proxy = self._get_performance_based_proxy()
        else:
            proxy = self.active_proxies[0]  # Default to first available
        
        if proxy:
            proxy.last_used = datetime.utcnow()
            self.proxy_usage_history.append({
                "proxy_id": proxy.id,
                "timestamp": datetime.utcnow(),
                "rotation_strategy": self.rotation_strategy
            })
        
        return proxy
    
    def _get_round_robin_proxy(self) -> Optional[ProxyConfig]:
        """Round robin selection"""
        
        if not self.active_proxies:
            return None
        
        proxy = self.active_proxies[self.current_index % len(self.active_proxies)]
        self.current_index += 1
        
        return proxy
    
    def _get_random_proxy(self) -> Optional[ProxyConfig]:
        """Random selection"""
        
        if not self.active_proxies:
            return None
        
        return random.choice(self.active_proxies)
    
    def _get_performance_based_proxy(self) -> Optional[ProxyConfig]:
        """Performance-based weighted selection"""
        
        if not self.active_proxies:
            return None
        
        # Calculate weights based on reliability and speed
        weights = []
        for proxy in self.active_proxies:
            # Base weight from reliability score
            weight = proxy.reliability_score
            
            # Boost weight for faster proxies
            if proxy.avg_response_time > 0:
                speed_factor = min(2.0, 2.0 / proxy.avg_response_time)  # Faster = higher weight
                weight *= speed_factor
            
            # Reduce weight for recently used proxies to encourage rotation
            if proxy.last_used:
                minutes_since_use = (datetime.utcnow() - proxy.last_used).total_seconds() / 60
                if minutes_since_use < 5:  # Used within last 5 minutes
                    weight *= 0.5
            
            weights.append(weight)
        
        if sum(weights) == 0:
            return random.choice(self.active_proxies)
        
        return random.choices(self.active_proxies, weights=weights)[0]
    
    # =============================================================================
    # PROXY HEALTH MONITORING
    # =============================================================================
    
    async def start_health_monitoring(self, interval: timedelta = None):
        """Start continuous health monitoring of proxies"""
        
        interval = interval or self.test_interval
        logger.info(f"💊 Starting proxy health monitoring (interval: {interval.total_seconds()}s)")
        
        while True:
            try:
                await self.test_all_proxies()
                await asyncio.sleep(interval.total_seconds())
            except Exception as e:
                logger.error(f"❌ Health monitoring error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def report_proxy_failure(self, proxy_id: str, error_details: Dict[str, Any] = None):
        """Report a proxy failure from external usage"""
        
        proxy = self.proxies.get(proxy_id)
        if not proxy:
            return
        
        proxy.failure_count += 1
        proxy.consecutive_failures += 1
        
        # Update status based on failure count
        if proxy.consecutive_failures >= self.max_failures_before_ban:
            proxy.status = ProxyStatus.BANNED
            
            # Remove from active list
            self.active_proxies = [p for p in self.active_proxies if p.id != proxy_id]
            
            logger.warning(f"🚫 Proxy banned due to failures: {proxy_id}")
        else:
            proxy.status = ProxyStatus.FAILED
        
        # Store failure details
        if error_details:
            failure_record = {
                "proxy_id": proxy_id,
                "timestamp": datetime.utcnow(),
                "error_details": error_details
            }
            # Could store this in a failures history if needed
    
    def report_proxy_success(self, proxy_id: str, response_time: float):
        """Report a successful proxy usage"""
        
        proxy = self.proxies.get(proxy_id)
        if not proxy:
            return
        
        proxy.success_count += 1
        proxy.consecutive_failures = 0
        proxy.status = ProxyStatus.ACTIVE
        proxy.last_used = datetime.utcnow()
        
        # Update average response time
        if proxy.avg_response_time == 0:
            proxy.avg_response_time = response_time
        else:
            proxy.avg_response_time = (proxy.avg_response_time * 0.8 + response_time * 0.2)
        
        # Ensure it's in active list if not already
        if proxy not in self.active_proxies and proxy.reliability_score > 30:
            self.active_proxies.append(proxy)
    
    # =============================================================================
    # STATISTICS AND REPORTING
    # =============================================================================
    
    def get_proxy_statistics(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        
        total_proxies = len(self.proxies)
        active_count = len(self.active_proxies)
        
        if total_proxies == 0:
            return {"total_proxies": 0, "active_proxies": 0}
        
        # Calculate aggregate metrics
        all_proxies = list(self.proxies.values())
        
        avg_reliability = sum(p.reliability_score for p in all_proxies) / len(all_proxies)
        avg_response_time = sum(p.avg_response_time for p in all_proxies if p.avg_response_time > 0) / max(1, len([p for p in all_proxies if p.avg_response_time > 0]))
        
        # Status distribution
        status_counts = {}
        for status in ProxyStatus:
            count = sum(1 for p in all_proxies if p.status == status)
            status_counts[status.value] = count
        
        # Performance distribution
        performance_tiers = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for proxy in all_proxies:
            if proxy.reliability_score >= 80:
                performance_tiers["excellent"] += 1
            elif proxy.reliability_score >= 60:
                performance_tiers["good"] += 1
            elif proxy.reliability_score >= 40:
                performance_tiers["fair"] += 1
            else:
                performance_tiers["poor"] += 1
        
        return {
            "total_proxies": total_proxies,
            "active_proxies": active_count,
            "availability_rate": (active_count / total_proxies) * 100,
            "avg_reliability_score": round(avg_reliability, 2),
            "avg_response_time": round(avg_response_time, 3),
            "status_distribution": status_counts,
            "performance_distribution": performance_tiers,
            "rotation_strategy": self.rotation_strategy,
            "total_usage_records": len(self.proxy_usage_history),
            "total_test_records": len(self.test_results_history)
        }
    
    def get_top_proxies(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing proxies"""
        
        sorted_proxies = sorted(
            self.active_proxies,
            key=lambda p: (p.reliability_score, -p.avg_response_time),
            reverse=True
        )
        
        return [
            {
                "id": proxy.id,
                "host": proxy.host,
                "port": proxy.port,
                "reliability_score": proxy.reliability_score,
                "avg_response_time": proxy.avg_response_time,
                "success_rate": proxy.success_rate,
                "status": proxy.status.value,
                "last_used": proxy.last_used.isoformat() if proxy.last_used else None
            }
            for proxy in sorted_proxies[:limit]
        ]
    
    # =============================================================================
    # CONFIGURATION METHODS
    # =============================================================================
    
    def set_rotation_strategy(self, strategy: str):
        """Change rotation strategy"""
        
        valid_strategies = ["round_robin", "random", "performance"]
        if strategy in valid_strategies:
            self.rotation_strategy = strategy
            logger.info(f"🔄 Rotation strategy changed to: {strategy}")
        else:
            logger.warning(f"⚠️ Invalid rotation strategy: {strategy}")
    
    def update_config(self, config_updates: Dict[str, Any]):
        """Update configuration"""
        
        self.config.update(config_updates)
        
        if "test_interval_minutes" in config_updates:
            self.test_interval = timedelta(minutes=config_updates["test_interval_minutes"])
        
        if "max_failures_before_ban" in config_updates:
            self.max_failures_before_ban = config_updates["max_failures_before_ban"]
        
        if "rotation_strategy" in config_updates:
            self.set_rotation_strategy(config_updates["rotation_strategy"])
        
        logger.info(f"📝 Proxy manager configuration updated")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_proxy_manager(config: Dict[str, Any] = None) -> ProxyManager:
    """Factory function to create proxy manager"""
    
    manager = ProxyManager(config or {})
    
    # Add some default free proxies for testing (these might not work reliably)
    # In production, you would load from a proxy service or configuration
    default_proxies = [
        # These are example proxies - replace with actual working proxies
        {"host": "proxy1.example.com", "port": 8080, "proxy_type": ProxyType.HTTP},
        {"host": "proxy2.example.com", "port": 3128, "proxy_type": ProxyType.HTTP},
    ]
    
    # Only add default proxies in development/testing
    if config and config.get("add_default_proxies", False):
        manager.add_proxy_list(default_proxies)
    
    return manager

async def test_proxy_manager():
    """Test function for proxy manager"""
    
    logger.info("🧪 Testing ProxyManager...")
    
    # Create manager
    manager = create_proxy_manager({"add_default_proxies": False})
    
    # Add some test proxies (these won't work, just for structure testing)
    manager.add_proxy("127.0.0.1", 8080, ProxyType.HTTP)
    manager.add_proxy("127.0.0.1", 3128, ProxyType.HTTP)
    
    # Test all proxies (will fail but shows structure)
    results = await manager.test_all_proxies()
    
    # Get statistics
    stats = manager.get_proxy_statistics()
    logger.info(f"📊 Proxy statistics: {stats}")
    
    return manager