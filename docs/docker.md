# Docker 部署指南

## 📦 快速开始

### 方式 1: 使用 Docker Compose（推荐）

1. **配置方式选择**

Docker 环境支持两种配置方式，**推荐使用环境变量**：

**方式 A: 使用环境变量（推荐）**
```bash
# 直接在 docker-compose.yml 中配置环境变量
# 或者创建 .env 文件
cat > .env << EOF
GITEA_DOCKER_CONTAINER=gitea
BACKUP_ROOT=/shared/backup
LOG_LEVEL=INFO
EOF
```

**方式 B: 使用配置文件（可选）**
```bash
# 如果你更喜欢用配置文件
cp config.example.yaml config.yaml
vim config.yaml

# 然后在 docker-compose.yml 中取消注释配置文件挂载
# - ./config.yaml:/app/config.yaml:ro
```

> **配置优先级**：环境变量 > config.yaml > 默认值

2. **选择运行模式**

```bash
# 【推荐】手动执行一次备份（执行完自动退出）
docker compose run --rm backup

# 启动 Web 管理界面（可选）
docker compose up -d web

# 启动定时任务（可选，每天凌晨 2 点自动备份）
docker compose up -d cron

# 同时启动 Web + 定时任务
docker compose up -d web cron

# 一键启动所有长期运行的服务（Web + 定时任务，不包含手动备份）
docker compose --profile full up -d

# 查看日志
docker compose logs -f web
docker compose logs -f cron

# 停止服务（需要指定服务名或 profile）
docker compose down web cron           # 停止指定的服务
docker compose --profile full down     # 停止所有服务
docker compose stop web                # 仅停止 web 服务
docker compose stop cron               # 仅停止 cron 服务
```

> **注意**：`docker compose up` 不会启动任何服务，这是设计行为。请根据需要选择上述命令。

### 方式 2: 使用 Docker 命令

1. **构建镜像**

```bash
docker build -t gitea-mirror-backup:latest .
```

2. **运行容器**

```bash
docker run -d \
  --name gitea-backup \
  -v /opt/gitea/gitea:/data/gitea:ro \
  -v /opt/backup/gitea-mirrors:/backup:rw \
  -v /var/log/gitea-backup:/logs:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -e GITEA_DOCKER_CONTAINER=gitea \
  -e BACKUP_ROOT=/backup \
  -e LOG_LEVEL=INFO \
  gitea-mirror-backup:latest
```

### 方式 3: 使用预构建镜像

```bash
# 拉取镜像
docker pull yourusername/gitea-mirror-backup:latest

# 运行
docker run -d \
  --name gitea-backup \
  -v /opt/gitea/gitea:/data/gitea:ro \
  -v /opt/backup/gitea-mirrors:/backup:rw \
  yourusername/gitea-mirror-backup:latest
```

## ⚙️ 配置

### 配置方式

#### 方式 1: 环境变量（推荐用于 Docker）

所有配置都可以通过环境变量设置，**这是 Docker 环境的推荐方式**：

```bash
# Gitea 配置
GITEA_DOCKER_CONTAINER=gitea
GITEA_DATA_VOLUME=/data/gitea
GITEA_REPOS_PATH=git/repositories

# 备份配置
BACKUP_ROOT=/backup
BACKUP_ORGANIZATIONS=Org1,Org2
CHECK_MIRROR_ONLY=false

# 保留策略
SNAPSHOT_RETENTION_DAYS=30
ARCHIVE_RETENTION_MONTHS=12
REPORT_RETENTION_DAYS=30

# 异常检测
COMMIT_DECREASE_THRESHOLD=10
SIZE_DECREASE_THRESHOLD=30
PROTECT_ABNORMAL_SNAPSHOTS=true

# 日志
LOG_FILE=/logs/gitea-mirror-backup.log
LOG_LEVEL=INFO

# 通知（可选）
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
WEBHOOK_NOTIFY_ON=on_alert
```

#### 方式 2: 配置文件（可选）

如果你更喜欢使用配置文件，可以挂载 `config.yaml`：

```yaml
# docker-compose.yml
services:
  backup:
    volumes:
      - ./config.yaml:/app/config.yaml:ro  # 取消注释这行
```

**配置优先级**：`环境变量` > `config.yaml` > `默认值`

> **提示**：
> - Docker 环境推荐使用环境变量（符合 12-factor 原则）
> - 本地运行脚本时推荐使用 config.yaml（方便管理）
> - 两种方式可以混用，环境变量会覆盖配置文件

### 卷挂载

