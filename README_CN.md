# Gitea 镜像仓库备份系统

[English](README.md) | [中文](#chinese)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**为 Gitea Docker 镜像仓库设计的智能备份解决方案**

*自动异常检测 • 快照保护 • 轻松恢复 • 灵活配置*

</div>

---

## ✨ 特性

- 🔄 **每日快照** - 基于硬链接的备份，几乎不占额外空间
- 📦 **每月归档** - Git bundle 格式，适合长期保存
- 🔍 **智能检测** - 自动检测 force push 和历史重写
- 🔒 **自动保护** - 异常时自动保护快照和报告
- 📊 **详细报告** - 全面的备份摘要和异常告警
- ⚡ **轻松恢复** - 多种恢复选项（原地/新库/Bundle）
- 💾 **节省空间** - 硬链接技术，未改变的文件几乎不占空间
- 🎯 **精准备份** - 按组织过滤，支持仅备份镜像仓库
- ⚙️ **灵活配置** - YAML 配置文件 + 环境变量支持
- 📧 **通知系统** - 邮件/Webhook/企业微信/钉钉通知

## 🎬 快速开始

### 方式 1: Docker（推荐）

```bash
# 使用 Docker Compose
docker compose up -d

# 查看日志
docker compose logs -f gitea-backup
```

详见 [Docker 部署指南](docs/docker.md)

### 方式 2: 直接安装

#### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/gitea-mirror-backup.git
cd gitea-mirror-backup

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建配置文件
cp config.example.yaml config.yaml
vim config.yaml
```

### 最小配置

编辑 `config.yaml`，至少配置这三项：

**直接部署**：
```yaml
gitea:
  docker_container: "gitea"              # 你的容器名
  data_volume: "/opt/gitea"              # 宿主机路径

backup:
  root: "/opt/backup/gitea-mirrors"      # 宿主机路径
```

**Docker 部署**：
```yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"           # 容器内路径

backup:
  root: "/shared/backup"                 # 容器内路径
```

> 💡 **提示**：Docker 部署请使用 `config.docker.yaml` 作为模板

### 运行

```bash
# 验证配置
python gitea_mirror_backup.py --validate-config

# 执行备份
python gitea_mirror_backup.py

# 查看报告
cat /opt/backup/gitea-mirrors/latest-report.md
```

### 定时任务

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点执行
0 2 * * * cd /path/to/gitea-mirror-backup && python gitea_mirror_backup.py
```

## ⚙️ 配置说明

### 配置方式

支持三种配置方式（优先级：环境变量 > 配置文件 > 默认值）：

#### 1. 混合配置（推荐）

基础配置放在 `config.yaml`，敏感信息放在 `.env`：

```yaml
# config/config.yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"

backup:
  root: "/shared/backup"
  organizations: []
  
notifications:
  wecom:
    enabled: true
    notify_on: "on_alert"
```

```bash
# .env（敏感信息，不提交到 Git）
SECRET_KEY=your-random-secret-key
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
EMAIL_SMTP_PASSWORD=your-password
```

#### 2. 纯 YAML 配置

```yaml
# config.yaml
gitea:
  docker_container: "gitea"
  docker_git_user: "git"
  data_volume: "/opt/gitea/gitea"
  repos_path: "git/repositories"

backup:
  root: "/opt/backup/gitea-mirrors"
  organizations:                    # 指定组织，留空则备份所有
    - "MyOrg"
  check_mirror_only: false          # true=只备份镜像仓库
  retention:
    snapshots_days: 30              # 快照保留天数
    archives_months: 12             # 归档保留月数
    reports_days: 30                # 报告保留天数

alerts:
  commit_decrease_threshold: 10     # 提交数减少阈值（%）
  size_decrease_threshold: 30       # 大小减少阈值（%）
  protect_abnormal_snapshots: true  # 自动保护异常快照

logging:
  file: "/var/log/gitea-mirror-backup.log"
  level: "INFO"                     # DEBUG/INFO/WARNING/ERROR

# 通知配置（可选）
notifications:
  # 企业微信
  wecom:
    enabled: false
    webhook_url: ""  # 建议使用环境变量 WECOM_WEBHOOK_URL
    notify_on: "on_alert"
  
  # 钉钉
  dingtalk:
    enabled: false
    webhook_url: ""  # 建议使用环境变量 DINGTALK_WEBHOOK_URL
    secret: ""       # 建议使用环境变量 DINGTALK_SECRET
    notify_on: "on_alert"
  
  # 邮件
  email:
    enabled: false
    smtp_host: "smtp.example.com"
    smtp_port: 587
    smtp_user: ""    # 建议使用环境变量 EMAIL_SMTP_USER
    smtp_password: "" # 建议使用环境变量 EMAIL_SMTP_PASSWORD
    from_addr: "backup@example.com"
    to_addrs:
      - "admin@example.com"
    notify_on: "on_alert"
  
  # 通用 Webhook
  webhook:
    enabled: false
    url: ""          # 建议使用环境变量 WEBHOOK_URL
    method: "POST"
    notify_on: "on_alert"
```

#### 3. 环境变量

```bash
# 基础配置
export GITEA_DOCKER_CONTAINER="gitea"
export BACKUP_ROOT="/backup/gitea"
export BACKUP_ORGANIZATIONS="Org1,Org2"
export LOG_LEVEL="DEBUG"

# 通知配置（敏感信息）
export WECOM_WEBHOOK_URL="https://qyapi.weixin.qq.com/..."
export EMAIL_SMTP_PASSWORD="your-password"
export DINGTALK_SECRET="SECxxx"

python gitea_mirror_backup.py
```

### 支持的环境变量

**基础配置**：
- `GITEA_DOCKER_CONTAINER` - Gitea 容器名
- `GITEA_DATA_VOLUME` - Gitea 数据目录
- `BACKUP_ROOT` - 备份根目录
- `BACKUP_ORGANIZATIONS` - 组织列表（逗号分隔）
- `LOG_LEVEL` - 日志级别

**通知配置**：
- `WECOM_WEBHOOK_URL` - 企业微信 Webhook URL
- `DINGTALK_WEBHOOK_URL` - 钉钉 Webhook URL
- `DINGTALK_SECRET` - 钉钉加签密钥
- `EMAIL_SMTP_HOST` - 邮件服务器
- `EMAIL_SMTP_PORT` - 邮件端口
- `EMAIL_SMTP_USER` - 邮件用户名
- `EMAIL_SMTP_PASSWORD` - 邮件密码
- `EMAIL_FROM_ADDR` - 发件人地址
- `EMAIL_TO_ADDRS` - 收件人地址（逗号分隔）
- `WEBHOOK_URL` - 通用 Webhook URL

完整列表请参考：[环境变量文档](docs/ENV-VARIABLES.md)

### 命令行选项

```bash
python gitea_mirror_backup.py --help              # 查看帮助
python gitea_mirror_backup.py -c config.yaml     # 指定配置文件
python gitea_mirror_backup.py --show-config      # 显示当前配置
python gitea_mirror_backup.py --validate-config  # 验证配置
python gitea_mirror_backup.py --report           # 只生成报告
python gitea_mirror_backup.py --cleanup          # 只清理旧报告
```

### 常用配置场景

**场景 1：备份所有仓库**
```yaml
backup:
  organizations: []           # 空列表
  check_mirror_only: false
```

**场景 2：只备份特定组织的镜像仓库**
```yaml
backup:
  organizations: ["mirrors", "upstream"]
  check_mirror_only: true
```

**场景 3：长期保留**
```yaml
backup:
  retention:
    snapshots_days: 90
    archives_months: 24
```

## 🔍 工作原理

### 备份策略

```
每日快照（保留 30 天）
├── 基于硬链接，几乎不占额外空间
├── 快速创建和删除
└── 自动清理过期快照

每月归档（保留 12 个月）
├── Git bundle 格式
├── 便携且压缩
└── 每月 1 号自动创建

异常检测与保护
├── 监控提交数和仓库大小
├── 检测到异常时自动保护快照
└── 对应报告永久保留
```

### 异常检测

监控指标：
- **提交数减少** > 10%（可配置）
- **仓库大小减少** > 30%（辅助参考）

触发后：
1. 🔒 保护异常前的快照（正常状态）
2. 📋 标记报告为永久保留
3. ⚠️ 记录详细告警信息

### 存储效率

示例：100 个仓库 × 500MB

```
原始大小:    50GB
快照 30 天:  ~5GB  (硬链接，只保存变化)
归档 12 月:  ~7GB  (压缩 bundle)
总计:       ~62GB (vs 完整复制 1500GB)
```

## 🔧 恢复操作

每个仓库都有自动生成的恢复脚本。

### Docker 部署（推荐）

backup 镜像的入口为 Python 备份程序，**请勿在宿主机直接运行 `restore.sh`**（脚本内路径为容器内 `/shared/backup/...`）。

```bash
# 方式 1：restore 辅助服务（推荐）
docker compose run --rm -it restore \
  /shared/backup/org/repo/restore.sh

# 方式 2：backup 服务 + 覆盖 entrypoint
docker compose run --rm -it --entrypoint bash backup \
  /shared/backup/org/repo/restore.sh

# 方式 3：仓库目录下的包装脚本（需先执行一次备份以生成）
/shared/backup/org/repo/restore-via-docker.sh
```

批量更新已有恢复脚本：

```bash
docker compose run --rm --entrypoint python backup \
  gitea_mirror_backup.py --regenerate-restore-scripts
```

### 直接部署

```bash
/opt/backup/gitea-mirrors/org/repo/restore.sh
```

### 三种恢复模式

**模式 1：恢复到原位置**
- 覆盖当前仓库
- 自动备份当前状态
- 修复权限和 hooks

**模式 2：导出为新仓库**
- 创建独立副本
- 不影响原仓库
- 需要在 Gitea 中手动采集

**模式 3：导出为 Bundle**
- 便携的 Git bundle 文件
- 可在任何地方克隆
- 适合传输和归档

### 恢复示例

**Docker 部署：**

```bash
docker compose run --rm -it restore /shared/backup/org/repo/restore.sh
```

**直接部署：**

```bash
cd /opt/backup/gitea-mirrors/org/repo
./restore.sh
```

## 📊 报告示例

### 正常报告

```markdown
## 📊 总体统计
- 备份仓库数: 15
- 总提交数: 45,678 commits
- 快照总数: 450
- 占用空间: 8.5 GB

## ✅ 全部正常
本周期内所有仓库均未检测到异常。
```

### 异常报告（自动保护）

```markdown
## ⚠️ 需要关注的仓库

### myorg/critical-repo
提交数异常减少: 45%
上次: 567 commits → 当前: 312 commits
可能原因: force push、分支删除或历史重写

🔒 受保护快照: 20260124-020000 (异常前的正常状态)
恢复命令: /backup/.../myorg/critical-repo/restore.sh
```

查看完整示例：[examples/](examples/)

## 🛠️ 高级用法

### 多环境配置

```bash
# 生产环境
python gitea_mirror_backup.py -c config.prod.yaml

# 测试环境
python gitea_mirror_backup.py -c config.test.yaml
```

### 手动管理受保护资源

```bash
# 查看所有受保护的快照
find /opt/backup -name ".protected"

# 查看保护原因
cat /path/to/snapshot/.protected

# 取消保护（允许自动清理）
rm /path/to/snapshot/.protected
```

### 监控和维护

```bash
# 查看日志
tail -f /var/log/gitea-mirror-backup.log

# 查看磁盘使用
du -sh /opt/backup/gitea-mirrors

# 手动清理旧报告
python gitea_mirror_backup.py --cleanup
```

## 📖 更多文档

- **[配置指南](docs/configuration.md)** - 详细的配置说明
- **[环境变量](docs/ENV-VARIABLES.md)** - 所有环境变量列表
- **[通知配置](docs/notifications.md)** - 通知系统配置
- **[Docker 部署](docs/docker.md)** - Docker 部署指南
- **[迁移指南](docs/MIGRATION-GUIDE.md)** - 配置迁移指南
- **[示例文件](examples/)** - 配置和报告示例
- **[更新日志](CHANGELOG.md)** - 版本历史 ([English](CHANGELOG_EN.md))

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📝 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

## 📮 支持

- 🐛 [报告问题](https://github.com/yourusername/gitea-mirror-backup/issues)
- 💡 [功能建议](https://github.com/yourusername/gitea-mirror-backup/issues/new)

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐ star！**

</div>
