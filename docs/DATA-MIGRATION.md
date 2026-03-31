# 数据迁移指南

## 📋 概述

本指南帮助你将运行中的 Gitea Mirror Backup 服务及其数据迁移到新服务器。

### 迁移包含的内容

- ✅ 备份文件数据（保留硬链接关系，节省存储空间）
- ✅ Web 数据库（用户账号、备份历史记录）
- ✅ 配置文件（`.env`、`config.yaml`）
- ✅ 日志文件（可选）

### 关键特性

- **保留硬链接** — 迁移后备份数据仍使用硬链接，不会导致存储空间翻倍
- **增量同步** — 支持断点续传，中途中断可重新运行
- **零停机** — 可以在服务运行时进行初始同步，最后只需短暂停机

---

## 🚀 快速开始

### 最小化停机时间方案（推荐）

```bash
# 1. 在旧服务器上进行初始同步（服务保持运行）
rsync -avH --progress /opt/gitea/backup/ user@new-server:/opt/gitea/backup/

# 2. 停止旧服务器的服务
docker compose --profile full down

# 3. 进行最后的增量同步（很快）
rsync -avH --delete --progress /opt/gitea/backup/ user@new-server:/opt/gitea/backup/

# 4. 在新服务器上启动服务
ssh user@new-server
cd /path/to/gitea-mirror-backup
docker compose --profile full up -d
```

---

## 📊 数据位置速查表

| 数据类型 | 旧服务器路径 | 新服务器路径 | 大小 | 重要性 |
|---|---|---|---|---|
| 备份快照 | `/opt/gitea/backup/` | `/opt/gitea/backup/` | 大（GB~TB） | 🔴 高 |
| Web 数据库 | `./web/data/web.db` | `./web/data/web.db` | 小（MB） | 🔴 高 |
| 配置文件 | `.env`、`config.yaml` | `.env`、`config.yaml` | 小（KB） | 🔴 高 |
| 日志 | `/var/log/gitea-backup/` | `/var/log/gitea-backup/` | 中（MB~GB） | 🟡 低 |

---

## 详细迁移步骤

### 第一步：准备工作

#### 1.1 检查源数据大小

```bash
# 在旧服务器上检查各部分数据大小
du -sh /opt/gitea/backup/          # 备份数据
du -sh ./web/data/                 # Web 数据库
du -sh /var/log/gitea-backup/      # 日志

# 检查硬链接使用情况
find /opt/gitea/backup -type f -links +1 | wc -l
# 输出数字表示有多少文件使用了硬链接
```

#### 1.2 检查目标服务器存储空间

```bash
# 在新服务器上检查可用空间
df -h /opt/
# 确保可用空间 > 备份数据大小 × 1.2（留余量）
```

#### 1.3 验证网络连接

```bash
# 测试 SSH 连接
ssh user@new-server "echo 'Connection OK'"

# 测试网络速度（可选）
iperf3 -c new-server  # 需要在两端都运行 iperf3
```

---

### 第二步：同步备份数据（保留硬链接）

#### 方案 A：使用 rsync（推荐，支持增量同步）

**优点**：
- ✅ 支持增量同步（中途中断可续传）
- ✅ 可以看到实时进度
- ✅ 支持 `--delete` 保持同步
- ✅ 网络友好（只传输变化部分）

**步骤**：

```bash
# 第一次完整同步（在旧服务器上执行）
# 这可能需要很长时间，取决于数据大小
rsync -avH --progress \
  --exclude='*.tmp' \
  --exclude='*.lock' \
  /opt/gitea/backup/ user@new-server:/opt/gitea/backup/

# 如果中途中断，重新运行同一命令会自动续传
# 只会同步未完成的部分
```

**参数说明**：
- `-a` — 归档模式（保留权限、时间戳、所有者等）
- `-v` — 详细输出
- `-H` — **保留硬链接**（关键参数！）
- `--progress` — 显示每个文件的进度
- `--exclude` — 排除临时文件

**监控进度**：

```bash
# 在另一个终端查看传输速度
watch -n 1 'du -sh /opt/gitea/backup/'  # 新服务器上

# 或者查看 rsync 进程
ps aux | grep rsync
```

#### 方案 B：使用 tar（适合一次性迁移）

