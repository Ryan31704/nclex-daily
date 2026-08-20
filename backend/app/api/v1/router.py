from fastapi import APIRouter

from app.api.v1.routes import health, me, questions, topics

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(me.router, tags=["profile"])
api_router.include_router(topics.router, tags=["topics"])
api_router.include_router(questions.router, tags=["questions"])
