"""单仓备份 CLI 参数测试"""

from pathlib import Path

import pytest

from gitea_mirror_backup import resolve_repo_path


def test_resolve_repo_path(tmp_path):
    repos_path = tmp_path / "repositories"
    (repos_path / "org" / "my-repo.git").mkdir(parents=True)
    repo_path = resolve_repo_path("org/my-repo", repos_path)
    assert repo_path == repos_path / "org" / "my-repo.git"


def test_resolve_repo_path_strips_git_suffix(tmp_path):
    repos_path = tmp_path / "repositories"
    (repos_path / "org" / "my-repo.git").mkdir(parents=True)
    repo_path = resolve_repo_path("org/my-repo.git", repos_path)
    assert repo_path == repos_path / "org" / "my-repo.git"


def test_resolve_repo_path_invalid(tmp_path):
    repos_path = tmp_path / "repositories"
    repos_path.mkdir()
    with pytest.raises(ValueError):
        resolve_repo_path("invalid", repos_path)


def test_resolve_repo_path_not_found(tmp_path):
    repos_path = tmp_path / "repositories"
    repos_path.mkdir()
    with pytest.raises(FileNotFoundError):
        resolve_repo_path("org/missing", repos_path)
