# Docker 硬链接配置指南

## 问题说明

Docker 容器中，如果 Gitea 数据目录和备份目录挂载在不同的宿主机路径或不同的 Docker 卷上，会导致：
- ❌ 硬链接失败（Invalid cross-device link）
- ❌ 备份占用大量磁盘空间
- ❌ 无法享受硬链接的空间节省优势

## 解决方案

### 方案 1：使用共享 Docker 卷（推荐）

让 Gitea 数据和备份目录都在同一个 Docker 卷上：

```yaml
version: '3.8'

volumes:
  gitea-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/gitea-data  # 宿主机实际路径

services:
  gitea:
    volumes:
      - gitea-data:/data
  
  gitea-backup:
    volumes:
      - gitea-data:/data:ro      # Gitea 数据（只读）
      - gitea-data:/backup:rw    # 备份目录（读写）- 同一卷
```

**目录结构**：
```
/opt/gitea-data/           # 宿主机路径
├── gitea/                 # Gitea 数据
│   └── git/repositories/
└── backup/                # 备份目录
    └── backuphub/
```

**优点**：
- ✅ 硬链接正常工作
- ✅ 节省磁盘空间
- ✅ 备份速度快

### 方案 2：宿主机同一文件系统

确保两个挂载路径在宿主机的同一文件系统上：

```yaml
services:
  gitea-backup:
    volumes:
      - /opt/gitea/gitea:/data/gitea:ro
      - /opt/gitea/backup:/backup:rw  # 在同一文件系统
```

**检查文件系统**：
```bash
# 查看挂载点
df -h /opt/gitea /opt/backup

# 如果输出显示相同的文件系统，硬链接可用
# 例如：
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       100G   50G   50G  50% /opt
```

### 方案 3：使用 Docker 命名卷

```yaml
volumes:
  gitea-storage:

services:
  gitea:
    volumes:
      - gitea-storage:/data
  
  gitea-backup:
    volumes:
      - gitea-storage:/data:ro
      - gitea-storage:/backup:rw
```

## 配置示例

### 完整的 docker-compose.yml

```yaml
version: '3.8'

volumes:
  gitea-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/gitea-data

services:
  gitea:
    image: gitea/gitea:latest
    container_name: gitea
    volumes:
      - gitea-data:/data
    ports:
      - "3000:3000"
      - "222:22"
    restart: unless-stopped

  gitea-backup:
    image: gitea-mirror-backup:latest
    container_name: gitea-backup
    environment:
      - TZ=Asia/Shanghai
      - GITEA_DOCKER_CONTAINER=gitea
      - GITEA_DATA_VOLUME=/data/gitea
      - BACKUP_ROOT=/backup
    volumes:
      - gitea-data:/data:ro
      - gitea-data:/backup:rw
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: "no"
```

### 目录结构规划

```
/opt/gitea-data/              # 共享卷根目录
├── gitea/                    # Gitea 数据
│   ├── git/
│   │   └── repositories/     # Git 仓库
│   ├── gitea/
│   └── ssh/
└── backup/                   # 备份目录
    ├── backuphub/
    │   └── repo1/
    │       ├── snapshots/    # 快照（硬链接）
    │       └── archives/     # 归档
    └── reports/
```

## 验证硬链接

### 1. 进入容器检查

```bash
# 进入备份容器
docker exec -it gitea-backup /bin/bash

# 检查文件系统
df -h /data /backup

# 应该显示相同的文件系统
```

### 2. 测试硬链接

```bash
# 在容器中测试
cd /data/gitea/git/repositories
cp -al some-repo.git /backup/test-hardlink

# 检查是否成功
ls -li /data/gitea/git/repositories/some-repo.git/objects/pack/*.pack
ls -li /backup/test-hardlink/objects/pack/*.pack

# 如果 inode 号相同，说明硬链接成功
```

### 3. 查看日志

```bash
# 查看备份日志
docker-compose logs gitea-backup

# 如果看到这个警告，说明硬链接失败：
# ⚠️  无法使用硬链接（跨文件系统），使用普通复制...

# 如果没有警告，说明硬链接成功
```

## 迁移现有部署

### 从分离卷迁移到共享卷

```bash
# 1. 停止服务
docker-compose down

# 2. 创建共享目录
mkdir -p /opt/gitea-data/gitea
mkdir -p /opt/gitea-data/backup

# 3. 移动数据
mv /opt/gitea/gitea/* /opt/gitea-data/gitea/
mv /opt/backup/gitea-mirrors/* /opt/gitea-data/backup/

# 4. 更新 docker-compose.yml（使用上面的配置）

# 5. 重新启动
docker-compose up -d

# 6. 验证
docker-compose logs gitea-backup
```

## 性能对比

### 使用硬链接（同一文件系统）
```
仓库大小: 500MB
快照数量: 30 个
实际占用: ~550MB（仅增量变化）
备份速度: 5-10 秒
```

### 不使用硬链接（跨文件系统）
```
仓库大小: 500MB
快照数量: 30 个
实际占用: ~15GB（每个快照完整复制）
备份速度: 2-5 分钟
```

## 常见问题

### Q: 我的 Gitea 已经在运行，如何改为共享卷？

A: 参考上面的"迁移现有部署"部分。

### Q: 使用 Docker 命名卷会不会影响性能？

A: 不会，命名卷和 bind mount 性能相当，都支持硬链接。

### Q: 可以只让备份目录使用硬链接吗？

A: 不行，硬链接要求源文件和目标文件在同一文件系统上。

### Q: 如何确认硬链接正在工作？

A: 查看日志，如果没有"无法使用硬链接"的警告，就是成功的。

## 推荐配置

**生产环境推荐**：使用方案 1（共享 Docker 卷）

```yaml
volumes:
  gitea-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/gitea-data

services:
  gitea-backup:
    volumes:
      - gitea-data:/data:ro
      - gitea-data:/backup:rw
```

**优点**：
- ✅ 硬链接工作正常
- ✅ 节省 90%+ 磁盘空间
- ✅ 备份速度快 10-30 倍
- ✅ 易于管理和维护

