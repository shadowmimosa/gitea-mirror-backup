"""
仓库管理路由
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..schemas import RepositoryInfo, RepositoryDetail, BackupTriggerResponse, MessageResponse
from ...utils.auth import get_current_user, get_current_admin_user
from ..models import User
from ..config import settings
from ...services.backup_service import BackupService
from ...services.task_service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["仓库管理"])


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    return BackupService(
        backup_base_path=settings.BACKUP_BASE_PATH,
        config_path=settings.BACKUP_CONFIG_PATH,
    )


def _get_recent_logs(repository: str, limit: int = 20) -> List[str]:
    """从 Web 任务日志中提取与仓库相关的最近日志行"""
    log_dir = Path(settings.TASK_LOG_DIR)
    if not log_dir.exists():
        return []

    logs: List[str] = []
    log_files = sorted(log_dir.glob("backup-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)

    for log_file in log_files[:5]:
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in reversed(lines):
                if repository in line or repository.split("/")[-1] in line:
                    logs.append(line)
                    if len(logs) >= limit:
                        return logs
        except Exception:
            continue

    return logs


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

    snapshots = backup_service.get_snapshots(
        repository=full_name,
        page=page,
        page_size=page_size,
        include_size=include_size,
    )

    recent_logs = _get_recent_logs(full_name)

    return RepositoryDetail(**repo, snapshots=snapshots, recent_logs=recent_logs)


@router.post(
    "/{repo_name:path}/backup",
    response_model=BackupTriggerResponse,
    summary="立即备份仓库",
)
async def backup_repository(
    repo_name: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    立即备份指定仓库（当前执行全量备份，并记录目标仓库）
    """
    repositories = backup_service.get_repositories()
    repo = next((r for r in repositories if r["full_name"] == repo_name), None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"仓库 {repo_name} 不存在"
        )

    service = TaskService(db)
    result = service.start_backup(user=current_admin, repository=repo_name)

    if result.get("already_running"):
        return BackupTriggerResponse(
            task_run_id=result["task_run_id"],
            status=result["status"],
            already_running=True,
            repository=repo_name,
            message="已有备份任务正在运行",
        )

    return BackupTriggerResponse(
        task_run_id=result["task_run_id"],
        status=result["status"],
        already_running=False,
        repository=repo_name,
        message="备份任务已启动",
    )


@router.delete("/{full_name:path}", response_model=MessageResponse, summary="删除仓库备份")
async def delete_repository(
    full_name: str,
    force: bool = False,
    current_admin: User = Depends(get_current_admin_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    删除整个仓库的本地备份数据（仅管理员，不删除 Gitea 源仓）

    - **full_name**: 仓库全名 owner/repo
    - **force**: 存在受保护快照时强制删除
    """
    repositories = backup_service.get_repositories()
    repo = next((r for r in repositories if r["full_name"] == full_name), None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"仓库 {full_name} 不存在",
        )

    protected_count = repo.get("protected_snapshots", 0)
    if protected_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"仓库 {full_name} 含 {protected_count} 个受保护快照，"
                "无法删除（可使用 force=true 强制删除）"
            ),
        )

    success = backup_service.delete_repository(full_name, force=force)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除仓库备份失败",
        )

    if protected_count > 0 and force:
        logger.warning(
            "管理员 %s 强制删除含受保护快照的仓库备份: %s",
            current_admin.username,
            full_name,
        )

    return MessageResponse(message=f"仓库备份 {full_name} 已删除")
