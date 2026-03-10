"""
Database configuration and async engine setup.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Get database URL from environment with default for development
DATABASE_URL = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform",
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session in FastAPI endpoints.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(retries: int = 5, delay: float = 3.0):
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    import asyncio
    from db.models import Base

    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"✅ Database connected on attempt {attempt}")
            return
        except Exception as e:
            print(f"⚠️  DB connection attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                raise


async def close_db():
    """
    Close database connection pool.
    Should be called on application shutdown.
    """
    await engine.dispose()
