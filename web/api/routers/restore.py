"""
恢复命令预览路由
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas import RestorePreviewRequest, RestorePreviewResponse
from ...utils.auth import get_current_admin_user
from ..models import User
from ..config import settings
from ...services.restore_service import RestoreService

router = APIRouter(prefix="/restore", tags=["恢复"])


def get_restore_service() -> RestoreService:
    return RestoreService(
        backup_base_path=settings.BACKUP_BASE_PATH,
        config_path=settings.BACKUP_CONFIG_PATH,
    )


@router.post(
    "/preview",
    response_model=RestorePreviewResponse,
    summary="预览恢复命令",
)
async def preview_restore(
    body: RestorePreviewRequest,
    current_user: User = Depends(get_current_admin_user),
    restore_service: RestoreService = Depends(get_restore_service),
):
    """
    根据所选快照和模式生成可复制执行的 shell 命令（不自动执行）。
    """
    try:
        result = restore_service.preview_restore(
            repository=body.repository,
            snapshot_id=body.snapshot_id,
            mode=body.mode,
            new_repo_name=body.new_repo_name,
            bundle_path=body.bundle_path,
        )
        return RestorePreviewResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
