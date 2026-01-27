"""
快照管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..schemas import SnapshotInfo, MessageResponse
from ...utils.auth import get_current_user, get_current_admin_user
from ..models import User
from ..config import settings
from ...services.backup_service import BackupService

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
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取快照列表（支持分页）

    - **repository**: 仓库名称（可选，不指定则返回所有快照）
    - **page**: 页码（从 1 开始，默认 1）
    - **page_size**: 每页数量（默认 10）
    - **include_size**: 是否计算大小（默认 False，设为 True 会变慢）
    """
    snapshots = backup_service.get_snapshots(
        repository=repository,
        page=page,
        page_size=page_size,
        include_size=include_size
    )
    return snapshots


@router.get("/count", summary="获取快照总数")
async def count_snapshots(
    repository: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取快照总数

    - **repository**: 仓库名称（可选，不指定则返回所有快照总数）
    """
    count = backup_service.count_snapshots(repository=repository)
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
    current_user: User = Depends(get_current_admin_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    删除指定快照（仅管理员）

    - **snapshot_id**: 快照 ID
    - **repository**: 仓库全名（格式：owner/repo）
    """
    # 先查找快照是否存在
    snapshots = backup_service.get_snapshots(repository=repository)
    snapshot = next((s for s in snapshots if s["id"] == snapshot_id), None)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"快照 {snapshot_id} 不存在",
        )

    # 检查是否受保护
    if snapshot.get("is_protected", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"快照 {snapshot_id} 已被保护，无法删除",
        )

    # 删除快照
    success = backup_service.delete_snapshot(snapshot_id, repository)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除快照失败",
        )

    return MessageResponse(message="快照已删除", detail=f"快照 ID: {snapshot_id}")
