from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
from datetime import datetime

from app.config import settings
from app.db.database import db
from app.db.database import DatabaseUnavailableError
from app.routes import chat, orders, payments

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Himalayan Willow AI Chatbot API",
    description="AI-powered conversational chatbot for cricket equipment store",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(chat.router)
app.include_router(orders.router)
app.include_router(payments.router)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration,
        client_ip=get_remote_address(request)
    )
    
    return response


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Himalayan Willow AI Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# Error handlers
@app.exception_handler(DatabaseUnavailableError)
async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError):
    """Return 503 when an endpoint needs the database but it is not available."""
    logger.warning("database_unavailable_request", path=request.url.path)
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": "SERVICE_UNAVAILABLE",
            "message": "Database is not configured or unavailable. Set DATABASE_URL in .env for orders and persistence.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    import traceback
    
    # Print to stdout for debugging
    if settings.environment == "development":
        print(f"\n{'='*60}")
        print(f"UNHANDLED EXCEPTION in {request.method} {request.url.path}")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error Message: {str(exc)}")
        print(f"Traceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")
    
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc() if settings.environment == "development" else None
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.environment == "development" else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup (optional if DATABASE_URL not set or invalid)."""
    await db.connect()
    logger.info("application_started")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await db.disconnect()
    logger.info("application_shutdown")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
