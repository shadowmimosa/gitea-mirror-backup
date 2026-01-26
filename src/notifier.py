#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知系统模块
支持多种通知方式：邮件、Webhook、企业微信、钉钉
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class NotificationManager:
    """通知管理器"""

    def __init__(self, config):
        """
        初始化通知管理器

        Args:
            config: 配置对象
        """
        self.config = config
        self.enabled_notifiers = []

        # 初始化各种通知器
        self._init_notifiers()

    def _init_notifiers(self):
        """初始化通知器"""
        loader = self.config.get_loader()

        # 邮件通知
        if loader.get('notifications.email.enabled', False):
            self.enabled_notifiers.append(EmailNotifier(loader, 'email'))

        # Webhook 通知
        if loader.get('notifications.webhook.enabled', False):
            self.enabled_notifiers.append(WebhookNotifier(loader, 'webhook'))

        # 企业微信通知
        if loader.get('notifications.wecom.enabled', False):
            self.enabled_notifiers.append(WeComNotifier(loader, 'wecom'))

        # 钉钉通知
        if loader.get('notifications.dingtalk.enabled', False):
            self.enabled_notifiers.append(DingTalkNotifier(loader, 'dingtalk'))

        if self.enabled_notifiers:
            logger.info(f"已启用 {len(self.enabled_notifiers)} 个通知渠道")
        else:
            logger.info("未启用任何通知渠道")

    def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: Optional[Dict] = None,
    ):
        """
        发送通知

        Args:
            title: 通知标题
            message: 通知内容
            level: 通知级别 (info/warning/error)
            details: 详细信息（可选）
        """
        if not self.enabled_notifiers:
            return

        has_alerts = details.get('has_alerts', False) if details else False

        for notifier in self.enabled_notifiers:
            try:
                # 检查是否应该发送
                if not notifier.should_send(level, has_alerts):
                    logger.debug(
                        f"跳过通知 ({notifier.__class__.__name__}): notify_on={notifier.notify_on}, level={level}, has_alerts={has_alerts}"
                    )
                    continue

                notifier.send(title, message, level, details)
            except Exception as e:
                logger.error(f"发送通知失败 ({notifier.__class__.__name__}): {e}")

    def send_backup_report(self, report_data: Dict):
        """
        发送备份报告

        Args:
            report_data: 报告数据
        """
        has_alerts = report_data.get('has_alerts', False)

        if has_alerts:
            level = "warning"
            title = "⚠️ Gitea 备份报告 - 检测到异常"
        else:
            level = "info"
            title = "✅ Gitea 备份报告 - 全部正常"

        # 构建消息
        message = self._build_report_message(report_data)

        self.send_notification(title, message, level, report_data)

    def _build_report_message(self, report_data: Dict) -> str:
        """构建报告消息"""
        lines = []

        # 基本信息
        lines.append(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"备份仓库数: {report_data.get('total_repos', 0)}")
        lines.append(f"总提交数: {report_data.get('total_commits', 0):,}")
        lines.append(f"快照总数: {report_data.get('total_snapshots', 0)}")
        lines.append(f"占用空间: {report_data.get('total_size_mb', 0)} MB")

        # 异常信息
        if report_data.get('has_alerts'):
            lines.append("")
            lines.append("⚠️ 检测到异常的仓库:")
            for repo in report_data.get('alert_repos', []):
                lines.append(f"  - {repo}")

        return "\n".join(lines)


class BaseNotifier:
    """通知器基类"""

    def __init__(self, config_loader, notify_type: str):
        """
        初始化通知器

        Args:
            config_loader: 配置加载器
            notify_type: 通知类型 (email/webhook/wecom/dingtalk)
        """
        self.config = config_loader
        self.notify_type = notify_type
        self.notify_on = config_loader.get(
            f'notifications.{notify_type}.notify_on', 'on_alert'
        )

    def should_send(self, level: str, has_alerts: bool = False) -> bool:
        """
        判断是否应该发送通知

        Args:
            level: 通知级别 (info/warning/error)
            has_alerts: 是否有异常

        Returns:
            是否应该发送
        """
        if self.notify_on == 'always':
            return True
        elif self.notify_on == 'on_error':
            return level == 'error'
        elif self.notify_on == 'on_alert':
            return has_alerts or level in ['warning', 'error']
        return False

    def send(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: Optional[Dict] = None,
    ):
        """发送通知（子类实现）"""
        raise NotImplementedError


