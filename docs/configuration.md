# 配置指南

## 📋 配置方式

Gitea Mirror Backup 支持三种配置方式，优先级从高到低：

1. **环境变量** - 最高优先级
2. **配置文件** (config.yaml) - 中等优先级
3. **默认值** - 最低优先级（内置合理默认值）

## 🎯 推荐使用场景

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| Docker 部署 | 环境变量 | 符合 12-factor 原则，灵活易管理 |
| 本地开发/测试 | config.yaml | 配置集中，便于版本控制 |
| 生产环境 | 环境变量 + config.yaml | 基础配置用文件，敏感信息用环境变量 |

## 🔧 方式 1: 环境变量（推荐用于 Docker）

### 优点
- ✅ 无需配置文件
- ✅ 符合容器化最佳实践
- ✅ 便于在不同环境切换
- ✅ 敏感信息不会提交到代码库

### 使用方法

**Docker Compose**:
```yaml
services:
  backup:
    environment:
      - GITEA_DOCKER_CONTAINER=gitea
      - BACKUP_ROOT=/backup
      - LOG_LEVEL=INFO
```

**Docker 命令**:
```bash
docker run -e GITEA_DOCKER_CONTAINER=gitea \
           -e BACKUP_ROOT=/backup \
           gitea-mirror-backup:latest
```

**使用 .env 文件**:
```bash
# 创建 .env 文件
cat > .env << EOF
GITEA_DOCKER_CONTAINER=gitea
BACKUP_ROOT=/shared/backup
LOG_LEVEL=INFO
WEBHOOK_URL=https://your-webhook-url
EOF

# docker-compose.yml 会自动读取 .env 文件
docker compose up -d
```

### 完整环境变量列表

```bash
# ============ Gitea 配置 ============
GITEA_DOCKER_CONTAINER=gitea              # Gitea 容器名称
GITEA_DOCKER_GIT_USER=git                 # Gitea 容器内的 git 用户
GITEA_DATA_VOLUME=/data/gitea             # Gitea 数据目录
GITEA_REPOS_PATH=git/repositories         # 仓库相对路径

# ============ 备份配置 ============
BACKUP_ROOT=/backup                       # 备份根目录
BACKUP_ORGANIZATIONS=Org1,Org2            # 要备份的组织（逗号分隔，留空表示全部）
CHECK_MIRROR_ONLY=false                   # 是否只备份镜像仓库

# ============ 保留策略 ============
SNAPSHOT_RETENTION_DAYS=30                # 快照保留天数
ARCHIVE_RETENTION_MONTHS=12               # 归档保留月数
REPORT_RETENTION_DAYS=30                  # 报告保留天数

# ============ 异常检测 ============
COMMIT_DECREASE_THRESHOLD=10              # 提交数减少阈值（百分比）
SIZE_DECREASE_THRESHOLD=30                # 大小减少阈值（百分比）
PROTECT_ABNORMAL_SNAPSHOTS=true           # 保护异常快照

# ============ 日志配置 ============
LOG_FILE=/logs/gitea-mirror-backup.log    # 日志文件路径
LOG_LEVEL=INFO                            # 日志级别：DEBUG, INFO, WARNING, ERROR

# ============ 通知配置（可选） ============
WEBHOOK_URL=https://your-webhook-url      # Webhook URL
WEBHOOK_NOTIFY_ON=on_alert                # 通知时机：always, on_alert, never
```

## 📄 方式 2: 配置文件 (config.yaml)

### 优点
- ✅ 配置集中管理
- ✅ 支持复杂配置结构
- ✅ 便于版本控制和文档化
- ✅ 适合本地开发

### 使用方法

1. **创建配置文件**:
```bash
cp config.example.yaml config.yaml
vim config.yaml
```

2. **本地运行**:
```bash
python gitea_mirror_backup.py
```

3. **Docker 中使用**:
```yaml
# docker-compose.yml
services:
  backup:
    volumes:
      - ./config.yaml:/app/config.yaml:ro
```

### 配置文件示例

