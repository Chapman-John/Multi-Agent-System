"""
Startup script for the Multi-Agent AI System
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings

def main():
    """Main entry point for the application"""
    
    # Determine port from environment or use default (changed from 5000 to 8000)
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Print startup information
    print(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"📡 Server will be available at: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    
    # Check for required API keys
    missing_keys = []
    if not settings.OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
    if not settings.ANTHROPIC_API_KEY:
        missing_keys.append("ANTHROPIC_API_KEY")
    
    if missing_keys:
        print(f"⚠️  Warning: Missing required API keys: {', '.join(missing_keys)}")
        print("   Please check your .env file")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=settings.DEBUG
    )

if __name__ == "__main__":
    main()