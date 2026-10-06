from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings

# Configure engine connect arguments based on DB driver (e.g. SQLite thread check)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarative class for future SQLAlchemy models"""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database sessions to FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
