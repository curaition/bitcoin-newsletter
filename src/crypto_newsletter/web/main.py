"""FastAPI main application."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text

from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.logging.config import configure_logging, get_logger
from crypto_newsletter.shared.monitoring.metrics import get_metrics_collector
from crypto_newsletter.web.routers import admin, api, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()

    # Configure logging first
    configure_logging()
    app_logger = get_logger("web.main")

    # Initialize metrics collector
    metrics = get_metrics_collector()

    # Startup
    app_logger.info("Starting Crypto Newsletter API", extra={
        "environment": settings.railway_environment,
        "service_type": settings.service_type,
        "debug": settings.debug
    })

    # Verify database connection (non-blocking for startup)
    try:
        async with get_db_session() as db:
            await db.execute(text("SELECT 1"))
        app_logger.info("Database connection verified")
    except Exception as e:
        app_logger.warning("Database connection failed during startup", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        app_logger.info("Service will start anyway - database will be checked on first request")
    
    # Verify Celery connection (if enabled) - non-blocking for startup
    if settings.enable_celery:
        try:
            from crypto_newsletter.shared.celery.app import celery_app
            # Test Redis connection
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                logger.info(f"✅ Celery workers available: {len(stats)}")
            else:
                logger.info("ℹ️ No Celery workers detected (normal during startup)")
        except Exception as e:
            logger.info(f"ℹ️ Celery connection will be established when workers start: {e}")
    
    logger.info("🚀 Crypto Newsletter API started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Crypto Newsletter API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Crypto Newsletter API",
        description="Bitcoin newsletter data pipeline and administration API",
        version="1.0.0",
        docs_url="/docs" if settings.railway_environment == "development" else None,
        redoc_url="/redoc" if settings.railway_environment == "development" else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.railway_environment == "development" else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])
    app.include_router(api.router, prefix="/api", tags=["api"])
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint for basic service verification."""
        return {
            "service": "crypto-newsletter",
            "status": "running",
            "version": "1.0.0",
            "environment": settings.railway_environment,
            "docs": "/docs" if settings.railway_environment == "development" else "disabled",
        }

    # Direct health endpoint for Railway (without trailing slash)
    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Direct health check endpoint for Railway deployment."""
        return {
            "status": "healthy",
            "service": "crypto-newsletter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for unhandled errors."""
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.railway_environment == "development" else "An error occurred",
            }
        )
    
    return app


# Create app instance
app = create_app()


def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """Start the FastAPI server."""
    settings = get_settings()
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    
    # Configure uvicorn
    config = {
        "app": "crypto_newsletter.web.main:app",
        "host": host,
        "port": port,
        "reload": reload,
        "workers": workers if not reload else 1,  # Reload mode requires single worker
        "log_level": "debug" if settings.railway_environment == "development" else "info",
        "access_log": True,
        "use_colors": True,
    }
    
    # Production optimizations
    if settings.is_production:
        config.update({
            "workers": workers,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "keepalive": 2,
            "max_requests": 1000,
            "max_requests_jitter": 100,
        })
    
    uvicorn.run(**config)


if __name__ == "__main__":
    # Default development server
    start_server(reload=True)
