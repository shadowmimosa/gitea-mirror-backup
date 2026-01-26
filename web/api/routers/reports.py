"""
报告管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ..schemas import ReportInfo, ReportDetail
from ...utils.auth import get_current_user
from ..models import User
from ..config import settings
from ...services.backup_service import BackupService

router = APIRouter(prefix="/reports", tags=["报告管理"])


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    return BackupService(
        backup_base_path=settings.BACKUP_BASE_PATH,
        config_path=settings.BACKUP_CONFIG_PATH,
    )


@router.get("", response_model=List[ReportInfo], summary="获取报告列表")
async def list_reports(
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取所有备份报告列表

    返回报告的基本信息，包括：
    - 文件名
    - 创建时间
    - 文件大小
    - 状态
    """
    reports = backup_service.get_reports()
    return reports


@router.get("/{filename}", response_model=ReportDetail, summary="获取报告详情")
async def get_report(
    filename: str,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取指定报告的详细内容

    - **filename**: 报告文件名（例如：report-20260126-153557.md）
    """
    # 获取报告基本信息
    reports = backup_service.get_reports()
    report = next((r for r in reports if r["filename"] == filename), None)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"报告 {filename} 不存在"
        )

    # 获取报告内容
    content = backup_service.get_report_content(filename)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"无法读取报告 {filename}"
        )

    return ReportDetail(**report, content=content)
