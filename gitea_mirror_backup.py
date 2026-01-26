#!/usr/bin/env python3
"""
Gitea Docker 镜像仓库备份系统
适用于: Docker 运行的 Gitea
功能: 每日快照 + 每周汇总报告
"""

import sys
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Optional, List
import argparse

# 导入配置加载器
try:
    from src.config_loader import Config
except ImportError:
    print("错误: 无法导入配置加载器")
    print("请确保 src/config_loader.py 存在")
    sys.exit(1)

# 导入通知系统（可选）
try:
    from src.notifier import NotificationManager

    NOTIFIER_AVAILABLE = True
except ImportError:
    NotificationManager = None
    NOTIFIER_AVAILABLE = False


# ============ 日志配置 ============
def setup_logging(config_instance: Config):
    """设置日志"""
    # 确保日志文件存在
    log_file = Path(config_instance.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.touch(exist_ok=True)

    # 获取日志级别
    log_level = getattr(logging, config_instance.LOG_LEVEL.upper(), logging.INFO)

    # 获取日志格式
    loader = config_instance.get_loader()
    log_format = loader.get('logging.format', '[%(asctime)s] %(message)s')
    date_format = loader.get('logging.date_format', '%Y-%m-%d %H:%M:%S')

    # 配置日志格式
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(config_instance.LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


# 全局变量，稍后初始化
logger = None
config = None
notifier = None


# ============ 工具函数 ============
def run_command(
    cmd: List[str], check=True, capture_output=True
) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, check=check, capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            logger.error(f"命令执行失败: {' '.join(cmd)}")
            logger.error(f"错误输出: {e.stderr}")
            raise
        return e


def check_docker_container() -> bool:
    """检查 Docker 容器是否运行"""
    try:
        result = run_command(['docker', 'ps'], check=False)
        if config.DOCKER_CONTAINER in result.stdout:
            logger.info("✓ Docker 容器运行正常")
            return True
        else:
            logger.error(f"Docker 容器 {config.DOCKER_CONTAINER} 未运行")
            return False
    except Exception as e:
        logger.error(f"检查 Docker 容器失败: {e}")
        return False


def get_directory_size(path: Path) -> int:
    """获取目录大小（KB）"""
    try:
        result = run_command(['du', '-sk', str(path)])
        return int(result.stdout.split()[0])
    except Exception as e:
        logger.warning(f"获取目录大小失败 {path}: {e}")
        return 0


def get_commit_count(repo_path: Path) -> int:
    """获取仓库的提交总数"""
    try:
        owner = repo_path.parent.name
        repo = repo_path.name
        container_path = f"/data/git/repositories/{owner}/{repo}"

        # 在容器中使用 git 用户执行 git rev-list --all --count
        result = run_command(
            [
                'docker',
                'exec',
                '-u',
                config.DOCKER_GIT_USER,
                config.DOCKER_CONTAINER,
                'git',
                '-C',
                container_path,
                'rev-list',
                '--all',
                '--count',
            ],
            check=False,
        )

        if result.returncode == 0:
            return int(result.stdout.strip())
        else:
            logger.warning(f"无法获取提交数 {repo_path}: {result.stderr}")
            return 0
    except Exception as e:
        logger.warning(f"获取提交数失败 {repo_path}: {e}")
        return 0


def is_mirror_repo(repo_path: Path) -> bool:
    """检查是否是镜像仓库"""
    if not config.CHECK_MIRROR_ONLY:
        logger.info("    CHECK_MIRROR_ONLY=False，备份所有仓库")
        return True  # 不检查，备份所有仓库

    try:
        owner = repo_path.parent.name
        repo = repo_path.name
        container_path = f"/data/git/repositories/{owner}/{repo}"

        logger.info(f"    检查容器路径: {container_path}")
        result = run_command(
            [
                'docker',
                'exec',
                '-u',
                config.DOCKER_GIT_USER,
                config.DOCKER_CONTAINER,
                'git',
                '-C',
                container_path,
                'config',
                '--get',
                'remote.origin.url',
            ],
            check=False,
        )

        if result.returncode == 0:
            logger.info(f"    ✓ 是镜像仓库，remote.origin.url: {result.stdout.strip()}")
            return True
        else:
            logger.info("    ✗ 不是镜像仓库，未找到 remote.origin.url")
            return False
    except Exception as e:
        logger.warning(f"    检查镜像仓库失败 {repo_path}: {e}")
        return False


# ============ 备份功能 ============
class RepositoryBackup:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.owner = repo_path.parent.name
        self.repo_name = repo_path.name.replace('.git', '')
        self.full_name = f"{self.owner}/{self.repo_name}"
        self.backup_dir = Path(config.BACKUP_ROOT) / self.owner / self.repo_name
        self.snapshot_dir = self.backup_dir / "snapshots"
        self.archive_dir = self.backup_dir / "archives"

    def should_backup(self) -> bool:
        """检查是否应该备份这个仓库"""
        # 检查组织过滤（大小写不敏感）
        if config.BACKUP_ORGANIZATIONS:
            logger.info(f"    组织过滤: {config.BACKUP_ORGANIZATIONS}")
            logger.info(f"    当前组织: {self.owner}")

            # 将组织名转换为小写进行比较
            owner_lower = self.owner.lower()
            orgs_lower = [org.lower() for org in config.BACKUP_ORGANIZATIONS]

            if owner_lower not in orgs_lower:
                logger.info(f"    ❌ 跳过 {self.full_name}: 不在备份组织列表中")
                return False
            logger.info("    ✓ 组织匹配")

        # 检查是否是镜像仓库
        logger.info(f"    检查镜像仓库: CHECK_MIRROR_ONLY={config.CHECK_MIRROR_ONLY}")
        if not is_mirror_repo(self.repo_path):
            logger.info(f"    ❌ 跳过 {self.full_name}: 不是镜像仓库")
            return False

        logger.info(f"    ✓ 将备份 {self.full_name}")
        return True

    def create_snapshot(self) -> Optional[Path]:
        """创建快照，返回快照路径"""
        try:
            date_stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            snapshot_path = self.snapshot_dir / date_stamp

            # 创建快照目录
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"  创建快照目录: {self.snapshot_dir}")

            logger.info(f"  创建快照: {self.full_name}")

            # 尝试使用硬链接创建快照 (cp -al)，如果失败则使用普通复制
            result = run_command(
                ['cp', '-al', str(self.repo_path), str(snapshot_path)], check=False
            )

            if result.returncode != 0:
                # 硬链接失败（可能是跨文件系统），使用普通复制
                if (
                    "Invalid cross-device link" in result.stderr
                    or "cross-device" in result.stderr.lower()
                ):
                    logger.warning("  ⚠️  无法使用硬链接（跨文件系统），使用普通复制...")
                    result = run_command(
                        ['cp', '-a', str(self.repo_path), str(snapshot_path)],
                        check=False,
                    )

                if result.returncode != 0:
                    logger.error(f"  ✗ 快照失败: {self.full_name}")
                    logger.error(f"  错误: {result.stderr}")
                    return None

            # 获取当前提交数
            current_commits = get_commit_count(self.repo_path)

            # 记录元数据
            meta_file = snapshot_path / ".snapshot_meta"
            with open(meta_file, 'w') as f:
                f.write(f"timestamp={datetime.now().isoformat()}\n")
                f.write(f"source={self.repo_path}\n")
                f.write(f"repo_name={self.full_name}\n")
                f.write(f"commit_count={current_commits}\n")

            logger.info(f"  ✓ 快照成功: {date_stamp} (提交数: {current_commits})")
            return snapshot_path

        except Exception as e:
            logger.error(f"  ✗ 创建快照失败 {self.full_name}: {e}")
            return None

    def check_commit_changes(
        self, snapshot_path: Optional[Path] = None
    ) -> Optional[int]:
        """检测提交数变化，返回减少百分比。如果检测到异常，保护上一次的快照（正常状态）"""
        commit_tracking_file = self.backup_dir / ".commit_tracking"
        size_tracking_file = self.backup_dir / ".size_tracking"

        # 获取当前提交数和大小
        current_commits = get_commit_count(self.repo_path)
        current_size = get_directory_size(self.repo_path)

        # 首次备份
        if not commit_tracking_file.exists():
            commit_tracking_file.parent.mkdir(parents=True, exist_ok=True)
            commit_tracking_file.write_text(str(current_commits))
            size_tracking_file.write_text(str(current_size))
            logger.info(f"  初始提交数: {current_commits}, 大小: {current_size}KB")
            return None

        # 读取上次的提交数和大小
        try:
            prev_commits = int(commit_tracking_file.read_text().strip())
            prev_size = (
                int(size_tracking_file.read_text().strip())
                if size_tracking_file.exists()
                else 0
            )
        except Exception as e:
            logger.warning(f"读取跟踪文件失败: {e}")
            commit_tracking_file.write_text(str(current_commits))
            size_tracking_file.write_text(str(current_size))
            return None

        # 检查提交数是否显著减少
        alert_triggered = False
        alert_messages = []

        if current_commits < prev_commits:
            decrease_percent = ((prev_commits - current_commits) * 100) // prev_commits

            if decrease_percent > config.COMMIT_DECREASE_THRESHOLD:
                alert_triggered = True
                alert_messages.append(f"提交数异常减少: {decrease_percent}%")
                alert_messages.append(
                    f"上次: {prev_commits} commits → 当前: {current_commits} commits"
                )
                logger.warning(
                    f"  ⚠️  提交数减少 {decrease_percent}% (从 {prev_commits} 到 {current_commits})"
                )

        # 同时检查大小变化（辅助参考）
        if current_size < prev_size:
            size_decrease = ((prev_size - current_size) * 100) // prev_size
            if size_decrease > config.SIZE_DECREASE_THRESHOLD:
                if not alert_triggered:
                    alert_messages.append(f"仓库大小异常减少: {size_decrease}%")
                else:
                    alert_messages.append(f"同时仓库大小减少: {size_decrease}%")
                alert_messages.append(f"上次: {prev_size}KB → 当前: {current_size}KB")
                logger.warning(f"  ⚠️  大小减少 {size_decrease}%")
                alert_triggered = True

        # 如果触发告警，记录到文件
        if alert_triggered:
            alert_file = self.backup_dir / ".alerts"
            with open(alert_file, 'a') as f:
                f.write(f"\n[{datetime.now().isoformat()}]\n")
                for msg in alert_messages:
                    f.write(f"{msg}\n")
                f.write("可能原因: force push、分支删除或历史重写\n")

            # 添加到审核列表
            need_review_file = Path(config.BACKUP_ROOT) / ".need_review"
            with open(need_review_file, 'a') as f:
                f.write(f"{self.full_name}\n")

            # 保护上一次的快照（异常发生前的正常状态）
            if config.PROTECT_ABNORMAL_SNAPSHOTS:
                previous_snapshot = self.get_previous_snapshot(snapshot_path)
                if previous_snapshot:
                    self.protect_snapshot(previous_snapshot, alert_messages)
                else:
                    logger.warning("  ⚠️  未找到上一次快照，无法自动保护")

            # 更新跟踪记录
            commit_tracking_file.write_text(str(current_commits))
            size_tracking_file.write_text(str(current_size))
            return decrease_percent if current_commits < prev_commits else size_decrease

        # 更新跟踪记录
        commit_tracking_file.write_text(str(current_commits))
        size_tracking_file.write_text(str(current_size))
        return None

    def get_previous_snapshot(self, current_snapshot: Optional[Path]) -> Optional[Path]:
        """获取上一次的快照（当前快照之前的最近快照）"""
        if not self.snapshot_dir.exists():
            return None

        try:
            # 获取所有快照，按时间排序（最新的在前）
            snapshots = sorted(
                [s for s in self.snapshot_dir.iterdir() if s.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            if not snapshots:
                return None

            # 如果提供了当前快照，找到它之前的快照
            if current_snapshot:
                for i, snapshot in enumerate(snapshots):
                    if snapshot == current_snapshot:
                        # 返回下一个（更早的）快照
                        if i + 1 < len(snapshots):
                            logger.info(f"  找到上一次快照: {snapshots[i + 1].name}")
                            return snapshots[i + 1]
                        break

            # 如果没有找到或没提供当前快照，返回最新的（第一个）
            if snapshots:
                logger.info(f"  找到上一次快照: {snapshots[0].name}")
                return snapshots[0]
            return None

        except Exception as e:
            logger.warning(f"查找上一次快照失败: {e}")
            return None

    def protect_snapshot(self, snapshot_path: Path, reasons: List[str]):
        """标记快照为永久保留"""
        try:
            protect_file = snapshot_path / ".protected"
            with open(protect_file, 'w') as f:
                f.write("# 此快照已被标记为永久保留\n")
                f.write("# 保护原因: 异常发生前的正常状态\n")
                f.write(f"# 标记时间: {datetime.now().isoformat()}\n")
                f.write(f"# 仓库: {self.full_name}\n")
                f.write("#\n")
                f.write("# 检测到的异常（发生在此快照之后）:\n")
                for reason in reasons:
                    f.write(f"#   - {reason}\n")
                f.write("#\n")
                f.write("# 此快照保存的是异常发生前的正常状态，可安全恢复\n")
                f.write("# 如需取消保护，删除此文件即可\n")
            logger.info(
                f"  🔒 快照已标记为永久保留: {snapshot_path.name} （异常前的正常状态）"
            )
        except Exception as e:
            logger.warning(f"标记快照保护失败: {e}")

    def cleanup_old_snapshots(self):
        """清理旧快照（跳过被保护的快照）"""
        if not self.snapshot_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=config.SNAPSHOT_RETENTION_DAYS)
        deleted_count = 0
        protected_count = 0

        for snapshot in self.snapshot_dir.iterdir():
            if not snapshot.is_dir():
                continue

            # 检查是否被保护
            protect_file = snapshot / ".protected"
            if protect_file.exists():
                protected_count += 1
                continue  # 跳过被保护的快照

            # 检查修改时间
            mtime = datetime.fromtimestamp(snapshot.stat().st_mtime)
            if mtime < cutoff_date:
                try:
                    shutil.rmtree(snapshot)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"删除旧快照失败 {snapshot}: {e}")

        if deleted_count > 0:
            logger.info(f"  清理旧快照: {deleted_count} 个")
        if protected_count > 0:
            logger.info(f"  跳过受保护快照: {protected_count} 个")

    def create_monthly_archive(self):
        """创建月度归档"""
        month_stamp = datetime.now().strftime('%Y%m')
        archive_file = self.archive_dir / f"archive-{month_stamp}.bundle"

        # 检查本月是否已创建
        if archive_file.exists():
            return

        self.archive_dir.mkdir(parents=True, exist_ok=True)
        logger.info("  创建月度归档...")

        try:
            # 在容器中创建 bundle
            container_repo_path = (
                f"/data/git/repositories/{self.owner}/{self.repo_name}.git"
            )

            # 创建 bundle
            run_command(
                [
                    'docker',
                    'exec',
                    '-u',
                    config.DOCKER_GIT_USER,
                    config.DOCKER_CONTAINER,
                    'git',
                    '-C',
                    container_repo_path,
                    'bundle',
                    'create',
                    '/tmp/temp.bundle',
                    '--all',
                ]
            )

            # 复制到宿主机
            run_command(
                [
                    'docker',
                    'cp',
                    f"{config.DOCKER_CONTAINER}:/tmp/temp.bundle",
                    str(archive_file),
                ]
            )

            # 删除临时文件
            run_command(
                [
                    'docker',
                    'exec',
                    '-u',
                    config.DOCKER_GIT_USER,
                    config.DOCKER_CONTAINER,
                    'rm',
                    '/tmp/temp.bundle',
                ]
            )

            logger.info("  ✓ 归档成功")

            # 清理旧归档
            cutoff_date = datetime.now() - timedelta(
                days=config.ARCHIVE_RETENTION_MONTHS * 30
            )
            for archive in self.archive_dir.glob("*.bundle"):
                mtime = datetime.fromtimestamp(archive.stat().st_mtime)
                if mtime < cutoff_date:
                    archive.unlink()

        except Exception as e:
            logger.error(f"  ✗ 创建归档失败: {e}")

    def process(self):
        """处理单个仓库的完整备份流程"""
        logger.info("=" * 50)
        logger.info(f"处理仓库: {self.full_name}")
        logger.info(f"仓库路径: {self.repo_path}")

        # 1. 创建快照
        snapshot_path = self.create_snapshot()
        if not snapshot_path:
            logger.error("快照创建失败，跳过后续操作")
            return

        # 2. 检测提交数和大小变化（如果异常会自动标记快照为永久保留）
        self.check_commit_changes(snapshot_path)

        # 3. 清理旧快照（跳过被保护的）
        self.cleanup_old_snapshots()

        # 4. 每月1号创建归档
        if datetime.now().day == 1:
            self.create_monthly_archive()

        # 5. 生成恢复脚本
        self.generate_restore_script()

    def generate_restore_script(self):
        """生成恢复脚本"""
        restore_script = self.backup_dir / "restore.sh"

        script_content = f"""#!/bin/bash

REPO_NAME="{self.full_name}"
SNAPSHOT_DIR="{self.snapshot_dir}"
CONTAINER="{config.DOCKER_CONTAINER}"
GIT_USER="{config.DOCKER_GIT_USER}"
CONTAINER_REPO_PATH="/data/git/repositories/{self.owner}/{self.repo_name}.git"
HOST_REPO_PATH="{self.repo_path}"

echo "=========================================="
echo "Gitea 镜像仓库恢复工具"
echo "=========================================="
echo "仓库: $REPO_NAME"
echo ""

# 列出可用快照
echo "可用的快照:"
mapfile -t snapshots < <(ls -td "$SNAPSHOT_DIR"/* 2>/dev/null)
if [ ${{#snapshots[@]}} -eq 0 ]; then
    echo "错误: 没有找到快照"
    exit 1
fi

# 显示快照（索引从1开始）
for i in "${{!snapshots[@]}}"; do
    snapshot_name=$(basename "${{snapshots[$i]}}")
    display_num=$((i + 1))
    echo "  [$display_num] $snapshot_name"

    # 显示快照信息
    if [ -f "${{snapshots[$i]}}/.snapshot_meta" ]; then
        grep timestamp "${{snapshots[$i]}}/.snapshot_meta" | sed 's/^/         /'
    fi
done

echo ""
echo "恢复选项:"
echo "  1) 恢复到原仓库位置（会覆盖现有仓库）"
echo "  2) 导出为新仓库（不影响原仓库）"
echo "  3) 导出为 Git Bundle 文件"
echo ""
read -p "选择恢复方式 [1]: " restore_mode
restore_mode=${{restore_mode:-1}}

echo ""
read -p "选择要恢复的快照编号 [1]: " choice
choice=${{choice:-1}}

# 转换为数组索引（从0开始）
array_index=$((choice - 1))

if [ $array_index -lt 0 ] || [ -z "${{snapshots[$array_index]}}" ]; then
    echo "错误: 无效的选择"
    exit 1
fi

SELECTED_SNAPSHOT="${{snapshots[$array_index]}}"
echo ""
echo "已选择快照: $(basename $SELECTED_SNAPSHOT)"
echo ""

case $restore_mode in
    1)
        # 恢复到原位置
        echo "⚠️  警告: 此操作将覆盖容器中的原仓库"
        echo "⚠️  注意: 如果这是镜像仓库，下次同步时可能再次被源仓库覆盖"
        read -p "确认继续? (yes/NO): " confirm

        if [ "$confirm" != "yes" ]; then
            echo "已取消"
            exit 0
        fi

        echo ""
        echo "正在恢复到原位置..."

        # 停止容器
        echo "1. 停止 Docker 容器..."
        docker stop $CONTAINER

        # 备份当前仓库
        BACKUP_CURRENT="${{HOST_REPO_PATH}}.backup-$(date +%Y%m%d-%H%M%S)"
        echo "2. 备份当前仓库到: $BACKUP_CURRENT"
        mv "$HOST_REPO_PATH" "$BACKUP_CURRENT"

        # 恢复快照
        echo "3. 恢复快照..."
        cp -a "$SELECTED_SNAPSHOT" "$HOST_REPO_PATH"

        # 修复权限
        echo "4. 修复文件权限..."
        docker exec $CONTAINER chown -R git:git "$CONTAINER_REPO_PATH"

        # 启动容器
        echo "5. 启动 Docker 容器..."
        docker start $CONTAINER

        # 等待容器启动
        sleep 2

        # 更新 server info（修复 git hooks）
        echo "6. 更新仓库信息..."
        docker exec -u $GIT_USER $CONTAINER git -C "$CONTAINER_REPO_PATH" update-server-info

        echo ""
        echo "✓ 恢复完成!"
        echo ""
        echo "如需回滚，当前仓库已备份至:"
        echo "  $BACKUP_CURRENT"
        echo ""
        echo "验证命令:"
        echo "  docker exec -u $GIT_USER $CONTAINER git -C $CONTAINER_REPO_PATH log --oneline -5"
        ;;

    2)
        # 导出为新仓库
        echo "导出为新仓库（独立副本，不影响原仓库）"
        read -p "输入新仓库名称（如 test-restored）: " new_repo_name

        if [ -z "$new_repo_name" ]; then
            echo "错误: 仓库名称不能为空"
            exit 1
        fi

        # 导出路径
        EXPORT_PATH="${{HOST_REPO_PATH%/*}}/${{new_repo_name}}.git"

        if [ -d "$EXPORT_PATH" ]; then
            echo "错误: 仓库已存在: $EXPORT_PATH"
            exit 1
        fi

        echo ""
        echo "正在导出新仓库..."

        # 复制快照
        echo "1. 复制仓库数据..."
        cp -a "$SELECTED_SNAPSHOT" "$EXPORT_PATH"

        # 修复文件权限
        echo "2. 修复文件权限..."
        # 在宿主机上修复权限（获取 git 用户的 UID/GID）
        GIT_UID=$(docker exec $CONTAINER id -u git 2>/dev/null || echo "1000")
        GIT_GID=$(docker exec $CONTAINER id -g git 2>/dev/null || echo "1000")
        echo "   设置所有者为 $GIT_UID:$GIT_GID"
        chown -R $GIT_UID:$GIT_GID "$EXPORT_PATH"

        # 更新配置（移除镜像配置）
        NEW_CONTAINER_PATH="/data/git/repositories/$(basename $(dirname $EXPORT_PATH))/${{new_repo_name}}.git"
        echo "3. 移除镜像配置..."
        docker exec -u $GIT_USER $CONTAINER git -C "$NEW_CONTAINER_PATH" config --unset remote.origin.url 2>/dev/null || true
        docker exec -u $GIT_USER $CONTAINER git -C "$NEW_CONTAINER_PATH" config --unset remote.origin.fetch 2>/dev/null || true
        docker exec -u $GIT_USER $CONTAINER git -C "$NEW_CONTAINER_PATH" update-server-info

        echo ""
        echo "✓ 仓库导出完成!"
        echo ""
        echo "新仓库位置: $EXPORT_PATH"
        echo ""

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✓ 仓库文件已导出完成!"
        echo ""
        # 获取实际的文件系统路径（小写）
        OWNER_NAME=$(basename $(dirname $EXPORT_PATH))
        SEARCH_PATH="$OWNER_NAME/$new_repo_name"

        echo "新仓库位置: $EXPORT_PATH"
        echo ""
        echo "📋 下一步：在 Gitea 中采集仓库"
        echo ""
        echo "由于 Gitea 没有命令行采集功能，需要手动操作："
        echo ""
        echo "1. 登录 Gitea 管理员账号"
        echo ""
        echo "2. 进入管理后台："
        echo "   访问: http://your-gitea/-/admin/repos/unadopted"
        echo "   或点击: 右上角头像 -> 管理后台 -> 仓库管理 -> 未采集的Git仓库"
        echo ""
        echo "3. 搜索仓库（重要！区分大小写）："
        echo "   在搜索框输入: $SEARCH_PATH"
        echo "   ⚠️  注意: 必须使用实际文件系统路径（小写），大小写敏感"
        echo ""
        echo "4. 找到仓库后，点击右侧的「采集」按钮"
        echo ""
        echo "5. 完成！访问: http://your-gitea/$SEARCH_PATH"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ;;

    3)
        # 导出为 Bundle
        read -p "输入 Bundle 文件保存路径 [/tmp/${{REPO_NAME//\\//-}}.bundle]: " bundle_path
        bundle_path=${{bundle_path:-/tmp/${{REPO_NAME//\\//-}}.bundle}}

        echo ""
        echo "正在导出 Git Bundle..."

        # 临时挂载快照到容器
        TMP_MOUNT="/tmp/restore-${{RANDOM}}"
        mkdir -p "$TMP_MOUNT"
        cp -a "$SELECTED_SNAPSHOT" "$TMP_MOUNT/repo.git"

        # 创建 bundle
        docker exec -u $GIT_USER $CONTAINER sh -c "cd /tmp && git clone --bare $TMP_MOUNT/repo.git temp-repo.git && cd temp-repo.git && git bundle create /tmp/export.bundle --all"

        # 复制 bundle 到宿主机
        docker cp "$CONTAINER:/tmp/export.bundle" "$bundle_path"

        # 清理
        docker exec $CONTAINER rm -rf /tmp/temp-repo.git /tmp/export.bundle
        rm -rf "$TMP_MOUNT"

        echo ""
        echo "✓ 导出完成!"
        echo ""
        echo "Bundle 文件: $bundle_path"
        echo ""
        echo "使用方法:"
        echo "  git clone $bundle_path restored-repo"
        ;;

    *)
        echo "错误: 无效的恢复方式"
        exit 1
        ;;
esac
"""

        restore_script.write_text(script_content)
        restore_script.chmod(0o755)


# ============ 报告生成 ============
def send_backup_notification(processed_count: int, skipped_count: int):
    """发送备份通知"""
    if not notifier:
        return

    backup_root = Path(config.BACKUP_ROOT)
    need_review_file = backup_root / ".need_review"
    has_alerts = need_review_file.exists() and need_review_file.stat().st_size > 0

    # 收集统计信息
    total_repos = 0
    total_commits = 0
    total_snapshots = 0
    alert_repos = []

    for org_dir in backup_root.iterdir():
        if not org_dir.is_dir() or org_dir.name.startswith('.'):
            continue
        for repo_dir in org_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            total_repos += 1

            # 统计快照
            snapshot_dir = repo_dir / "snapshots"
            if snapshot_dir.exists():
                total_snapshots += len(
                    [s for s in snapshot_dir.iterdir() if s.is_dir()]
                )

            # 统计提交数
            commit_file = repo_dir / ".commit_tracking"
            if commit_file.exists():
                try:
                    commits = int(commit_file.read_text().strip())
                    total_commits += commits
                except Exception:
                    pass

            # 检查异常
            alert_file = repo_dir / ".alerts"
            if alert_file.exists():
                repo_name = f"{org_dir.name}/{repo_dir.name}"
                alert_repos.append(repo_name)

    # 构建报告数据
    report_data = {
        'total_repos': total_repos,
        'total_commits': total_commits,
        'total_snapshots': total_snapshots,
        'processed_count': processed_count,
        'skipped_count': skipped_count,
        'has_alerts': has_alerts,
        'alert_repos': alert_repos,
        'total_size_mb': 0,  # 可以添加大小统计
    }

    # 发送通知
    notifier.send_backup_report(report_data)
    logger.info("备份通知已发送")


def cleanup_old_reports():
    """清理旧报告（跳过被保护的报告）"""
    report_dir = Path(config.REPORT_DIR)
    if not report_dir.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=config.REPORT_RETENTION_DAYS)
    deleted_count = 0
    protected_count = 0

    for report_file in report_dir.glob("report-*.md"):
        try:
            # 检查是否被保护
            protect_file = report_file.with_suffix('.md.protected')
            if protect_file.exists():
                protected_count += 1
                continue  # 跳过被保护的报告

            mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
            if mtime < cutoff_date:
                report_file.unlink()
                deleted_count += 1
        except Exception as e:
            logger.warning(f"删除旧报告失败 {report_file}: {e}")

    if deleted_count > 0:
        logger.info(f"清理了 {deleted_count} 个旧报告")
    if protected_count > 0:
        logger.info(f"跳过受保护报告: {protected_count} 个")


