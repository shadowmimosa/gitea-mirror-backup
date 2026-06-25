"""
备份配置管理服务
"""

from pathlib import Path
from typing import Dict, List

from src.config_loader import ConfigLoader


class ConfigService:
    """读写 config.yaml 中的备份范围等配置"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)

    def _loader(self) -> ConfigLoader:
        return ConfigLoader(str(self.config_path))

    def get_backup_scope(self) -> Dict:
        loader = self._loader()
        raw = loader.load_raw_yaml()
        backup = raw.get("backup", {})
        organizations = backup.get("organizations", [])
        if not isinstance(organizations, list):
            organizations = []
        check_mirror_only = bool(backup.get("check_mirror_only", False))
        available = loader.list_gitea_organizations()
        warnings = loader.get_backup_scope_warnings()
        effective_orgs = loader.get("backup.organizations", [])
        effective_mirror = loader.get("backup.check_mirror_only", False)
        return {
            "organizations": organizations,
            "check_mirror_only": check_mirror_only,
            "available_organizations": available,
            "effective_organizations": effective_orgs if isinstance(effective_orgs, list) else [],
            "effective_check_mirror_only": bool(effective_mirror),
            "warnings": warnings,
            "config_path": str(self.config_path),
        }

    def update_backup_scope(
        self, organizations: List[str], check_mirror_only: bool
    ) -> Dict:
        loader = self._loader()
        cleaned_orgs = sorted(
            {org.strip() for org in organizations if org and org.strip()}
        )
        loader.update_backup_scope(cleaned_orgs, check_mirror_only)
        return self.get_backup_scope()