**优点**：
- ✅ 保留硬链接
- ✅ 可以压缩传输
- ✅ 原子性操作

**步骤**：

```bash
# 在旧服务器上打包（保留硬链接）
cd /opt && tar -chf - gitea/backup/ | pv | gzip > gitea_backup.tar.gz

# 传输到新服务器
scp gitea_backup.tar.gz user@new-server:/tmp/

# 在新服务器上解包
cd /opt && tar -xzf /tmp/gitea_backup.tar.gz

# 清理临时文件
rm /tmp/gitea_backup.tar.gz
```

**参数说明**：
- `-c` — 创建归档
- `-h` — **跟随符号链接并保留硬链接**
- `-f -` — 输出到标准输出
- `pv` — 显示进度（需要安装 `apt install pv`）

---

### 第三步：同步 Web 数据库

```bash
# 在旧服务器上
rsync -av --progress ./web/data/ user@new-server:/path/to/gitea-mirror-backup/web/data/

# 或者使用 scp（如果数据较小）
scp -r ./web/data user@new-server:/path/to/gitea-mirror-backup/
```

---

### 第四步：同步配置文件

```bash
# 在旧服务器上
rsync -av --progress \
  .env \
  config.yaml \
  docker-compose.yml \
  user@new-server:/path/to/gitea-mirror-backup/
```

---

### 第五步：停止旧服务器（可选但推荐）

如果使用了 rsync 增量同步，现在可以停止旧服务器以确保数据一致性：

```bash
# 在旧服务器上
docker compose --profile full down

# 进行最后的增量同步（很快）
rsync -avH --delete --progress /opt/gitea/backup/ user@new-server:/opt/gitea/backup/
rsync -av --delete --progress ./web/data/ user@new-server:/path/to/gitea-mirror-backup/web/data/
```

---

### 第六步：在新服务器上验证和启动

#### 6.1 验证数据完整性

```bash
# SSH 到新服务器
ssh user@new-server

# 检查备份数据
ls -lh /opt/gitea/backup/
du -sh /opt/gitea/backup/

# 检查 Web 数据库
ls -lh /path/to/gitea-mirror-backup/web/data/web.db

# 检查配置文件
ls -lh /path/to/gitea-mirror-backup/.env
ls -lh /path/to/gitea-mirror-backup/config.yaml
```

#### 6.2 验证硬链接是否保留

```bash
# 检查硬链接数量
find /opt/gitea/backup -type f -links +1 | wc -l

# 应该有大量文件显示硬链接数 > 1
# 例如：
ls -li /opt/gitea/backup/backuphub/repo1/snapshots/
# 12345678 -rw-r--r-- 5 user group 1024 Mar 31 10:00 file.txt
#                      ↑ 这个数字 > 1 表示有硬链接
```

#### 6.3 调整配置（如果需要）

```bash
cd /path/to/gitea-mirror-backup

# 编辑 .env（如果新服务器环境不同）
nano .env
# 检查以下内容：
# - SECRET_KEY（建议重新生成）
# - 通知 Webhook URL
# - 其他环境特定配置

# 编辑 config.yaml（如果路径不同）
nano config.yaml
# 检查以下内容：
# - gitea.docker_container
# - backup.root
# - 其他路径配置
```

#### 6.4 启动服务

```bash
# 构建镜像（如果需要）
docker compose build

# 验证配置
docker compose run --rm backup --validate-config

# 启动 Web 服务
docker compose --profile web up -d

# 查看日志
docker compose logs -f web

# 启动定时任务
docker compose --profile cron up -d

# 或全部启动
docker compose --profile full up -d
```

#### 6.5 验证服务正常运行

```bash
# 检查容器状态
docker compose ps

# 查看 Web 服务日志
docker compose logs web

# 访问 Web 界面
# http://new-server:8010

# 检查备份历史是否完整
# 登录 Web 界面 → 查看 Snapshots 和 Reports
```

---

## 🔍 故障排查

### 问题 1：硬链接没有保留

**症状**：迁移后存储空间翻倍

**原因**：rsync 没有使用 `-H` 参数，或目标文件系统不支持硬链接

**解决方案**：

