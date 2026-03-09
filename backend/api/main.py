"""Agent Nexus FastAPI Application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Load .env file FIRST (before any other imports)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .middleware import SecurityMiddleware

# Configuration (now loaded from .env)
NEXUS_DB_PATH = Path(os.getenv("NEXUS_DB_PATH", "~/.nexus/nexus.db")).expanduser()
NEXUS_PASSWORD = os.getenv("NEXUS_PASSWORD", "")
NEXUS_PORT = int(os.getenv("NEXUS_PORT", "18888"))
NEXUS_HOST = os.getenv("NEXUS_HOST", "0.0.0.0")
NEXUS_IP_WHITELIST = os.getenv("NEXUS_IP_WHITELIST", "").split(",") if os.getenv("NEXUS_IP_WHITELIST") else []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("🚀 Agent Nexus starting...")
    print(f"   Database: {NEXUS_DB_PATH}")

    # Ensure database directory exists
    NEXUS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    print("👋 Agent Nexus shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Agent Nexus",
    description="Real-time AI coding agent monitoring dashboard",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted by IP whitelist
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (IP whitelist, rate limiting)
app.add_middleware(SecurityMiddleware)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"

    # Content Security Policy (with CDN for Swagger UI)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "connect-src 'self' ws: wss:;"
    )

    return response


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "agent-nexus",
        "version": "0.1.0",
    }


# API info endpoint
@app.get("/api", tags=["System"])
async def api_info():
    """API information."""
    return {
        "name": "Agent Nexus API",
        "version": "0.1.0",
        "endpoints": {
            "sessions": "/api/sessions",
            "metrics": "/api/metrics",
            "websocket": "/ws",
            "docs": "/api/docs",
        }
    }


# Robots.txt - block all crawlers
@app.get("/robots.txt", tags=["System"])
async def robots_txt():
    """Block search engine crawlers."""
    return JSONResponse(
        content={"text": "User-agent: *\nDisallow: /"},
        media_type="text/plain"
    )


# Import and include routers
from .routes import sessions_router, websocket_router, auth_router
app.include_router(sessions_router)
app.include_router(websocket_router)
app.include_router(auth_router)