| 宿主机路径 | 容器路径 | 权限 | 说明 |
|-----------|---------|------|------|
| `/opt/gitea/gitea` | `/data/gitea` | ro | Gitea 数据目录（只读） |
| `/opt/backup/gitea-mirrors` | `/backup` | rw | 备份存储目录（读写） |
| `/var/log/gitea-backup` | `/logs` | rw | 日志目录（读写） |
| `/var/run/docker.sock` | `/var/run/docker.sock` | ro | Docker socket（只读） |
| `./config.yaml` | `/app/config.yaml` | ro | 配置文件（可选） |

## 🕐 定时任务

### 方式 1: 使用 Docker Compose Cron 服务（推荐）

```bash
# 启动定时任务服务（每天凌晨 2 点自动执行）
docker compose up -d cron

# 查看日志
docker compose logs -f cron

# 停止定时任务
docker compose stop cron
```

### 方式 2: 宿主机 Cron

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点执行）
0 2 * * * cd /path/to/gitea-mirror-backup && docker compose run --rm backup >> /var/log/gitea-backup/cron.log 2>&1
```

### 方式 3: Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gitea-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: gitea-mirror-backup:latest
            volumeMounts:
            - name: gitea-data
              mountPath: /data/gitea
              readOnly: true
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: gitea-data
            hostPath:
              path: /opt/gitea/gitea
          - name: backup-storage
            hostPath:
              path: /opt/backup/gitea-mirrors
          restartPolicy: OnFailure
```

## 🔍 监控和维护

### 查看日志

```bash
# Docker Compose
docker-compose logs -f gitea-backup

# Docker
docker logs -f gitea-backup

# 查看日志文件
tail -f /var/log/gitea-backup/gitea-mirror-backup.log
```

### 查看备份状态

```bash
# 进入容器
docker exec -it gitea-backup /bin/bash

# 查看最新报告
cat /backup/latest-report.md

# 查看备份目录
ls -lh /backup
```

### 手动执行备份

```bash
# Docker Compose（推荐）
docker compose run --rm backup

# Docker 命令
docker run --rm \
  -v /opt/gitea/gitea:/data/gitea:ro \
  -v /opt/backup/gitea-mirrors:/backup:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  gitea-mirror-backup:latest
```

### 验证配置

```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  gitea-mirror-backup:latest --validate-config
```

## 🛠️ 故障排查

### 问题 1: 无法访问 Docker socket

**错误**: `Cannot connect to the Docker daemon`

**解决**:
```bash
# 确保挂载了 Docker socket
-v /var/run/docker.sock:/var/run/docker.sock:ro

# 检查权限
ls -l /var/run/docker.sock
```

### 问题 2: 权限不足

**错误**: `Permission denied`

**解决**:
```bash
# 检查目录权限
chmod 755 /opt/backup/gitea-mirrors
chmod 755 /var/log/gitea-backup

# 或使用 root 用户运行
docker run --user root ...
```

### 问题 3: 找不到 Gitea 容器

**错误**: `Container 'gitea' not found`

**解决**:
```bash
# 检查容器名称
docker ps | grep gitea

# 设置正确的容器名
-e GITEA_DOCKER_CONTAINER=your-gitea-container-name
```

## 📊 资源使用

### 推荐配置

- **CPU**: 0.5-1.0 核心
- **内存**: 256-512 MB
- **磁盘**: 取决于备份大小

### 性能优化

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## 🔒 安全建议

1. **只读挂载** - Gitea 数据目录使用只读模式
2. **最小权限** - 仅授予必要的权限
3. **网络隔离** - 使用独立的 Docker 网络
4. **定期更新** - 及时更新镜像版本
5. **日志审计** - 定期检查日志文件

## 📝 使用场景示例

### 场景 1: 仅手动备份（最简单）

适合：偶尔手动执行备份，不需要 Web 界面和自动化

```bash
# 执行一次备份
docker compose run --rm backup
```

### 场景 2: 定时自动备份

适合：需要定期自动备份，不需要 Web 管理界面

```bash
# 启动定时任务服务
docker compose up -d cron

# 查看执行日志
docker compose logs -f cron
```

### 场景 3: Web 管理 + 手动备份

适合：需要通过 Web 界面查看备份状态和历史记录

```bash
# 启动 Web 服务
docker compose up -d web

# 访问 http://localhost:8000

# 需要时手动执行备份
docker compose run --rm backup
```

### 场景 4: 完整功能（Web + 定时任务）

适合：生产环境，需要自动化备份和 Web 管理

