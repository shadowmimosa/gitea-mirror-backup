"""
配置管理
"""

import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from src.config_loader import ConfigLoader

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "Gitea Mirror Backup Web"
    APP_VERSION: str = "1.5.0"
    DEBUG: bool = False

    # API 配置
    API_PREFIX: str = "/api"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 小时

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/web.db"

    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:8000"]

    # 备份配置路径
    BACKUP_CONFIG_PATH: str = "/app/config.yaml"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # 配置加载器实例
    _config_loader: Optional[ConfigLoader] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化配置加载器（从 config.yaml 读取配置）
        if self._config_loader is None:
            try:
                self._config_loader = ConfigLoader(self.BACKUP_CONFIG_PATH)
            except Exception as e:
                print(f"警告: 无法加载备份配置文件: {e}")
                print("将使用环境变量中的 BACKUP_ROOT")
                self._config_loader = None

    @property
    def BACKUP_ROOT(self) -> str:
        """
        从 config.yaml 或环境变量获取 BACKUP_ROOT
        优先级：环境变量 > config.yaml > 默认值
        """
        # 1. 优先使用环境变量
        env_backup_root = os.environ.get('BACKUP_ROOT')
        if env_backup_root:
            return env_backup_root

        # 2. 从 config.yaml 读取
        if self._config_loader:
            config_backup_root = self._config_loader.get('backup.root')
            if config_backup_root:
                return config_backup_root

        # 3. 使用默认值
        return "/shared/backup"

    @property
    def BACKUP_BASE_PATH(self) -> str:
        """兼容旧代码：BACKUP_BASE_PATH 指向 BACKUP_ROOT"""
        return self.BACKUP_ROOT


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
