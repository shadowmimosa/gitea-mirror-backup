# 恢复脚本使用示例

本文档展示如何使用自动生成的 `restore.sh` 恢复脚本。

## Docker 部署

backup 容器内路径为 `/shared/backup/...`。在宿主机**不要**直接执行 `restore.sh`，应通过容器运行：

```bash
# 推荐：restore 辅助服务
docker compose run --rm -it restore \
  /shared/backup/myorg/myrepo/restore.sh

# 或使用 backup 服务并覆盖 entrypoint
docker compose run --rm -it --entrypoint bash backup \
  /shared/backup/myorg/myrepo/restore.sh

# 或使用仓库目录下的包装脚本
/shared/backup/myorg/myrepo/restore-via-docker.sh
```

> backup 镜像 `ENTRYPOINT` 为 `python gitea_mirror_backup.py`，若省略 `--entrypoint bash`，
> `bash restore.sh` 会被当作 Python 脚本参数，无法进入恢复流程。

批量更新所有仓库的恢复脚本：

```bash
docker compose run --rm --entrypoint python backup \
  gitea_mirror_backup.py --regenerate-restore-scripts
```

## 直接部署

## 恢复脚本位置

每个备份的仓库都会生成一个恢复脚本：

```
/backup/gitea-mirrors/
└── myorg/
    └── myrepo/
        ├── snapshots/          # 快照目录
        │   ├── 20260124-020000/
        │   ├── 20260123-020000/
        │   └── ...
        ├── archives/           # 归档目录
        └── restore.sh          # 恢复脚本 ← 这个！
```

## 运行恢复脚本

**Docker 部署** — 见上文 Docker 专节。

**直接部署：**

```bash
/backup/gitea-mirrors/myorg/myrepo/restore.sh
```

## 交互式恢复流程

### 步骤 1: 选择快照

```
==========================================
Gitea 镜像仓库恢复工具
==========================================
仓库: myorg/myrepo

可用的快照:
  [1] 20260124-020000
      timestamp=2026-01-24T02:00:00.123456
  [2] 20260123-020000
      timestamp=2026-01-23T02:00:00.123456
  [3] 20260122-020000
      timestamp=2026-01-22T02:00:00.123456

恢复选项:
  1) 恢复到原仓库位置（会覆盖现有仓库）
  2) 导出为新仓库（不影响原仓库）
  3) 导出为 Git Bundle 文件

选择恢复方式 [1]:
```

### 步骤 2: 选择快照编号

```
选择要恢复的快照编号 [1]: 2
```

## 恢复模式详解

### 模式 1: 恢复到原位置

**适用场景**：
- 源仓库已修复，需要同步回来
- 临时查看历史版本
- 非镜像仓库

**注意事项**：
- ⚠️ 会覆盖现有仓库
- ⚠️ 镜像仓库下次同步可能再次被覆盖
- ✅ 自动备份当前版本到 `.backup-时间戳`
- ✅ 自动修复文件权限和 Git hooks

**执行流程**：
```
选择恢复方式 [1]: 1
选择要恢复的快照编号 [1]: 2

已选择快照: 20260123-020000

⚠️  警告: 此操作将覆盖容器中的原仓库
⚠️  注意: 如果这是镜像仓库，下次同步时可能再次被源仓库覆盖
确认继续? (yes/NO): yes

正在恢复到原位置...
1. 停止 Docker 容器...
2. 备份当前仓库到: /path/to/repo.git.backup-20260124-143000
3. 恢复快照...
4. 修复文件权限...
5. 启动 Docker 容器...
6. 更新仓库信息...

✓ 恢复完成!

如需回滚，当前仓库已备份至:
  /path/to/repo.git.backup-20260124-143000

验证命令:
  docker exec -u git gitea git -C /data/git/repositories/myorg/myrepo.git log --oneline -5
```

### 模式 2: 导出为新仓库（推荐用于镜像仓库）

**适用场景**：
- 镜像仓库被 force push，需要保留完整历史
- 创建独立副本用于开发
- 不想影响原仓库

**优势**：
- ✅ 原仓库不受影响
- ✅ 创建独立的新仓库
- ✅ 自动移除镜像配置
- ✅ 可以正常推送新代码