```bash
# 检查是否使用了 -H 参数
# 重新同步（使用正确参数）
rsync -avH --delete --progress /opt/gitea/backup/ user@new-server:/opt/gitea/backup/

# 检查文件系统类型
df -T /opt/gitea/backup/
# 应该是 ext4、btrfs 等支持硬链接的文件系统
# 如果是 NFS、SMB 等网络文件系统，硬链接可能不支持
```

### 问题 2：rsync 中途中断

**症状**：传输未完成

**解决方案**：

```bash
# 重新运行同一命令，rsync 会自动续传
rsync -avH --progress /opt/gitea/backup/ user@new-server:/opt/gitea/backup/

# 如果还是有问题，可以加上 --partial 参数
rsync -avH --partial --progress /opt/gitea/backup/ user@new-server:/opt/gitea/backup/
```

### 问题 3：Web 服务无法启动

**症状**：`docker compose up -d web` 失败

**解决方案**：

```bash
# 查看详细错误日志
docker compose logs web

# 检查数据库文件权限
ls -la /path/to/gitea-mirror-backup/web/data/

# 检查 .env 文件
cat /path/to/gitea-mirror-backup/.env | grep SECRET_KEY

# 如果 SECRET_KEY 为空，生成一个新的
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 然后更新 .env 文件
```

### 问题 4：备份历史丢失

**症状**：Web 界面看不到之前的备份记录

**解决方案**：

```bash
# 检查 Web 数据库是否正确迁移
ls -lh /path/to/gitea-mirror-backup/web/data/web.db

# 检查数据库文件大小（应该 > 0）
# 如果文件大小为 0，说明没有正确迁移

# 重新同步 Web 数据库
rsync -av --progress ./web/data/ user@new-server:/path/to/gitea-mirror-backup/web/data/
```

---

## 📈 性能对比

### 使用硬链接（正确迁移）

```
备份数据大小: 500GB
快照数量: 100 个
实际占用: ~550GB（仅增量变化）
迁移时间: 2-4 小时（取决于网络速度）
```

### 不使用硬链接（错误迁移）

```
备份数据大小: 500GB
快照数量: 100 个
实际占用: ~50TB（每个快照完整复制）
迁移时间: 20-40 小时
```

---

## ✅ 迁移检查清单

完成迁移后，请逐项检查：

- [ ] 备份数据已同步到新服务器
- [ ] 硬链接已保留（`find /opt/gitea/backup -type f -links +1 | wc -l` 有输出）
- [ ] Web 数据库已同步
- [ ] 配置文件已同步
- [ ] 新服务器存储空间正常（不是翻倍）
- [ ] `.env` 文件已更新（SECRET_KEY 等）
- [ ] `config.yaml` 文件已更新（路径等）
- [ ] Web 服务已启动并可访问
- [ ] 备份历史在 Web 界面可见
- [ ] 定时任务已启动
- [ ] 日志正常输出（无错误）

---

## 🔐 安全建议

### 迁移前

- [ ] 备份旧服务器的所有数据（以防万一）
- [ ] 测试新服务器的网络连接和存储
- [ ] 验证 SSH 密钥配置

### 迁移中

- [ ] 使用 SSH 密钥认证（不要用密码）
- [ ] 在安全的网络环境中进行迁移
- [ ] 监控迁移进度，确保没有中断

### 迁移后

- [ ] 验证数据完整性
- [ ] 更新 DNS 或负载均衡器指向新服务器
- [ ] 保留旧服务器数据一段时间（作为备份）
- [ ] 更新文档和监控告警

---

## 📚 相关文档

- [配置指南](./configuration.md) — 配置文件说明
- [Docker 硬链接指南](./docker-hardlink.md) — 硬链接配置详解
- [部署指南](./deployment.md) — 部署相关信息
- [恢复指南](./recovery.md) — 数据恢复方法

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
   ```

3. **检查文件权限**：
   ```bash
   ls -la /opt/gitea/backup/
   ls -la /path/to/gitea-mirror-backup/web/data/
   ```

4. **查看相关文档**：
   - 本文档的"故障排查"部分
   - [Docker 硬链接指南](./docker-hardlink.md)
   - 项目 README 和其他文档

---

**迁移完成！** 🎉

现在你的服务已经成功迁移到新服务器，并保留了硬链接的存储优势。
