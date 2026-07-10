# backend/main.py

import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add paths for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import database and routes
from backend.database import init_database
from backend.api.routes import router as travel_api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Step 1: Boot up local database storage schemas
try:
    init_database()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    sys.exit(1)

# Step 2: Initialize the FastAPI Application Core Configuration
app = FastAPI(
    title="AI Multi-Agent Travel Platform Engine",
    description=(
        "Isolated backend computing network powering dynamic pricing, safety optimization, "
        "and structured multi-agent travel configurations natively."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Step 3: Configure CORS (Cross-Origin Resource Sharing)
# This allows your frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React default
        "http://localhost:5173",   # Vite default
        "http://localhost:4200",   # Angular default
        "http://localhost:8080",   # Vue default
        "http://localhost:5500",   # Live Server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Add Trusted Host middleware for security in production
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
# )

# Step 4: Connect and register your application routers
app.include_router(travel_api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint to verify the API is running.
    """
    return {
        "message": "🚀 Travel AI API is running!",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health-check", tags=["System Lifecycle Diagnostics"])
def perform_health_check():
    """
    Diagnostic system channel to verify that the backend engine 
    and database links are running perfectly.
    """
    return {
        "engine_status": "operational",
        "database_connectivity": "healthy",
        "active_version": "1.0.0",
        "status": "online"
    }


@app.get("/ping", tags=["System Lifecycle Diagnostics"])
def ping():
    """
    Simple ping endpoint for connectivity testing.
    """
    return {"ping": "pong", "timestamp": __import__("datetime").datetime.now().isoformat()}


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler - runs when the application starts.
    """
    logger.info("🚀 Travel AI API starting up...")
    logger.info(f"📚 API Documentation available at /docs")
    logger.info(f"🔗 Redoc available at /redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler - runs when the application stops.
    """
    logger.info("👋 Travel AI API shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    
    # Step 5: Run the ASGI server
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )