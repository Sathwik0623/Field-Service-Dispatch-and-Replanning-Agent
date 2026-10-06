"""
API v1 Router Package
"""
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.requests import router as requests_router
from app.api.v1.technicians import router as technicians_router
from app.api.v1.planning import router as planning_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.audit import router as audit_router
from app.api.v1.ai_planning import router as ai_planning_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(requests_router, tags=["requests"])
api_router.include_router(technicians_router, tags=["technicians"])
api_router.include_router(planning_router, tags=["planning"])
api_router.include_router(schedules_router, tags=["schedules"])
api_router.include_router(audit_router, tags=["audit"])
api_router.include_router(ai_planning_router, tags=["ai_planning"])
