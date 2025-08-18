#!/usr/bin/env python3
"""
Detailed Monitoring Dashboard Testing - Investigate Validation Issues
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DetailedMonitoringTester:
    def __init__(self):
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=')[1].strip() + "/api"
                        break
                else:
                    self.base_url = "https://aptitude-test-repair.preview.emergentagent.com/api"
        except:
            self.base_url = "https://aptitude-test-repair.preview.emergentagent.com/api"
        
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_monitoring_status_detailed(self):
        """Detailed test of monitoring status endpoint"""
        logger.info("🔍 DETAILED TEST: Monitoring System Status")
        
        try:
            async with self.session.get(f"{self.base_url}/monitoring/status") as response:
                logger.info(f"Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Response Data: {json.dumps(data, indent=2, default=str)}")
                    
                    # Check each expected field
                    logger.info("Field Analysis:")
                    logger.info(f"  - status: {data.get('status')} (expected: string)")
                    logger.info(f"  - services: {data.get('services')} (expected: dict/object)")
                    logger.info(f"  - timestamp: {data.get('timestamp')} (expected: datetime)")
                    logger.info(f"  - uptime_hours: {data.get('uptime_hours')} (expected: float)")
                    logger.info(f"  - active_connections: {data.get('active_connections')} (expected: int)")
                    logger.info(f"  - events_processed: {data.get('events_processed')} (expected: int)")
                    logger.info(f"  - alerts_active: {data.get('alerts_active')} (expected: int)")
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Error Response: {error_text}")
                    
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
    
    async def test_performance_metrics_detailed(self):
        """Detailed test of performance metrics endpoint"""
        logger.info("🔍 DETAILED TEST: Performance Metrics")
        
        try:
            async with self.session.get(f"{self.base_url}/monitoring/metrics") as response:
                logger.info(f"Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Response Data: {json.dumps(data, indent=2, default=str)}")
                    
                    # Check each expected field
                    logger.info("Field Analysis:")
                    logger.info(f"  - timestamp: {data.get('timestamp')} (expected: datetime)")
                    logger.info(f"  - uptime_hours: {data.get('uptime_hours')} (expected: float)")
                    logger.info(f"  - metrics: {data.get('metrics')} (expected: dict/object)")
                    logger.info(f"  - cpu_usage: {data.get('cpu_usage')} (expected: float)")
                    logger.info(f"  - memory_usage: {data.get('memory_usage')} (expected: float)")
                    logger.info(f"  - disk_usage: {data.get('disk_usage')} (expected: float)")
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Error Response: {error_text}")
                    
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
    
    async def test_create_alert_detailed(self):
        """Detailed test of create alert endpoint"""
        logger.info("🔍 DETAILED TEST: Create Alert")
        
        try:
            payload = {
                "title": "Test Alert for Detailed Analysis",
                "description": "This is a detailed test alert",
                "severity": "warning",
                "category": "system",
                "source": "detailed_test",
                "metadata": {"test": True},
                "tags": ["test", "detailed"]
            }
            
            logger.info(f"Request Payload: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(
                f"{self.base_url}/monitoring/alerts",
                json=payload
            ) as response:
                logger.info(f"Status Code: {response.status}")
                
                if response.status in [200, 201]:
                    data = await response.json()
                    logger.info(f"Response Data: {json.dumps(data, indent=2, default=str)}")
                    
                    # Check each expected field
                    logger.info("Field Analysis:")
                    logger.info(f"  - id: {data.get('id')} (expected: string)")
                    logger.info(f"  - title: {data.get('title')} (expected: '{payload['title']}')")
                    logger.info(f"  - severity: {data.get('severity')} (expected: '{payload['severity']}')")
                    logger.info(f"  - category: {data.get('category')} (expected: '{payload['category']}')")
                    logger.info(f"  - status: {data.get('status')} (expected: string)")
                    logger.info(f"  - created_at: {data.get('created_at')} (expected: datetime)")
                    
                    # Test validation logic
                    validation_checks = [
                        ("id" in data, "id field present"),
                        ("title" in data, "title field present"),
                        (data.get("title") == payload["title"], "title matches"),
                        (data.get("severity") == payload["severity"], "severity matches")
                    ]
                    
                    logger.info("Validation Checks:")
                    for check, description in validation_checks:
                        logger.info(f"  - {description}: {'✅ PASS' if check else '❌ FAIL'}")
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Error Response: {error_text}")
                    
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
    
    async def test_websocket_detailed(self):
        """Detailed test of WebSocket endpoint"""
        logger.info("🔍 DETAILED TEST: WebSocket Connection")
        
        try:
            # Try different WebSocket libraries and approaches
            logger.info("Testing WebSocket connectivity...")
            
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://") + "/monitoring/ws"
            logger.info(f"WebSocket URL: {ws_url}")
            
            # Test 1: Try with websockets library
            try:
                import websockets
                logger.info("✅ websockets library available")
                
                # Test connection without timeout parameter
                try:
                    async with websockets.connect(ws_url) as websocket:
                        logger.info("✅ WebSocket connection established")
                        
                        # Try to receive a message
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            logger.info(f"✅ Received message: {message[:100]}...")
                        except asyncio.TimeoutError:
                            logger.info("⚠️ No immediate message received (this is normal)")
                        
                        logger.info("✅ WebSocket test completed successfully")
                        
                except Exception as ws_e:
                    logger.error(f"❌ WebSocket connection failed: {str(ws_e)}")
                    
            except ImportError:
                logger.error("❌ websockets library not available")
            
            # Test 2: Try with aiohttp WebSocket client
            try:
                logger.info("Testing with aiohttp WebSocket client...")
                async with self.session.ws_connect(ws_url) as ws:
                    logger.info("✅ aiohttp WebSocket connection established")
                    
                    # Try to receive a message
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                        logger.info(f"✅ Received message: {msg}")
                    except asyncio.TimeoutError:
                        logger.info("⚠️ No immediate message received (this is normal)")
                    
                    logger.info("✅ aiohttp WebSocket test completed successfully")
                    
            except Exception as aio_e:
                logger.error(f"❌ aiohttp WebSocket failed: {str(aio_e)}")
                
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
    
    async def run_detailed_tests(self):
        """Run all detailed tests"""
        logger.info("🚀 Starting Detailed Monitoring Dashboard Analysis...")
        logger.info(f"Testing backend at: {self.base_url}")
        logger.info("=" * 80)
        
        await self.test_monitoring_status_detailed()
        logger.info("=" * 80)
        
        await self.test_performance_metrics_detailed()
        logger.info("=" * 80)
        
        await self.test_create_alert_detailed()
        logger.info("=" * 80)
        
        await self.test_websocket_detailed()
        logger.info("=" * 80)
        
        logger.info("🎯 Detailed analysis completed!")

async def main():
    async with DetailedMonitoringTester() as tester:
        await tester.run_detailed_tests()

if __name__ == "__main__":
    asyncio.run(main())