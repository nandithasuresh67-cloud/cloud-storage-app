from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping avoids stale-connection errors against Supabase's pooler
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True) if settings.DATABASE_URL else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session per-request."""
    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Copy backend/.env.example to "
            "backend/.env and fill in your Supabase connection string."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
