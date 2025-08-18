"""
Production Startup System
Comprehensive initialization and setup for production deployment
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import traceback
from datetime import datetime, timezone

from config.production_config import (
    get_production_config, 
    validate_production_readiness,
    production_config_manager
)
from utils.production_logging import setup_production_logging
from utils.error_tracking import setup_error_tracking, error_tracker
from utils.health_monitoring import setup_health_monitoring


class ProductionStartupManager:
    """Manages production system initialization and startup sequence"""
    
    def __init__(self):
        self.logger = None  # Will be initialized after logging setup
        self.config = None
        self.startup_errors: List[str] = []
        self.startup_warnings: List[str] = []
        self.initialization_status: Dict[str, bool] = {}
        
    async def initialize_production_system(self) -> bool:
        """
        Complete production system initialization
        Returns True if successful, False if critical failures
        """
        print("🚀 Starting AI-Enhanced Scraping System Production Initialization...")
        
        try:
            # Step 1: Load and validate configuration
            success = await self._initialize_configuration()
            if not success:
                return False
            
            # Step 2: Setup logging system
            success = await self._initialize_logging()
            if not success:
                return False
            
            # Get logger after logging setup
            self.logger = logging.getLogger(__name__)
            self.logger.info("🔧 Production startup initiated")
            
            # Step 3: Validate production readiness
            success = await self._validate_production_readiness()
            if not success:
                return False
            
            # Step 4: Initialize error tracking
            success = await self._initialize_error_tracking()
            if not success:
                return False
            
            # Step 5: Initialize monitoring systems
            success = await self._initialize_monitoring()
            if not success:
                return False
            
            # Step 6: Validate environment variables
            success = await self._validate_environment()
            if not success:
                return False
            
            # Step 7: Test database connectivity
            success = await self._test_database_connection()
            if not success:
                return False
            
            # Step 8: Initialize AI services
            success = await self._initialize_ai_services()
            if not success:
                return False
            
            # Step 9: Initialize scraping infrastructure
            success = await self._initialize_scraping_system()
            if not success:
                return False
            
            # Step 10: Final system validation
            success = await self._final_system_validation()
            if not success:
                return False
            
            # Report startup status
            await self._report_startup_status()
            
            return True
            
        except Exception as e:
            error_msg = f"Critical error during production startup: {str(e)}"
            print(f"❌ {error_msg}")
            if self.logger:
                self.logger.critical(error_msg, exc_info=True)
            return False
    
    async def _initialize_configuration(self) -> bool:
        """Initialize and validate production configuration"""
        try:
            print("📋 Loading production configuration...")
            
            # Load configuration
            self.config = get_production_config()
            
            # Validate configuration
            validation_report = production_config_manager.validate_configuration()
            
            if not validation_report["valid"]:
                for error in validation_report["errors"]:
                    self.startup_errors.append(f"Configuration error: {error}")
                print("❌ Configuration validation failed")
                return False
            
            # Log warnings
            for warning in validation_report["warnings"]:
                self.startup_warnings.append(f"Configuration warning: {warning}")
            
            self.initialization_status["configuration"] = True
            print("✅ Configuration loaded and validated")
            return True
            
        except Exception as e:
            error_msg = f"Configuration initialization failed: {str(e)}"
            self.startup_errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def _initialize_logging(self) -> bool:
        """Initialize production logging system"""
        try:
            print("📝 Initializing production logging...")
            
            # Create log directory
            log_dir = Path(self.config.logging.log_directory)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup production logging
            setup_production_logging()
            
            self.initialization_status["logging"] = True
            print("✅ Production logging initialized")
            return True
            
        except Exception as e:
            error_msg = f"Logging initialization failed: {str(e)}"
            self.startup_errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def _validate_production_readiness(self) -> bool:
        """Validate system readiness for production"""
        try:
            self.logger.info("🔍 Validating production readiness...")
            
            # Perform comprehensive validation
            is_ready = validate_production_readiness()
            
            if not is_ready:
                error_msg = "System not ready for production deployment"
                self.startup_errors.append(error_msg)
                self.logger.error(error_msg)
                return False
            
            self.initialization_status["production_validation"] = True
            self.logger.info("✅ Production readiness validated")
            return True
            
        except Exception as e:
            error_msg = f"Production validation failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _initialize_error_tracking(self) -> bool:
        """Initialize error tracking system"""
        try:
            self.logger.info("🔍 Initializing error tracking...")
            
            # Setup error tracking
            setup_error_tracking()
            
            # Test error tracking
            test_fingerprint = error_tracker.capture_message(
                "Production startup test message",
                category="system",
                severity="low"
            )
            
            if not test_fingerprint:
                raise Exception("Error tracking test failed")
            
            self.initialization_status["error_tracking"] = True
            self.logger.info("✅ Error tracking initialized")
            return True
            
        except Exception as e:
            error_msg = f"Error tracking initialization failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _initialize_monitoring(self) -> bool:
        """Initialize health monitoring system"""
        try:
            self.logger.info("📊 Initializing health monitoring...")
            
            # Setup health monitoring
            await setup_health_monitoring()
            
            # Test health monitoring
            from utils.health_monitoring import health_monitor
            health_summary = health_monitor.get_health_summary()
            
            if not health_summary:
                raise Exception("Health monitoring test failed")
            
            self.initialization_status["monitoring"] = True
            self.logger.info("✅ Health monitoring initialized")
            return True
            
        except Exception as e:
            error_msg = f"Health monitoring initialization failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _validate_environment(self) -> bool:
        """Validate critical environment variables"""
        try:
            self.logger.info("🔧 Validating environment variables...")
            
            # Required environment variables
            required_vars = [
                'MONGO_URL',
                'DB_NAME',
                'GEMINI_API_KEY',
                'GROQ_API_KEY',
                'HUGGINGFACE_API_TOKEN'
            ]
            
            missing_vars = []
            for var in required_vars:
                value = os.getenv(var)
                if not value:
                    missing_vars.append(var)
            
            if missing_vars:
                error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
                self.startup_errors.append(error_msg)
                self.logger.error(error_msg)
                return False
            
            # Validate API key formats (basic validation)
            api_keys = {
                'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
                'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
                'HUGGINGFACE_API_TOKEN': os.getenv('HUGGINGFACE_API_TOKEN')
            }
            
            for key_name, key_value in api_keys.items():
                if len(key_value) < 20:  # Basic length check
                    warning_msg = f"{key_name} appears to be invalid (too short)"
                    self.startup_warnings.append(warning_msg)
                    self.logger.warning(warning_msg)
            
            self.initialization_status["environment"] = True
            self.logger.info("✅ Environment variables validated")
            return True
            
        except Exception as e:
            error_msg = f"Environment validation failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _test_database_connection(self) -> bool:
        """Test database connectivity"""
        try:
            self.logger.info("🗄️ Testing database connection...")
            
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Test MongoDB connection
            mongo_url = os.getenv('MONGO_URL')
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            
            # Test connection with ping
            await client.admin.command('ping')
            
            # Test database access
            db_name = os.getenv('DB_NAME')
            db = client[db_name]
            
            # Simple test operation
            test_result = await db.command('buildInfo')
            if not test_result:
                raise Exception("Database test operation failed")
            
            client.close()
            
            self.initialization_status["database"] = True
            self.logger.info("✅ Database connection validated")
            return True
            
        except Exception as e:
            error_msg = f"Database connection test failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _initialize_ai_services(self) -> bool:
        """Initialize and test AI services"""
        try:
            self.logger.info("🤖 Initializing AI services...")
            
            # Test AI service imports and initialization
            try:
                from ai_services.gemini_service import GeminiService
                from ai_services.groq_service import GroqService
                
                # Basic initialization test (without actual API calls)
                gemini_service = GeminiService()
                groq_service = GroqService()
                
                self.logger.info("AI service classes loaded successfully")
                
            except ImportError as e:
                warning_msg = f"AI service import warning: {str(e)}"
                self.startup_warnings.append(warning_msg)
                self.logger.warning(warning_msg)
            
            self.initialization_status["ai_services"] = True
            self.logger.info("✅ AI services initialized")
            return True
            
        except Exception as e:
            error_msg = f"AI services initialization failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _initialize_scraping_system(self) -> bool:
        """Initialize scraping infrastructure"""
        try:
            self.logger.info("🕸️ Initializing scraping system...")
            
            # Test scraping system imports
            try:
                from scraping.scraper_engine import ScrapingEngine
                from services.source_management_service import SourceManagementService
                
                # Basic initialization test
                source_service = SourceManagementService()
                
                self.logger.info("Scraping system classes loaded successfully")
                
            except ImportError as e:
                warning_msg = f"Scraping system import warning: {str(e)}"
                self.startup_warnings.append(warning_msg)
                self.logger.warning(warning_msg)
            
            self.initialization_status["scraping_system"] = True
            self.logger.info("✅ Scraping system initialized")
            return True
            
        except Exception as e:
            error_msg = f"Scraping system initialization failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _final_system_validation(self) -> bool:
        """Perform final system validation"""
        try:
            self.logger.info("✅ Performing final system validation...")
            
            # Check all initialization statuses
            failed_components = [
                component for component, status in self.initialization_status.items()
                if not status
            ]
            
            if failed_components:
                error_msg = f"Failed components: {', '.join(failed_components)}"
                self.startup_errors.append(error_msg)
                self.logger.error(error_msg)
                return False
            
            # Test system health
            from utils.health_monitoring import health_monitor
            try:
                health_summary = health_monitor.get_health_summary()
                if health_summary.get("overall_status") == "critical":
                    warning_msg = "System health check shows critical status"
                    self.startup_warnings.append(warning_msg)
                    self.logger.warning(warning_msg)
            except Exception as e:
                warning_msg = f"Health check validation warning: {str(e)}"
                self.startup_warnings.append(warning_msg)
                self.logger.warning(warning_msg)
            
            self.initialization_status["final_validation"] = True
            self.logger.info("✅ Final system validation completed")
            return True
            
        except Exception as e:
            error_msg = f"Final system validation failed: {str(e)}"
            self.startup_errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    async def _report_startup_status(self):
        """Report final startup status"""
        try:
            startup_time = datetime.now(timezone.utc).isoformat()
            
            # Success summary
            successful_components = [
                component for component, status in self.initialization_status.items()
                if status
            ]
            
            self.logger.info(f"🎉 Production system startup completed successfully!")
            self.logger.info(f"✅ Initialized components: {', '.join(successful_components)}")
            
            if self.startup_warnings:
                self.logger.warning(f"⚠️ Startup warnings ({len(self.startup_warnings)}):")
                for warning in self.startup_warnings:
                    self.logger.warning(f"  - {warning}")
            
            # Log startup metrics
            self.logger.info("📊 Startup Summary:", extra={
                "event_type": "production_startup",
                "startup_time": startup_time,
                "successful_components": successful_components,
                "warning_count": len(self.startup_warnings),
                "error_count": len(self.startup_errors),
                "environment": self.config.environment.value,
                "app_version": self.config.version
            })
            
            print("🎉 AI-Enhanced Scraping System Production Startup Completed Successfully!")
            print(f"✅ Initialized {len(successful_components)} components")
            if self.startup_warnings:
                print(f"⚠️ {len(self.startup_warnings)} warnings logged")
            
        except Exception as e:
            error_msg = f"Startup status reporting failed: {str(e)}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            else:
                print(f"❌ {error_msg}")
    
    def get_startup_status(self) -> Dict[str, Any]:
        """Get current startup status"""
        return {
            "initialization_status": self.initialization_status,
            "startup_errors": self.startup_errors,
            "startup_warnings": self.startup_warnings,
            "total_components": len(self.initialization_status),
            "successful_components": sum(1 for status in self.initialization_status.values() if status),
            "failed_components": sum(1 for status in self.initialization_status.values() if not status)
        }


# Global startup manager instance
production_startup_manager = ProductionStartupManager()


async def initialize_production_system() -> bool:
    """Initialize production system - main entry point"""
    return await production_startup_manager.initialize_production_system()


def get_startup_status() -> Dict[str, Any]:
    """Get production startup status"""
    return production_startup_manager.get_startup_status()


# Production startup decorator for FastAPI
def production_startup_required(func):
    """Decorator to ensure production startup is completed"""
    def wrapper(*args, **kwargs):
        status = get_startup_status()
        if status["failed_components"] > 0:
            raise Exception("Production system not properly initialized")
        return func(*args, **kwargs)
    return wrapper