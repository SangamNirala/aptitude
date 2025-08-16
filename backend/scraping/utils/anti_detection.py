"""
Anti-Detection Manager
Comprehensive anti-detection measures for ethical web scraping
"""

import random
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

class DetectionRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class UserAgentProfile:
    """User agent profile with associated characteristics"""
    user_agent: str
    browser: str
    version: str
    os: str
    platform: str
    popularity_score: float  # Higher = more common
    last_used: Optional[datetime] = None
    detection_incidents: int = 0

@dataclass
class RequestFingerprint:
    """Unique fingerprint for request patterns"""
    url_pattern: str
    request_frequency: float
    headers_signature: str
    timing_pattern: str
    risk_score: float

# =============================================================================
# ANTI-DETECTION MANAGER
# =============================================================================

class AntiDetectionManager:
    """
    Comprehensive anti-detection manager for ethical web scraping
    Implements multiple layers of detection avoidance while respecting websites
    """
    
    def __init__(self, source_name: str, config: Dict[str, Any] = None):
        self.source_name = source_name
        self.config = config or {}
        
        # Detection tracking
        self.session_start = datetime.utcnow()
        self.request_count = 0
        self.detection_incidents = []
        self.current_risk_level = DetectionRiskLevel.LOW
        
        # User agent management
        self.user_agents = self._load_user_agents()
        self.current_user_agent = None
        self.user_agent_rotation_frequency = self.config.get("user_agent_rotation_frequency", 50)
        
        # Request patterns
        self.request_patterns = {}
        self.request_history = []
        self.max_history_size = 1000
        
        # Behavioral simulation
        self.human_behavior_config = self.config.get("human_behavior", {})
        self.session_duration_limits = self.config.get("session_duration", {"min": 300, "max": 1800})  # 5-30 minutes
        
        logger.info(f"🛡️ AntiDetectionManager initialized for {source_name}")
    
    def _load_user_agents(self) -> List[UserAgentProfile]:
        """Load and initialize user agent profiles"""
        
        # Comprehensive user agent database with popularity scores
        user_agents_data = [
            # Chrome (Most popular - higher scores)
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "browser": "Chrome", "version": "120.0", "os": "Windows", "platform": "desktop", "popularity": 0.95
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "browser": "Chrome", "version": "119.0", "os": "Windows", "platform": "desktop", "popularity": 0.92
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "browser": "Chrome", "version": "120.0", "os": "macOS", "platform": "desktop", "popularity": 0.88
            },
            {
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "browser": "Chrome", "version": "120.0", "os": "Linux", "platform": "desktop", "popularity": 0.75
            },
            
            # Firefox
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                "browser": "Firefox", "version": "119.0", "os": "Windows", "platform": "desktop", "popularity": 0.82
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
                "browser": "Firefox", "version": "119.0", "os": "macOS", "platform": "desktop", "popularity": 0.78
            },
            
            # Safari
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "browser": "Safari", "version": "17.1", "os": "macOS", "platform": "desktop", "popularity": 0.85
            },
            
            # Edge
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "browser": "Edge", "version": "120.0", "os": "Windows", "platform": "desktop", "popularity": 0.70
            },
            
            # Mobile User Agents
            {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "browser": "Safari Mobile", "version": "17.1", "os": "iOS", "platform": "mobile", "popularity": 0.80
            },
            {
                "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "browser": "Chrome Mobile", "version": "120.0", "os": "Android", "platform": "mobile", "popularity": 0.77
            }
        ]
        
        profiles = []
        for ua_data in user_agents_data:
            profile = UserAgentProfile(
                user_agent=ua_data["user_agent"],
                browser=ua_data["browser"],
                version=ua_data["version"],
                os=ua_data["os"],
                platform=ua_data["platform"],
                popularity_score=ua_data["popularity"]
            )
            profiles.append(profile)
        
        # Sort by popularity (most popular first)
        profiles.sort(key=lambda x: x.popularity_score, reverse=True)
        return profiles
    
    # =============================================================================
    # USER AGENT ROTATION
    # =============================================================================
    
    def get_user_agent(self, force_rotation: bool = False) -> str:
        """Get current user agent or rotate if needed"""
        
        should_rotate = (
            force_rotation or 
            self.current_user_agent is None or 
            self.request_count % self.user_agent_rotation_frequency == 0 or
            self.current_risk_level in [DetectionRiskLevel.HIGH, DetectionRiskLevel.CRITICAL]
        )
        
        if should_rotate:
            self._rotate_user_agent()
        
        return self.current_user_agent.user_agent if self.current_user_agent else self.user_agents[0].user_agent
    
    def _rotate_user_agent(self):
        """Intelligently rotate user agent based on popularity and detection history"""
        
        # Filter available user agents (exclude recently detected ones)
        available_agents = [
            ua for ua in self.user_agents 
            if ua.detection_incidents < 3 and 
            (ua.last_used is None or datetime.utcnow() - ua.last_used > timedelta(hours=1))
        ]
        
        if not available_agents:
            # If all agents have issues, reset and use the most popular ones
            for ua in self.user_agents:
                ua.detection_incidents = 0
                ua.last_used = None
            available_agents = self.user_agents[:3]  # Top 3 most popular
        
        # Weighted random selection based on popularity
        weights = [ua.popularity_score for ua in available_agents]
        self.current_user_agent = random.choices(available_agents, weights=weights)[0]
        self.current_user_agent.last_used = datetime.utcnow()
        
        logger.debug(f"🔄 Rotated to user agent: {self.current_user_agent.browser} {self.current_user_agent.version}")
    
    # =============================================================================
    # REQUEST HEADERS GENERATION
    # =============================================================================
    
    def get_request_headers(self, url: str, referer: Optional[str] = None) -> Dict[str, str]:
        """Generate realistic request headers based on current user agent"""
        
        headers = {
            "User-Agent": self.get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none" if not referer else "same-origin",
            "Cache-Control": "max-age=0"
        }
        
        # Add referer if provided
        if referer:
            headers["Referer"] = referer
        
        # Browser-specific headers
        if self.current_user_agent and self.current_user_agent.browser == "Chrome":
            headers["sec-ch-ua"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
            headers["sec-ch-ua-mobile"] = "?0" if "Mobile" not in self.current_user_agent.user_agent else "?1"
            headers["sec-ch-ua-platform"] = f'"{self.current_user_agent.os}"'
        
        # Add some randomization to avoid fingerprinting
        if random.random() < 0.3:  # 30% chance to add optional headers
            optional_headers = {
                "Accept-CH": "DPR,Width,Viewport-Width",
                "Sec-GPC": "1",
            }
            headers.update(random.sample(list(optional_headers.items()), k=1))
        
        return headers
    
    # =============================================================================
    # BEHAVIORAL SIMULATION
    # =============================================================================
    
    def get_human_delay(self, base_delay: float = 2.0) -> float:
        """Generate human-like delay patterns"""
        
        # Human behavior simulation
        behavior_type = random.choices(
            ["focused", "distracted", "careful", "impatient"],
            weights=[0.4, 0.2, 0.25, 0.15]
        )[0]
        
        if behavior_type == "focused":
            # Consistent, slightly faster than base
            delay = base_delay * random.uniform(0.8, 1.2)
        elif behavior_type == "distracted":
            # Occasional long pauses
            if random.random() < 0.2:
                delay = base_delay * random.uniform(3.0, 8.0)  # Long pause
            else:
                delay = base_delay * random.uniform(1.0, 1.5)
        elif behavior_type == "careful":
            # Slower, more deliberate
            delay = base_delay * random.uniform(1.5, 2.5)
        else:  # impatient
            # Faster, but with occasional rapid bursts
            delay = base_delay * random.uniform(0.5, 1.0)
        
        # Add small random jitter to avoid exact timing patterns
        jitter = random.uniform(-0.3, 0.3)
        return max(0.5, delay + jitter)  # Minimum 0.5 second delay
    
    def simulate_reading_time(self, content_length: int) -> float:
        """Simulate realistic reading time based on content length"""
        
        # Average reading speed: 200-300 words per minute
        # Assume ~5 characters per word
        estimated_words = content_length / 5
        reading_speed_wpm = random.uniform(200, 300)
        
        # Base reading time in seconds
        base_reading_time = (estimated_words / reading_speed_wpm) * 60
        
        # Add variance for different user types
        user_type = random.choices(
            ["skimmer", "normal", "thorough"],
            weights=[0.3, 0.5, 0.2]
        )[0]
        
        if user_type == "skimmer":
            reading_time = base_reading_time * random.uniform(0.2, 0.5)
        elif user_type == "thorough":
            reading_time = base_reading_time * random.uniform(1.5, 2.5)
        else:  # normal
            reading_time = base_reading_time * random.uniform(0.8, 1.5)
        
        # Minimum and maximum bounds
        return max(2.0, min(60.0, reading_time))
    
    # =============================================================================
    # DETECTION MONITORING
    # =============================================================================
    
    def analyze_response(self, response_status: int, response_headers: Dict[str, str], 
                        response_content: str, response_time: float) -> DetectionRiskLevel:
        """Analyze response for potential detection indicators"""
        
        risk_indicators = []
        risk_score = 0.0
        
        # Status code analysis
        if response_status == 429:  # Too Many Requests
            risk_indicators.append("Rate limit detected")
            risk_score += 0.4
        elif response_status in [403, 406]:  # Forbidden/Not Acceptable
            risk_indicators.append("Access denied - possible detection")
            risk_score += 0.3
        elif response_status in [503, 502]:  # Service unavailable
            risk_indicators.append("Service unavailable - possible overload")
            risk_score += 0.2
        
        # Response header analysis
        if "cloudflare" in response_headers.get("Server", "").lower():
            if "cf-ray" in response_headers:
                risk_indicators.append("Cloudflare protection detected")
                risk_score += 0.1
        
        # Content analysis (look for bot detection indicators)
        content_lower = response_content.lower()
        bot_detection_keywords = [
            "captcha", "recaptcha", "bot detected", "automated traffic",
            "suspicious activity", "blocked", "access denied", "rate limit"
        ]
        
        for keyword in bot_detection_keywords:
            if keyword in content_lower:
                risk_indicators.append(f"Bot detection keyword found: {keyword}")
                risk_score += 0.2
        
        # Response time analysis (too fast might indicate cached/automated response)
        if response_time < 0.1:
            risk_indicators.append("Unusually fast response time")
            risk_score += 0.1
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = DetectionRiskLevel.CRITICAL
        elif risk_score >= 0.4:
            risk_level = DetectionRiskLevel.HIGH
        elif risk_score >= 0.2:
            risk_level = DetectionRiskLevel.MEDIUM
        else:
            risk_level = DetectionRiskLevel.LOW
        
        # Log detection incident if significant
        if risk_level != DetectionRiskLevel.LOW:
            incident = {
                "timestamp": datetime.utcnow(),
                "risk_level": risk_level,
                "risk_score": risk_score,
                "indicators": risk_indicators,
                "response_status": response_status,
                "user_agent": self.current_user_agent.user_agent if self.current_user_agent else "Unknown"
            }
            self.detection_incidents.append(incident)
            
            # Update user agent detection count
            if self.current_user_agent:
                self.current_user_agent.detection_incidents += 1
            
            logger.warning(f"⚠️ Detection risk {risk_level.value}: {risk_indicators}")
        
        self.current_risk_level = risk_level
        return risk_level
    
    def get_adaptive_delay(self, base_delay: float) -> float:
        """Get adaptive delay based on current risk level"""
        
        risk_multipliers = {
            DetectionRiskLevel.LOW: 1.0,
            DetectionRiskLevel.MEDIUM: 1.5,
            DetectionRiskLevel.HIGH: 2.5,
            DetectionRiskLevel.CRITICAL: 4.0
        }
        
        multiplier = risk_multipliers.get(self.current_risk_level, 1.0)
        adaptive_delay = base_delay * multiplier
        
        # Add human-like randomization
        return self.get_human_delay(adaptive_delay)
    
    # =============================================================================
    # SESSION MANAGEMENT
    # =============================================================================
    
    def should_pause_session(self) -> Tuple[bool, float]:
        """Determine if session should be paused to avoid detection"""
        
        session_duration = (datetime.utcnow() - self.session_start).total_seconds()
        
        # Check various pause conditions
        should_pause = False
        pause_duration = 0.0
        
        # Long session pause (simulate human taking breaks)
        if session_duration > self.session_duration_limits["max"]:
            should_pause = True
            pause_duration = random.uniform(300, 900)  # 5-15 minute break
            logger.info(f"📴 Taking long session break: {pause_duration:.1f} seconds")
        
        # High detection risk pause
        elif self.current_risk_level == DetectionRiskLevel.CRITICAL:
            should_pause = True
            pause_duration = random.uniform(600, 1800)  # 10-30 minute pause
            logger.warning(f"🛑 Critical detection risk - pausing: {pause_duration:.1f} seconds")
        
        # Too many detection incidents
        elif len(self.detection_incidents) >= 5:
            recent_incidents = [
                inc for inc in self.detection_incidents 
                if datetime.utcnow() - inc["timestamp"] < timedelta(minutes=30)
            ]
            if len(recent_incidents) >= 3:
                should_pause = True
                pause_duration = random.uniform(1800, 3600)  # 30-60 minute pause
                logger.warning(f"🚨 Too many detection incidents - long pause: {pause_duration:.1f} seconds")
        
        return should_pause, pause_duration
    
    def reset_session(self):
        """Reset session state for new scraping session"""
        
        self.session_start = datetime.utcnow()
        self.request_count = 0
        self.current_risk_level = DetectionRiskLevel.LOW
        self.detection_incidents = []
        
        # Force user agent rotation for new session
        self._rotate_user_agent()
        
        logger.info(f"🔄 Session reset for {self.source_name}")
    
    # =============================================================================
    # REQUEST TRACKING
    # =============================================================================
    
    def track_request(self, url: str, method: str = "GET"):
        """Track request for pattern analysis"""
        
        self.request_count += 1
        
        request_record = {
            "timestamp": datetime.utcnow(),
            "url": url,
            "method": method,
            "user_agent": self.current_user_agent.user_agent if self.current_user_agent else "Unknown",
            "request_number": self.request_count
        }
        
        self.request_history.append(request_record)
        
        # Maintain history size limit
        if len(self.request_history) > self.max_history_size:
            self.request_history = self.request_history[-self.max_history_size:]
    
    def get_request_statistics(self) -> Dict[str, Any]:
        """Get statistics about request patterns"""
        
        if not self.request_history:
            return {}
        
        session_duration = (datetime.utcnow() - self.session_start).total_seconds()
        requests_per_minute = (self.request_count / max(session_duration / 60, 1))
        
        return {
            "session_duration_seconds": session_duration,
            "total_requests": self.request_count,
            "requests_per_minute": round(requests_per_minute, 2),
            "current_risk_level": self.current_risk_level.value,
            "detection_incidents": len(self.detection_incidents),
            "current_user_agent": self.current_user_agent.browser if self.current_user_agent else "Unknown",
            "user_agent_rotations": sum(1 for ua in self.user_agents if ua.last_used is not None)
        }
    
    # =============================================================================
    # CONFIGURATION METHODS
    # =============================================================================
    
    def update_config(self, config_updates: Dict[str, Any]):
        """Update configuration parameters"""
        
        self.config.update(config_updates)
        
        # Apply specific configuration updates
        if "user_agent_rotation_frequency" in config_updates:
            self.user_agent_rotation_frequency = config_updates["user_agent_rotation_frequency"]
        
        if "session_duration" in config_updates:
            self.session_duration_limits.update(config_updates["session_duration"])
        
        logger.info(f"📝 Updated configuration for {self.source_name}")
    
    async def cleanup(self):
        """Cleanup resources and save state if needed"""
        
        stats = self.get_request_statistics()
        logger.info(f"🧹 Anti-detection cleanup for {self.source_name}: {stats}")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_anti_detection_manager(source_name: str, config: Optional[Dict[str, Any]] = None) -> AntiDetectionManager:
    """Factory function to create anti-detection manager"""
    
    # Default configuration based on source
    default_configs = {
        "indiabix": {
            "user_agent_rotation_frequency": 25,
            "session_duration": {"min": 180, "max": 1200},  # 3-20 minutes
            "human_behavior": {"reading_time_multiplier": 1.2}
        },
        "geeksforgeeks": {
            "user_agent_rotation_frequency": 35,
            "session_duration": {"min": 240, "max": 1800},  # 4-30 minutes
            "human_behavior": {"reading_time_multiplier": 1.0}
        }
    }
    
    source_config = default_configs.get(source_name.lower(), {})
    if config:
        source_config.update(config)
    
    return AntiDetectionManager(source_name, source_config)