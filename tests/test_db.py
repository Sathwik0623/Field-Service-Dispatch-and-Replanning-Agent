from sqlalchemy import text
from app.db.session import SessionLocal


def test_database_connection(db_session):
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_session_local_instantiation():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        db.close()
