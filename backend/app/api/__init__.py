"""API router registry for ReproCheck backend."""

from fastapi import APIRouter
from app.api.checklists import router as checklists_router
from app.api.qna import router as qna_router
from app.api.reviews import router as reviews_router
from app.api.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(sessions_router)
api_router.include_router(checklists_router)
api_router.include_router(reviews_router)
api_router.include_router(qna_router)
