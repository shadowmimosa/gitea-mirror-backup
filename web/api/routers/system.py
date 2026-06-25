"""
系统信息路由
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import settings
from ...utils.auth import get_current_admin_user, get_current_user
from ..models import User
from ..schemas import (
    ConfigContentResponse,
    ConfigValidateResponse,
    BackupScopeResponse,
    BackupScopeUpdateRequest,
    NotificationTestRequest,
    NotificationTestResponse,
)
from ...services.config_service import ConfigService

router = APIRouter(prefix="/system", tags=["系统信息"])


def get_config_service() -> ConfigService:
    return ConfigService(settings.BACKUP_CONFIG_PATH)


@router.get("/info", summary="获取系统信息")
async def get_system_info():
    """获取应用名称和版本号"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/config", response_model=ConfigContentResponse, summary="获取备份配置")
async def get_backup_config(current_user: User = Depends(get_current_user)):
    """只读展示 config.yaml 内容"""
    config_path = Path(settings.BACKUP_CONFIG_PATH)
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件不存在: {config_path}",
        )
    content = config_path.read_text(encoding="utf-8")
    return ConfigContentResponse(content=content, path=str(config_path))


@router.post("/config/validate", response_model=ConfigValidateResponse, summary="校验配置")
async def validate_backup_config(
    current_admin: User = Depends(get_current_admin_user),
):
    """校验当前 config.yaml"""
    loader = settings._config_loader
    if not loader:
        return ConfigValidateResponse(valid=False, errors=["无法加载配置加载器"])

    errors = loader.validate()
    return ConfigValidateResponse(valid=len(errors) == 0, errors=errors)


@router.get(
    "/backup-scope",
    response_model=BackupScopeResponse,
    summary="获取备份范围配置",
)
async def get_backup_scope(
    current_admin: User = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service),
):
    """获取组织白名单与镜像仓开关（配置文件中的值）"""
    config_path = Path(settings.BACKUP_CONFIG_PATH)
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件不存在: {config_path}",
        )
    return config_service.get_backup_scope()


@router.put(
    "/backup-scope",
    response_model=BackupScopeResponse,
    summary="更新备份范围配置",
)
async def update_backup_scope(
    body: BackupScopeUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service),
):
    """写入 config.yaml，下次全量备份任务生效"""
    config_path = Path(settings.BACKUP_CONFIG_PATH)
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件不存在: {config_path}",
        )
    result = config_service.update_backup_scope(
        organizations=body.organizations,
        check_mirror_only=body.check_mirror_only,
    )
    settings.reload_config_loader()
    return result


@router.post(
    "/notifications/test",
    response_model=NotificationTestResponse,
    summary="测试通知渠道",
)
async def test_notification(
    body: NotificationTestRequest,
    current_admin: User = Depends(get_current_admin_user),
):
    """发送测试通知"""
    try:
        from src.notifier import NotificationManager
        from src.config_loader import ConfigLoader

        loader = ConfigLoader(settings.BACKUP_CONFIG_PATH)

        class _ConfigWrapper:
            def get_loader(self):
                return loader

        notifier = NotificationManager(_ConfigWrapper())
        channel = body.channel.lower()

        if channel == "email":
            enabled = loader.get("notifications.email.enabled", False)
            if not enabled:
                return NotificationTestResponse(success=False, message="邮件通知未启用")
            for n in notifier.enabled_notifiers:
                if n.__class__.__name__ == "EmailNotifier":
                    n.send(
                        "Gitea Backup 测试通知",
                        "这是一条来自 Web 管理界面的测试通知。",
                        level="info",
                    )
                    return NotificationTestResponse(success=True, message="测试邮件已发送")

        elif channel == "webhook":
            enabled = loader.get("notifications.webhook.enabled", False)
            if not enabled:
                return NotificationTestResponse(success=False, message="Webhook 未启用")
            for n in notifier.enabled_notifiers:
                if n.__class__.__name__ == "WebhookNotifier":
                    n.send(
                        "Gitea Backup 测试通知",
                        "这是一条来自 Web 管理界面的测试通知。",
                        level="info",
                    )
                    return NotificationTestResponse(success=True, message="Webhook 测试已发送")

        elif channel == "wechat":
            enabled = loader.get("notifications.wecom.enabled", False)
            if not enabled:
                return NotificationTestResponse(success=False, message="企业微信未启用")
            for n in notifier.enabled_notifiers:
                if n.__class__.__name__ == "WeComNotifier":
                    n.send(
                        "Gitea Backup 测试通知",
                        "这是一条来自 Web 管理界面的测试通知。",
                        level="info",
                    )
                    return NotificationTestResponse(success=True, message="企业微信测试已发送")

        elif channel == "dingtalk":
            enabled = loader.get("notifications.dingtalk.enabled", False)
            if not enabled:
                return NotificationTestResponse(success=False, message="钉钉未启用")
            for n in notifier.enabled_notifiers:
                if n.__class__.__name__ == "DingTalkNotifier":
                    n.send(
                        "Gitea Backup 测试通知",
                        "这是一条来自 Web 管理界面的测试通知。",
                        level="info",
                    )
                    return NotificationTestResponse(success=True, message="钉钉测试已发送")

        return NotificationTestResponse(
            success=False, message=f"未找到可用的通知渠道: {channel}"
        )
    except Exception as exc:
        return NotificationTestResponse(success=False, message=str(exc))
