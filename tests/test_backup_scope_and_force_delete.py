"""备份范围配置与强制删除快照测试"""

import tempfile
import unittest
from pathlib import Path

import yaml

from src.config_loader import ConfigLoader
from src.snapshot_utils import protection_marker_path
from web.services.backup_service import BackupService


class TestBackupScopeConfig(unittest.TestCase):
    def test_update_backup_scope_writes_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(
                yaml.dump(
                    {
                        "gitea": {"data_volume": tmp, "repos_path": "repos"},
                        "backup": {"root": tmp, "organizations": [], "check_mirror_only": False},
                    },
                    default_flow_style=False,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            repos = Path(tmp) / "repos"
            repos.mkdir()
            (repos / "OrgA").mkdir()
            (repos / "OrgB").mkdir()

            loader = ConfigLoader(str(config_path))
            loader.update_backup_scope(["OrgA"], True)

            reloaded = ConfigLoader(str(config_path))
            self.assertEqual(reloaded.get("backup.organizations"), ["OrgA"])
            self.assertTrue(reloaded.get("backup.check_mirror_only"))

    def test_list_gitea_organizations(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            repos = Path(tmp) / "repos"
            repos.mkdir()
            (repos / "Alpha").mkdir()
            (repos / "Beta").mkdir()
            config_path.write_text(
                yaml.dump(
                    {
                        "gitea": {"data_volume": tmp, "repos_path": "repos"},
                        "backup": {"root": tmp},
                    },
                    default_flow_style=False,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            loader = ConfigLoader(str(config_path))
            self.assertEqual(loader.list_gitea_organizations(), ["Alpha", "Beta"])


class TestForceDeleteSnapshot(unittest.TestCase):
    def test_delete_protected_snapshot_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup_root = Path(tmp) / "backup"
            owner, repo = "org", "demo"
            snap_id = "20260625-120000"
            snapshot_path = backup_root / owner / repo / "snapshots" / snap_id
            snapshot_path.mkdir(parents=True)
            protection_marker_path(snapshot_path.parent, snap_id).write_text("protected")

            config_path = Path(tmp) / "config.yaml"
            config_path.write_text("backup:\n  root: {}\n".format(backup_root), encoding="utf-8")

            service = BackupService(str(backup_root), str(config_path))
            self.assertFalse(service.delete_snapshot(snap_id, f"{owner}/{repo}"))
            self.assertTrue(service.delete_snapshot(snap_id, f"{owner}/{repo}", force=True))
            self.assertFalse(snapshot_path.exists())
            self.assertFalse(protection_marker_path(snapshot_path.parent, snap_id).exists())


if __name__ == "__main__":
    unittest.main()
