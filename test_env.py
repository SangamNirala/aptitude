#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

from dotenv import load_dotenv

print('Current working directory:', os.getcwd())
print('Script path:', Path(__file__).parent)

# Try different paths
backend_env = Path('/app/backend/.env')
print('Backend env file exists:', backend_env.exists())

if backend_env.exists():
    load_dotenv(backend_env)
    print('After loading backend .env:')
    print('GEMINI_API_KEY:', os.getenv('GEMINI_API_KEY', 'NOT FOUND')[:20] + '...' if os.getenv('GEMINI_API_KEY') else 'NOT FOUND')
    print('GROQ_API_KEY:', os.getenv('GROQ_API_KEY', 'NOT FOUND')[:20] + '...' if os.getenv('GROQ_API_KEY') else 'NOT FOUND')
    print('HUGGINGFACE_API_TOKEN:', os.getenv('HUGGINGFACE_API_TOKEN', 'NOT FOUND')[:20] + '...' if os.getenv('HUGGINGFACE_API_TOKEN') else 'NOT FOUND')

    # Test AI service initialization
    try:
        from ai_services.gemini_service import GeminiService
        gemini = GeminiService()
        print('✅ GeminiService initialized successfully')
    except Exception as e:
        print(f'❌ GeminiService failed: {str(e)}')