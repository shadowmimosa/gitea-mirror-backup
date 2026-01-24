# Gitea Docker 版本备份系统 - 部署指南

## 📋 你的环境信息

- **Gitea 运行方式**: Docker 容器 (Debian 宿主机)
- **Gitea 访问地址**: http://localhost:3000
- **备份组织**: BackupHub
- **测试仓库**: BackupHub/test.git

## 🔍 第一步：确认 Docker 卷路径

首先需要找到 Gitea 的数据卷在宿主机上的实际路径：

```bash
# 查看 Gitea 容器信息
docker inspect gitea | grep -A 10 Mounts

# 或者查看所有卷
docker volume ls
docker volume inspect gitea_data

# 找到类似这样的输出：
# "Mountpoint": "/var/lib/docker/volumes/gitea_data/_data"
```

常见的路径有：
- `/var/lib/docker/volumes/gitea_data/_data`
- `/data/gitea` (如果你用了自定义绑定挂载)
- `~/gitea-data` (如果挂载到用户目录)

## 🚀 第二步：修改脚本配置

下载脚本后，修改配置部分：

```bash
# 编辑脚本
nano /usr/local/bin/gitea-docker-backup.sh

# 修改这几个关键配置：
DOCKER_CONTAINER="gitea"  # 你的容器名，用 docker ps 查看

# 这个是最关键的！根据第一步找到的路径填写
GITEA_DATA_VOLUME="/var/lib/docker/volumes/gitea_data/_data"

# 仓库在数据卷中的相对路径（一般不需要改）
GITEA_REPOS_PATH="git/repositories"

# 备份存储位置（可以自定义）
BACKUP_ROOT="/backup/gitea-mirrors"

# 只备份 BackupHub 组织的仓库
BACKUP_ORGANIZATIONS="BackupHub"
```

## 📂 第三步：测试路径是否正确

```bash
# 假设你的配置是：
GITEA_DATA_VOLUME="/var/lib/docker/volumes/gitea_data/_data"
GITEA_REPOS_PATH="git/repositories"

# 测试完整路径
ls -la /var/lib/docker/volumes/gitea_data/_data/git/repositories/BackupHub/

# 应该能看到 test.git 目录
# 输出类似：
# drwxr-xr-x 7 git git 4096 Jan 24 10:00 test.git
```

## ⚙️ 第四步：安装和测试

### 安装脚本

```bash
# 创建脚本文件
sudo nano /usr/local/bin/gitea-docker-backup.sh
# 粘贴脚本内容，修改配置，保存

# 设置执行权限
sudo chmod +x /usr/local/bin/gitea-docker-backup.sh

# 创建备份目录
sudo mkdir -p /backup/gitea-mirrors

# 创建日志目录
sudo touch /var/log/gitea-mirror-backup.log
```

### 首次测试运行

```bash
# 手动运行一次
sudo /usr/local/bin/gitea-docker-backup.sh

# 实时查看日志
tail -f /var/log/gitea-mirror-backup.log
```

成功的输出应该类似：

```
[2025-01-24 10:00:00] ==========================================
[2025-01-24 10:00:00] Gitea Docker 镜像备份任务开始
[2025-01-24 10:00:00] ==========================================
[2025-01-24 10:00:00] ✓ Docker 容器运行正常
[2025-01-24 10:00:00] ----------------------------------------
[2025-01-24 10:00:00] 处理: BackupHub/test
[2025-01-24 10:00:00] 创建快照: BackupHub/test
[2025-01-24 10:00:00]   ✓ 快照成功: 20250124-100000
[2025-01-24 10:00:00] 处理了 1 个仓库
[2025-01-24 10:00:00] ==========================================
[2025-01-24 10:00:00] 备份任务完成
[2025-01-24 10:00:00] ==========================================
```

### 检查备份结果

```bash
# 查看备份目录结构
tree /backup/gitea-mirrors/

# 应该看到：
# /backup/gitea-mirrors/
# └── BackupHub/
#     └── test/
#         ├── snapshots/
#         │   └── 20250124-100000/
#         ├── restore.sh
#         └── .size_tracking
```

