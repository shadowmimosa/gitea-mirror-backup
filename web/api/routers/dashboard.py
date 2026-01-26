"""
仪表板路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime, timedelta

from ..database import get_db
from ..schemas import DashboardStats, DashboardTrend
from ...utils.auth import get_current_user
from ..models import User
from ..config import settings

router = APIRouter(prefix="/dashboard", tags=["仪表板"])


def get_backup_stats() -> dict:
    """
    获取备份统计信息

    扫描实际的备份结构：
    BACKUP_ROOT/
      └── {owner}/
          └── {repo_name}/
              └── snapshots/
    """
    backup_path = Path(settings.BACKUP_BASE_PATH)

    stats = {
        "total_repositories": 0,
        "total_snapshots": 0,
        "total_disk_usage": 0,
        "last_backup_time": None,
        "success_rate": 100.0,
        "failed_backups": 0,
    }

    if not backup_path.exists():
        return stats

    latest_snapshot_time = None
    total_repos = 0
    total_snapshots = 0
    total_size = 0
    repos_with_alerts = 0

    # 遍历所有组织目录
    for owner_dir in backup_path.iterdir():
        if not owner_dir.is_dir() or owner_dir.name.startswith('.'):
            continue

        # 遍历组织下的所有仓库目录
        for repo_dir in owner_dir.iterdir():
            if not repo_dir.is_dir():
                continue

            # 检查是否有 snapshots 目录（标识这是一个备份仓库）
            snapshots_dir = repo_dir / "snapshots"
            if not snapshots_dir.exists():
                continue

            total_repos += 1

            # 检查是否有异常告警
            if (repo_dir / ".alerts").exists():
                repos_with_alerts += 1

            # 统计快照
            for snapshot_dir in snapshots_dir.iterdir():
                if not snapshot_dir.is_dir():
                    continue

                total_snapshots += 1

                # 获取快照时间
                snapshot_time = datetime.fromtimestamp(snapshot_dir.stat().st_mtime)
                if latest_snapshot_time is None or snapshot_time > latest_snapshot_time:
                    latest_snapshot_time = snapshot_time

                # 计算快照大小（这可能很慢，可以考虑只统计最近的）
                try:
                    size = sum(
                        f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file()
                    )
                    total_size += size
                except Exception:
                    pass

    stats["total_repositories"] = total_repos
    stats["total_snapshots"] = total_snapshots
    stats["total_disk_usage"] = total_size
    stats["last_backup_time"] = latest_snapshot_time
    stats["failed_backups"] = repos_with_alerts

    # 计算成功率
    if total_repos > 0:
        stats["success_rate"] = ((total_repos - repos_with_alerts) / total_repos) * 100

    return stats


@router.get("/stats", response_model=DashboardStats, summary="获取仪表板统计数据")
async def get_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
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
    stats = get_backup_stats()
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
