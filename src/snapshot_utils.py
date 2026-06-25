"""快照受保护标记：使用侧车文件，禁止落在快照目录内（cp -al 会硬链接继承）"""

from pathlib import Path


def protection_marker_path(snapshot_dir: Path, snapshot_name: str) -> Path:
    """侧车保护标记：snapshots/<快照ID>.protected"""
    return snapshot_dir / f"{snapshot_name}.protected"


def is_snapshot_protected(snapshot_path: Path) -> bool:
    """仅侧车标记视为受保护（目录内的 .protected 为误继承/遗留）"""
    return protection_marker_path(snapshot_path.parent, snapshot_path.name).exists()


def clear_inline_protection_artifact(snapshot_path: Path) -> bool:
    """仅移除快照目录内遗留的 .protected（误继承），不触碰侧车标记"""
    inside = snapshot_path / ".protected"
    if inside.exists():
        inside.unlink()
        return True
    return False


def clear_protection_markers(snapshot_path: Path) -> int:
    """清除指定快照的保护标记（侧车 + 目录内遗留）"""
    cleared = 0
    if clear_inline_protection_artifact(snapshot_path):
        cleared += 1
    sidecar = protection_marker_path(snapshot_path.parent, snapshot_path.name)
    if sidecar.exists():
        sidecar.unlink()
        cleared += 1
    return cleared
