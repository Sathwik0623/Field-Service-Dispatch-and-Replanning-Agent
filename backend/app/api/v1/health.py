from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint to verify backend operational status and database connectivity.
    """
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"disconnected ({str(exc)})"

    return {
        "status": "ok",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "database": db_status,
    }
