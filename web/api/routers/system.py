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
    NotificationTestRequest,
    NotificationTestResponse,
)

router = APIRouter(prefix="/system", tags=["系统信息"])


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
