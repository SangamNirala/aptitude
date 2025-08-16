# Routers package
from .ai_enhanced_questions import router as ai_questions_router
from .analytics_router import router as analytics_router
from .user_performance import router as performance_router

__all__ = [
    'ai_questions_router',
    'analytics_router', 
    'performance_router'
]