```yaml
# Gitea 配置
gitea:
  docker_container: gitea
  docker_git_user: git
  data_volume: /opt/gitea/gitea
  repos_path: git/repositories

# 备份配置
backup:
  root: /opt/backup/gitea-mirrors
  organizations: []  # 留空表示备份所有组织
  check_mirror_only: false
  
  # 保留策略
  retention:
    snapshots_days: 30
    archives_months: 12
    reports_days: 30

# 异常检测
alerts:
  commit_decrease_threshold: 10
  size_decrease_threshold: 30
  protect_abnormal_snapshots: true

# 日志配置
logging:
  file: /var/log/gitea-mirror-backup.log
  level: INFO
  format: '[%(asctime)s] %(levelname)s: %(message)s'
  date_format: '%Y-%m-%d %H:%M:%S'

# 报告配置
reports:
  directory: reports
  latest_link: latest-report.md

# 高级配置
advanced:
  concurrent_backups: 0  # 0 表示自动
  backup_timeout: 0      # 0 表示无限制
  verify_docker: true
  generate_restore_script: true

# 通知配置（可选）
notifications:
  webhook:
    url: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
    notify_on: on_alert  # always, on_alert, never
```

## 🔀 方式 3: 混合使用（推荐用于生产环境）

### 使用场景
- 基础配置放在 config.yaml 中（便于管理和文档化）
- 敏感信息和环境特定配置用环境变量（安全且灵活）

### 示例

**config.yaml** (基础配置):
```yaml
gitea:
  docker_container: gitea
  data_volume: /data/gitea

backup:
  root: /backup
  retention:
    snapshots_days: 30
    archives_months: 12

logging:
  level: INFO
```

**docker-compose.yml** (环境特定配置):
```yaml
services:
  backup:
    volumes:
      - ./config.yaml:/app/config.yaml:ro
    environment:
      # 覆盖配置文件中的值
      - LOG_LEVEL=DEBUG
      # 添加敏感信息
      - WEBHOOK_URL=${WEBHOOK_URL}
```

**.env** (敏感信息):
```bash
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=secret-key
```

## 🔍 配置验证

### 验证配置是否正确

```bash
# 本地验证
python src/config_loader.py -c config.yaml --validate

# Docker 验证
docker compose run --rm backup python src/config_loader.py --validate
```

### 查看当前生效的配置

```bash
# 本地查看
python src/config_loader.py -c config.yaml

# Docker 查看
docker compose run --rm backup python src/config_loader.py
```

## 📝 配置最佳实践

### 1. 敏感信息管理

❌ **不推荐**：
```yaml
# config.yaml
notifications:
  webhook:
    url: https://webhook.site/secret-key-123  # 不要把密钥写在配置文件中
```

✅ **推荐**：
```bash
# .env 文件（不要提交到 git）
WEBHOOK_URL=https://webhook.site/secret-key-123

# .gitignore
.env
config.yaml
```

### 2. 环境隔离

```bash
# 开发环境
.env.dev
BACKUP_ROOT=/tmp/backup
LOG_LEVEL=DEBUG

# 生产环境
.env.prod
BACKUP_ROOT=/opt/backup
LOG_LEVEL=INFO
WEBHOOK_URL=https://production-webhook
```

### 3. 配置文件模板

```bash
# 提交到 git 的模板
config.example.yaml

# 实际使用的配置（不提交）
config.yaml

# .gitignore
config.yaml
.env
.env.*
```

## 🆘 常见问题

### Q: 环境变量和配置文件冲突怎么办？

A: 环境变量优先级更高，会覆盖配置文件中的值。

### Q: 如何知道当前使用的是哪个配置？

A: 运行时会输出配置来源：
```
✓ 已加载配置文件: /app/config.yaml
✓ 应用了 3 个环境变量覆盖
```

### Q: Docker 环境必须要 config.yaml 吗？

A: **不需要**。如果只使用环境变量，完全不需要 config.yaml。

### Q: 如何在不重启容器的情况下修改配置？

A: 
- 环境变量：需要重启容器
- 配置文件：如果挂载了配置文件，修改后重新运行备份即可（不需要重启容器）

---

**相关文档**:
- [Docker 部署指南](docker.md)
- [主文档](../README_CN.md)

