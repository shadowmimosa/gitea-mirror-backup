# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.2] - 2026-01-28

### Changed

- 🔧 **配置系统重构** - 统一配置管理方式
  - 统一所有服务（backup、web、cron）使用相同的配置方式
  - 配置优先级：环境变量 > config.yaml > 默认值
  - 移除 docker-compose.yml 中的硬编码环境变量
  - 所有服务统一使用 `.env` + `config.yaml` 配置

- 📝 **配置文件模板优化**
  - 新增 `config.docker.yaml` - Docker 部署专用配置模板（容器路径）
  - 新增 `config.example.yaml` - 直接部署配置模板（宿主机路径）
  - 明确区分容器路径（/shared/gitea）和宿主机路径（/opt/gitea）
  - 简化配置文件结构，移除不必要的 `config/` 目录层级

- 🔔 **通知配置增强**
  - 新增 10 个通知相关环境变量映射
  - 支持通过环境变量覆盖所有通知配置
  - 环境变量：WECOM_WEBHOOK_URL、DINGTALK_WEBHOOK_URL、DINGTALK_SECRET、EMAIL_SMTP_HOST、EMAIL_SMTP_PORT、EMAIL_USE_TLS、EMAIL_USERNAME、EMAIL_PASSWORD、EMAIL_FROM、EMAIL_TO

- 📚 **文档全面更新**
  - 新增 `docs/CONFIG-FILES.md` - 配置文件使用指南
  - 新增 `docs/ENV-VARIABLES.md` - 环境变量完整参考
  - 新增 `docs/MIGRATION-GUIDE.md` - 配置迁移指南
  - 更新 `README.md` 和 `README_CN.md` - 简化配置说明
  - 更新 `docs/docker.md` - Docker 部署配置说明
  - 更新 `docs/configuration.md` - 配置系统详细说明
  - 更新 `docs/notifications.md` - 通知配置说明
  - 更新 `env.example` - 完整的环境变量示例

### Fixed

- 🐛 **配置一致性修复**
  - 修复 Web 服务使用硬编码环境变量的问题
  - 修复通知环境变量无法覆盖 config.yaml 的问题
  - 修复配置文件路径混淆（容器路径 vs 宿主机路径）
  - 修复服务间配置方式不一致的问题

### Added

- ✨ **配置管理工具**
  - `.gitignore` 新增 `.env` 和 `config.yaml`（防止敏感信息泄露）
  - 提供两套配置模板，适配不同部署场景

### Removed

- 🗑️ **清理冗余文档**
  - 删除 `docs/configuration-analysis.md`（临时分析文档）
  - 删除 `docs/DOCS-UPDATE-SUMMARY.md`（临时更新记录）
  - 删除 `docs/REFACTOR-SUMMARY.md`（临时重构记录）

### Technical Details

**配置优先级**：
```
环境变量 > config.yaml > 代码默认值
```

**配置文件选择**：
- Docker 部署：使用 `config.docker.yaml`（容器路径如 /shared/gitea）
- 直接部署：使用 `config.example.yaml`（宿主机路径如 /opt/gitea）

**环境变量映射**（新增）：
```python
'WECOM_WEBHOOK_URL': 'notifications.wecom.webhook_url',
'DINGTALK_WEBHOOK_URL': 'notifications.dingtalk.webhook_url',
'DINGTALK_SECRET': 'notifications.dingtalk.secret',
'EMAIL_SMTP_HOST': 'notifications.email.smtp_host',
'EMAIL_SMTP_PORT': 'notifications.email.smtp_port',
'EMAIL_USE_TLS': 'notifications.email.use_tls',
'EMAIL_USERNAME': 'notifications.email.username',
'EMAIL_PASSWORD': 'notifications.email.password',
'EMAIL_FROM': 'notifications.email.from',
'EMAIL_TO': 'notifications.email.to',
```

**影响范围**：
- 所有 Docker 部署用户需要更新配置文件
- 建议使用新的配置模板重新配置
- 旧配置仍然兼容，但建议迁移

### Upgrade Notes

#### Docker 部署用户

1. **备份现有配置**：
   ```bash
   cp config.yaml config.yaml.backup
   cp .env .env.backup
   ```

2. **使用新模板**：
   ```bash
   cp config.docker.yaml config.yaml
   vim config.yaml  # 根据实际情况调整
   ```

3. **更新 docker-compose.yml**：
   ```bash
   docker compose down
   docker compose pull
   docker compose up -d
   ```

4. **验证配置**：
   ```bash
   docker compose logs backup
   ```

#### 直接部署用户