## ⏰ 第五步：设置定时任务

```bash
# 编辑 root 的 crontab
sudo crontab -e

# 添加以下内容：
# 每天凌晨 2 点运行备份
0 2 * * * /usr/local/bin/gitea-docker-backup.sh >> /var/log/gitea-mirror-backup.log 2>&1

# 每周一早上 8 点查看报告（可选，给自己发个提醒）
0 8 * * 1 cat /backup/gitea-mirrors/weekly-report.md | mail -s "Gitea 备份周报" your-email@example.com
```

## 📊 第六步：查看报告

每周一会自动生成报告：

```bash
# 查看报告
cat /backup/gitea-mirrors/weekly-report.md

# 或用浏览器查看（如果安装了 markdown 查看器）
# 或转换成 HTML
markdown /backup/gitea-mirrors/weekly-report.md > /tmp/report.html
```

报告示例：

```markdown
# Gitea 镜像仓库备份报告

**生成时间**: 2025-01-27 02:00:00

## 📊 总体统计

- **备份仓库数**: 50
- **快照总数**: 1500
- **归档总数**: 6
- **占用空间**: 25.3GB

## ✅ 全部正常

本周期内所有仓库均未检测到异常。

## 📦 仓库备份详情

| 仓库 | 快照数 | 最新快照 | 归档数 | 占用空间 |
|------|--------|----------|--------|----------|
| BackupHub/test | 30 | 20250127-020000 | 1 | 120MB |
| BackupHub/repo2 | 30 | 20250127-020000 | 1 | 450MB |
...
```

## 🔧 测试场景：模拟 force push

让我们用 test 仓库测试一下异常检测：

### 1. 模拟正常使用

```bash
# 正常情况下，脚本每天备份，不会有告警
# 查看大小跟踪文件
cat /backup/gitea-mirrors/BackupHub/test/.size_tracking
# 输出: 120000  (表示 120MB)
```

### 2. 模拟 force push 删除大量历史

在 GitHub 上对源仓库执行 force push，删除大量提交后：

```bash
# Gitea 镜像同步后，第二天凌晨运行备份脚本
sudo /usr/local/bin/gitea-docker-backup.sh

# 查看日志
tail /var/log/gitea-mirror-backup.log

# 如果检测到大小减少超过 30%，会看到：
# [2025-01-25 02:00:00] 处理: BackupHub/test
# [2025-01-25 02:00:00]   ⚠️  大小减少 65%

# 查看异常记录
cat /backup/gitea-mirrors/BackupHub/test/.alerts

# 输出:
# [2025-01-25T02:00:00+00:00]
# 仓库大小异常减少: 65%
# 上次: 120000KB → 当前: 42000KB
# 可能原因: force push 或分支删除
```

### 3. 查看周报（周一生成）

```bash
cat /backup/gitea-mirrors/weekly-report.md

# 会包含：
## ⚠️ 需要关注的仓库

### BackupHub/test
```
[2025-01-25T02:00:00+00:00]
仓库大小异常减少: 65%
上次: 120000KB → 当前: 42000KB
可能原因: force push 或分支删除
```

**最新快照**: 20250124-020000

**恢复命令**:
```bash
/backup/gitea-mirrors/BackupHub/test/restore.sh
```
```

## 🔄 恢复操作

如果确认需要恢复（比如 test 仓库被 force push 清空了）：

