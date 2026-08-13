"""Routers package."""
from app.routers.dashboard import router as dashboard_router
from app.routers.operations import router as operations_router
from app.routers.resources import router as resources_router
from app.routers.audit import router as audit_router

__all__ = [
    'dashboard_router',
    'operations_router',
    'resources_router',
    'audit_router',
]
