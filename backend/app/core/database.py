"""Database engine, session management, and table setup."""
import os
import pathlib
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Ensure data directory exists if using local SQLite file
if settings.database_url.startswith("sqlite:////") or settings.database_url.startswith("sqlite:///./"):
    db_path = settings.database_url.replace("sqlite:///", "")
    if not db_path.startswith(":memory:"):
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency providing a transactional SQLAlchemy database session."""
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
    """Creates database tables on startup."""
    import app.models.entities  # noqa: F401
    Base.metadata.create_all(bind=engine)
