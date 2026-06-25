"""快照保护与上一快照定位逻辑测试"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from gitea_mirror_backup import RepositoryBackup


class SnapshotProtectionTests(unittest.TestCase):
    def _make_backup(self, snapshot_dir: Path) -> RepositoryBackup:
        repo_path = snapshot_dir.parent / "repo.git"
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        repo_path.mkdir(exist_ok=True)

        mock_config = MagicMock()
        mock_config.BACKUP_ROOT = str(snapshot_dir.parent.parent)

        with patch("gitea_mirror_backup.config", mock_config):
            backup = RepositoryBackup(repo_path)

        backup.snapshot_dir = snapshot_dir
        backup.backup_dir = snapshot_dir.parent
        backup.full_name = "anti404/repo"
        return backup

    def test_sorted_snapshots_use_name_not_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap_dir = Path(tmp) / "snapshots"
            snap_dir.mkdir()
            older = snap_dir / "20260625-020004"
            newer = snap_dir / "20260625-154615"
            older.mkdir()
            newer.mkdir()
            # 故意让旧目录 mtime 更新得更晚
            (older / "touch.txt").write_text("x")

            backup = self._make_backup(snap_dir)
            ordered = RepositoryBackup._sorted_snapshots(snap_dir)
            self.assertEqual([s.name for s in ordered], ["20260625-154615", "20260625-020004"])

    def test_get_previous_snapshot_returns_older_by_name(self):
        with patch("gitea_mirror_backup.logger", MagicMock()):
            with tempfile.TemporaryDirectory() as tmp:
                snap_dir = Path(tmp) / "snapshots"
                snap_dir.mkdir()
                first = snap_dir / "20260625-020004"
                second = snap_dir / "20260625-154615"
                first.mkdir()
                second.mkdir()
                (first / "touch.txt").write_text("x")

                backup = self._make_backup(snap_dir)
                previous = backup.get_previous_snapshot(second)
                self.assertEqual(previous.name, "20260625-020004")

    def test_get_previous_snapshot_first_snapshot_returns_none(self):
        with patch("gitea_mirror_backup.logger", MagicMock()):
            with tempfile.TemporaryDirectory() as tmp:
                snap_dir = Path(tmp) / "snapshots"
                snap_dir.mkdir()
                only = snap_dir / "20260625-154615"
                only.mkdir()

                backup = self._make_backup(snap_dir)
                self.assertIsNone(backup.get_previous_snapshot(only))

    def test_check_commit_changes_skips_zero_commit_read_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap_dir = Path(tmp) / "snapshots"
            snap_dir.mkdir()
            current = snap_dir / "20260625-154615"
            current.mkdir()

            backup = self._make_backup(snap_dir)
            backup.backup_dir.mkdir(parents=True, exist_ok=True)
            (backup.backup_dir / ".commit_tracking").write_text("139")
            (backup.backup_dir / ".size_tracking").write_text("6000")

            mock_config = MagicMock()
            mock_config.COMMIT_DECREASE_THRESHOLD = 10
            mock_config.SIZE_DECREASE_THRESHOLD = 30
            mock_config.PROTECT_ABNORMAL_SNAPSHOTS = True
            mock_config.BACKUP_ROOT = str(Path(tmp))

            with patch("gitea_mirror_backup.config", mock_config), patch(
                "gitea_mirror_backup.logger", MagicMock()
            ), patch(
                "gitea_mirror_backup.get_commit_count", return_value=0
            ), patch(
                "gitea_mirror_backup.get_directory_size", return_value=6000
            ), patch.object(
                backup, "protect_snapshot"
            ) as protect_mock:
                result = backup.check_commit_changes(current)

            self.assertIsNone(result)
            protect_mock.assert_not_called()
            self.assertFalse((current / ".protected").exists())
            self.assertFalse((snap_dir / "20260625-154615.protected").exists())
            self.assertEqual(
                (backup.backup_dir / ".commit_tracking").read_text(), "139"
            )

    def test_strip_inline_protection_on_new_snapshot(self):
        with patch("gitea_mirror_backup.logger", MagicMock()):
            with tempfile.TemporaryDirectory() as tmp:
                snap_dir = Path(tmp) / "snapshots"
                snap_dir.mkdir(parents=True)
                snap = snap_dir / "20260625-155737"
                snap.mkdir()
                (snap / ".protected").write_text("inherited")

                backup = self._make_backup(snap_dir)
                removed = backup._strip_inline_protection_artifact(snap)
                self.assertTrue(removed)
                self.assertFalse((snap / ".protected").exists())

    def test_protect_snapshot_uses_sidecar_not_inline(self):
        with patch("gitea_mirror_backup.logger", MagicMock()):
            with tempfile.TemporaryDirectory() as tmp:
                snap_dir = Path(tmp) / "snapshots"
                snap_dir.mkdir(parents=True)
                snap = snap_dir / "20260625-155737"
                snap.mkdir()

                backup = self._make_backup(snap_dir)
                backup.protect_snapshot(snap, ["测试异常"])

                self.assertTrue((snap_dir / "20260625-155737.protected").exists())
                self.assertFalse((snap / ".protected").exists())

    def test_reconcile_clears_inline_only_without_alerts(self):
        with patch("gitea_mirror_backup.logger", MagicMock()):
            with tempfile.TemporaryDirectory() as tmp:
                snap_dir = Path(tmp) / "snapshots"
                snap_dir.mkdir(parents=True)
                snap = snap_dir / "20260625-020004"
                snap.mkdir()
                (snap / ".protected").write_text("legacy")
                (snap_dir / "20260625-020004.protected").write_text("sidecar")

                backup = self._make_backup(snap_dir)
                backup.backup_dir.mkdir(parents=True, exist_ok=True)

                mock_config = MagicMock()
                mock_config.BACKUP_ROOT = str(Path(tmp))

                with patch("gitea_mirror_backup.config", mock_config):
                    cleared = backup.reconcile_stale_protection()

                self.assertEqual(cleared, 1)
                self.assertFalse((snap / ".protected").exists())
                self.assertTrue((snap_dir / "20260625-020004.protected").exists())


    def test_repair_missing_protection_restores_sidecar(self):
        with patch("gitea_mirror_backup.logger", MagicMock()):
            with tempfile.TemporaryDirectory() as tmp:
                snap_dir = Path(tmp) / "snapshots"
                snap_dir.mkdir(parents=True)
                older = snap_dir / "20260625-020004"
                newer = snap_dir / "20260625-154615"
                older.mkdir()
                newer.mkdir()

                backup = self._make_backup(snap_dir)
                backup.backup_dir.mkdir(parents=True, exist_ok=True)
                (backup.backup_dir / ".alerts").write_text(
                    "[2026-06-25] 提交数异常减少\n", encoding="utf-8"
                )

                mock_config = MagicMock()
                mock_config.BACKUP_ROOT = str(Path(tmp))
                mock_config.PROTECT_ABNORMAL_SNAPSHOTS = True

                with patch("gitea_mirror_backup.config", mock_config):
                    repaired = backup.repair_missing_protection()

                self.assertTrue(repaired)
                self.assertTrue((snap_dir / "20260625-020004.protected").exists())
                self.assertFalse((snap_dir / "20260625-154615.protected").exists())


if __name__ == "__main__":
    unittest.main()
