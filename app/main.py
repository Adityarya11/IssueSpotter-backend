from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
import logging

# API Routers
from app.api.v1.moderation import router as moderation_router
from app.api.v1.dashboard import router as dashboard_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IssueSpotter AI Guardian",
    description="Lightweight AI-powered content moderation microservice for images, videos, and text",
    version="1.0.0",
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(moderation_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    """Initialize AI Guardian services on startup"""
    logger.info("🛡️ Starting IssueSpotter AI Guardian...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info("✅ AI Guardian Ready")

@app.get("/")
async def root():
    return {
        "service": "IssueSpotter AI Guardian",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-powered content moderation for images, videos, and text"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-guardian",
        "models": {
            "text_embedder": "all-MiniLM-L6-v2",
            "image_embedder": "CLIP ViT-B/32",
            "image_analyzer": "NudeNet",
            "video_analyzer": "enabled"
        }
    }