class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def send(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: Optional[Dict] = None,
    ):
        """发送邮件通知"""
        smtp_host = self.config.get('notifications.email.smtp_host')
        smtp_port = self.config.get('notifications.email.smtp_port', 587)
        smtp_user = self.config.get('notifications.email.smtp_user')
        smtp_password = self.config.get('notifications.email.smtp_password')
        from_addr = self.config.get('notifications.email.from_addr')
        to_addrs = self.config.get('notifications.email.to_addrs', [])

        if not all([smtp_host, smtp_user, smtp_password, from_addr, to_addrs]):
            logger.warning("邮件配置不完整，跳过邮件通知")
            return

        # 构建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = title
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)

        # 文本内容
        text_part = MIMEText(message, 'plain', 'utf-8')
        msg.attach(text_part)

        # HTML 内容
        html_content = self._build_html_content(title, message, level, details)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # 发送邮件
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            logger.info(f"邮件通知已发送: {title}")
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            raise

    def _build_html_content(
        self, title: str, message: str, level: str, details: Optional[Dict]
    ) -> str:
        """构建 HTML 邮件内容"""
        color_map = {'info': '#28a745', 'warning': '#ffc107', 'error': '#dc3545'}
        color = color_map.get(level, '#6c757d')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: {color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .footer {{ padding: 20px; color: #666; font-size: 12px; }}
                pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{title}</h2>
            </div>
            <div class="content">
                <pre>{message}</pre>
            </div>
            <div class="footer">
                <p>此邮件由 Gitea Mirror Backup 自动发送</p>
                <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        return html


class WebhookNotifier(BaseNotifier):
    """Webhook 通知器"""

    def send(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: Optional[Dict] = None,
    ):
        """发送 Webhook 通知"""
        if not requests:
            logger.warning("requests 库未安装，跳过 Webhook 通知")
            return

        url = self.config.get('notifications.webhook.url')
        method = self.config.get('notifications.webhook.method', 'POST')
        headers = self.config.get('notifications.webhook.headers', {})

        if not url:
            logger.warning("Webhook URL 未配置")
            return

        # 检测是否是企业微信 URL
        is_wecom = 'qyapi.weixin.qq.com' in url

        # 构建请求数据
        if is_wecom:
            # 企业微信格式
            emoji_map = {'info': '✅', 'warning': '⚠️', 'error': '❌'}
            emoji = emoji_map.get(level, 'ℹ️')
            content = f"{emoji} {title}\n\n{message}"
            payload = {
                'msgtype': 'text',
                'text': {
                    'content': content
                }
            }
        else:
            # 通用格式
            payload = {
                'title': title,
                'message': message,
                'level': level,
                'timestamp': datetime.now().isoformat(),
                'details': details or {},
            }

        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            else:
                response = requests.get(
                    url, params=payload, headers=headers, timeout=10
                )

            response.raise_for_status()
            logger.info(f"Webhook 通知已发送: {title}")
        except Exception as e:
            logger.error(f"发送 Webhook 失败: {e}")
            raise


class WeComNotifier(BaseNotifier):
    """企业微信通知器"""

    def send(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: Optional[Dict] = None,
    ):
        """发送企业微信通知"""
        if not requests:
            logger.warning("requests 库未安装，跳过企业微信通知")
            return

        webhook_url = self.config.get('notifications.wecom.webhook_url')

        if not webhook_url:
            logger.warning("企业微信 Webhook URL 未配置")
            return

        # 构建消息
        emoji_map = {'info': '✅', 'warning': '⚠️', 'error': '❌'}
        emoji = emoji_map.get(level, 'ℹ️')

        content = f"{emoji} {title}\n\n{message}"

        payload = {"msgtype": "text", "text": {"content": content}}

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"企业微信通知已发送: {title}")
        except Exception as e:
            logger.error(f"发送企业微信通知失败: {e}")
            raise


class DingTalkNotifier(BaseNotifier):
    """钉钉通知器"""

    def send(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: Optional[Dict] = None,
    ):
        """发送钉钉通知"""
        if not requests:
            logger.warning("requests 库未安装，跳过钉钉通知")
            return

        webhook_url = self.config.get('notifications.dingtalk.webhook_url')
        secret = self.config.get('notifications.dingtalk.secret', '')

        if not webhook_url:
            logger.warning("钉钉 Webhook URL 未配置")
            return

        # 如果配置了加签密钥，计算签名
        if secret:
            webhook_url = self._sign_url(webhook_url, secret)

        # 构建消息
        emoji_map = {'info': '✅', 'warning': '⚠️', 'error': '❌'}
        emoji = emoji_map.get(level, 'ℹ️')

        content = f"{emoji} {title}\n\n{message}"

        payload = {"msgtype": "text", "text": {"content": content}}

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"钉钉通知已发送: {title}")
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
            raise

    def _sign_url(self, webhook_url: str, secret: str) -> str:
        """计算钉钉加签"""
        import time
        import hmac
        import hashlib
        import base64
        from urllib.parse import quote_plus

        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')

        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))

        return f"{webhook_url}&timestamp={timestamp}&sign={sign}"