**执行流程**：
```
选择恢复方式 [1]: 2
选择要恢复的快照编号 [1]: 2

已选择快照: 20260123-020000

导出为新仓库（独立副本，不影响原仓库）
输入新仓库名称（如 test-restored）: myrepo-recovered

正在导出新仓库...
1. 复制仓库数据...
2. 修复文件权限...
3. 移除镜像配置...

✓ 仓库文件已导出完成!

新仓库位置: /path/to/git/repositories/myorg/myrepo-recovered.git

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 下一步：在 Gitea 中采集仓库

由于 Gitea 没有命令行采集功能，需要手动操作：

1. 登录 Gitea 管理员账号

2. 进入管理后台：
   访问: http://your-gitea/-/admin/repos/unadopted
   或点击: 右上角头像 -> 管理后台 -> 仓库管理 -> 未采集的Git仓库

3. 搜索仓库（重要！区分大小写）：
   在搜索框输入: myorg/myrepo-recovered
   ⚠️  注意: 必须使用实际文件系统路径（小写），大小写敏感

4. 找到仓库后，点击右侧的「采集」按钮

5. 完成！访问: http://your-gitea/myorg/myrepo-recovered

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 模式 3: 导出为 Bundle

**适用场景**：
- 需要传输给其他人
- 离线保存
- 在其他服务器恢复

**执行流程**：
```
选择恢复方式 [1]: 3
选择要恢复的快照编号 [1]: 2

已选择快照: 20260123-020000

输入 Bundle 文件保存路径 [/tmp/myorg-myrepo.bundle]: /tmp/backup.bundle

正在导出 Git Bundle...

✓ 导出完成!

Bundle 文件: /tmp/backup.bundle

使用方法:
  git clone /tmp/backup.bundle restored-repo
```

## 验证恢复结果

### 模式 1 验证（原位置恢复）

```bash
# 查看提交历史
docker exec -u git gitea git -C /data/git/repositories/myorg/myrepo.git log --oneline -10

# 检查仓库完整性
docker exec -u git gitea git -C /data/git/repositories/myorg/myrepo.git fsck

# 在 Gitea 界面查看
http://your-gitea/myorg/myrepo
```

### 模式 2 验证（新仓库）

```bash
# 查看新仓库文件
ls -la /path/to/git/repositories/myorg/myrepo-recovered.git

# 查看提交历史
docker exec -u git gitea git -C /data/git/repositories/myorg/myrepo-recovered.git log --oneline

# 采集后在 Gitea 界面访问
http://your-gitea/myorg/myrepo-recovered
```

### 模式 3 验证（Bundle）

```bash
# 克隆 bundle
git clone /tmp/backup.bundle test-repo
cd test-repo

# 查看历史
git log --oneline -10

# 添加远程仓库并推送（可选）
git remote remove origin  # 移除 bundle 源
git remote add origin https://your-git-server/path/to/repo.git
git push -u origin main
```

## 常见问题

### Q: 恢复后 Gitea 显示 "Git 钩子已损坏"

**原因**: 恢复后权限或 hooks 未正确设置

**解决**: 脚本会自动执行 `update-server-info`，但如果还有问题：

```bash
# 重新修复权限
docker exec gitea chown -R git:git /data/git/repositories/myorg/myrepo.git

# 更新仓库信息
docker exec -u git gitea git -C /data/git/repositories/myorg/myrepo.git update-server-info

# 重启容器
docker restart gitea
```

### Q: 模式 2 导出后在 Gitea 界面看不到

**原因**: 需要手动采集，且搜索**区分大小写**

**解决**: 
1. 访问 `http://your-gitea/-/admin/repos/unadopted`
2. 搜索完整路径（小写）：`myorg/myrepo-recovered`
3. 点击「采集」按钮

### Q: 恢复后提交历史不完整

**原因**: 可能选择了异常后的快照

**解决**: 查看受保护的快照，选择有 🔒 标记的：

```bash
# 查看哪些快照被保护
find /backup/gitea-mirrors/myorg/myrepo/snapshots -name ".protected"

# 查看保护原因
cat /backup/gitea-mirrors/myorg/myrepo/snapshots/20260123-020000/.protected
```

受保护的快照通常是异常发生**之前**的正常状态，包含完整历史。

## 最佳实践

1. **镜像仓库发生 force push**
   - 使用模式 2 导出为新仓库
   - 让原镜像继续同步（保持最新）
   - 新仓库保留完整历史供参考

2. **临时查看历史版本**
   - 使用模式 3 导出 bundle
   - 本地克隆查看
   - 不影响服务器

3. **恢复到生产环境**
   - 先用模式 2 测试
   - 确认无误后再用模式 1
   - 或直接保留新仓库

## 更多信息

参考文档：
- [配置指南](../docs/configuration.md)
- [故障排查](../docs/troubleshooting.md)