```bash
# 方式 1: 分别启动
docker compose up -d web cron

# 方式 2: 使用 full profile
docker compose --profile full up -d

# 访问 Web: http://localhost:8000
# 定时任务会在每天凌晨 2 点自动执行
```

## 🚀 生产环境部署

### 使用 Docker Swarm

```bash
# 启动完整功能
docker stack deploy -c docker-compose.yml gitea-backup
```

### 使用 Kubernetes

参考 `examples/kubernetes/` 目录中的示例配置。

## 🎯 常见使用模式

### 模式对比

| 使用模式 | 启动命令 | 停止命令 | 适用场景 | 资源占用 |
|---------|---------|---------|---------|---------|
| 手动备份 | `docker compose run --rm backup` | 自动退出 | 测试、临时备份 | 仅运行时占用 |
| 仅定时任务 | `docker compose up -d cron` | `docker compose stop cron` | 自动化备份，无需 Web | 低（~100MB） |
| 仅 Web | `docker compose up -d web` | `docker compose stop web` | 查看历史，手动触发 | 低（~150MB） |
| Web + 定时 | `docker compose up -d web cron` | `docker compose down web cron` | 生产环境推荐 | 中（~250MB） |
| 完整功能 | `docker compose --profile full up -d` | `docker compose --profile full down` | Web + 定时任务（不含手动备份） | 中（~250MB） |

### 推荐配置

**开发/测试环境**：
```bash
# 手动执行即可
docker compose run --rm backup
```

**小型生产环境**：
```bash
# 仅定时任务，节省资源
docker compose up -d cron
```

**企业生产环境**：
```bash
# Web + 定时任务，便于管理和监控
docker compose up -d web cron
```

## ❓ 常见问题

### Q: 为什么 `docker compose up` 不启动任何服务？

A: 这是设计行为。为了避免意外启动不需要的服务，所有服务都使用了 `profiles`。请根据需要选择：
- 手动备份：`docker compose run --rm backup`（一次性任务，执行完自动退出）
- 启动 Web：`docker compose up -d web`
- 启动定时任务：`docker compose up -d cron`
- 启动所有长期服务：`docker compose --profile full up -d`（Web + 定时任务，不含手动备份）

> **注意**：`backup` 服务是一次性任务，不会被 `--profile full` 启动，需要手动执行。

### Q: 为什么 `docker compose down` 不能停止服务？

A: 因为服务使用了 `profiles`，需要明确指定服务名或 profile：

```bash
# ❌ 这样不会停止使用 profile 的服务
docker compose down

# ✅ 正确的停止方式
docker compose down web cron           # 停止指定服务
docker compose --profile full down     # 停止所有服务
docker compose stop cron               # 仅停止 cron

# 查看当前运行的服务
docker compose ps
```

### Q: 必须要 config.yaml 文件吗？

A: **不需要**。配置系统支持三种方式（优先级从高到低）：
1. **环境变量**（推荐用于 Docker）- 在 `docker-compose.yml` 中配置
2. **config.yaml**（可选）- 如果需要可以挂载
3. **默认值** - 内置的合理默认配置

Docker 环境推荐使用环境变量，这样更灵活且符合容器化最佳实践。

### Q: 如何同时使用配置文件和环境变量？

A: 可以混用，环境变量会覆盖配置文件中的值。例如：
```yaml
# config.yaml 中设置基础配置
backup:
  root: /backup
  
# docker-compose.yml 中用环境变量覆盖
environment:
  - BACKUP_ROOT=/custom/backup  # 这个会生效
```

### Q: 如何修改定时任务的执行时间？

A: 编辑 `docker-compose.yml` 中 `cron` 服务的 `command` 部分：

```yaml
# 默认：每天凌晨 2 点
command: -c "echo '0 2 * * * ...' | crontab - && cron -f"

# 改为：每天中午 12 点
command: -c "echo '0 12 * * * ...' | crontab - && cron -f"

# 改为：每 6 小时一次
command: -c "echo '0 */6 * * * ...' | crontab - && cron -f"
```

### Q: Web 界面可以触发备份吗？

A: 可以。访问 Web 界面后，可以手动触发备份任务。或者使用命令：

```bash
docker compose run --rm backup
```

### Q: 如何查看备份是否成功？

A: 有多种方式：
1. 查看日志：`docker compose logs -f cron`
2. 访问 Web 界面查看备份历史
3. 查看备份目录：`ls -lh /opt/backup/gitea-mirrors`
4. 查看报告文件：`cat /opt/backup/gitea-mirrors/latest-report.md`

---

**更多信息**: 
- [主文档](../README_CN.md)
- [配置指南](../README_CN.md#配置)
- [通知配置](notifications.md)

