"""Main FastAPI application entry point."""

import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from core.events import create_shutdown_handler, create_startup_handler
from core.middleware.correlation_id import CorrelationIdMiddleware, is_valid_uuid4
from core.settings import settings
from modules.rules.api.routes.rule_routes import rule_router
from modules.rules.api.routes.section_routes import section_router

# Create FastAPI application
app = FastAPI(
    title=settings.app.app_name,
    description=settings.app.project_description,
    version=settings.app.version,
    openapi_url=f"{settings.app.root_path}/openapi.json"
    if settings.app.root_path
    else "/openapi.json",
    docs_url=f"{settings.app.root_path}/docs" if settings.app.root_path else "/docs",
    redoc_url=f"{settings.app.root_path}/redoc" if settings.app.root_path else "/redoc",
    contact={
        "name": settings.app.contact_name,
        "email": settings.app.contact_email,
    },
    debug=settings.app.debug,
)

# Add event handlers
app.add_event_handler("startup", create_startup_handler())
app.add_event_handler("shutdown", create_shutdown_handler())

# Security Middleware (order matters!)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.app.allowed_hosts)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.app.backend_cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Request-ID",
        "X-Requested-With",
    ],
    expose_headers=["X-Request-ID"],
)

# Correlation ID Middleware for request tracing
app.add_middleware(
    CorrelationIdMiddleware,
    header_name="X-Request-ID",
    generator=lambda: str(uuid.uuid4()),
    validator=is_valid_uuid4,
)

# Include API routers
app.include_router(section_router, prefix=settings.app.api_v1_prefix)
app.include_router(rule_router, prefix=settings.app.api_v1_prefix)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint returning a welcome message."""
    return {
        "message": settings.app.app_name,
        "version": settings.app.version,
        "description": settings.app.project_description,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app.version,
        "environment": "development" if settings.app.debug else "production",
    }
