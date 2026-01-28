# 配置迁移指南

## 📋 概述

本指南帮助你从旧的配置方式迁移到新的混合配置方案。

### 变更内容

- ✅ 简化了 `docker-compose.yml`，移除了大量环境变量
- ✅ 引入 `config/config.yaml` 用于基础配置和复杂配置
- ✅ 引入 `.env` 文件用于敏感信息和环境特定配置
- ✅ 统一了配置命名（`BACKUP_ROOT` 替代 `BACKUP_BASE_PATH`）
- ✅ 所有服务共享配置，减少重复

### 配置优先级

```
.env 环境变量 > config/config.yaml > 默认值
```

---

## 🚀 迁移步骤

### 步骤 1: 备份当前配置

```bash
# 备份 docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# 如果有旧的 config.yaml，也备份
cp config.yaml config.yaml.backup 2>/dev/null || true
```

### 步骤 2: 创建配置目录和文件

**直接部署**：
```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 复制环境变量模板
cp env.example .env
```

**Docker 部署**：
```bash
# 复制 Docker 配置模板（使用容器内路径）
cp config.docker.yaml config.yaml

# 复制环境变量模板
cp env.example .env
```

> **重要**：Docker 部署必须使用 `config.docker.yaml`，不要使用 `config.example.yaml`

### 步骤 3: 迁移配置

#### 3.1 基础配置迁移到 config/config.yaml

编辑 `config/config.yaml`，设置基础配置：

```yaml
gitea:
  docker_container: "gitea"  # 你的 Gitea 容器名
  data_volume: "/shared/gitea"

backup:
  root: "/shared/backup"
  organizations: []  # 如果需要过滤组织，在这里设置
  check_mirror_only: false

# 其他配置保持默认或根据需要修改
```

#### 3.2 敏感信息迁移到 .env

编辑 `.env`，设置敏感信息：

```bash
# 必需：Web 服务密钥
SECRET_KEY=your-production-secret-key-here

# 可选：如果需要覆盖 config.yaml 中的配置
# BACKUP_ORGANIZATIONS=Org1,Org2
# LOG_LEVEL=INFO

# 可选：通知配置
# WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/...
```

**生成安全密钥**：

```bash
# Python 方式
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL 方式
openssl rand -base64 32
```

### 步骤 4: 更新 docker-compose.yml

新的 `docker-compose.yml` 已经简化，主要变更：

1. **移除了大量环境变量**（现在在 config.yaml 和 .env 中）
2. **添加了 env_file 引用**（所有服务都加载 .env）
3. **挂载了配置目录**（`./config:/app/config:ro`）
4. **统一了配置命名**（Web 服务也使用 `BACKUP_ROOT`）

如果你有自定义修改，请手动合并。

### 步骤 5: 验证配置

```bash
# 检查配置文件语法
docker compose config

# 验证备份配置
docker compose run --rm backup --validate-config

# 查看当前配置（脱敏）
docker compose run --rm backup --show-config
```

### 步骤 6: 测试运行

```bash
# 测试备份（不实际执行）
docker compose run --rm backup --dry-run

# 执行一次备份测试
docker compose run --rm backup

# 检查日志
tail -f /var/log/gitea-backup/gitea-mirror-backup.log
```

### 步骤 7: 启动服务

```bash
# 启动 Web 服务
docker compose up -d web

# 启动定时任务
docker compose up -d cron

# 或全部启动
docker compose --profile full up -d
```

---

## 📝 配置对照表

### 旧配置 vs 新配置

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `docker-compose.yml` 环境变量 | `config/config.yaml` | 基础配置 |
| `docker-compose.yml` 环境变量 | `.env` | 敏感信息 |
| `BACKUP_BASE_PATH` | `BACKUP_ROOT` | 统一命名 |
| Web 服务独立环境变量 | 共享 `.env` | 统一配置 |

### 环境变量映射

| 旧环境变量 | 新位置 | 说明 |
|-----------|--------|------|
| `GITEA_DOCKER_CONTAINER` | `config.yaml` 或 `.env` | Gitea 容器名 |
| `GITEA_DATA_VOLUME` | `config.yaml` | Gitea 数据目录 |
| `BACKUP_ROOT` | `config.yaml` 或 `.env` | 备份根目录 |
| `BACKUP_ORGANIZATIONS` | `config.yaml` 或 `.env` | 组织过滤 |
| `SECRET_KEY` | `.env`（必需） | Web 服务密钥 |
| `WECOM_WEBHOOK_URL` | `.env` | 企业微信通知 |

---

## 🔧 常见问题

### Q1: 我的配置文件在哪里？

