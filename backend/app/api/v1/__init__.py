# Router Principal API v1
from fastapi import APIRouter
from app.api.v1.triage import router as triage_router
from app.api.v1.dynamic_questions import router as dynamic_questions_router
from app.api.v1.doctor import router as doctor_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(triage_router)
api_v1_router.include_router(dynamic_questions_router)
api_v1_router.include_router(doctor_router)

__all__ = ["api_v1_router"]
