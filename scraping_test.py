#!/usr/bin/env python3
"""
Scraping Foundation Testing
Tests the newly implemented scraping models, configurations, and services
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingFoundationTester:
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "critical_issues": []
        }
        
    def log_test_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name} - PASSED: {details}")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} - FAILED: {details}")
            if "critical" in details.lower() or "import" in details.lower():
                self.test_results["critical_issues"].append(f"{test_name}: {details}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def test_model_imports(self):
        """Test that all new scraping models can be imported"""
        logger.info("🔍 Testing Model Imports...")
        
        # Test scraping models import
        try:
            from models.scraping_models import (
                DataSourceConfig, ScrapingTarget, ScrapingJob, 
                RawExtractedQuestion, ProcessedScrapedQuestion,
                ScrapingQualityMetrics, CreateScrapingJobRequest,
                ScrapingJobResponse, SourceReliabilityReport
            )
            self.log_test_result("Scraping Models Import", True, "All scraping models imported successfully")
        except Exception as e:
            self.log_test_result("Scraping Models Import", False, f"Import error: {str(e)}")
        
        # Test analytics models import
        try:
            from models.analytics_models import (
                ScrapingSourceAnalytics, ScrapingJobAnalytics,
                ContentQualityAnalytics, ScrapingSystemHealth
            )
            self.log_test_result("Analytics Models Import", True, "Scraping analytics models imported successfully")
        except Exception as e:
            self.log_test_result("Analytics Models Import", False, f"Import error: {str(e)}")
    
    def test_model_instantiation(self):
        """Test that models can be instantiated with valid data"""
        logger.info("🏗️ Testing Model Instantiation...")
        
        try:
            from models.scraping_models import DataSourceConfig, ScrapingSourceType, ContentExtractionMethod
            
            # Test DataSourceConfig instantiation
            config = DataSourceConfig(
                name="Test Source",
                source_type=ScrapingSourceType.INDIABIX,
                base_url="https://test.com",
                extraction_method=ContentExtractionMethod.SELENIUM
            )
            
            success = (
                config.name == "Test Source" and
                config.source_type == ScrapingSourceType.INDIABIX and
                config.base_url == "https://test.com" and
                config.is_active == True and
                config.rate_limit_delay == 2.0
            )
            
            details = f"Created DataSourceConfig with ID: {config.id}"
            self.log_test_result("DataSourceConfig Instantiation", success, details)
            
        except Exception as e:
            self.log_test_result("DataSourceConfig Instantiation", False, f"Instantiation error: {str(e)}")
        
        try:
            from models.scraping_models import ScrapingTarget
            
            # Test ScrapingTarget instantiation
            target = ScrapingTarget(
                source_id="test-source-123",
                category="quantitative",
                subcategory="arithmetic",
                target_url="https://test.com/arithmetic"
            )
            
            success = (
                target.source_id == "test-source-123" and
                target.category == "quantitative" and
                target.is_active == True and
                target.priority == 1
            )
            
            details = f"Created ScrapingTarget with ID: {target.id}"
            self.log_test_result("ScrapingTarget Instantiation", success, details)
            
        except Exception as e:
            self.log_test_result("ScrapingTarget Instantiation", False, f"Instantiation error: {str(e)}")
    
    def test_configuration_loading(self):
        """Test that scraping configurations load correctly"""
        logger.info("⚙️ Testing Configuration Loading...")
        
        try:
            from config.scraping_config import (
                get_source_config, get_source_targets, 
                get_quality_thresholds, get_anti_detection_config,
                INDIABIX_CONFIG, GEEKSFORGEEKS_CONFIG
            )
            
            # Test IndiaBix config loading
            indiabix_config = get_source_config("indiabix")
            success = (
                indiabix_config.name == "IndiaBix" and
                indiabix_config.base_url == "https://www.indiabix.com" and
                len(indiabix_config.selectors) > 0 and
                indiabix_config.rate_limit_delay == 3.0
            )
            
            details = f"IndiaBix config loaded with {len(indiabix_config.selectors)} selectors"
            self.log_test_result("IndiaBix Configuration Loading", success, details)
            
        except Exception as e:
            self.log_test_result("IndiaBix Configuration Loading", False, f"Config error: {str(e)}")
        
        try:
            # Test GeeksforGeeks config loading
            geeks_config = get_source_config("geeksforgeeks")
            success = (
                geeks_config.name == "GeeksforGeeks" and
                geeks_config.base_url == "https://www.geeksforgeeks.org" and
                len(geeks_config.selectors) > 0 and
                geeks_config.rate_limit_delay == 2.5
            )
            
            details = f"GeeksforGeeks config loaded with {len(geeks_config.selectors)} selectors"
            self.log_test_result("GeeksforGeeks Configuration Loading", success, details)
            
        except Exception as e:
            self.log_test_result("GeeksforGeeks Configuration Loading", False, f"Config error: {str(e)}")
        
        try:
            # Test targets loading
            indiabix_targets = get_source_targets("indiabix")
            geeks_targets = get_source_targets("geeksforgeeks")
            
            success = (
                len(indiabix_targets) > 0 and
                len(geeks_targets) > 0 and
                all(target.category in ["quantitative", "logical", "verbal"] for target in indiabix_targets) and
                all(target.priority >= 1 for target in indiabix_targets)
            )
            
            details = f"Loaded {len(indiabix_targets)} IndiaBix targets, {len(geeks_targets)} GeeksforGeeks targets"
            self.log_test_result("Scraping Targets Loading", success, details)
            
        except Exception as e:
            self.log_test_result("Scraping Targets Loading", False, f"Targets error: {str(e)}")
    
    async def test_database_integration(self):
        """Test database integration and MongoDB connection"""
        logger.info("💾 Testing Database Integration...")
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            # Test MongoDB connection
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'test_database')]
            
            # Test connection
            await db.command("ping")
            self.log_test_result("MongoDB Connection", True, f"Connected to MongoDB at {mongo_url}")
            
            # Test collections creation
            collections_to_test = [
                'scraping_sources', 'scraping_targets', 'source_reliability',
                'scraping_jobs', 'raw_extracted_questions', 'processed_scraped_questions'
            ]
            
            for collection_name in collections_to_test:
                collection = db[collection_name]
                # Insert a test document
                test_doc = {"test": True, "created_at": datetime.utcnow()}
                result = await collection.insert_one(test_doc)
                
                # Clean up test document
                await collection.delete_one({"_id": result.inserted_id})
                
            self.log_test_result("Database Collections", True, f"Successfully tested {len(collections_to_test)} collections")
            
            client.close()
            
        except Exception as e:
            self.log_test_result("Database Integration", False, f"Database error: {str(e)}")
    
    async def test_source_management_service(self):
        """Test the source management service"""
        logger.info("🔧 Testing Source Management Service...")
        
        try:
            from services.source_management_service import SourceManagementService
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            # Setup database connection
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'test_database')]
            
            # Initialize service
            service = SourceManagementService(db)
            
            # Test service initialization
            self.log_test_result("Source Management Service Init", True, "Service initialized successfully")
            
            # Test getting all sources (should work even if empty)
            sources = await service.get_all_sources()
            self.log_test_result("Get All Sources", True, f"Retrieved {len(sources)} sources")
            
            # Test source health check methods
            health_reports = await service.check_all_sources_health()
            self.log_test_result("Source Health Check", True, f"Generated health reports for {len(health_reports)} sources")
            
            # Test target statistics
            stats = await service.get_target_statistics()
            success = isinstance(stats, dict)
            self.log_test_result("Target Statistics", success, f"Generated statistics: {len(stats)} entries")
            
            client.close()
            
        except Exception as e:
            self.log_test_result("Source Management Service", False, f"Service error: {str(e)}")
    
    def test_enum_validations(self):
        """Test enum validations and constraints"""
        logger.info("🔒 Testing Enum Validations...")
        
        try:
            from models.scraping_models import (
                ScrapingSourceType, ScrapingJobStatus, 
                ContentExtractionMethod, QualityGate
            )
            
            # Test enum values
            source_types = list(ScrapingSourceType)
            job_statuses = list(ScrapingJobStatus)
            extraction_methods = list(ContentExtractionMethod)
            quality_gates = list(QualityGate)
            
            success = (
                len(source_types) >= 3 and
                ScrapingSourceType.INDIABIX in source_types and
                ScrapingSourceType.GEEKSFORGEEKS in source_types and
                ScrapingJobStatus.PENDING in job_statuses and
                ContentExtractionMethod.SELENIUM in extraction_methods and
                QualityGate.AUTO_APPROVE in quality_gates
            )
            
            details = f"Validated {len(source_types)} source types, {len(job_statuses)} job statuses"
            self.log_test_result("Enum Validations", success, details)
            
        except Exception as e:
            self.log_test_result("Enum Validations", False, f"Enum error: {str(e)}")
    
    def test_request_response_models(self):
        """Test API request/response models"""
        logger.info("📡 Testing Request/Response Models...")
        
        try:
            from models.scraping_models import (
                CreateScrapingJobRequest, ScrapingJobResponse,
                ScrapingJobStatusResponse, BulkScrapingRequest
            )
            
            # Test CreateScrapingJobRequest
            job_request = CreateScrapingJobRequest(
                job_name="Test Scraping Job",
                description="Test job for validation",
                source_names=["indiabix", "geeksforgeeks"],
                max_questions_per_source=500,
                quality_threshold=75.0
            )
            
            success = (
                job_request.job_name == "Test Scraping Job" and
                len(job_request.source_names) == 2 and
                job_request.max_questions_per_source == 500 and
                job_request.enable_ai_processing == True
            )
            
            self.log_test_result("CreateScrapingJobRequest", success, "Request model validation passed")
            
            # Test ScrapingJobResponse
            job_response = ScrapingJobResponse(
                job_id="test-job-123",
                status="pending",
                message="Job created successfully",
                created_at=datetime.utcnow()
            )
            
            success = (
                job_response.job_id == "test-job-123" and
                job_response.status == "pending" and
                isinstance(job_response.created_at, datetime)
            )
            
            self.log_test_result("ScrapingJobResponse", success, "Response model validation passed")
            
        except Exception as e:
            self.log_test_result("Request/Response Models", False, f"Model error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all scraping foundation tests"""
        logger.info("🚀 Starting Scraping Foundation Testing...")
        start_time = datetime.utcnow()
        
        # Run all test suites
        self.test_model_imports()
        self.test_model_instantiation()
        self.test_configuration_loading()
        await self.test_database_integration()
        await self.test_source_management_service()
        self.test_enum_validations()
        self.test_request_response_models()
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 SCRAPING FOUNDATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed_tests']}")
        logger.info(f"❌ Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {(self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("=" * 60)
        
        # Show critical issues
        if self.test_results["critical_issues"]:
            logger.error("🚨 CRITICAL ISSUES:")
            for issue in self.test_results["critical_issues"]:
                logger.error(f"  - {issue}")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results["test_details"] if not t["success"]]
        if failed_tests:
            logger.info("❌ FAILED TESTS:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results

async def main():
    """Main test execution"""
    tester = ScrapingFoundationTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    import json
    with open('/app/scraping_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("📊 Scraping test results saved to scraping_test_results.json")
    
    # Return exit code based on results
    if results["failed_tests"] > 0:
        logger.error("Some scraping foundation tests failed!")
        return 1
    else:
        logger.info("All scraping foundation tests passed! 🎉")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)