**新配置结构**：

```
项目根目录/
├── config/
│   └── config.yaml          # 基础配置（不提交到 Git）
├── .env                     # 敏感信息（不提交到 Git）
├── config.example.yaml      # 配置模板（提交到 Git）
├── env.example              # 环境变量模板（提交到 Git）
└── docker-compose.yml       # 容器编排（提交到 Git）
```

### Q2: 我需要修改哪些文件？

**最小配置**：

1. 复制 `env.example` 为 `.env`，修改 `SECRET_KEY`
2. 复制 `config.example.yaml` 为 `config/config.yaml`，修改 Gitea 容器名和路径
3. 修改 `docker-compose.yml` 中的 `volumes.gitea-data.driver_opts.device`

### Q3: 环境变量还能用吗？

**可以！** 环境变量优先级最高，会覆盖 `config.yaml` 中的配置。

你可以：
- 在 `.env` 中设置环境变量
- 在 `docker-compose.yml` 中设置环境变量
- 在系统中设置环境变量

### Q4: 如何只使用环境变量，不用 config.yaml？

如果你不想使用 `config.yaml`，可以：

1. 不创建 `config/config.yaml` 文件
2. 在 `.env` 中设置所有配置
3. 系统会使用默认值 + 环境变量

### Q5: Web 服务的配置在哪里？

Web 服务现在与备份服务共享配置：

- 共享 `.env` 文件（通过 `env_file`）
- 共享 `config/config.yaml`（通过卷挂载）
- 使用统一的配置命名（`BACKUP_ROOT`）

### Q6: 旧的 config.yaml 还能用吗？

可以，但建议迁移到 `config/config.yaml`：

```bash
# 如果你有旧的 config.yaml
mkdir -p config
mv config.yaml config/config.yaml
```

### Q7: 如何回滚到旧配置？

```bash
# 恢复备份的 docker-compose.yml
cp docker-compose.yml.backup docker-compose.yml

# 删除新配置
rm -rf config/ .env

# 重启服务
docker compose down
docker compose up -d
```

---

## 📚 配置示例

### 示例 1: 最小配置

**config/config.yaml**:
```yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"

backup:
  root: "/shared/backup"
```

**.env**:
```bash
SECRET_KEY=your-secret-key-here
```

### 示例 2: 带组织过滤

**config/config.yaml**:
```yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"

backup:
  root: "/shared/backup"
  organizations:
    - "MyOrg1"
    - "MyOrg2"
  check_mirror_only: true
```

### 示例 3: 带通知配置

**config/config.yaml**:
```yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"

backup:
  root: "/shared/backup"

notifications:
  wecom:
    enabled: true
    notify_on: "on_alert"
```

**.env**:
```bash
SECRET_KEY=your-secret-key-here
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

### 示例 4: 使用环境变量覆盖

**config/config.yaml**:
```yaml
backup:
  organizations: []  # 默认备份所有
```

**.env**:
```bash
SECRET_KEY=your-secret-key-here
BACKUP_ORGANIZATIONS=Org1,Org2  # 覆盖为只备份这两个组织
LOG_LEVEL=DEBUG  # 覆盖日志级别
```

---

## ✅ 迁移检查清单

完成迁移后，请检查：

- [ ] 已创建 `config/config.yaml` 并配置基础信息
- [ ] 已创建 `.env` 并设置 `SECRET_KEY`
- [ ] 已更新 `docker-compose.yml`（或使用新版本）
- [ ] 已更新 `.gitignore`（确保 `.env` 和 `config/config.yaml` 不被提交）
- [ ] 已验证配置：`docker compose run --rm backup --validate-config`
- [ ] 已测试备份：`docker compose run --rm backup`
- [ ] 已检查日志：`tail -f /var/log/gitea-backup/gitea-mirror-backup.log`
- [ ] Web 服务正常启动：`docker compose up -d web`
- [ ] 定时任务正常运行：`docker compose up -d cron`

---

## 🆘 需要帮助？

如果迁移过程中遇到问题：

1. **查看日志**：
   ```bash
   docker compose logs backup
   docker compose logs web
   ```

2. **验证配置**：
   ```bash
   docker compose run --rm backup --validate-config
   docker compose run --rm backup --show-config
   ```

3. **检查文件权限**：
   ```bash
   ls -la config/
   ls -la .env
   ```

4. **查看文档**：
   - `docs/configuration.md` - 配置说明
   - `docs/configuration-analysis.md` - 配置分析
   - `docs/docker.md` - Docker 部署指南

---

**迁移完成！** 🎉

现在你的配置更加清晰、安全和易于维护了。