1. **使用新模板**：
   ```bash
   cp config.example.yaml config.yaml
   vim config.yaml  # 根据实际情况调整
   ```

2. **验证配置**：
   ```bash
   python src/gitea_mirror_backup.py --show-config
   ```

详细迁移指南请参考：`docs/MIGRATION-GUIDE.md`

---

## [1.4.1] - 2026-01-28

### Fixed

- 🐛 **Cron 服务环境变量传递问题**
  - 修复 cron 定时任务无法读取容器环境变量的问题
  - 在 cron 任务中添加 `. /etc/environment` 以加载环境变量
  - 确保 cron 任务使用正确的配置路径（`/shared/gitea` 和 `/shared/backup`）
  - 修复 cron 任务中 Python 命令路径（`python` → `python3`）

- 🔧 **Docker Compose 配置优化**
  - 移除过时的 `version: '3.8'` 配置（避免警告信息）
  - 优化 cron 服务的环境变量导出机制

### Changed

- 📝 **文档更新**
  - 统一使用新版 `docker compose` 命令（替代旧版 `docker-compose`）
  - 更新 README.md、README_CN.md 和 docs/docker.md 中的所有命令示例

### Technical Details

**问题原因**：
- cron 守护进程执行任务时运行在最小化环境中，不会自动继承容器的环境变量
- 导致程序读取 config.yaml 中的默认路径而非环境变量配置的路径

**解决方案**：
```bash
# 容器启动时将环境变量导出到 /etc/environment
printenv | grep -v 'no_proxy' >> /etc/environment

# cron 任务执行前加载环境变量
. /etc/environment && cd /app && /usr/local/bin/python3 gitea_mirror_backup.py
```

**影响范围**：
- 仅影响使用 `docker compose up -d cron` 启动的定时任务服务
- 手动执行（`docker compose run --rm backup`）和 Web 服务不受影响

### Upgrade Notes

如果你正在使用 cron 服务，需要重启以应用修复：

```bash
docker compose down cron
docker compose up -d cron
```

---

## [1.4.0] - 2026-01-27

### Added

- 🌐 **Web 管理界面** - 基于 FastAPI + Vue 3 的现代化 Web 管理系统
  - 用户认证系统（JWT Token）
  - 仪表板 - 实时统计和趋势图表
  - 仓库管理 - 查看所有备份仓库信息
  - 仓库详情页 - 查看单个仓库的所有快照
  - 快照管理 - 浏览、删除快照
  - 报告查看 - Markdown 格式报告展示
  - 暗色主题界面设计

- 📊 **仪表板功能**
  - 总仓库数、快照数、磁盘使用量统计
  - 最后备份时间显示
  - 备份成功率计算
  - 异常仓库数量统计

- 🗂️ **仓库管理功能**
  - 显示仓库全名（owner/repo 格式）
  - 显示提交数、快照数、受保护快照数
  - 显示磁盘使用量和最后备份时间
  - 异常状态标识（⚠️ 有异常）
  - 点击仓库名跳转到详情页

- 📸 **快照管理功能**
  - 查看所有快照或按仓库过滤
  - 显示快照大小、创建时间、保护状态
  - 单个删除和批量删除快照
  - 受保护的快照无法删除（自动禁用）
  - 批量操作时自动跳过受保护快照

- 🔍 **仓库详情页**
  - 显示仓库完整信息（提交数、快照数、磁盘使用等）
  - 列出该仓库的所有快照
  - 支持快照的多选和批量删除
  - 受保护快照的可视化标识（🔒）

- 📝 **报告查看功能**
  - Markdown 格式报告渲染
  - 暗色主题适配
  - 显示报告创建时间和大小
  - 受保护报告标识

- 🐳 **Docker 部署支持**
  - Dockerfile.web - 多阶段构建优化
  - docker-compose.web.yml - Web 服务编排
  - 前后端集成部署
  - 数据持久化配置

### Changed

- 🏗️ **项目结构优化**
  - 新增 `web/` 目录存放 Web 应用代码
  - `web/api/` - FastAPI 后端代码
  - `web/frontend/` - Vue 3 前端代码
  - `web/services/` - 业务逻辑服务
  - `web/models/` - 数据库模型
  - `web/utils/` - 工具函数

- 🔧 **BackupService 适配**
  - 适配实际的备份目录结构（{owner}/{repo_name}/snapshots/）
  - 读取 `.commit_tracking` 获取提交数
  - 读取 `.size_tracking` 获取仓库大小
  - 检测 `.protected` 文件判断快照保护状态
  - 检测 `.alerts` 文件判断仓库异常状态

