from fastapi import APIRouter
from app.api.v1 import health, vendors

api_router = APIRouter()

# Include health check router
api_router.include_router(health.router, tags=["health"])

# Include vendors router
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
