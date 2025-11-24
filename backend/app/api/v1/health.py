from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.schemas.contracts import HealthCheck
from app.db.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        database_status = "connected"
    except Exception:
        database_status = "disconnected"
    
    return HealthCheck(
        status="healthy" if database_status == "connected" else "unhealthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database=database_status
    )