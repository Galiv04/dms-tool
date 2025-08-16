# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.routers import health, auth, documents, approval, admin
from app.configurations import settings
from app.services.scheduler import get_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestione ciclo di vita applicazione"""
    # Startup
    logger.info(f"🚀 Starting {settings.app_name}...")
    
    # Avvia scheduler
    try:
        scheduler = get_scheduler()
        scheduler.start_scheduler()
        logger.info("✅ Task Scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info(f"🔄 Shutting down {settings.app_name}...")
    try:
        scheduler = get_scheduler()
        scheduler.stop_scheduler()
        logger.info("✅ Task Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan  # ✅ Aggiungi gestione scheduler
)

# Serve static files
app.mount("/static", StaticFiles(directory=settings.static_files_path), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(documents.router, tags=["documents"])
app.include_router(approval.router, tags=["approvals"])
app.include_router(admin.router, tags=["admin"])  # ✅ Aggiungi admin router

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "features": settings.app_features
    }

@app.get("/favicon.ico")
async def favicon():
    return {"message": "Favicon not configured"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