- 🎨 **前端体验优化**
  - 使用 Naive UI 组件库实现暗色主题
  - 响应式布局设计
  - 统一的分页和表格样式
  - 友好的错误提示和确认对话框
  - 批量操作的智能提示

### Fixed

- 🐛 **目录结构兼容性修复**
  - 修复 Web 界面期望的目录结构与实际备份结构不匹配的问题
  - 修复仪表板统计数据为 0 的问题
  - 修复快照删除 API 缺少 repository 参数的问题

- 🔒 **受保护资源处理**
  - 受保护的快照无法被选择和删除
  - 批量删除时自动跳过受保护的快照
  - 清晰的保护状态可视化标识

### Technical Details

**后端技术栈：**
- FastAPI - 现代化 Python Web 框架
- SQLAlchemy - ORM 数据库操作
- JWT - 用户认证
- bcrypt - 密码加密
- Pydantic - 数据验证

**前端技术栈：**
- Vue 3 - 渐进式 JavaScript 框架
- TypeScript - 类型安全
- Vite - 快速构建工具
- Naive UI - Vue 3 组件库
- Pinia - 状态管理
- Vue Router - 路由管理
- Axios - HTTP 客户端
- Marked - Markdown 渲染

**部署方式：**
```bash
# 构建并启动 Web 服务
docker-compose -f docker-compose.web.yml up -d

# 访问 Web 界面
http://localhost:8000

# 默认账号
用户名: admin
密码: admin123
```

### Documentation

- 📖 新增 `docs/web-usage.md` - Web 管理界面使用文档
- 📖 更新 README 添加 Web 管理界面说明

### Security

- 🔐 JWT Token 认证机制
- 🔐 密码 bcrypt 加密存储
- 🔐 管理员权限控制（删除操作需要管理员权限）
- 🔐 受保护资源的删除保护

---

## [1.3.3] - 2026-01-27

### Added

* 📄 **Markdown 报告渲染支持**

  * 新增 Markdown 报告展示能力
  * 适配暗色主题，使用暗色 Markdown 样式
  * 报告区域背景透明，与系统主题保持一致

* 👁️ **仓库与快照操作增强**

  * 支持分页大小选择（10 / 20 / 50 / 100）
  * 新增快照保护状态展示
  * 新增快照总数展示，信息更完整

### Fixed

* 🐛 **分页与数据显示修复**

  * 修复快照列表分页显示异常问题
  * 修复仓库详情页面分页逻辑不一致的问题
  * 修复仓库详情页部分快照数据显示错误
  * 修复多处 TypeScript 类型错误与 UI 交互问题

* 🧩 **跨平台兼容性修复**

  * 修复 Windows 系统下快照大小计算异常问题
  * Windows 环境下自动回退为 Python 递归计算方式

### Changed

* ⚡ **性能与架构优化**

  * 快照列表改为服务端分页，查询性能提升 10–100 倍
  * 新增快照总数接口，支持前端分页计算
  * 快照大小改为按需计算，仅统计当前页数据
  * Linux / Unix 环境使用 `du` 命令计算快照大小，替代 Python 递归遍历

* 🎨 **前端体验与布局优化**

  * 重构分页逻辑，使用独立分页器组件统一 UI 风格
  * 提升整体可读性与操作一致性

### Technical Details

* 分页机制：

  * 快照列表与仓库详情均支持服务端分页
  * 接口支持 `page`、`pageSize` 参数
* 快照大小计算策略：

  * Linux：优先使用 `du` 命令
  * Windows：自动降级为 Python 递归统计
* 本次更新未引入新的第三方依赖

## [1.3.2] - 2026-01-27

### Fixed

* 🌙 **Markdown 暗色主题适配**

  * 将 Markdown 样式从 `github-markdown-light.css` 切换为 `github-markdown-dark.css`
  * 修复暗色主题下背景不协调问题（背景改为透明）
  * 修复表格、代码块在暗色模式下可读性不足的问题

    * 表格边框使用半透明白色
    * 代码块背景使用半透明白色
    * 表格斑马纹使用半透明背景
  * Markdown 报告区域现已与系统暗色主题完美融合

* 📐 **仪表板布局问题修复**

  * 移除 `max-width: 1400px` 与 `margin: 0 auto` 的布局限制
  * 移除局部 `padding: 20px`（统一由外层布局控制）
  * 修复仪表板页面与仓库管理、快照管理页面宽度不一致的问题

### Added

* 👁️ **仓库管理新增查看入口**

  * 仓库列表新增「操作」列
  * 添加“查看”按钮，使用 `EyeOutline` 图标
  * 支持一键跳转至仓库详情页面
  * 提升仓库列表的可操作性与直观性

