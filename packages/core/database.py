"""
Database configuration and connection management for Carai Receptionist
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

from packages.core.config import settings

logger = logging.getLogger(__name__)

# Create engine with configuration suitable for the database backend
from sqlalchemy.engine.url import make_url

_database_url = settings.database_url
_url = make_url(_database_url)
_engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.DEBUG,
}

if _url.drivername.startswith("sqlite"):
    engine = create_engine(
        _database_url,
        connect_args={"check_same_thread": False},
        **_engine_kwargs,
    )
else:
    engine = create_engine(
        _database_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        **_engine_kwargs,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database session outside of FastAPI"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables"""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

def drop_db() -> None:
    """Drop all database tables (use with caution!)"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database tables dropped")