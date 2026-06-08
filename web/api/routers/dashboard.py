"""
仪表板路由
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timedelta

from ..schemas import DashboardStats, DashboardTrend
from ...utils.auth import get_current_user
from ..models import User
from ..config import settings
from ...services.backup_service import BackupService

router = APIRouter(prefix="/dashboard", tags=["仪表板"])


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    return BackupService(
        backup_base_path=settings.BACKUP_BASE_PATH,
        config_path=settings.BACKUP_CONFIG_PATH,
    )


def get_backup_stats(backup_service: BackupService) -> dict:
    """
    获取备份统计信息

    复用 BackupService，通过 .size_tracking 和目录遍历统计，避免对每个快照 rglob 扫描。
    """
    stats = {
        "total_repositories": 0,
        "total_snapshots": 0,
        "protected_snapshots": 0,
        "total_disk_usage": 0,
        "last_backup_time": None,
        "success_rate": 100.0,
        "failed_backups": 0,
    }

    repos = backup_service.get_repositories()
    if not repos:
        return stats

    stats["total_repositories"] = len(repos)
    stats["total_snapshots"] = sum(r.get("snapshot_count", 0) for r in repos)
    stats["protected_snapshots"] = backup_service.count_snapshots(is_protected=True)
    stats["total_disk_usage"] = sum(r.get("disk_usage", 0) for r in repos)
    stats["failed_backups"] = sum(1 for r in repos if r.get("status") == "warning")

    last_times = [r["last_backup_time"] for r in repos if r.get("last_backup_time")]
    if last_times:
        stats["last_backup_time"] = max(last_times)

    if stats["total_repositories"] > 0:
        stats["success_rate"] = (
            (stats["total_repositories"] - stats["failed_backups"])
            / stats["total_repositories"]
        ) * 100

    return stats


@router.get("/stats", response_model=DashboardStats, summary="获取仪表板统计数据")
async def get_stats(
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取仪表板统计数据

    包括：
    - 总仓库数
    - 总快照数
    - 磁盘使用量
    - 最后备份时间
    - 成功率
    - 失败备份数
    """
    stats = get_backup_stats(backup_service)
    return DashboardStats(**stats)


@router.get("/trends", response_model=list[DashboardTrend], summary="获取趋势数据")
async def get_trends(days: int = 7, current_user: User = Depends(get_current_user)):
    """
    获取趋势数据

    - **days**: 天数（默认7天）
    """
    trends = []

    # 生成最近N天的数据
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i - 1)
        date_str = date.strftime("%Y-%m-%d")

        # 这里简化处理，实际应该从日志或数据库读取
        trends.append(
            DashboardTrend(date=date_str, success_count=0, failed_count=0, disk_usage=0)
        )

    return trends
