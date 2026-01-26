#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器测试脚本
"""

import os
import sys
import tempfile

# 设置 UTF-8 输出（Windows 兼容）
if sys.platform == 'win32':
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 导入配置加载器
from config_loader import Config, ConfigLoader


def test_default_config():
    """测试默认配置"""
    print("\n" + "=" * 50)
    print("测试 1: 默认配置")
    print("=" * 50)

    loader = ConfigLoader()

    # 检查默认值
    assert loader.get('gitea.docker_container') == 'gitea'
    assert loader.get('backup.root') == '/opt/backup/gitea-mirrors'
    assert loader.get('backup.retention.snapshots_days') == 30
    assert loader.get('alerts.commit_decrease_threshold') == 10

    print("[OK] 默认配置加载成功")
    return True


def test_yaml_config():
    """测试 YAML 配置文件"""
    print("\n" + "=" * 50)
    print("测试 2: YAML 配置文件")
    print("=" * 50)

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', delete=False, encoding='utf-8'
    ) as f:
        f.write(
            """
gitea:
  docker_container: "test-gitea"
  data_volume: "/test/gitea"

backup:
  root: "/test/backup"
  organizations:
    - "TestOrg1"
    - "TestOrg2"
  retention:
    snapshots_days: 60

alerts:
  commit_decrease_threshold: 20
"""
        )
        config_file = f.name

    try:
        loader = ConfigLoader(config_file)

        # 验证配置
        assert loader.get('gitea.docker_container') == 'test-gitea'
        assert loader.get('gitea.data_volume') == '/test/gitea'
        assert loader.get('backup.root') == '/test/backup'
        assert loader.get('backup.organizations') == ['TestOrg1', 'TestOrg2']
        assert loader.get('backup.retention.snapshots_days') == 60
        assert loader.get('alerts.commit_decrease_threshold') == 20

        print("[OK] YAML 配置文件加载成功")
        return True
    finally:
        os.unlink(config_file)


def test_env_override():
    """测试环境变量覆盖"""
    print("\n" + "=" * 50)
    print("测试 3: 环境变量覆盖")
    print("=" * 50)

    # 设置环境变量
    os.environ['GITEA_DOCKER_CONTAINER'] = 'env-gitea'
    os.environ['BACKUP_ROOT'] = '/env/backup'
    os.environ['BACKUP_ORGANIZATIONS'] = 'EnvOrg1,EnvOrg2,EnvOrg3'
    os.environ['SNAPSHOT_RETENTION_DAYS'] = '90'
    os.environ['COMMIT_DECREASE_THRESHOLD'] = '15'
    os.environ['PROTECT_ABNORMAL_SNAPSHOTS'] = 'false'

    try:
        loader = ConfigLoader()

        # 验证环境变量覆盖
        assert loader.get('gitea.docker_container') == 'env-gitea'
        assert loader.get('backup.root') == '/env/backup'
        assert loader.get('backup.organizations') == ['EnvOrg1', 'EnvOrg2', 'EnvOrg3']
        assert loader.get('backup.retention.snapshots_days') == 90
        assert loader.get('alerts.commit_decrease_threshold') == 15
        assert loader.get('alerts.protect_abnormal_snapshots') is False

        print("[OK] 环境变量覆盖成功")
        return True
    finally:
        # 清理环境变量
        for key in [
            'GITEA_DOCKER_CONTAINER',
            'BACKUP_ROOT',
            'BACKUP_ORGANIZATIONS',
            'SNAPSHOT_RETENTION_DAYS',
            'COMMIT_DECREASE_THRESHOLD',
            'PROTECT_ABNORMAL_SNAPSHOTS',
        ]:
            os.environ.pop(key, None)


def test_config_class():
    """测试 Config 类（兼容性）"""
    print("\n" + "=" * 50)
    print("测试 4: Config 类兼容性")
    print("=" * 50)

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', delete=False, encoding='utf-8'
    ) as f:
        f.write(
            """
gitea:
  docker_container: "compat-gitea"
  docker_git_user: "git"
  data_volume: "/compat/gitea"
  repos_path: "git/repositories"

backup:
  root: "/compat/backup"
  organizations:
    - "CompatOrg"
  check_mirror_only: true
  retention:
    snapshots_days: 45
    archives_months: 18
    reports_days: 60

alerts:
  commit_decrease_threshold: 12
  size_decrease_threshold: 35
  protect_abnormal_snapshots: true

logging:
  file: "/var/log/compat.log"
  level: "DEBUG"
"""
        )
        config_file = f.name

    try:
        Config.init(config_file)
        config = Config()

        # 验证属性访问
        assert config.DOCKER_CONTAINER == 'compat-gitea'
        assert config.DOCKER_GIT_USER == 'git'
        assert config.GITEA_DATA_VOLUME == '/compat/gitea'
        assert config.GITEA_REPOS_PATH == 'git/repositories'
        assert config.BACKUP_ROOT == '/compat/backup'
        assert config.BACKUP_ORGANIZATIONS == ['CompatOrg']
        assert config.CHECK_MIRROR_ONLY is True
        assert config.SNAPSHOT_RETENTION_DAYS == 45
        assert config.ARCHIVE_RETENTION_MONTHS == 18
        assert config.REPORT_RETENTION_DAYS == 60
        assert config.COMMIT_DECREASE_THRESHOLD == 12
        assert config.SIZE_DECREASE_THRESHOLD == 35
        assert config.PROTECT_ABNORMAL_SNAPSHOTS is True
        assert config.LOG_FILE == '/var/log/compat.log'
        assert config.LOG_LEVEL == 'DEBUG'
        assert config.REPORT_DIR == '/compat/backup/reports'
        assert config.LATEST_REPORT == '/compat/backup/latest-report.md'

        print("[OK] Config 类兼容性测试通过")
        return True
    finally:
        os.unlink(config_file)


def test_type_conversion():
    """测试类型转换"""
    print("\n" + "=" * 50)
    print("测试 5: 类型转换")
    print("=" * 50)

    # 设置各种类型的环境变量
    os.environ['SNAPSHOT_RETENTION_DAYS'] = '100'
    os.environ['PROTECT_ABNORMAL_SNAPSHOTS'] = 'true'
    os.environ['BACKUP_ORGANIZATIONS'] = 'Org1,Org2,Org3'

    try:
        loader = ConfigLoader()

        # 验证类型转换
        days = loader.get('backup.retention.snapshots_days')
        assert isinstance(days, int) and days == 100

        protect = loader.get('alerts.protect_abnormal_snapshots')
        assert isinstance(protect, bool) and protect is True

        orgs = loader.get('backup.organizations')
        assert isinstance(orgs, list) and orgs == ['Org1', 'Org2', 'Org3']

        print("[OK] 类型转换测试通过")
        return True
    finally:
        for key in [
            'SNAPSHOT_RETENTION_DAYS',
            'PROTECT_ABNORMAL_SNAPSHOTS',
            'BACKUP_ORGANIZATIONS',
        ]:
            os.environ.pop(key, None)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("配置加载器测试套件")
    print("=" * 60)

    tests = [
        test_default_config,
        test_yaml_config,
        test_env_override,
        test_config_class,
        test_type_conversion,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"[FAIL] {test.__name__} 失败")
        except Exception as e:
            failed += 1
            print(f"[ERROR] {test.__name__} 异常: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
