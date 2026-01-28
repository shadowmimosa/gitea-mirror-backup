#!/usr/bin/env python3
"""
配置加载器
支持 YAML 配置文件和环境变量覆盖
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("错误: 需要安装 PyYAML")
    print("请运行: pip install pyyaml")
    sys.exit(1)


class ConfigLoader:
    """配置加载器"""

    # 默认配置
    DEFAULT_CONFIG = {
        'gitea': {
            'docker_container': 'gitea',
            'docker_git_user': 'git',
            'data_volume': '/opt/gitea/gitea',
            'repos_path': 'git/repositories',
        },
        'backup': {
            'root': '/opt/backup/gitea-mirrors',
            'organizations': [],
            'check_mirror_only': False,
            'retention': {
                'snapshots_days': 30,
                'archives_months': 12,
                'reports_days': 30,
            },
        },
        'alerts': {
            'commit_decrease_threshold': 10,
            'size_decrease_threshold': 30,
            'protect_abnormal_snapshots': True,
        },
        'logging': {
            'file': '/var/log/gitea-mirror-backup.log',
            'level': 'INFO',
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
        },
        'reports': {
            'directory': 'reports',
            'latest_link': 'latest-report.md',
        },
        'advanced': {
            'concurrent_backups': 0,
            'backup_timeout': 0,
            'verify_docker': True,
            'generate_restore_script': True,
        },
    }

    # 环境变量映射
    ENV_MAPPING = {
        'GITEA_DOCKER_CONTAINER': 'gitea.docker_container',
        'GITEA_DOCKER_GIT_USER': 'gitea.docker_git_user',
        'GITEA_DATA_VOLUME': 'gitea.data_volume',
        'GITEA_REPOS_PATH': 'gitea.repos_path',
        'BACKUP_ROOT': 'backup.root',
        'BACKUP_ORGANIZATIONS': 'backup.organizations',  # 逗号分隔
        'BACKUP_CHECK_MIRROR_ONLY': 'backup.check_mirror_only',
        'SNAPSHOT_RETENTION_DAYS': 'backup.retention.snapshots_days',
        'ARCHIVE_RETENTION_MONTHS': 'backup.retention.archives_months',
        'REPORT_RETENTION_DAYS': 'backup.retention.reports_days',
        'COMMIT_DECREASE_THRESHOLD': 'alerts.commit_decrease_threshold',
        'SIZE_DECREASE_THRESHOLD': 'alerts.size_decrease_threshold',
        'PROTECT_ABNORMAL_SNAPSHOTS': 'alerts.protect_abnormal_snapshots',
        'LOG_FILE': 'logging.file',
        'LOG_LEVEL': 'logging.level',
        # 通知配置 - 企业微信
        'WECOM_WEBHOOK_URL': 'notifications.wecom.webhook_url',
        # 通知配置 - 钉钉
        'DINGTALK_WEBHOOK_URL': 'notifications.dingtalk.webhook_url',
        'DINGTALK_SECRET': 'notifications.dingtalk.secret',
        # 通知配置 - 邮件
        'EMAIL_SMTP_HOST': 'notifications.email.smtp_host',
        'EMAIL_SMTP_PORT': 'notifications.email.smtp_port',
        'EMAIL_SMTP_USER': 'notifications.email.smtp_user',
        'EMAIL_SMTP_PASSWORD': 'notifications.email.smtp_password',
        'EMAIL_FROM_ADDR': 'notifications.email.from_addr',
        'EMAIL_TO_ADDRS': 'notifications.email.to_addrs',  # 逗号分隔
        # 通知配置 - 通用 Webhook
        'WEBHOOK_URL': 'notifications.webhook.url',
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，如果为 None 则自动查找
        """
        self.config_path = self._find_config_file(config_path)
        self.config = self._load_config()

    def _find_config_file(self, config_path: Optional[str]) -> Optional[Path]:
        """查找配置文件"""
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                print(f"警告: 指定的配置文件不存在: {config_path}")
                return None

        # 自动查找配置文件
        search_paths = [
            Path('config.yaml'),
            Path('config.yml'),
            Path.home() / '.config' / 'gitea-mirror-backup' / 'config.yaml',
            Path('/etc/gitea-mirror-backup/config.yaml'),
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 从默认配置开始
        config = self._deep_copy(self.DEFAULT_CONFIG)

        # 加载配置文件
        if self.config_path:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                    config = self._deep_merge(config, file_config)
                    print(f"✓ 已加载配置文件: {self.config_path}")
            except Exception as e:
                print(f"警告: 加载配置文件失败: {e}")
                print("将使用默认配置")
        else:
            print("未找到配置文件，使用默认配置")
            print("提示: 可以复制 config.example.yaml 为 config.yaml")

        # 应用环境变量覆盖
        config = self._apply_env_overrides(config)

        return config

    def _deep_copy(self, obj: Any) -> Any:
        """深拷贝对象"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config: Dict) -> Dict:
        """应用环境变量覆盖"""
        for env_var, config_path in self.ENV_MAPPING.items():
            value = os.environ.get(env_var)
            if value is not None:
                self._set_nested_value(config, config_path, value)

        return config

    def _set_nested_value(self, config: Dict, path: str, value: str):
        """设置嵌套配置值"""
        keys = path.split('.')
        current = config

        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 设置值（自动类型转换）
        final_key = keys[-1]
        current[final_key] = self._convert_value(value, current.get(final_key))

    def _convert_value(self, value: str, reference: Any) -> Any:
        """根据参考值自动转换类型"""
        # 布尔值
        if isinstance(reference, bool):
            return value.lower() in ('true', '1', 'yes', 'on')

        # 整数
        if isinstance(reference, int):
            try:
                return int(value)
            except ValueError:
                return reference

        # 浮点数
        if isinstance(reference, float):
            try:
                return float(value)
            except ValueError:
                return reference

        # 列表（逗号分隔）
        if isinstance(reference, list):
            return [item.strip() for item in value.split(',') if item.strip()]

        # 默认返回字符串
        return value

    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            path: 配置路径，如 'gitea.docker_container'
            default: 默认值

        Returns:
            配置值
        """
        keys = path.split('.')
        current = self.config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def validate(self) -> List[str]:
        """
        验证配置

        Returns:
            错误列表，如果为空则配置有效
        """
        errors = []

        # 检查必需的配置
        required_paths = [
            'gitea.docker_container',
            'gitea.data_volume',
            'backup.root',
        ]

        for path in required_paths:
            if not self.get(path):
                errors.append(f"缺少必需配置: {path}")

        # 检查路径是否存在
        data_volume = Path(self.get('gitea.data_volume', ''))
        if data_volume and not data_volume.exists():
            errors.append(f"Gitea 数据卷不存在: {data_volume}")

        # 检查阈值范围
        commit_threshold = self.get('alerts.commit_decrease_threshold', 0)
        if not 0 <= commit_threshold <= 100:
            errors.append(f"提交数阈值必须在 0-100 之间: {commit_threshold}")

        size_threshold = self.get('alerts.size_decrease_threshold', 0)
        if not 0 <= size_threshold <= 100:
            errors.append(f"大小阈值必须在 0-100 之间: {size_threshold}")

        return errors

    def print_config(self):
        """打印当前配置（用于调试）"""
        print("\n" + "=" * 50)
        print("当前配置:")
        print("=" * 50)
        self._print_dict(self.config)
        print("=" * 50 + "\n")

    def _print_dict(self, d: Dict, indent: int = 0):
        """递归打印字典"""
        for key, value in d.items():
            if isinstance(value, dict):
                print("  " * indent + f"{key}:")
                self._print_dict(value, indent + 1)
            else:
                print("  " * indent + f"{key}: {value}")


class Config:
    """配置类（兼容旧代码）"""

    _loader: Optional[ConfigLoader] = None

    @classmethod
    def init(cls, config_path: Optional[str] = None):
        """初始化配置"""
        cls._loader = ConfigLoader(config_path)

        # 验证配置
        errors = cls._loader.validate()
        if errors:
            print("\n配置错误:")
            for error in errors:
                print(f"  ✗ {error}")
            print("\n请检查配置文件或环境变量\n")
            sys.exit(1)

    @classmethod
    def get_loader(cls) -> ConfigLoader:
        """获取配置加载器"""
        if cls._loader is None:
            cls.init()
        return cls._loader

    # 兼容旧代码的属性
    @property
    def DOCKER_CONTAINER(self) -> str:
        return self.get_loader().get('gitea.docker_container')

    @property
    def DOCKER_GIT_USER(self) -> str:
        return self.get_loader().get('gitea.docker_git_user')

    @property
    def GITEA_DATA_VOLUME(self) -> str:
        return self.get_loader().get('gitea.data_volume')

    @property
    def GITEA_REPOS_PATH(self) -> str:
        return self.get_loader().get('gitea.repos_path')

    @property
    def BACKUP_ROOT(self) -> str:
        return self.get_loader().get('backup.root')

    @property
    def BACKUP_ORGANIZATIONS(self) -> List[str]:
        return self.get_loader().get('backup.organizations', [])

    @property
    def CHECK_MIRROR_ONLY(self) -> bool:
        return self.get_loader().get('backup.check_mirror_only')

    @property
    def SNAPSHOT_RETENTION_DAYS(self) -> int:
        return self.get_loader().get('backup.retention.snapshots_days')

    @property
    def ARCHIVE_RETENTION_MONTHS(self) -> int:
        return self.get_loader().get('backup.retention.archives_months')

    @property
    def REPORT_RETENTION_DAYS(self) -> int:
        return self.get_loader().get('backup.retention.reports_days')

    @property
    def COMMIT_DECREASE_THRESHOLD(self) -> int:
        return self.get_loader().get('alerts.commit_decrease_threshold')

    @property
    def SIZE_DECREASE_THRESHOLD(self) -> int:
        return self.get_loader().get('alerts.size_decrease_threshold')

    @property
    def PROTECT_ABNORMAL_SNAPSHOTS(self) -> bool:
        return self.get_loader().get('alerts.protect_abnormal_snapshots')

    @property
    def LOG_FILE(self) -> str:
        return self.get_loader().get('logging.file')

    @property
    def LOG_LEVEL(self) -> str:
        return self.get_loader().get('logging.level')

    @property
    def REPORT_DIR(self) -> str:
        backup_root = self.get_loader().get('backup.root')
        report_dir = self.get_loader().get('reports.directory')
        return f"{backup_root}/{report_dir}"

    @property
    def LATEST_REPORT(self) -> str:
        backup_root = self.get_loader().get('backup.root')
        latest_link = self.get_loader().get('reports.latest_link')
        return f"{backup_root}/{latest_link}"


# 创建全局配置实例
config = Config()


if __name__ == "__main__":
    # 测试配置加载
    import argparse

    parser = argparse.ArgumentParser(description='配置加载器测试')
    parser.add_argument('-c', '--config', help='配置文件路径')
    parser.add_argument('-v', '--validate', action='store_true', help='验证配置')
    args = parser.parse_args()

    # 加载配置
    Config.init(args.config)
    loader = Config.get_loader()

    # 打印配置
    loader.print_config()

    # 验证配置
    if args.validate:
        errors = loader.validate()
        if errors:
            print("\n配置错误:")
            for error in errors:
                print(f"  ✗ {error}")
        else:
            print("\n✓ 配置验证通过")