### Changed

* 🎨 **前端视觉一致性优化**

  * 统一仪表板与其他管理页面的宽度与留白策略
  * 提升暗色主题下整体 UI 的一致性与可读性

### Technical Details

* Markdown 样式适配：

  * 使用 `github-markdown-dark.css`
  * 自定义覆盖样式实现暗色主题无缝融合
* 仓库列表操作列：

  * 新增图标按钮组件，无需额外依赖
* 本次更新不新增第三方依赖（`marked` 与 `github-markdown-css` 已在此前版本引入）

## [1.3.1] - 2026-01-26

### Fixed

- 🐛 **Docker 环境修复**
  - 修复 Docker 容器时区配置（添加 TZ 环境变量）
  - 修复 cron 服务启动问题（Debian 使用 `cron` 而非 `crond`）
  - 修复跨文件系统硬链接失败问题（自动降级到普通复制）
  - 修复软链接使用绝对路径导致宿主机无法访问的问题（改用相对路径）

- 🔗 **硬链接优化**
  - 添加共享卷配置策略（挂载父目录实现同文件系统硬链接）
  - 添加详细的硬链接配置文档（docs/docker-hardlink.md）
  - 添加硬链接故障排查文档（docs/docker-hardlink-fix.md）
  - 硬链接成功时可节省 90%+ 磁盘空间

### Changed

- 📝 **文档完善**
  - 更新 docker-compose.yml 配置示例
  - 添加硬链接配置最佳实践
  - 添加时区配置说明

### Technical Details

- 跨文件系统检测：捕获 `OSError: [Errno 18] Invalid cross-device link`
- 自动降级策略：硬链接失败时使用 `cp -a` 保持文件属性
- 软链接相对路径：`latest_report.symlink_to(report_file.relative_to(latest_report.parent))`
- 共享卷策略：挂载 `/shared` 父目录，所有数据在同一文件系统

## [1.3.0] - 2026-01-26

### Added

- 🐳 **Docker 容器化支持**
  - Dockerfile - 基于 python:3.9-slim 的轻量级镜像
  - docker-compose.yml - 快速部署配置
  - 支持所有配置选项（环境变量 + 配置文件）
  - 健康检查和资源限制
  - 定时任务服务（可选）
  - 完整的卷挂载配置

- 📝 **Docker 文档**
  - docs/docker.md - 完整的 Docker 部署指南
  - 快速开始指南
  - 配置说明和示例
  - 定时任务配置（3 种方式）
  - 监控和维护指南
  - 故障排查指南
  - 生产环境部署建议


### Changed

- 📚 **文档更新**
  - README.md / README_CN.md 添加 Docker 快速开始
  - 推荐使用 Docker 部署方式

- 🔧 **项目结构**
  - 新增 .dockerignore 优化构建上下文
  - 开发依赖独立管理

### Docker 特性

- ✅ 轻量级镜像（预计 150-200MB）
- ✅ 支持环境变量配置
- ✅ 支持配置文件挂载
- ✅ 自动健康检查
- ✅ 资源限制配置
- ✅ 日志管理
- ✅ 定时任务支持
- ✅ Docker Compose 一键部署

### 部署方式

```bash
# 快速开始
docker-compose up -d

# 查看日志
docker-compose logs -f gitea-backup

# 手动执行
docker-compose run --rm gitea-backup
```

---

## [1.2.0] - 2026-01-26

### Added

- 📧 **通知系统** - 支持多种通知方式
  - 邮件通知（SMTP，支持 HTML 格式）
  - Webhook 通知（通用 HTTP POST/GET，自动识别企业微信格式）
  - 企业微信机器人通知
  - 钉钉机器人通知（支持加签验证）
  - 灵活的通知条件（always/on_error/on_alert）
  - 详细的备份报告和异常告警

- 🏗️ **项目结构重构**
  - 模块化目录结构（src/tests/docs/examples）
  - 源代码移至 `src/` 目录
  - 测试文件移至 `tests/` 目录
  - 文档整理至 `docs/` 目录
  - 示例文件分类至 `examples/` 子目录
  - 添加 `.gitignore` 文件

- 📝 **文档完善**
  - 新增通知配置指南（docs/notifications.md）
  - 新增恢复操作指南（docs/recovery.md）
  - 新增项目结构说明（PROJECT_STRUCTURE.md）
  - 更新中英文 README，添加通知系统说明

- 🧪 **测试文件**
  - tests/test_config.py - 配置系统测试
  - tests/test_notifier.py - 通知系统测试
  - tests/test_notification.py - 快速通知测试脚本

