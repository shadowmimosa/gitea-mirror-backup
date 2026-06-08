"""
恢复命令预览服务
"""

from pathlib import Path
from typing import List, Optional

from src.config_loader import ConfigLoader


class RestoreService:
    """生成可复制执行的恢复 shell 命令（不在 Web 内执行）"""

    def __init__(self, backup_base_path: str, config_path: str):
        self.backup_base_path = Path(backup_base_path)
        loader = ConfigLoader(config_path)
        self.config = loader
        self.backup_root = loader.get('backup.root', backup_base_path)
        self.gitea_data_volume = loader.get('gitea.data_volume', '/shared/gitea')
        self.repos_path = loader.get('gitea.repos_path', 'git/repositories')
        self.docker_container = loader.get('gitea.docker_container', 'gitea')
        self.docker_git_user = loader.get('gitea.docker_git_user', 'git')

    @property
    def is_docker_deployment(self) -> bool:
        return str(self.backup_root).startswith('/shared/')

    def preview_restore(
        self,
        repository: str,
        snapshot_id: str,
        mode: str = 'interactive',
        new_repo_name: Optional[str] = None,
        bundle_path: Optional[str] = None,
    ) -> dict:
        parts = repository.split('/')
        if len(parts) != 2:
            raise ValueError('仓库名称格式应为 owner/repo')

        owner, repo_name = parts
        repo_dir = self.backup_base_path / owner / repo_name
        snapshot_path = repo_dir / 'snapshots' / snapshot_id
        restore_script_path = repo_dir / 'restore.sh'
        archives_dir = repo_dir / 'archives'

        if not snapshot_path.is_dir():
            raise ValueError(f'快照不存在: {snapshot_id}')

        if not str(snapshot_path.resolve()).startswith(
            str(self.backup_base_path.resolve())
        ):
            raise ValueError('无效的快照路径')

        host_repo_path = (
            Path(self.gitea_data_volume) / self.repos_path / owner / f'{repo_name}.git'
        )
        container_repo_path = f'/data/git/repositories/{owner}/{repo_name}.git'

        warnings: List[str] = []
        commands: List[str] = []
        notes: List[str] = [
            '以下命令需在宿主机 SSH 会话中执行，Web 不会自动运行。',
        ]

        if mode == 'inplace':
            warnings.append('此操作将覆盖 Gitea 中的原仓库，镜像仓库下次同步可能被再次覆盖。')
        elif mode == 'export_new' and not new_repo_name:
            raise ValueError('导出为新仓库时需要 new_repo_name')
        elif mode == 'bundle' and not bundle_path:
            bundle_path = f'/tmp/{repository.replace("/", "-")}.bundle'

        if self.is_docker_deployment:
            container_script = f'{self.backup_root}/{owner}/{repo_name}/restore.sh'
            notes.append('检测到 Docker 部署，使用 backup/restore 容器执行交互式恢复。')
            commands.append(
                f'docker compose run --rm -it restore {container_script}'
            )
            commands.append(
                f'# 若无 restore 服务: docker compose run --rm -it --entrypoint bash backup {container_script}'
            )
            if (repo_dir / 'restore-via-docker.sh').exists():
                commands.append(
                    f'# 或使用包装脚本: {repo_dir / "restore-via-docker.sh"}'
                )
        else:
            commands.append(f'{restore_script_path}')

        archive_commands = self._archive_fallback_commands(archives_dir)

        return {
            'repository': repository,
            'snapshot_id': snapshot_id,
            'mode': mode,
            'snapshot_path': str(snapshot_path),
            'restore_script_path': str(restore_script_path),
            'host_repo_path': str(host_repo_path),
            'container_repo_path': container_repo_path,
            'is_docker': self.is_docker_deployment,
            'commands': commands,
            'warnings': warnings,
            'notes': notes,
            'archives': archive_commands,
        }

    @staticmethod
    def _archive_fallback_commands(archives_dir: Path) -> List[str]:
        if not archives_dir.is_dir():
            return []
        bundles = sorted(archives_dir.glob('*.bundle'))
        if not bundles:
            return []
        return [
            f'git clone "{bundle}" restored-repo  # {bundle.name}'
            for bundle in bundles
        ]
