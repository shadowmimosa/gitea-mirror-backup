# 环境变量完整列表

本文档列出了所有支持的环境变量及其说明。

## 📖 使用说明

环境变量可以通过以下方式设置：
1. `.env` 文件（推荐）
2. `docker-compose.yml` 中的 `environment` 部分
3. 系统环境变量

**配置优先级**：环境变量 > config.yaml > 默认值

---

## 🔧 Gitea 配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `GITEA_DOCKER_CONTAINER` | string | `gitea` | Gitea Docker 容器名称 |
| `GITEA_DOCKER_GIT_USER` | string | `git` | Docker 容器内的 Git 用户 |
| `GITEA_DATA_VOLUME` | string | `/opt/gitea/gitea` | Gitea 数据卷路径 |
| `GITEA_REPOS_PATH` | string | `git/repositories` | 仓库在数据卷中的相对路径 |

---

## 💾 备份配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `BACKUP_ROOT` | string | `/opt/backup/gitea-mirrors` | 备份根目录 |
| `BACKUP_ORGANIZATIONS` | list | `[]` | 要备份的组织列表（逗号分隔，留空表示全部）|
| `BACKUP_CHECK_MIRROR_ONLY` | boolean | `false` | 是否只备份镜像仓库 |

**示例**：
```bash
BACKUP_ORGANIZATIONS=Org1,Org2,Org3
BACKUP_CHECK_MIRROR_ONLY=true
```

---

## 🗄️ 保留策略

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `SNAPSHOT_RETENTION_DAYS` | integer | `30` | 快照保留天数 |
| `ARCHIVE_RETENTION_MONTHS` | integer | `12` | 归档保留月数 |
| `REPORT_RETENTION_DAYS` | integer | `30` | 报告保留天数 |

---

## ⚠️ 异常检测

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `COMMIT_DECREASE_THRESHOLD` | integer | `10` | 提交数减少阈值（百分比）|
| `SIZE_DECREASE_THRESHOLD` | integer | `30` | 仓库大小减少阈值（百分比）|
| `PROTECT_ABNORMAL_SNAPSHOTS` | boolean | `true` | 是否保护异常快照 |

---

## 📝 日志配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `LOG_FILE` | string | `/var/log/gitea-mirror-backup.log` | 日志文件路径 |
| `LOG_LEVEL` | string | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR）|

---

## 📧 通知配置

### 企业微信

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `WECOM_WEBHOOK_URL` | string | - | 企业微信机器人 Webhook URL |

**示例**：
```bash
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

### 钉钉

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `DINGTALK_WEBHOOK_URL` | string | - | 钉钉机器人 Webhook URL |
| `DINGTALK_SECRET` | string | - | 钉钉加签密钥（可选）|

**示例**：
```bash
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
```

### 邮件通知

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `EMAIL_SMTP_HOST` | string | - | SMTP 服务器地址 |
| `EMAIL_SMTP_PORT` | integer | `587` | SMTP 服务器端口 |
| `EMAIL_SMTP_USER` | string | - | SMTP 用户名 |
| `EMAIL_SMTP_PASSWORD` | string | - | SMTP 密码 |
| `EMAIL_FROM_ADDR` | string | - | 发件人地址 |
| `EMAIL_TO_ADDRS` | list | - | 收件人地址（逗号分隔）|

**示例**：
```bash
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDR=backup@example.com
EMAIL_TO_ADDRS=admin@example.com,team@example.com
```

### 通用 Webhook

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `WEBHOOK_URL` | string | - | 自定义 Webhook URL |

**示例**：
```bash
WEBHOOK_URL=https://your-webhook-endpoint.com/notify
```

---

## 🌐 Web 服务配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `SECRET_KEY` | string | - | **必需**，JWT 签名密钥 |
| `DATABASE_URL` | string | `sqlite:///./data/web.db` | 数据库连接 URL |
| `BACKUP_CONFIG_PATH` | string | `./config/config.yaml` | 配置文件路径 |
| `DEBUG` | boolean | `false` | 是否启用调试模式 |

**生成 SECRET_KEY**：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔧 高级配置

| 环境变量 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| `CONCURRENT_BACKUPS` | integer | `0` | 并发备份数量（0=串行）|
| `BACKUP_TIMEOUT` | integer | `0` | 备份超时时间（秒，0=无限制）|
| `VERIFY_DOCKER` | boolean | `true` | 是否验证 Docker 容器 |
| `GENERATE_RESTORE_SCRIPT` | boolean | `true` | 是否生成恢复脚本 |

---

## 📋 完整示例

### 最小配置（.env）

```bash
# Web 服务必需
SECRET_KEY=your-random-secret-key-here

# 可选：覆盖默认配置
BACKUP_ORGANIZATIONS=MyOrg1,MyOrg2
LOG_LEVEL=INFO
```

### 完整配置（.env）

```bash
# ============ Web 服务 ============
SECRET_KEY=your-random-secret-key-here
DATABASE_URL=sqlite:///./data/web.db

# ============ Gitea 配置 ============
GITEA_DOCKER_CONTAINER=gitea
GITEA_DATA_VOLUME=/shared/gitea

# ============ 备份配置 ============
BACKUP_ROOT=/shared/backup
BACKUP_ORGANIZATIONS=Org1,Org2
BACKUP_CHECK_MIRROR_ONLY=false

# ============ 保留策略 ============
SNAPSHOT_RETENTION_DAYS=30
ARCHIVE_RETENTION_MONTHS=12
REPORT_RETENTION_DAYS=30

# ============ 异常检测 ============
COMMIT_DECREASE_THRESHOLD=10
SIZE_DECREASE_THRESHOLD=30
PROTECT_ABNORMAL_SNAPSHOTS=true

# ============ 日志配置 ============
LOG_FILE=/logs/gitea-mirror-backup.log
LOG_LEVEL=INFO

# ============ 通知配置 ============
# 企业微信
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 钉钉
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx

# 邮件
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDR=backup@example.com
EMAIL_TO_ADDRS=admin@example.com,team@example.com

# 通用 Webhook
WEBHOOK_URL=https://your-webhook-endpoint.com/notify
```

---

## 💡 使用技巧

### 1. 环境特定配置

为不同环境创建不同的 `.env` 文件：

```bash
.env.dev      # 开发环境
.env.staging  # 测试环境
.env.prod     # 生产环境
```

使用时指定：
```bash
docker compose --env-file .env.prod up -d
```

### 2. 敏感信息管理

将敏感信息放在 `.env` 中，基础配置放在 `config.yaml` 中：

```yaml
# config.yaml（可提交到 Git）
notifications:
  wecom:
    enabled: true
    notify_on: "on_alert"
```

```bash
# .env（不提交到 Git）
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/...
```

### 3. 验证环境变量

```bash
# 查看当前配置
docker compose run --rm backup --show-config

# 验证配置
docker compose run --rm backup --validate-config
```

### 4. 调试环境变量

```bash
# 查看容器中的环境变量
docker compose run --rm backup env | grep BACKUP

# 测试特定环境变量
BACKUP_ORGANIZATIONS=TestOrg docker compose run --rm backup --show-config
```

---

## 🔗 相关文档

- [配置说明](configuration.md)
- [配置分析](configuration-analysis.md)
- [迁移指南](MIGRATION-GUIDE.md)
- [Docker 部署](docker.md)

---

**最后更新**: 2026-01-28

