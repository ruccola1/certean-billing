"""
Certean Billing Backend Service
Separate service for Stripe billing and subscription management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import MongoDB
from backend.api import stripe_routes
from backend.config import settings
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Certean Billing API",
    description="Stripe billing and subscription management service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Stripe routes
app.include_router(stripe_routes.router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("🚀 Starting Certean Billing Service...")
        
        # Connect to MongoDB
        try:
            await MongoDB.connect()
            logger.info("✅ MongoDB connected")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            logger.warning("⚠️ Continuing startup despite MongoDB connection failure")
        
        logger.info("✅ Billing service initialized")
    except Exception as e:
        logger.error(f"❌ Error during application startup: {e}")
        import traceback
        logger.error(traceback.format_exc())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await MongoDB.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "certean-billing",
        "database": "connected" if MongoDB.client else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)