```bash
# 运行自动生成的恢复脚本
sudo /backup/gitea-mirrors/BackupHub/test/restore.sh

# 交互式选择：
# ==========================================
# Gitea 镜像仓库恢复工具
# ==========================================
# 仓库: BackupHub/test
#
# 可用的快照:
#   [0] 20250124-020000
#       timestamp=2025-01-24T02:00:00+00:00
#   [1] 20250123-020000
#       timestamp=2025-01-23T02:00:00+00:00
#   [2] 20250122-020000
#       timestamp=2025-01-22T02:00:00+00:00
#
# 选择要恢复的快照编号 [0]: 0
#
# 已选择: 20250124-020000
#
# ⚠️  警告: 此操作将覆盖容器中的仓库
# 确认继续? (yes/NO): yes
#
# 正在恢复...
# 1. 停止 Docker 容器...
# 2. 备份当前仓库到: /var/lib/.../test.git.backup-20250125-100000
# 3. 恢复快照...
# 4. 启动 Docker 容器...
#
# ✓ 恢复完成!
```

## 🎯 实际使用建议

基于你有几十到几百个库的情况：

### 每日自动化
- ✅ 每天凌晨自动备份（无需人工干预）
- ✅ 保留 30 天的快照（硬链接，几乎不占额外空间）
- ✅ 每月 1 号自动创建 bundle 归档

### 每周检查
- ✅ 周一早上看一眼周报
- ✅ 如果有"需要关注的仓库"，决定是否恢复
- ✅ 大多数情况下报告会显示"全部正常"

### 只在需要时恢复
- ✅ 看到告警后，运行 restore.sh 即可
- ✅ 选择要恢复的快照（通常是昨天的）
- ✅ 自动停止容器、恢复、重启，全程自动化

## 💾 磁盘空间估算

假设你有 100 个仓库，平均每个 500MB：

```
原始仓库总大小: 50GB
每日快照（硬链接）: ~5GB (只保存变化的文件)
30 天快照: ~150GB
每月归档: ~600MB/月 × 12 = ~7.2GB
总计: 约 200GB 左右
```

如果空间不够，调整参数：
```bash
SNAPSHOT_RETENTION_DAYS=14  # 只保留 14 天
ARCHIVE_RETENTION_MONTHS=6   # 只保留 6 个月
```

## ❓ 常见问题

### Q1: 脚本运行报错找不到仓库？

```bash
# 检查容器名
docker ps
# 修改 DOCKER_CONTAINER="实际的容器名"

# 检查数据卷路径
docker volume inspect gitea_data
# 修改 GITEA_DATA_VOLUME="实际路径"
```

### Q2: 如何只备份特定仓库？

```bash
# 方法1: 按组织过滤
BACKUP_ORGANIZATIONS="BackupHub AnotherOrg"

# 方法2: 在脚本中添加排除列表
# 修改 process_repository 函数，添加：
if [[ "$repo_name" == "BackupHub/large-repo" ]]; then
    return 0
fi
```

### Q3: 快照占用空间太大？

```bash
# 检查是否真的是硬链接
ls -li /backup/gitea-mirrors/BackupHub/test/snapshots/*/objects/pack/*.pack

# 如果 inode 号相同，说明是硬链接（正常）
# 如果 inode 号不同，说明复制了文件（异常）

# 解决方法：确保备份目录和数据卷在同一个文件系统
df -h /var/lib/docker/volumes/gitea_data/_data
df -h /backup/gitea-mirrors
# 应该显示同一个设备
```

### Q4: 如何手动触发报告生成？

```bash
# 方法1: 修改日期判断（临时）
sudo /usr/local/bin/gitea-docker-backup.sh

# 方法2: 直接调用函数（需要修改脚本）
# 在脚本最后添加：
# if [ "$1" = "--report" ]; then
#     generate_weekly_report
#     exit 0
# fi

# 然后运行：
sudo /usr/local/bin/gitea-docker-backup.sh --report
```

## 📝 总结

这套方案给你提供：

- ✅ **全自动**: 设置好后不用管，每天自动备份
- ✅ **零打扰**: 只在周一看一眼报告，平时不会收到通知
- ✅ **高效率**: 硬链接技术，几百个库也不会占用太多空间
- ✅ **易恢复**: 一行命令就能恢复，带交互式选择
- ✅ **双保险**: 每日快照 + 每月归档

对于几十到几百个仓库的场景非常合适！