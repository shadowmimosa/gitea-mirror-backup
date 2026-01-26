#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知系统测试脚本
"""

import sys
import os

from src.config_loader import Config
from src.notifier import NotificationManager

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 UTF-8 输出（Windows 兼容）
if sys.platform == 'win32':
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def test_notifications():
    """测试通知系统"""
    print("\n" + "=" * 60)
    print("通知系统测试")
    print("=" * 60)

    # 初始化配置
    try:
        Config.init()
        config = Config()
        print("\n[OK] 配置加载成功")
    except Exception as e:
        print(f"\n[ERROR] 配置加载失败: {e}")
        return False

    # 初始化通知管理器
    try:
        notifier = NotificationManager(config)
        print("[OK] 通知管理器初始化成功")
        print(f"[INFO] 已启用 {len(notifier.enabled_notifiers)} 个通知渠道")

        if not notifier.enabled_notifiers:
            print("\n[WARN] 未启用任何通知渠道")
            print("[INFO] 请在 config.yaml 中启用至少一个通知渠道")
            print("\n示例配置:")
            print(
                """
notifications:
  email:
    enabled: true
    smtp_host: "smtp.example.com"
    smtp_port: 587
    smtp_user: "user@example.com"
    smtp_password: "password"
    from_addr: "backup@example.com"
    to_addrs:
      - "admin@example.com"
"""
            )
            return False

    except Exception as e:
        print(f"[ERROR] 通知管理器初始化失败: {e}")
        return False

    # 测试通知
    print("\n" + "-" * 60)
    print("发送测试通知...")
    print("-" * 60)

    try:
        # 测试信息通知
        notifier.send_notification(
            title="✅ Gitea 备份系统 - 测试通知",
            message="这是一条测试通知\n\n如果您收到此消息，说明通知系统配置正确！",
            level="info",
        )
        print("[OK] 测试通知已发送")

        # 测试备份报告
        print("\n发送测试备份报告...")
        test_report_data = {
            'total_repos': 10,
            'total_commits': 5000,
            'total_snapshots': 300,
            'processed_count': 10,
            'skipped_count': 0,
            'has_alerts': False,
            'alert_repos': [],
            'total_size_mb': 1024,
        }

        notifier.send_backup_report(test_report_data)
        print("[OK] 测试备份报告已发送")

        # 测试异常报告
        print("\n发送测试异常报告...")
        alert_report_data = {
            'total_repos': 10,
            'total_commits': 4500,
            'total_snapshots': 300,
            'processed_count': 10,
            'skipped_count': 0,
            'has_alerts': True,
            'alert_repos': ['test-org/test-repo', 'test-org/another-repo'],
            'total_size_mb': 1024,
        }

        notifier.send_backup_report(alert_report_data)
        print("[OK] 测试异常报告已发送")

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        print("\n请检查您的通知渠道（邮箱/企业微信/钉钉）是否收到测试消息")
        print()

        return True

    except Exception as e:
        print(f"\n[ERROR] 发送通知失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_notifications()
    sys.exit(0 if success else 1)
