"""备份范围与报告统计一致性测试"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from gitea_mirror_backup import (
    _clear_scoped_need_review_entries,
    _filter_scoped_need_review_entries,
    _iter_scoped_org_dirs,
)


class BackupReportScopeTests(unittest.TestCase):
    def test_scoped_need_review_and_org_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "OrgA" / "repo1").mkdir(parents=True)
            (root / "OrgB" / "repo2").mkdir(parents=True)
            (root / ".need_review").write_text(
                "OrgA/repo1\nOrgB/repo2\n", encoding="utf-8"
            )

            mock_config = MagicMock()
            mock_config.BACKUP_ORGANIZATIONS = ["OrgA"]

            with patch("gitea_mirror_backup.config", mock_config):
                scoped_entries = _filter_scoped_need_review_entries(root)
                self.assertEqual(scoped_entries, ["OrgA/repo1"])

                org_names = [org.name for org in _iter_scoped_org_dirs(root)]
                self.assertEqual(org_names, ["OrgA"])

                _clear_scoped_need_review_entries(root)
                remaining = root / ".need_review"
                self.assertTrue(remaining.exists())
                self.assertEqual(
                    remaining.read_text(encoding="utf-8").strip(), "OrgB/repo2"
                )


if __name__ == "__main__":
    unittest.main()
