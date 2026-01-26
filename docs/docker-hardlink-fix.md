# 重要：配置硬链接的正确方法

## 关键点

Docker 中要使硬链接工作，**源文件和目标文件必须在容器内的同一个挂载点下**。

## 错误配置 ❌

```yaml
volumes:
  - gitea-data:/data:ro      # 挂载点 1
  - gitea-data:/backup:rw    # 挂载点 2（即使是同一个卷，也是不同挂载点！）

environment:
  - GITEA_DATA_VOLUME=/data/gitea
  - BACKUP_ROOT=/backup
```

**问题**：虽然都是 `gitea-data` 卷，但在容器内是两个不同的挂载点（`/data` 和 `/backup`），硬链接会失败！

## 正确配置 ✅

```yaml
volumes:
  - gitea-data:/shared:rw    # 只有一个挂载点！

environment:
  - GITEA_DATA_VOLUME=/shared/gitea    # 在同一挂载点下的子目录
  - BACKUP_ROOT=/shared/backup         # 在同一挂载点下的子目录
```

**原理**：`/shared/gitea` 和 `/shared/backup` 都在同一个挂载点 `/shared` 下，硬链接可以工作！

## 宿主机目录结构

```bash
/opt/gitea-data/              # 宿主机路径（对应容器内的 /shared）
├── gitea/                    # Gitea 数据
│   └── git/
│       └── repositories/     # Git 仓库
└── backup/                   # 备份目录
    └── backuphub/
        └── repo1/
            └── snapshots/    # 快照（使用硬链接）
```

## 完整配置示例

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
    image: gitea/gitea:latest
    volumes:
      - gitea-data:/data  # Gitea 使用 /data
    environment:
      - USER_UID=1000
      - USER_GID=1000

  gitea-backup:
    image: gitea-mirror-backup:latest
    volumes:
      - gitea-data:/shared:rw  # 备份使用 /shared（同一个卷）
    environment:
      - GITEA_DATA_VOLUME=/shared/gitea  # 指向 Gitea 数据的实际位置
      - BACKUP_ROOT=/shared/backup
```

## 验证方法

### 1. 检查挂载点

```bash
# 进入容器
docker exec -it gitea-backup /bin/bash

# 查看挂载点
df -h

# 应该看到 /shared/gitea 和 /shared/backup 在同一个文件系统
```

### 2. 测试硬链接

```bash
# 在容器内
cd /shared/gitea/git/repositories
touch test-file
ln test-file /shared/backup/test-hardlink

# 如果成功，说明硬链接可用
ls -li test-file /shared/backup/test-hardlink
# inode 号应该相同
```

### 3. 查看备份日志

```bash
docker-compose logs gitea-backup

# 如果没有 "⚠️ 无法使用硬链接" 的警告，说明成功
```

## 迁移步骤

如果你的 Gitea 已经在运行：

```bash
# 1. 停止服务
docker-compose down

# 2. 创建新的目录结构
mkdir -p /opt/gitea-data/gitea
mkdir -p /opt/gitea-data/backup

# 3. 移动 Gitea 数据
# 假设原来 Gitea 数据在 /opt/gitea/gitea
mv /opt/gitea/gitea/* /opt/gitea-data/gitea/

# 4. 更新 docker-compose.yml
# - Gitea 服务：volumes: - gitea-data:/data
# - 备份服务：volumes: - gitea-data:/shared:rw
#            environment: GITEA_DATA_VOLUME=/shared/gitea

# 5. 重新启动
docker-compose up -d

# 6. 验证
docker-compose logs gitea-backup
```

## 常见错误

### 错误 1：多个挂载点
```yaml
❌ volumes:
  - gitea-data:/data:ro
  - gitea-data:/backup:rw
```

### 错误 2：路径不匹配
```yaml
❌ volumes:
  - gitea-data:/shared:rw
environment:
  - GITEA_DATA_VOLUME=/data/gitea  # 路径不在 /shared 下！
```

### 错误 3：不同的卷
```yaml
❌ volumes:
  gitea-vol:
  backup-vol:
services:
  gitea-backup:
    volumes:
      - gitea-vol:/data
      - backup-vol:/backup  # 不同的卷！
```

## 总结

✅ **关键原则**：在容器内，源路径和目标路径必须在**同一个挂载点**下！

- 正确：`/shared/gitea` → `/shared/backup` ✅
- 错误：`/data` → `/backup` ❌（不同挂载点）

