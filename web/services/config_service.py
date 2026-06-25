"""
备份配置管理服务
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.config_loader import ConfigLoader
from src.config_merge import write_merged_config


class ConfigService:
    """读写备份范围：基础 config.yaml（只读）+ data 目录覆盖文件"""

    SCOPE_OVERRIDE_NAME = "backup-scope.override.yaml"
    EFFECTIVE_CONFIG_NAME = "backup-config.effective.yaml"

    def __init__(self, config_path: str, web_data_dir: str):
        self.config_path = Path(config_path)
        self.web_data_dir = Path(web_data_dir)
        self.scope_override_path = self.web_data_dir / self.SCOPE_OVERRIDE_NAME
        self.effective_config_path = self.web_data_dir / self.EFFECTIVE_CONFIG_NAME

    def _loader(self) -> ConfigLoader:
        self._ensure_effective_config()
        path = (
            self.effective_config_path
            if self.effective_config_path.exists()
            else self.config_path
        )
        return ConfigLoader(str(path))

    def _ensure_effective_config(self) -> None:
        if self.scope_override_path.exists():
            write_merged_config(
                self.config_path,
                self.scope_override_path,
                self.effective_config_path,
            )

    def _read_scope_from_override(self) -> Optional[Dict]:
        if not self.scope_override_path.exists():
            return None
        with open(self.scope_override_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        backup = data.get("backup", {})
        if not isinstance(backup, dict):
            return None
        return backup

    def get_backup_scope(self) -> Dict:
        loader = self._loader()
        override_backup = self._read_scope_from_override()
        if override_backup is not None:
            organizations = override_backup.get("organizations", [])
            if not isinstance(organizations, list):
                organizations = []
            check_mirror_only = bool(override_backup.get("check_mirror_only", False))
            scope_source = str(self.scope_override_path)
        else:
            raw = loader.load_raw_yaml() if self.config_path.exists() else {}
            backup = raw.get("backup", {})
            organizations = backup.get("organizations", [])
            if not isinstance(organizations, list):
                organizations = []
            check_mirror_only = bool(backup.get("check_mirror_only", False))
            scope_source = str(self.config_path)

        base_loader = ConfigLoader(str(self.config_path))
        available = base_loader.list_gitea_organizations()
        warnings = base_loader.get_backup_scope_warnings()
        if self.scope_override_path.exists():
            warnings = list(warnings)
            warnings.append(
                f"备份范围已保存到可写覆盖文件: {self.scope_override_path}"
            )
            warnings.append(
                "定时任务与手动 backup 需挂载 web/data 后才会读取合并配置"
            )

        effective_loader = self._loader()
        effective_orgs = effective_loader.get("backup.organizations", [])
        effective_mirror = effective_loader.get("backup.check_mirror_only", False)

        return {
            "organizations": organizations,
            "check_mirror_only": check_mirror_only,
            "available_organizations": available,
            "effective_organizations": effective_orgs if isinstance(effective_orgs, list) else [],
            "effective_check_mirror_only": bool(effective_mirror),
            "warnings": warnings,
            "config_path": scope_source,
        }

    def update_backup_scope(
        self, organizations: List[str], check_mirror_only: bool
    ) -> Dict:
        cleaned_orgs = sorted(
            {org.strip() for org in organizations if org and org.strip()}
        )
        self.web_data_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "backup": {
                "organizations": cleaned_orgs,
                "check_mirror_only": check_mirror_only,
            }
        }
        with open(self.scope_override_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        write_merged_config(
            self.config_path,
            self.scope_override_path,
            self.effective_config_path,
        )
        return self.get_backup_scope()
