"""
FastAPI Main Application
AI Chatbot Backend for Meeting Room Management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .config import settings
from .routers import chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Chatbot Backend",
    description="Backend API for AI-powered meeting room chatbot with OpenAI Function Calling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Chatbot Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 AI Chatbot Backend starting up...")
    logger.info(f"📍 Environment: {settings.environment}")
    logger.info(f"🔗 Odoo URL: {settings.odoo_url}")
    logger.info(f"🤖 OpenAI Model: {settings.openai_model}")
    logger.info(f"🌐 CORS Origins: {settings.cors_origins}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 AI Chatbot Backend shutting down...")

# Run with: python -m app.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
