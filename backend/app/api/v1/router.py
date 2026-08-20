from fastapi import APIRouter

from app.api.v1.routes import dashboard, health, me, practice, progress, questions, review, topics

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(me.router, tags=["profile"])
api_router.include_router(topics.router, tags=["topics"])
api_router.include_router(questions.router, tags=["questions"])
api_router.include_router(practice.router, tags=["practice"])
api_router.include_router(progress.router, tags=["progress"])
api_router.include_router(review.router, tags=["review"])
api_router.include_router(dashboard.router, tags=["dashboard"])
