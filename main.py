from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.api import api_router
import traceback
import logging
import subprocess
import sys
from nicegui import app as nicegui_app, ui

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import NiceGUI pages and components
from app.components.header import header
from app.pages.home_page import home_page
from app.pages.new_contract import new_contract
from app.pages.new_vendor import new_vendor
from app.pages.login import login_page
from app.pages.terminated_contracts import terminated_contracts
from app.pages.active_contracts import active_contracts
from app.pages.pending_contracts import pending_contracts
from app.pages.expired_contracts import expired_contracts
from app.pages.vendor_info import vendor_info
from app.pages.vendors_list import vendors_list
from app.pages.contract_managers import contract_managers
from app.pages.manager import manager
from app.pages.pending_reviews import pending_reviews
from app.pages.contract_updates import contract_updates


# Define lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(root_app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("Starting Aruba Bank Contract Management Application")
    logger.info("=" * 60)
    
    # Run database migrations on startup
    logger.info("Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Database migrations completed successfully")
        if result.stdout:
            logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        # Don't exit - let the app start and show the error
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
    
    logger.info(f"Server: http://0.0.0.0:8000")
    logger.info(f"Web UI: http://0.0.0.0:8000/")
    logger.info(f"API Documentation: http://0.0.0.0:8000{settings.api_v1_prefix}/docs")
    logger.info(f"API Health Check: http://0.0.0.0:8000{settings.api_v1_prefix}/health")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application with lifespan
root_app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Contract Management System - Unified Application (API + Web UI)",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
root_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Add exception handler middleware
@root_app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal server error: {str(exc)}"}
        )

# Include API router
root_app.include_router(api_router, prefix=settings.api_v1_prefix)


# ============================================================================
# NiceGUI Web UI Pages
# ============================================================================

@ui.page("/")
def main_page():
    """Home page with authentication check"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    home_page()


@ui.page("/login")
def login_route():
    """Login page"""
    login_page()


@ui.page("/new-contract")
def new_contract_page():
    """Create new contract page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    new_contract()


@ui.page("/new-vendor")
def new_vendor_page():
    """Create new vendor page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    new_vendor()


@ui.page("/active-contracts")
def active_contracts_page():
    """Active contracts page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    active_contracts()


@ui.page("/pending-contracts")
def pending_contracts_page():
    """Pending contracts page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    pending_contracts()


@ui.page("/expired-contracts")
def expired_contracts_page():
    """Expired contracts page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    expired_contracts()


@ui.page("/terminated-contracts")
def terminated_contracts_page():
    """Terminated contracts page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    terminated_contracts()


@ui.page("/vendors")
def vendors_list_page():
    """Vendors list page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    vendors_list()


@ui.page("/vendor-info/{vendor_id}")
def vendor_info_page(vendor_id: int):
    """Vendor information page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    vendor_info(vendor_id)


@ui.page("/contract-managers")
def contract_managers_page():
    """Contract managers page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    contract_managers()


@ui.page("/manager")
def manager_page():
    """Manager dashboard page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    manager()


@ui.page("/pending-reviews")
def pending_reviews_page():
    """Pending reviews page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    pending_reviews()


@ui.page("/contract-updates")
def contract_updates_page():
    """Contract updates page"""
    if not nicegui_app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    contract_updates()


# ============================================================================
# Initialize NiceGUI with FastAPI - Monolithic Application
# ============================================================================

ui.run_with(
    root_app,
    mount_path='/',
    storage_secret='jhdshd-d287y487f-ISUd-jsd92-287yds'
)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:root_app', host='0.0.0.0', port=8000, log_level='info', reload=True)