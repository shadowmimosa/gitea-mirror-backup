#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知系统测试脚本（跳过配置验证）
"""

import sys
import os
import logging

from src.config_loader import ConfigLoader
from src.notifier import NotificationManager

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 UTF-8 输出（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


class SimpleConfig:
    """简化的配置类，用于测试"""

    def __init__(self, loader):
        self._loader = loader

    def get_loader(self):
        return self._loader


def test_notifications():
    """测试通知系统"""
    print("\n" + "=" * 60)
    print("通知系统测试")
    print("=" * 60)

    # 加载配置（不验证）
    try:
        loader = ConfigLoader('config.yaml')
        config = SimpleConfig(loader)
        print("\n[OK] 配置加载成功")
    except Exception as e:
        print(f"\n[ERROR] 配置加载失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 初始化通知管理器
    try:
        notifier = NotificationManager(config)
        print("[OK] 通知管理器初始化成功")
        print(f"[INFO] 已启用 {len(notifier.enabled_notifiers)} 个通知渠道")

        if not notifier.enabled_notifiers:
            print("\n[WARN] 未启用任何通知渠道")
            print("[INFO] 请在 config.yaml 中启用至少一个通知渠道")
            return False

        # 显示启用的通知渠道
        for n in notifier.enabled_notifiers:
            print(f"  - {n.__class__.__name__}: notify_on={n.notify_on}")

    except Exception as e:
        print(f"[ERROR] 通知管理器初始化失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试通知
    print("\n" + "-" * 60)
    print("发送测试通知...")
    print("-" * 60)

    try:
        # 测试1: 信息通知（notify_on=always 会发送）
        print("\n[测试1] 发送信息通知...")
        notifier.send_notification(
            title="✅ Gitea 备份系统 - 测试通知",
            message="这是一条测试通知\n\n如果您收到此消息，说明通知系统配置正确！",
            level="info",
            details={'has_alerts': False},
        )
        print("[OK] 信息通知已发送")

        # 测试2: 正常备份报告（has_alerts=False）
        print("\n[测试2] 发送正常备份报告...")
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
        print("[OK] 正常备份报告已发送")

        # 测试3: 异常报告（has_alerts=True）
        print("\n[测试3] 发送异常报告...")
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
        print("[OK] 异常报告已发送")

        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)
        print("\n请检查您的通知渠道是否收到消息：")
        print("  - notify_on=always: 应该收到所有3条消息")
        print("  - notify_on=on_alert: 应该只收到测试3（异常报告）")
        print("  - notify_on=on_error: 不应该收到任何消息（没有错误）")
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