def generate_report():
    """生成备份报告"""
    logger.info("生成备份报告...")

    backup_root = Path(config.BACKUP_ROOT)
    report_dir = Path(config.REPORT_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)

    # 生成带时间戳的报告文件
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    report_file = report_dir / f"report-{timestamp}.md"
    latest_report = Path(config.LATEST_REPORT)

    # 统计信息
    total_repos = 0
    total_snapshots = 0
    total_archives = 0
    total_size = 0
    total_commits = 0
    repo_details = []

    # 遍历所有仓库
    for org_dir in backup_root.iterdir():
        if not org_dir.is_dir() or org_dir.name.startswith('.'):
            continue

        for repo_dir in org_dir.iterdir():
            if not repo_dir.is_dir():
                continue

            repo_name = f"{org_dir.name}/{repo_dir.name}"
            total_repos += 1

            # 统计快照
            snapshot_count = 0
            protected_snapshot_count = 0
            latest_snapshot = "无"
            snapshot_dir = repo_dir / "snapshots"
            if snapshot_dir.exists():
                snapshots = sorted(
                    snapshot_dir.iterdir(),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                )
                all_snapshots = [s for s in snapshots if s.is_dir()]
                snapshot_count = len(all_snapshots)
                # 统计受保护的快照
                protected_snapshot_count = len(
                    [s for s in all_snapshots if (s / ".protected").exists()]
                )
                if snapshots:
                    latest_snapshot = snapshots[0].name
                total_snapshots += snapshot_count

            # 统计归档
            archive_count = 0
            archive_dir = repo_dir / "archives"
            if archive_dir.exists():
                archive_count = len(list(archive_dir.glob("*.bundle")))
                total_archives += archive_count

            # 计算大小
            dir_size = get_directory_size(repo_dir)
            total_size += dir_size

            # 读取提交数和历史变化
            commit_count = "N/A"
            commit_change = None
            commit_tracking_file = repo_dir / ".commit_tracking"
            if commit_tracking_file.exists():
                try:
                    commit_count = commit_tracking_file.read_text().strip()
                    if commit_count.isdigit():
                        total_commits += int(commit_count)
                except Exception:
                    pass

            # 检查是否有提交数变化告警
            alert_file = repo_dir / ".alerts"
            if alert_file.exists():
                try:
                    alert_content = alert_file.read_text()
                    # 查找最后一次提交数变化记录
                    if "提交数异常减少" in alert_content:
                        lines = alert_content.strip().split('\n')
                        for line in lines:
                            if "提交数异常减少" in line:
                                commit_change = line
                                break
                except Exception:
                    pass

            repo_details.append(
                {
                    'name': repo_name,
                    'snapshot_count': snapshot_count,
                    'protected_snapshots': protected_snapshot_count,
                    'latest_snapshot': latest_snapshot,
                    'archive_count': archive_count,
                    'size_kb': dir_size,
                    'commits': commit_count,
                    'commit_change': commit_change,
                }
            )

    # 检查是否有异常
    need_review_file = backup_root / ".need_review"
    has_alerts = need_review_file.exists() and need_review_file.stat().st_size > 0

    # 生成报告
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Gitea 镜像仓库备份报告\n\n")

        # 如果有异常，在标题下方标注
        if has_alerts:
            f.write("> 🔒 **此报告已自动标记为永久保留**（检测到仓库异常）\n\n")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"**生成时间**: {current_time}\n")
        f.write(f"**报告文件**: {report_file.name}\n\n")

        # 总体统计
        f.write("## 📊 总体统计\n\n")
        f.write(f"- **备份仓库数**: {total_repos}\n")
        f.write(f"- **总提交数**: {total_commits:,} commits\n")
        f.write(f"- **快照总数**: {total_snapshots}\n")
        f.write(f"- **归档总数**: {total_archives}\n")
        f.write(f"- **占用空间**: {total_size // 1024} MB\n\n")

        # 异常报告
        if has_alerts:
            f.write("## ⚠️ 需要关注的仓库\n\n")
            f.write(
                "以下仓库检测到提交数或大小异常减少，可能发生了 force push 或历史重写：\n\n"
            )

            reviewed_repos = set()
            for line in (backup_root / ".need_review").read_text().splitlines():
                repo_name = line.strip()
                if not repo_name or repo_name in reviewed_repos:
                    continue
                reviewed_repos.add(repo_name)

                alert_file = backup_root / repo_name / ".alerts"
                if alert_file.exists():
                    f.write(f"### {repo_name}\n")
                    f.write("```\n")
                    # 只显示最后20行
                    alerts = alert_file.read_text().splitlines()
                    f.write('\n'.join(alerts[-20:]))
                    f.write("\n```\n\n")

                    # 显示当前状态
                    commit_tracking_file = backup_root / repo_name / ".commit_tracking"
                    size_tracking_file = backup_root / repo_name / ".size_tracking"

                    current_info = []
                    if commit_tracking_file.exists():
                        try:
                            commits = commit_tracking_file.read_text().strip()
                            current_info.append(f"当前提交数: {commits}")
                        except Exception:
                            pass
                    if size_tracking_file.exists():
                        try:
                            size_kb = int(size_tracking_file.read_text().strip())
                            size_mb = size_kb // 1024
                            current_info.append(f"当前大小: {size_mb}MB")
                        except Exception:
                            pass

                    if current_info:
                        f.write(f"**当前状态**: {' | '.join(current_info)}\n\n")

                    # 受保护的快照
                    snapshot_dir = backup_root / repo_name / "snapshots"
                    if snapshot_dir.exists():
                        snapshots = sorted(
                            snapshot_dir.iterdir(),
                            key=lambda x: x.stat().st_mtime,
                            reverse=True,
                        )
                        latest = snapshots[0].name if snapshots else "无"
                        f.write(f"**最新快照**: {latest}\n")

                        # 列出受保护的快照
                        protected_snapshots = [
                            s.name
                            for s in snapshots
                            if s.is_dir() and (s / ".protected").exists()
                        ]
                        if protected_snapshots:
                            f.write(
                                f"**🔒 受保护快照** ({len(protected_snapshots)}个，永久保留):\n"
                            )
                            for ps in protected_snapshots[:5]:  # 只显示前5个
                                f.write(f"  - {ps}\n")
                            if len(protected_snapshots) > 5:
                                f.write(
                                    f"  - ... 还有 {len(protected_snapshots) - 5} 个\n"
                                )
                        f.write("\n")

                    f.write("**恢复命令**:\n")
                    f.write("```bash\n")
                    f.write(f"{backup_root}/{repo_name}/restore.sh\n")
                    f.write("```\n\n")
                    f.write("---\n\n")

            # 清空待审核列表
            (backup_root / ".need_review").unlink()
        else:
            f.write("## ✅ 全部正常\n\n")
            f.write("本周期内所有仓库均未检测到异常。\n\n")

        # 提交数变化统计
        repos_with_changes = [r for r in repo_details if r['commit_change']]
        if repos_with_changes:
            f.write("## 📈 提交数变化记录\n\n")
            f.write("| 仓库 | 当前提交数 | 变化情况 |\n")
            f.write("|------|-----------|----------|\n")
            for repo in repos_with_changes:
                f.write(
                    f"| {repo['name']} | {repo['commits']} | {repo['commit_change']} |\n"
                )
            f.write("\n")

        # 仓库详情
        f.write("## 📦 仓库备份详情\n\n")
        f.write(
            "| 仓库 | 提交数 | 快照数 | 受保护 | 最新快照 | 归档数 | 占用空间 | 状态 |\n"
        )
        f.write(
            "|------|--------|--------|--------|----------|--------|----------|------|\n"
        )

        for repo in repo_details:
            size_mb = repo['size_kb'] // 1024

            # 状态标识
            status = "✅"
            if repo['commit_change']:
                status = "⚠️ 提交数减少"

            # 受保护快照显示
            protected_display = (
                f"🔒 {repo['protected_snapshots']}"
                if repo['protected_snapshots'] > 0
                else "-"
            )

            f.write(
                f"| {repo['name']} | {repo['commits']} | {repo['snapshot_count']} | {protected_display} | "
                f"{repo['latest_snapshot']} | {repo['archive_count']} | {size_mb}MB | {status} |\n"
            )

        # 磁盘使用情况
        f.write("\n## 💾 磁盘使用情况\n\n")
        try:
            df_result = run_command(['df', '-h', str(backup_root)])
            lines = df_result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                f.write(f"- **分区**: {parts[0]}\n")
                f.write(f"- **总空间**: {parts[1]}\n")
                f.write(f"- **已用**: {parts[2]} ({parts[4]})\n")
                f.write(f"- **可用**: {parts[3]}\n")
        except Exception as e:
            logger.warning(f"获取磁盘使用情况失败: {e}")

        f.write("\n---\n\n")
        f.write("**说明**:\n")
        f.write("- 快照使用硬链接技术，实际占用空间远小于显示值\n")
        f.write(
            "- 报告每次备份时自动生成，历史报告保留 {} 天\n".format(
                config.REPORT_RETENTION_DAYS
            )
        )
        f.write("- 🔒 检测到异常时，对应的**快照和报告**会自动标记为**永久保留**\n")
        f.write("- 如需恢复仓库，使用对应的 restore.sh 脚本\n")
        f.write(f"- 最新报告链接: {config.LATEST_REPORT}\n")
        f.write("\n")
        f.write("**受保护资源管理**:\n")
        f.write("- 查看快照保护: `cat /path/to/snapshot/.protected`\n")
        f.write("- 查看报告保护: `cat /path/to/report-xxx.md.protected`\n")
        f.write("- 取消保护: 删除对应的 `.protected` 文件\n")
        f.write("- 再次运行备份后，超期资源将被清理\n")

    # 检查是否需要保护此报告（已经在前面检查过了）
    if has_alerts:
        # 有需要关注的仓库，保护此报告
        protect_file = report_file.with_suffix('.md.protected')
        try:
            with open(protect_file, 'w') as f:
                f.write("# 此报告已被标记为永久保留\n")
                f.write("# 保护原因: 包含异常检测记录\n")
                f.write(f"# 标记时间: {datetime.now().isoformat()}\n")
                f.write("#\n")
                f.write("# 此报告记录了仓库异常，与受保护的快照相对应\n")
                f.write("# 如需取消保护，删除此文件即可\n")
            logger.info("🔒 报告已标记为永久保留（包含异常记录）")
        except Exception as e:
            logger.warning(f"标记报告保护失败: {e}")

    # 创建或更新到最新报告的软链接（使用相对路径）
    try:
        if latest_report.exists() or latest_report.is_symlink():
            latest_report.unlink()
        # 使用相对路径创建软链接
        relative_path = report_file.relative_to(latest_report.parent)
        latest_report.symlink_to(relative_path)
        logger.info(f"✓ 报告生成: {report_file}")
        logger.info(f"✓ 最新报告: {latest_report}")
    except Exception as e:
        logger.warning(f"创建软链接失败: {e}")
        logger.info(f"✓ 报告生成: {report_file}")


