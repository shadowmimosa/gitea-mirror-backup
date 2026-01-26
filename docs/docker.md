# Docker 部署指南

## 📦 快速开始

### 方式 1: 使用 Docker Compose（推荐）

1. **准备配置文件**

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置
vim config.yaml
```

2. **启动服务**

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f gitea-backup

# 停止服务
docker-compose down
```

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

### 环境变量

所有配置都可以通过环境变量设置：

```yaml
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

### 卷挂载

| 宿主机路径 | 容器路径 | 权限 | 说明 |
|-----------|---------|------|------|
| `/opt/gitea/gitea` | `/data/gitea` | ro | Gitea 数据目录（只读） |
| `/opt/backup/gitea-mirrors` | `/backup` | rw | 备份存储目录（读写） |
| `/var/log/gitea-backup` | `/logs` | rw | 日志目录（读写） |
| `/var/run/docker.sock` | `/var/run/docker.sock` | ro | Docker socket（只读） |
| `./config.yaml` | `/app/config.yaml` | ro | 配置文件（可选） |

## 🕐 定时任务

### 方式 1: 使用 Cron 服务（Docker Compose）

```bash
# 启动定时任务服务
docker-compose --profile cron up -d gitea-backup-cron

# 查看日志
docker-compose logs -f gitea-backup-cron
```

### 方式 2: 宿主机 Cron

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点执行）
0 2 * * * docker run --rm \
  -v /opt/gitea/gitea:/data/gitea:ro \
  -v /opt/backup/gitea-mirrors:/backup:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  gitea-mirror-backup:latest
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
# Docker Compose
docker-compose run --rm gitea-backup

# Docker
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

## 📝 示例配置

### 最小配置

```yaml
version: '3.8'
services:
  gitea-backup:
    image: gitea-mirror-backup:latest
    volumes:
      - /opt/gitea/gitea:/data/gitea:ro
      - /opt/backup:/backup:rw
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - GITEA_DOCKER_CONTAINER=gitea
      - BACKUP_ROOT=/backup
```

### 完整配置（带通知）

```yaml
version: '3.8'
services:
  gitea-backup:
    image: gitea-mirror-backup:latest
    volumes:
      - /opt/gitea/gitea:/data/gitea:ro
      - /opt/backup:/backup:rw
      - /var/log/gitea-backup:/logs:rw
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - GITEA_DOCKER_CONTAINER=gitea
      - BACKUP_ROOT=/backup
      - LOG_LEVEL=INFO
      - WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
      - WEBHOOK_NOTIFY_ON=on_alert
    restart: unless-stopped
```

## 🚀 生产环境部署

### 使用 Docker Swarm

```bash
docker stack deploy -c docker-compose.yml gitea-backup
```

### 使用 Kubernetes

参考 `examples/kubernetes/` 目录中的示例配置。

---

**更多信息**: 
- [主文档](../README_CN.md)
- [配置指南](../README_CN.md#配置)
- [通知配置](notifications.md)

