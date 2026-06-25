"""备份范围配置与强制删除快照测试"""

import tempfile
import unittest
from pathlib import Path

import yaml

from src.config_loader import ConfigLoader
from src.snapshot_utils import protection_marker_path
from web.services.backup_service import BackupService
from web.services.config_service import ConfigService


class TestBackupScopeConfig(unittest.TestCase):
    def test_update_backup_scope_writes_override_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_config = Path(tmp) / "config.yaml"
            web_data = Path(tmp) / "data"
            base_config.write_text(
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

            service = ConfigService(str(base_config), str(web_data))
            service.update_backup_scope(["OrgA"], True)

            override = web_data / "backup-scope.override.yaml"
            effective = web_data / "backup-config.effective.yaml"
            self.assertTrue(override.exists())
            self.assertTrue(effective.exists())
            override_data = yaml.safe_load(override.read_text(encoding="utf-8"))
            self.assertEqual(override_data["backup"]["organizations"], ["OrgA"])

            reloaded = ConfigService(str(base_config), str(web_data))
            scope = reloaded.get_backup_scope()
            self.assertEqual(scope["organizations"], ["OrgA"])
            self.assertTrue(scope["check_mirror_only"])
            self.assertEqual(scope["effective_organizations"], ["OrgA"])

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


    def test_get_snapshot_by_id_skips_pagination(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup_root = Path(tmp) / "backup"
            owner, repo = "org", "demo"
            snap_id = "20260613-020006"
            snapshot_path = backup_root / owner / repo / "snapshots" / snap_id
            snapshot_path.mkdir(parents=True)

            # 造 15 个快照，目标 ID 不在默认分页第一页
            snap_dir = backup_root / owner / repo / "snapshots"
            for i in range(15):
                (snap_dir / f"20260625-{i:06d}").mkdir(exist_ok=True)

            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(f"backup:\n  root: {backup_root}\n", encoding="utf-8")

            service = BackupService(str(backup_root), str(config_path))
            page = service.get_snapshots(repository=f"{owner}/{repo}", page=1, page_size=10)
            self.assertNotIn(snap_id, [s["id"] for s in page])

            found = service.get_snapshot_by_id(snap_id, repository=f"{owner}/{repo}")
            self.assertIsNotNone(found)
            self.assertEqual(found["id"], snap_id)


class TestEffectiveConfigAutoload(unittest.TestCase):
    def test_config_loader_prefers_effective_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_config = Path(tmp) / "config.yaml"
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            base_config.write_text(
                yaml.dump({"backup": {"organizations": [], "check_mirror_only": False}}),
                encoding="utf-8",
            )
            effective = data_dir / "backup-config.effective.yaml"
            effective.write_text(
                yaml.dump(
                    {"backup": {"organizations": ["CronOrg"], "check_mirror_only": True}}
                ),
                encoding="utf-8",
            )

            import os

            old_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                loader = ConfigLoader()
                self.assertEqual(loader.get("backup.organizations"), ["CronOrg"])
                self.assertTrue(loader.get("backup.check_mirror_only"))
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