# ============ 主函数 ============
def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Gitea Docker 镜像备份任务开始")
    logger.info("=" * 50)

    # 检查 Docker
    if not check_docker_container():
        sys.exit(1)

    # 确保备份目录存在
    backup_root = Path(config.BACKUP_ROOT)
    backup_root.mkdir(parents=True, exist_ok=True)

    # 获取仓库路径
    repos_path = Path(config.GITEA_DATA_VOLUME) / config.GITEA_REPOS_PATH

    if not repos_path.exists():
        logger.error(f"仓库目录不存在: {repos_path}")
        sys.exit(1)

    logger.info(f"仓库目录: {repos_path}")

    # 列出目录内容以便调试
    logger.info("扫描组织目录...")
    org_dirs = [d for d in repos_path.iterdir() if d.is_dir()]
    logger.info(f"找到 {len(org_dirs)} 个组织目录: {[d.name for d in org_dirs]}")

    # 处理所有仓库
    processed_count = 0
    skipped_count = 0

    for org_dir in repos_path.iterdir():
        if not org_dir.is_dir():
            continue

        logger.info(f"检查组织: {org_dir.name}")

        # 查找所有 .git 目录
        git_repos = list(org_dir.glob("*.git"))
        logger.info(f"  找到 {len(git_repos)} 个 .git 仓库")

        for repo_path in git_repos:
            if not repo_path.is_dir():
                continue

            try:
                backup = RepositoryBackup(repo_path)
                logger.info(f"  检查仓库: {backup.full_name}")

                if not backup.should_backup():
                    logger.info(f"  跳过: {backup.full_name}")
                    skipped_count += 1
                    continue

                backup.process()
                processed_count += 1

            except Exception as e:
                logger.error(f"处理仓库失败 {repo_path}: {e}", exc_info=True)

    logger.info(f"跳过了 {skipped_count} 个仓库")

    logger.info("=" * 50)
    logger.info(f"处理了 {processed_count} 个仓库")

    # 每次都生成报告
    generate_report()

    # 清理旧报告
    cleanup_old_reports()

    # 发送通知
    if notifier:
        try:
            send_backup_notification(processed_count, skipped_count)
        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    logger.info("=" * 50)
    logger.info("备份任务完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(
            description='Gitea Docker 镜像仓库备份系统',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  %(prog)s                          # 执行完整备份
  %(prog)s -c config.yaml           # 使用指定配置文件
  %(prog)s --report                 # 只生成报告
  %(prog)s --cleanup                # 只清理旧报告
  %(prog)s --show-config            # 显示当前配置
  %(prog)s --validate-config        # 验证配置文件

环境变量:
  GITEA_DOCKER_CONTAINER            # Docker 容器名称
  BACKUP_ROOT                       # 备份根目录
  BACKUP_ORGANIZATIONS              # 备份组织（逗号分隔）
  更多环境变量请参考文档
            """,
        )

        parser.add_argument('-c', '--config', help='配置文件路径（默认: config.yaml）')
        parser.add_argument(
            '--report', action='store_true', help='只生成报告，不执行备份'
        )
        parser.add_argument('--cleanup', action='store_true', help='只清理旧报告')
        parser.add_argument('--show-config', action='store_true', help='显示当前配置')
        parser.add_argument(
            '--validate-config', action='store_true', help='验证配置文件'
        )

        args = parser.parse_args()

        # 初始化配置
        Config.init(args.config)
        config = Config()

        # 初始化日志
        logger = setup_logging(config)

        # 初始化通知系统
        if NOTIFIER_AVAILABLE:
            try:
                notifier = NotificationManager(config)
                logger.info("通知系统已初始化")
            except Exception as e:
                logger.warning(f"通知系统初始化失败: {e}")
                notifier = None
        else:
            notifier = None
            logger.info("通知系统不可用（未安装 requests 库）")

        # 显示配置
        if args.show_config:
            config.get_loader().print_config()
            sys.exit(0)

        # 验证配置
        if args.validate_config:
            errors = config.get_loader().validate()
            if errors:
                print("\n配置错误:")
                for error in errors:
                    print(f"  ✗ {error}")
                sys.exit(1)
            else:
                print("\n✓ 配置验证通过")
                sys.exit(0)

        # 只生成报告
        if args.report:
            logger.info("手动生成报告...")
            generate_report()
            sys.exit(0)

        # 只清理旧报告
        if args.cleanup:
            logger.info("清理旧报告...")
            cleanup_old_reports()
            sys.exit(0)

        # 执行完整备份
        main()

    except KeyboardInterrupt:
        if logger:
            logger.info("\n任务被用户中断")
        sys.exit(130)
    except Exception as e:
        if logger:
            logger.error(f"任务执行失败: {e}", exc_info=True)
        else:
            print(f"错误: {e}")
        sys.exit(1)
