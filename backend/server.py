from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Import AI-enhanced routers (fix relative imports)
from routers.ai_enhanced_questions import router as ai_questions_router
# Import scraping management routers (Task 14 & 15)
from routers.scraping_management import router as scraping_management_router
from routers.scraping_analytics import router as scraping_analytics_router
# Import monitoring dashboard router (Task 16)
from routers.monitoring_dashboard import router as monitoring_dashboard_router
# Import performance optimization router (Task 18)
from routers.performance_optimization import router as performance_optimization_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="AI-Enhanced Aptitude Questions API",
    description="World-class AI-powered aptitude questions platform with Gemini, Groq, and HuggingFace integration",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models (keeping existing ones for compatibility)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Original routes (keeping for compatibility)
@api_router.get("/")
async def root():
    return {
        "message": "AI-Enhanced Aptitude Questions API v2.0", 
        "features": [
            "AI Question Generation (Gemini)",
            "Ultra-fast Feedback (Groq)", 
            "Smart Categorization (HuggingFace)",
            "Personalized Learning",
            "Company-specific Patterns",
            "Real-time Analytics"
        ]
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Health check for AI services
@api_router.get("/health")
async def health_check():
    """Health check endpoint for AI services"""
    try:
        # Check MongoDB connection
        await db.command("ping")
        mongo_status = "healthy"
    except Exception:
        mongo_status = "unhealthy"
    
    # Check AI service availability (basic check)
    ai_services_status = {
        "gemini": "available" if os.getenv('GEMINI_API_KEY') else "not_configured",
        "groq": "available" if os.getenv('GROQ_API_KEY') else "not_configured", 
        "huggingface": "available" if os.getenv('HUGGINGFACE_API_TOKEN') else "not_configured"
    }
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "ai_services": ai_services_status,
        "timestamp": datetime.utcnow()
    }

# Include the original router
app.include_router(api_router)

# Include AI-enhanced question router  
app.include_router(ai_questions_router)

# Include scraping management routers (Task 14 & 15)
app.include_router(scraping_management_router)
app.include_router(scraping_analytics_router)

# Include monitoring dashboard router (Task 16)
app.include_router(monitoring_dashboard_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize AI services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize AI services and check configuration"""
    logger.info("🚀 Starting AI-Enhanced Aptitude Questions API")
    
    # Verify AI API keys
    required_keys = ['GEMINI_API_KEY', 'GROQ_API_KEY', 'HUGGINGFACE_API_TOKEN']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        logger.warning(f"Missing AI API keys: {missing_keys}")
    else:
        logger.info("✅ All AI API keys configured successfully")
    
    # Test MongoDB connection
    try:
        await db.command("ping")
        logger.info("✅ MongoDB connection established")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
    
    # Initialize scraping services
    try:
        from routers.scraping_management import initialize_scraping_services
        from routers.scraping_analytics import initialize_analytics_services
        # Import monitoring dashboard initialization (Task 16)
        from routers.monitoring_dashboard import initialize_monitoring_services
        
        await initialize_scraping_services()
        await initialize_analytics_services()
        await initialize_monitoring_services()
        logger.info("✅ Scraping and monitoring services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Services initialization failed: {str(e)}")
    
    # Create indexes for performance
    try:
        # Index for question filtering
        await db.enhanced_questions.create_index([("category", 1), ("difficulty", 1), ("is_active", 1)])
        await db.enhanced_questions.create_index([("ai_metrics.quality_score", -1)])
        await db.enhanced_questions.create_index([("metadata.company_patterns", 1)])
        await db.enhanced_questions.create_index([("metadata.concepts", 1)])
        
        # Index for analytics
        await db.question_attempts.create_index([("question_id", 1), ("timestamp", -1)])
        
        logger.info("✅ Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {str(e)}")
    
    logger.info("🎯 AI-Enhanced API startup completed successfully!")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("👋 AI-Enhanced API shutdown completed")
