"""
系统信息路由
"""

from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix="/system", tags=["系统信息"])


@router.get("/info", summary="获取系统信息")
async def get_system_info():
    """
    获取系统信息

    返回应用名称和版本号
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
