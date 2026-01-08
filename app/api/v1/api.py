from fastapi import APIRouter
from app.api.v1 import health, vendors, contracts, auth, dashboards, contract_updates

api_router = APIRouter()

# Include health check router
api_router.include_router(health.router, tags=["health"])

# Include authentication router
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include dashboards router
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])

# Include vendors router
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])

# Include contracts router
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])

# Include contract updates router
api_router.include_router(contract_updates.router, prefix="/contract-updates", tags=["contract-updates"])
