"""
PDF Platform - FastAPI Main Application

Database schema, models, and async engine have been set up with:
- SQLAlchemy ORM models for users, plans, subscriptions, sessions, jobs, payments
- All 9 indexes for optimized queries
- Alembic migrations with seed data
- Pydantic v2 schemas for request/response DTOs
- Async engine using asyncpg
- Complete authentication system with JWT, rate limiting, and email verification
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
    has_slowapi = True
except ImportError:
    has_slowapi = False

from config import settings
from db import close_db, init_db
from routers import admin_router, auth_router, payments_router, session_router, upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan context manager."""
    # Startup
    print("🚀 Starting PDF Platform API...")
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("🛑 Shutting down PDF Platform API...")
    await close_db()
    print("✅ Database connections closed")


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter if available
if has_slowapi:
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        """Handle rate limit exceeded errors"""
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

# Include routers
app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(session_router)
app.include_router(upload_router)
app.include_router(admin_router)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Enhanced health check for production monitoring."""
    import redis as redis_lib
    import os
    from minio import Minio
    from sqlalchemy import text
    
    health = {"api": "ok"}
    
    # 1. Check DB
    try:
        await db.execute(text("SELECT 1"))
        health["db"] = "ok"
    except Exception as e:
        health["db"] = f"fail: {str(e)}"
    
    # 2. Check Redis
    try:
        r = redis_lib.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        r.ping()
        health["redis"] = "ok"
        health["worker_queue_depth"] = r.llen("celery")
    except Exception as e:
        health["redis"] = f"fail: {str(e)}"
        health["worker_queue_depth"] = -1
    
    # 3. Check MinIO
    try:
        m = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        m.list_buckets()
        health["minio"] = "ok"
    except Exception as e:
        health["minio"] = f"fail: {str(e)}"
    
    overall_ok = all(v == "ok" for k, v in health.items() if k != "worker_queue_depth")
    return JSONResponse(health, status_code=200 if overall_ok else 503)


@app.get("/api/status")
async def status():
    """API status endpoint"""
    return JSONResponse({
        "status": "running",
        "service": "PDF Conversion Platform API",
        "version": "1.0.0",
    })


@app.get("/api/docs")
async def docs():
    """API documentation redirect"""
    return JSONResponse({"message": "See /docs for Swagger UI or /redoc for ReDoc"})


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "message": "PDF Conversion Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
