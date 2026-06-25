"""
仪表板路由
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

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


def _load_trends_from_reports(backup_root: Path, days: int) -> list[DashboardTrend]:
    """从报告 meta 文件解析趋势数据"""
    reports_dir = backup_root / "reports"
    daily: dict[str, dict] = defaultdict(
        lambda: {"success_count": 0, "failed_count": 0, "disk_usage": 0}
    )

    if reports_dir.exists():
        for meta_file in reports_dir.glob("report-*.md.meta.json"):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                date_str = meta.get("date") or meta_file.stem.split(".")[0].replace(
                    "report-", ""
                )[:10]
                if len(date_str) >= 10:
                    date_str = date_str[:10]
                has_alerts = bool(meta.get("has_alerts"))
                if has_alerts:
                    daily[date_str]["failed_count"] += 1
                else:
                    daily[date_str]["success_count"] += 1
                disk = meta.get("total_disk_usage") or meta.get("disk_usage") or 0
                if disk:
                    daily[date_str]["disk_usage"] = max(daily[date_str]["disk_usage"], disk)
            except Exception:
                continue

        # 无 meta 时从报告文件名推断日期
        for report_file in reports_dir.glob("report-*.md"):
            meta_file = report_file.with_suffix(".md.meta.json")
            if meta_file.exists():
                continue
            try:
                name = report_file.stem  # report-20260124
                if name.startswith("report-") and len(name) >= 15:
                    date_str = name[7:15]
                    if len(date_str) == 8:
                        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    content_head = report_file.read_text(encoding="utf-8")[:2048]
                    has_alerts = "需要关注的仓库" in content_head
                    if has_alerts:
                        daily[date_str]["failed_count"] += 1
                    else:
                        daily[date_str]["success_count"] += 1
            except Exception:
                continue

    trends = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i - 1)
        date_str = date.strftime("%Y-%m-%d")
        data = daily.get(date_str, {"success_count": 0, "failed_count": 0, "disk_usage": 0})
        trends.append(
            DashboardTrend(
                date=date_str,
                success_count=data["success_count"],
                failed_count=data["failed_count"],
                disk_usage=data["disk_usage"],
            )
        )

    return trends


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
async def get_trends(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
):
    """
    获取趋势数据

    - **days**: 天数（默认7天）
    """
    backup_root = Path(settings.BACKUP_BASE_PATH)
    return _load_trends_from_reports(backup_root, days)
