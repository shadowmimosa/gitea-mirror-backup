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
            self.assertEqual(
                (backup.backup_dir / ".commit_tracking").read_text(), "139"
            )


if __name__ == "__main__":
    unittest.main()
