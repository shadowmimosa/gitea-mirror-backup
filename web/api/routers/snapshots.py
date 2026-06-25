"""
快照管理路由
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..schemas import SnapshotInfo, MessageResponse
from ...utils.auth import get_current_user, get_current_admin_user
from ..models import User
from ..config import settings
from ...services.backup_service import BackupService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/snapshots", tags=["快照管理"])


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    return BackupService(
        backup_base_path=settings.BACKUP_BASE_PATH,
        config_path=settings.BACKUP_CONFIG_PATH,
    )


@router.get("", response_model=List[SnapshotInfo], summary="获取快照列表")
async def list_snapshots(
    repository: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    include_size: bool = False,
    is_protected: Optional[bool] = None,
    repository_search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取快照列表（支持分页）

    - **repository**: 仓库名称（可选，不指定则返回所有快照）
    - **page**: 页码（从 1 开始，默认 1）
    - **page_size**: 每页数量（默认 10）
    - **include_size**: 是否计算大小（默认 False，设为 True 会变慢）
    - **is_protected**: 筛选受保护快照（true/false，不传则全部）
    - **repository_search**: 仓库名模糊搜索
    """
    snapshots = backup_service.get_snapshots(
        repository=repository,
        page=page,
        page_size=page_size,
        include_size=include_size,
        is_protected=is_protected,
        repository_search=repository_search,
    )
    return snapshots


@router.get("/count", summary="获取快照总数")
async def count_snapshots(
    repository: Optional[str] = None,
    is_protected: Optional[bool] = None,
    repository_search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取快照总数

    - **repository**: 仓库名称（可选，不指定则返回所有快照总数）
    - **is_protected**: 筛选受保护快照
    - **repository_search**: 仓库名模糊搜索
    """
    count = backup_service.count_snapshots(
        repository=repository,
        is_protected=is_protected,
        repository_search=repository_search,
    )
    return {"count": count}


@router.get("/{snapshot_id}", response_model=SnapshotInfo, summary="获取快照详情")
async def get_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取指定快照的详细信息

    - **snapshot_id**: 快照 ID
    """
    snapshots = backup_service.get_snapshots()
    snapshot = next((s for s in snapshots if s["id"] == snapshot_id), None)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"快照 {snapshot_id} 不存在"
        )

    return snapshot


@router.delete("/{snapshot_id}", response_model=MessageResponse, summary="删除快照")
async def delete_snapshot(
    snapshot_id: str,
    repository: str,
    force: bool = False,
    current_user: User = Depends(get_current_admin_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    删除指定快照（仅管理员）

    - **snapshot_id**: 快照 ID
    - **repository**: 仓库全名（格式：owner/repo）
    - **force**: 强制删除受保护快照（需管理员二次确认，由前端保障）
    """
    snapshots = backup_service.get_snapshots(repository=repository)
    snapshot = next((s for s in snapshots if s["id"] == snapshot_id), None)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"快照 {snapshot_id} 不存在",
        )

    is_protected = snapshot.get("is_protected", False)
    if is_protected and not force:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"快照 {snapshot_id} 已被保护，无法删除（可使用 force=true 强制删除）",
        )

    success = backup_service.delete_snapshot(snapshot_id, repository, force=force)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除快照失败",
        )

    if is_protected and force:
        logger.warning(
            "管理员 %s 强制删除受保护快照: %s (%s)",
            current_user.username,
            snapshot_id,
            repository,
        )

    detail = f"快照 ID: {snapshot_id}"
    if is_protected and force:
        detail += "（已强制删除受保护快照）"

    return MessageResponse(message="快照已删除", detail=detail)
