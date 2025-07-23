from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from config.env import Config
from api.router import router, initialize_components
import llm_router
from utils.logger import setup_logger

# Setup logging
logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting LangChain Project application...")
    try:
        # Initialize components
        initialize_components()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down LangChain Project application...")

# Create FastAPI app
app = FastAPI(
    title="LangChain Project API",
    description="A comprehensive LangChain-based application with RAG, Agents, and Vector Search capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)
app.include_router(llm_router.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to LangChain Project API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "langchain_project"}

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,  # Enable auto-reload for development
        log_level=Config.LOG_LEVEL.lower()
    )
