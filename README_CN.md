# Gitea 镜像仓库备份系统

[English](README.md) | [中文](#chinese)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**为 Gitea Docker 镜像仓库设计的智能备份解决方案**

*自动异常检测 • 快照保护 • 轻松恢复*

</div>

---

## ✨ 特性

- 🔄 **每日快照** - 基于硬链接的备份，几乎不占额外空间
- 📦 **每月归档** - Git bundle 格式，适合长期保存
- 🔍 **智能检测** - 自动检测 force push 和历史重写（10% 阈值）
- 🔒 **自动保护** - 关键快照和报告永久保留
- 📊 **详细报告** - 全面的备份摘要和异常告警
- ⚡ **轻松恢复** - 多种恢复选项（原地恢复、导出新库、Bundle 文件）
- 💾 **节省空间** - 硬链接技术，未改变的文件几乎不占空间
- 🎯 **精准备份** - 按组织/用户过滤，支持仅备份镜像仓库

## 🎬 快速开始

### 前置要求

- Python 3.6+
- 运行 Gitea 的 Docker 容器
- Gitea 数据目录和备份目录在同一文件系统（硬链接需要）

### 安装

```bash
# 1. 下载脚本
wget https://raw.githubusercontent.com/yourusername/gitea-mirror-backup/main/gitea_mirror_backup.py

# 或克隆仓库
git clone https://github.com/yourusername/gitea-mirror-backup.git
cd gitea-mirror-backup

# 2. 添加执行权限
chmod +x gitea_mirror_backup.py
```

### 配置

编辑脚本，修改这些关键配置：

```python
class Config:
    # Docker 容器名称
    DOCKER_CONTAINER = "gitea"
    
    # Gitea 数据卷路径（宿主机上的路径）
    GITEA_DATA_VOLUME = "/var/lib/docker/volumes/gitea_data/_data"
    
    # 备份根目录
    BACKUP_ROOT = "/backup/gitea-mirrors"
    
    # 要备份的组织（留空备份所有）
    BACKUP_ORGANIZATIONS = ["你的组织名"]
```

### 首次运行

```bash
# 手动运行
python3 gitea_mirror_backup.py

# 查看日志
tail -f /var/log/gitea-mirror-backup.log

# 查看报告
cat /backup/gitea-mirrors/latest-report.md
```

### 设置自动备份

```bash
# 编辑 crontab
crontab -e

# 添加这一行（每天凌晨 2 点运行）
0 2 * * * /usr/bin/python3 /path/to/gitea_mirror_backup.py
```

## 📖 文档

- **[部署指南](docs/deployment.md)** - 详细的安装配置说明
- **[恢复使用示例](examples/restore-usage-example.md)** - 如何使用恢复脚本
- **[Crontab 配置](examples/crontab.example)** - 定时任务配置示例

## 🔍 工作原理

### 备份策略

```
每日快照（保留 30 天）
├── 基于硬链接的复制
├── 未改变的文件几乎不占空间
└── 快速创建和删除

每月归档（保留 12 个月）
├── Git bundle 格式
├── 便携且压缩
└── 每月 1 号创建

自动保护
├── 检测异常（提交数/大小减少）
├── 保护异常前的快照
└── 保留对应的报告
```

### 异常检测

脚本监控：
- **提交数变化** - 减少 >10% 触发告警（可配置）
- **仓库大小变化** - 减少 >30% 触发告警（辅助检查）

检测到异常时：
1. 🔒 上一次快照（正常状态）被保护，不会被清理
2. 📋 当前报告被标记为永久保留
3. ⚠️ 告警详情被记录以供审查

### 存储效率

示例：100 个仓库，平均每个 500MB

```
原始总大小:     50GB
每日快照:       ~5GB (30天，只保存变化的文件)
每月归档:       ~7GB (12个月，压缩的 bundle)
总计:          ~62GB (对比完整复制需要 1500GB!)
```

## 🔧 恢复选项

生成的恢复脚本提供三种模式：

### 选项 1：恢复到原位置
```bash
/backup/gitea-mirrors/org/repo/restore.sh
# 选择模式 1，选择快照
# ⚠️ 会覆盖当前仓库
```

### 选项 2：导出为新仓库
```bash
# 选择模式 2
# 创建独立副本
# 适合镜像仓库（原仓库不受影响）
```

### 选项 3：导出为 Bundle
```bash
# 选择模式 3
# 便携的 Git bundle 文件
# 可以在任何地方克隆
```

## 📊 报告示例

查看完整示例：
- [正常备份报告](examples/report-normal-example.md) - 所有仓库正常时的报告
- [异常检测报告](examples/report-alert-example.md) - 检测到异常时的报告（🔒 自动永久保留）
- [保护文件示例](examples/snapshot-protected-example.txt) - 快照保护标记文件

### 异常报告预览

```markdown
## ⚠️ 需要关注的仓库

### myorg/critical-repo
提交数异常减少: 45%
上次: 567 commits → 当前: 312 commits

🔒 受保护快照: 20260124-020000 (异常前状态)
恢复命令: /backup/.../myorg/critical-repo/restore.sh
```

## 🛠️ 高级配置

```python
# 快照保留天数
SNAPSHOT_RETENTION_DAYS = 30

# 归档保留月数
ARCHIVE_RETENTION_MONTHS = 12

# 提交数减少阈值（%）
COMMIT_DECREASE_THRESHOLD = 10

# 大小减少阈值（%）
SIZE_DECREASE_THRESHOLD = 30

# 自动保护异常快照
PROTECT_ABNORMAL_SNAPSHOTS = True

# 仅检查镜像仓库
CHECK_MIRROR_ONLY = False
```

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 为 [Gitea](https://gitea.io/) 自托管 Git 服务设计
- 源于对可靠镜像仓库备份的需求
- 用 ❤️ 为自托管社区打造

## 📮 支持

- 🐛 [报告问题](https://github.com/yourusername/gitea-mirror-backup/issues)
- 💡 [功能建议](https://github.com/yourusername/gitea-mirror-backup/issues/new)
- 📖 [阅读文档](docs/)

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐ star！**

用 🐍 Python 制作

</div>
