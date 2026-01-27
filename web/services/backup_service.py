"""
备份服务 - 与核心备份脚本交互
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import subprocess


class BackupService:
    """备份服务类 - 适配实际的备份目录结构"""

    def __init__(self, backup_base_path: str, config_path: str):
        """
        初始化备份服务

        实际的备份结构：
        BACKUP_ROOT/
          └── {owner}/
              └── {repo_name}/
                  ├── snapshots/
                  │   └── 20250126-120000/
                  ├── archives/
                  ├── .commit_tracking
                  ├── .size_tracking
                  └── restore.sh
        """
        self.backup_base_path = Path(backup_base_path)
        self.config_path = Path(config_path)

    def get_repositories(self) -> List[Dict]:
        """
        获取仓库列表
        扫描 BACKUP_ROOT/{owner}/{repo_name}/ 结构

        Returns:
            仓库信息列表
        """
        repos = []

        if not self.backup_base_path.exists():
            return repos

        # 遍历所有组织目录
        for owner_dir in self.backup_base_path.iterdir():
            if not owner_dir.is_dir() or owner_dir.name.startswith('.'):
                continue

            # 遍历组织下的所有仓库目录
            for repo_dir in owner_dir.iterdir():
                if not repo_dir.is_dir():
                    continue

                # 检查是否有 snapshots 目录（标识这是一个备份仓库）
                if (repo_dir / "snapshots").exists():
                    repo_info = self._get_repo_info(owner_dir.name, repo_dir)
                    repos.append(repo_info)

        return sorted(
            repos, key=lambda x: x.get('last_backup_time') or datetime.min, reverse=True
        )

    def _get_repo_info(self, owner: str, repo_dir: Path) -> Dict:
        """获取单个仓库信息"""
        repo_name = repo_dir.name
        full_name = f"{owner}/{repo_name}"

        # 读取提交数跟踪文件
        commit_count = 0
        commit_tracking_file = repo_dir / ".commit_tracking"
        if commit_tracking_file.exists():
            try:
                commit_count = int(commit_tracking_file.read_text().strip())
            except Exception:
                pass

        # 读取大小跟踪文件
        repo_size = 0
        size_tracking_file = repo_dir / ".size_tracking"
        if size_tracking_file.exists():
            try:
                repo_size = (
                    int(size_tracking_file.read_text().strip()) * 1024
                )  # KB -> Bytes
            except Exception:
                pass

        # 统计快照数量和获取最新快照时间
        snapshot_count = 0
        last_backup_time = None
        protected_count = 0
        snapshots_dir = repo_dir / "snapshots"

        if snapshots_dir.exists():
            snapshots = [s for s in snapshots_dir.iterdir() if s.is_dir()]
            snapshot_count = len(snapshots)

            # 统计受保护的快照
            protected_count = len([s for s in snapshots if (s / ".protected").exists()])

            # 获取最新快照时间
            if snapshots:
                latest_snapshot = max(snapshots, key=lambda x: x.stat().st_mtime)
                last_backup_time = datetime.fromtimestamp(
                    latest_snapshot.stat().st_mtime
                )

        # 检查是否有异常告警
        has_alert = (repo_dir / ".alerts").exists()

        return {
            "name": repo_name,
            "full_name": full_name,
            "owner": owner,
            "description": None,
            "last_backup_time": last_backup_time,
            "snapshot_count": snapshot_count,
            "protected_snapshots": protected_count,
            "commit_count": commit_count,
            "disk_usage": repo_size,
            "status": "warning" if has_alert else "success",
        }

    def get_snapshots(
        self,
        repository: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        include_size: bool = False,
    ) -> List[Dict]:
        """
        获取快照列表（支持分页）
        扫描 BACKUP_ROOT/{owner}/{repo_name}/snapshots/ 目录

        Args:
            repository: 仓库全名 "owner/repo"（可选，不指定则返回所有快照）
            page: 页码（从 1 开始）
            page_size: 每页数量
            include_size: 是否计算大小（默认 False，可以大幅提升速度）

        Returns:
            快照信息列表
        """

        # 第一步：快速收集所有快照的基本信息（不计算大小）
        snapshot_basics = []

        if not self.backup_base_path.exists():
            return []

        # 如果指定了仓库，只扫描该仓库
        if repository:
            parts = repository.split('/')
            if len(parts) == 2:
                owner, repo_name = parts
                repo_dir = self.backup_base_path / owner / repo_name
                if repo_dir.exists():
                    snapshot_basics.extend(
                        self._get_repo_snapshots_basic(owner, repo_name, repo_dir)
                    )
        else:
            # 扫描所有仓库的快照
            for owner_dir in self.backup_base_path.iterdir():
                if not owner_dir.is_dir() or owner_dir.name.startswith('.'):
                    continue

                for repo_dir in owner_dir.iterdir():
                    if not repo_dir.is_dir():
                        continue

                    snapshot_basics.extend(
                        self._get_repo_snapshots_basic(
                            owner_dir.name, repo_dir.name, repo_dir
                        )
                    )

        # 第二步：按创建时间倒序排序
        snapshot_basics.sort(key=lambda x: x["created_at"], reverse=True)

        # 第三步：只对当前页的快照计算大小（如果需要）
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_snapshots = snapshot_basics[start_idx:end_idx]

        # 第四步：如果需要大小信息，只计算当前页的
        if include_size:
            for i, snapshot in enumerate(page_snapshots):
                snapshot['size'] = self._calculate_snapshot_size(snapshot['_path'])
                del snapshot['_path']  # 删除内部使用的路径字段
        else:
            # 不计算大小，设为 0
            for snapshot in page_snapshots:
                snapshot['size'] = 0
                del snapshot['_path']

        return page_snapshots

    def _get_repo_snapshots(
        self, owner: str, repo_name: str, repo_dir: Path
    ) -> List[Dict]:
        """获取单个仓库的所有快照"""
        snapshots = []
        snapshots_dir = repo_dir / "snapshots"

        if not snapshots_dir.exists():
            return snapshots

        for snapshot_dir in snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            # 读取快照元数据
            meta_file = snapshot_dir / ".snapshot_meta"
            created_at = datetime.fromtimestamp(snapshot_dir.stat().st_mtime)

            if meta_file.exists():
                try:
                    meta_content = meta_file.read_text()
                    for line in meta_content.splitlines():
                        if line.startswith('timestamp='):
                            timestamp_str = line.split('=', 1)[1]
                            created_at = datetime.fromisoformat(timestamp_str)
                            break  # 只需要时间戳，找到后立即退出
                except Exception:
                    pass

            # 检查是否受保护
            is_protected = (snapshot_dir / ".protected").exists()

            # 使用 du 命令快速获取目录大小（比 Python 递归快得多）
            size = 0
            try:
                result = subprocess.run(
                    ['du', '-sb', str(snapshot_dir)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    size = int(result.stdout.split()[0])
            except Exception:
                # 如果 du 命令失败，使用目录的 stat 大小作为估算（不准确但很快）
                try:
                    size = snapshot_dir.stat().st_size
                except Exception:
                    size = 0

            snapshot_info = {
                "id": snapshot_dir.name,
                "repository": f"{owner}/{repo_name}",
                "created_at": created_at,
                "size": size,
                "is_protected": is_protected,
                "status": "protected" if is_protected else "success",
            }
            snapshots.append(snapshot_info)

        return snapshots

    def _get_repo_snapshots_basic(
        self, owner: str, repo_name: str, repo_dir: Path
    ) -> List[Dict]:
        """快速获取单个仓库的所有快照基本信息（不计算大小）"""
        snapshots = []
        snapshots_dir = repo_dir / "snapshots"

        if not snapshots_dir.exists():
            return snapshots

        for snapshot_dir in snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            # 只读取最基本的信息
            created_at = datetime.fromtimestamp(snapshot_dir.stat().st_mtime)

            # 尝试从元数据获取更准确的时间
            meta_file = snapshot_dir / ".snapshot_meta"
            if meta_file.exists():
                try:
                    meta_content = meta_file.read_text()
                    for line in meta_content.splitlines():
                        if line.startswith('timestamp='):
                            timestamp_str = line.split('=', 1)[1]
                            created_at = datetime.fromisoformat(timestamp_str)
                            break
                except Exception:
                    pass

            # 检查是否受保护
            is_protected = (snapshot_dir / ".protected").exists()

            snapshot_info = {
                "id": snapshot_dir.name,
                "repository": f"{owner}/{repo_name}",
                "created_at": created_at,
                "is_protected": is_protected,
                "status": "protected" if is_protected else "success",
                "_path": snapshot_dir,  # 保存路径用于后续计算大小
            }
            snapshots.append(snapshot_info)

        return snapshots

    def _calculate_snapshot_size(self, snapshot_path: Path) -> int:
        """计算单个快照的大小"""
        import platform

        # 在 Unix/Linux 系统上使用 du 命令（更快）
        if platform.system() != 'Windows':
            try:
                result = subprocess.run(
                    ['du', '-sb', str(snapshot_path)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return int(result.stdout.split()[0])
            except Exception:
                pass

        # Windows 或 du 命令失败时，使用 Python 递归计算
        try:
            total_size = 0
            for item in snapshot_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        pass
            return total_size
        except Exception:
            return 0

    def count_snapshots(self, repository: Optional[str] = None) -> int:
        """
        获取快照总数（快速，不计算大小）

        Args:
            repository: 仓库全名 "owner/repo"（可选）

        Returns:
            快照总数
        """
        count = 0

        if not self.backup_base_path.exists():
            return count

        if repository:
            parts = repository.split('/')
            if len(parts) == 2:
                owner, repo_name = parts
                repo_dir = self.backup_base_path / owner / repo_name
                if repo_dir.exists():
                    snapshots_dir = repo_dir / "snapshots"
                    if snapshots_dir.exists():
                        count = len([s for s in snapshots_dir.iterdir() if s.is_dir()])
        else:
            for owner_dir in self.backup_base_path.iterdir():
                if not owner_dir.is_dir() or owner_dir.name.startswith('.'):
                    continue

                for repo_dir in owner_dir.iterdir():
                    if not repo_dir.is_dir():
                        continue

                    snapshots_dir = repo_dir / "snapshots"
                    if snapshots_dir.exists():
                        count += len([s for s in snapshots_dir.iterdir() if s.is_dir()])

        return count

    def get_reports(self) -> List[Dict]:
        """
        获取报告列表
        扫描 BACKUP_ROOT/reports/ 目录

        Returns:
            报告信息列表
        """
        reports = []
        reports_path = self.backup_base_path / "reports"

        if not reports_path.exists():
            return reports

        for report_file in reports_path.glob("report-*.md"):
            # 检查是否受保护
            is_protected = report_file.with_suffix('.md.protected').exists()

            report_info = {
                "filename": report_file.name,
                "created_at": datetime.fromtimestamp(report_file.stat().st_mtime),
                "size": report_file.stat().st_size,
                "is_protected": is_protected,
                "status": "protected" if is_protected else "success",
            }
            reports.append(report_info)

        return sorted(reports, key=lambda x: x["created_at"], reverse=True)

    def get_report_content(self, filename: str) -> Optional[str]:
        """
        获取报告内容

        Args:
            filename: 报告文件名

        Returns:
            报告内容（Markdown）
        """
        report_path = self.backup_base_path / "reports" / filename

        if not report_path.exists():
            return None

        return report_path.read_text(encoding="utf-8")

    def trigger_backup(self, repository: Optional[str] = None) -> Dict:
        """
        触发备份任务

        Args:
            repository: 仓库名称（可选，不指定则备份所有仓库）

        Returns:
            任务信息
        """
        # 这里应该调用主备份脚本
        # 暂时返回模拟数据
        return {
            "task_id": "backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            "status": "running",
            "started_at": datetime.now(),
        }

    def delete_snapshot(self, snapshot_id: str, repository: str) -> bool:
        """
        删除快照

        Args:
            snapshot_id: 快照 ID（时间戳格式，如 20250126-120000）
            repository: 仓库全名 "owner/repo"

        Returns:
            是否成功
        """
        parts = repository.split('/')
        if len(parts) != 2:
            return False

        owner, repo_name = parts
        snapshot_path = (
            self.backup_base_path / owner / repo_name / "snapshots" / snapshot_id
        )

        if not snapshot_path.exists() or not snapshot_path.is_dir():
            return False

        # 检查是否受保护
        if (snapshot_path / ".protected").exists():
            return False  # 不允许删除受保护的快照

        try:
            import shutil

            shutil.rmtree(snapshot_path)
            return True
        except Exception:
            return False
