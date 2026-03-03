from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import structlog

from app.limiter import limiter
from datetime import datetime
import sys

from app.config import settings
from app.db.database import db
from app.db.database import DatabaseUnavailableError
from app.routes import chat, orders, payments, analytics, chat_enhanced, greeting, user_profile, products, auth

# Configure Sentry if enabled
if settings.enable_sentry and settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1 if settings.environment == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.environment == "production" else 1.0,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
            before_send=lambda event, hint: event if settings.environment != "development" else None,
        )
        print("✓ Sentry initialized successfully")
    except ImportError:
        print("⚠ Sentry SDK not installed. Install with: pip install sentry-sdk", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Failed to initialize Sentry: {e}", file=sys.stderr)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle. Replaces deprecated on_event."""
    await db.connect()
    logger.info("application_started")

    # Index products into ChromaDB for conversational/semantic search
    from app.services.vector_search import vector_search_service
    if vector_search_service.is_available and db.is_available:
        try:
            rows = await db.fetch_all(
                "SELECT id, name, category, description, price, in_stock, specifications FROM products"
            )
            products = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "category": r["category"],
                    "description": r["description"] or "",
                    "price": float(r["price"]),
                    "in_stock": r["in_stock"],
                    "specifications": r["specifications"] or {},
                }
                for r in rows
            ]
            if products:
                vector_search_service.bulk_index(products)
                logger.info("chromadb_indexed_at_startup", count=len(products))
        except Exception as e:
            logger.warning("chromadb_startup_index_failed", error=str(e))

    yield

    await db.disconnect()
    logger.info("application_shutdown")


# Create FastAPI app
app = FastAPI(
    title="Himalayan Willow AI Chatbot API",
    description="AI-powered conversational chatbot for cricket equipment store",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(chat_enhanced.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(analytics.router)
app.include_router(greeting.router)
app.include_router(user_profile.router)
app.include_router(products.router)

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
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with enhanced metrics"""
    start_time = datetime.utcnow()
    request_id = f"{start_time.timestamp()}-{get_remote_address(request)}"
    
    # Add request ID to context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    try:
        response = await call_next(request)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Log level based on status code
        log_level = "info"
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        
        log_func = getattr(logger, log_level)
        log_func(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=round(duration, 3),
            client_ip=get_remote_address(request),
            user_agent=request.headers.get("user-agent", "")[:100]
        )
        
        # Add custom headers for debugging
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_seconds=round(duration, 3),
            error=str(e),
            error_type=type(e).__name__,
            client_ip=get_remote_address(request)
        )
        raise


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
    """Health check endpoint with circuit breaker status"""
    from app.utils.circuit_breaker import llm_circuit_breaker
    
    circuit_state = llm_circuit_breaker.get_state()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "database": "connected" if db.is_available else "unavailable",
        "circuit_breaker": circuit_state
    }


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/health")
async def api_v1_health_check():
    """Versioned keep-alive endpoint for uptime monitors and load balancers."""
    from app.utils.circuit_breaker import llm_circuit_breaker
    from app.services.llm import llm_service

    circuit_state = llm_circuit_breaker.get_state()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db.is_available else "unavailable",
        "llm_provider": llm_service.active_provider,
        "circuit_breaker": circuit_state,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