### Changed

- 🔧 **依赖更新**
  - 新增 `requests>=2.28.0` 用于 HTTP 通知

- 🔄 **导入路径**
  - 更新所有导入路径以适配新的目录结构
  - 保持向后兼容性

### Fixed

- 修复 Windows 平台编码问题
- 优化配置加载逻辑

---

## [1.1.0] - 2026-01-26

### Added

- ✨ **配置文件支持** - YAML 配置文件支持
  - 自动搜索配置文件（当前目录、用户目录、系统目录）
  - 通过 `-c` 参数指定配置文件
  - 完整的配置验证和错误提示
  
- 🔧 **环境变量覆盖** - 通过环境变量动态配置
  - 支持所有主要配置项
  - 自动类型转换（字符串、整数、布尔、列表）
  - 优先级：环境变量 > 配置文件 > 默认值

- 📋 **新增命令行选项**
  - `--config/-c`: 指定配置文件路径
  - `--show-config`: 显示当前生效的配置
  - `--validate-config`: 验证配置正确性
  - `--help`: 显示详细帮助信息
  - `--report`: 仅生成报告（不执行备份）
  - `--cleanup`: 仅清理旧报告

- 🧪 **测试支持**
  - 新增配置加载器测试脚本（test_config.py）
  - 覆盖默认配置、YAML 加载、环境变量、类型转换等测试

### Changed

- 🔄 **重构配置系统**
  - 将硬编码配置迁移到配置加载器
  - 保持向后兼容，旧代码无需修改
  - 通过属性访问器透明访问配置

- 📝 **改进日志系统**
  - 可配置日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
  - 支持自定义日志格式和日期格式
  - 延迟初始化日志，由配置文件控制

- 🎯 **增强命令行界面**
  - 使用 argparse 改进参数解析
  - 详细的帮助信息和使用示例
  - 改进错误消息和用户反馈

- 📚 **文档优化**
  - 将配置文档整合到 README
  - 精简文档结构
  - 删除冗余文档文件

### Dependencies

- ➕ 新增: `PyYAML>=6.0` - 用于 YAML 配置文件解析

### Backward Compatibility

- ✅ 完全向后兼容之前的版本
- ✅ 未提供配置文件时使用默认配置
- ✅ 原有 Config 类接口保持不变
- ✅ 所有现有脚本和 cron 任务无需修改即可工作

---

## [1.0.0] - 2026-01-24

### Added

- 🔄 每日快照备份，使用硬链接节省空间
- 📦 每月 Git bundle 归档，用于长期存储
- 🔍 智能异常检测（提交数和仓库大小监控）
- 🔒 自动保护异常前的快照和报告
- 📊 全面的备份报告，包含统计和告警
- ⚡ 多种恢复选项（原地恢复、新仓库、bundle 导出）
- 🎯 按组织/用户过滤，实现针对性备份
- 💾 可配置的快照和归档保留策略
- 📝 带时间戳的详细日志
- 🛠️ 为每个仓库自动生成恢复脚本

### Features

- 提交数减少检测（可配置阈值，默认 10%）
- 仓库大小监控（默认 30% 阈值）
- 受保护的快照不会被清理
- 受保护的报告永久保留
- 用户友好的恢复脚本，带交互式提示
- 自动修复权限和 Git hooks
- 支持不区分大小写的组织名称匹配

### Documentation

- 中英文 README
- 部署指南
- Crontab 配置示例
- 报告示例（正常和告警场景）
- 恢复使用指南
- MIT 许可证

---

## 升级指南

### 从 v1.1.0 升级到 v1.2.0

**无破坏性变更！** 升级过程简单：

1. **更新代码**:
   ```bash
   git pull
   ```

2. **安装新依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置通知（可选）**:
   ```bash
   vim config.yaml  # 配置 notifications 部分
   ```

4. **测试通知**:
   ```bash
   python tests/test_notification.py
   ```

**新功能**:
- 多渠道通知系统
- 模块化项目结构
- 完善的测试套件

### 从 v1.0.0 升级到 v1.1.0

**无破坏性变更！** 升级过程无缝：

1. **更新文件**:
   ```bash
   git pull
   pip install -r requirements.txt
   ```

2. **可选：创建配置文件**（推荐）:
   ```bash
   cp config.example.yaml config.yaml
   vim config.yaml
   ```

3. **继续使用** - 所有现有脚本无需修改即可工作！

**新功能**:
- 使用 `--show-config` 查看当前配置
- 使用 `--validate-config` 检查配置
- 使用 `-c config.yaml` 指定自定义配置文件
