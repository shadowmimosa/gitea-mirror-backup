"""
配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional


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
    BACKUP_CONFIG_PATH: str = "/app/config/config.yaml"
    # 统一使用 BACKUP_ROOT（与备份服务保持一致）
    BACKUP_ROOT: str = "/shared/backup"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def BACKUP_BASE_PATH(self) -> str:
        """兼容旧代码：BACKUP_BASE_PATH 指向 BACKUP_ROOT"""
        return self.BACKUP_ROOT


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
