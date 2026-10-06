from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import AuditLog
from app.api.v1.schemas import AuditLogResponse

router = APIRouter()


@router.get("/audit", response_model=List[AuditLogResponse])
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
