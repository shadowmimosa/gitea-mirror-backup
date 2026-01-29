"""
路由模块
"""

from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .repositories import router as repositories_router
from .snapshots import router as snapshots_router
from .reports import router as reports_router
from .system import router as system_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "repositories_router",
    "snapshots_router",
    "reports_router",
    "system_router",
]
