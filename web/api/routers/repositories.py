"""
仓库管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..schemas import RepositoryInfo, RepositoryDetail, MessageResponse
from ...utils.auth import get_current_user
from ..models import User
from ..config import settings
from ...services.backup_service import BackupService

router = APIRouter(prefix="/repositories", tags=["仓库管理"])


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    return BackupService(
        backup_base_path=settings.BACKUP_BASE_PATH,
        config_path=settings.BACKUP_CONFIG_PATH,
    )


@router.get("", response_model=List[RepositoryInfo], summary="获取仓库列表")
async def list_repositories(
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取所有仓库列表

    返回仓库的基本信息，包括：
    - 仓库名称
    - 最后备份时间
    - 快照数量
    - 磁盘使用量
    - 状态
    """
    repositories = backup_service.get_repositories()
    return repositories


@router.get("/{full_name:path}", response_model=RepositoryDetail, summary="获取仓库详情")
async def get_repository(
    full_name: str,
    page: int = 1,
    page_size: int = 10,
    include_size: bool = False,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取指定仓库的详细信息

    - **full_name**: 仓库全名（格式：owner/repo）
    - **page**: 页码（从 1 开始，默认 1）
    - **page_size**: 每页数量（默认 10）
    - **include_size**: 是否计算快照大小（默认 False）
    """
    repositories = backup_service.get_repositories()
    repo = next((r for r in repositories if r["full_name"] == full_name), None)

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"仓库 {full_name} 不存在"
        )

    # 获取快照列表（支持分页）
    snapshots = backup_service.get_snapshots(
        repository=full_name,
        page=page,
        page_size=page_size,
        include_size=include_size
    )

    # 获取最近日志（简化处理）
    recent_logs = []

    return RepositoryDetail(**repo, snapshots=snapshots, recent_logs=recent_logs)


@router.post(
    "/{repo_name}/backup", response_model=MessageResponse, summary="立即备份仓库"
)
async def backup_repository(
    repo_name: str,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    立即备份指定仓库

    - **repo_name**: 仓库名称
    """
    result = backup_service.trigger_backup(repository=repo_name)

    return MessageResponse(
        message="备份任务已启动", detail=f"任务 ID: {result['task_id']}"
    )
