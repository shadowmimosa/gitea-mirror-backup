# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

---

[1.2.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.2.0
[1.1.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.1.0
[1.0.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.0.0


### Added

- ✨ **Configuration File Support** - YAML configuration file support
  - Auto-search for config files (current dir, user dir, system dir)
  - Specify config file via `-c` parameter
  - Complete configuration validation with error messages
  
- 🔧 **Environment Variable Override** - Dynamic configuration via environment variables
  - Support for all major configuration items
  - Automatic type conversion (string, int, bool, list)
  - Priority: environment variables > config file > defaults

- 📋 **New Command Line Options**
  - `--config/-c`: Specify configuration file path
  - `--show-config`: Display current effective configuration
  - `--validate-config`: Validate configuration correctness
  - `--help`: Show detailed help information
  - `--report`: Generate report only (no backup)
  - `--cleanup`: Cleanup old reports only

- 🧪 **Test Support**
  - New configuration loader test script (`test_config.py`)
  - Coverage for default config, YAML loading, env vars, type conversion

### Changed

- 🔄 **Refactored Configuration System**
  - Migrated hard-coded config to configuration loader
  - Maintained backward compatibility, no changes needed for old code
  - Transparent configuration access via property accessors

- 📝 **Improved Logging System**
  - Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Custom log format and date format support
  - Lazy initialization of logging with config file control

- 🎯 **Enhanced Command Line Interface**
  - Better argument parsing with argparse
  - Detailed help information and usage examples
  - Improved error messages and user feedback

- 📚 **Documentation Optimization**
  - Consolidated configuration docs into README
  - Streamlined documentation structure
  - Removed redundant documentation files

### Dependencies

- ➕ Added: `PyYAML>=6.0` - For YAML configuration file parsing

### Backward Compatibility

- ✅ Fully backward compatible with previous versions
- ✅ Uses default configuration if no config file provided
- ✅ Original Config class interface unchanged
- ✅ All existing scripts and cron jobs work without modification

### Documentation

- 📖 Integrated configuration guide into README
- 📖 Added CONTRIBUTING.md for contributors
- 📖 Updated examples and usage instructions
- 📖 Streamlined documentation structure

---

## [1.0.0] - 2026-01-24

### Added

- 🔄 Daily snapshot backups using hard-links for space efficiency
- 📦 Monthly Git bundle archives for long-term storage
- 🔍 Smart anomaly detection (commit count and repository size monitoring)
- 🔒 Automatic protection of pre-anomaly snapshots and reports
- 📊 Comprehensive backup reports with statistics and alerts
- ⚡ Multiple recovery options (in-place, new repo, bundle export)
- 🎯 Organization/user filtering for targeted backups
- 💾 Configurable retention policies for snapshots and archives
- 📝 Detailed logging with timestamps
- 🛠️ Automatic restore script generation for each repository

### Features

- Commit decrease detection (configurable threshold, default 10%)
- Repository size monitoring (default 30% threshold)
- Protected snapshots excluded from cleanup
- Protected reports preserved permanently
- User-friendly restore script with interactive prompts
- Automatic permission and Git hooks fixing
- Case-insensitive organization name matching

### Documentation

- English and Chinese README
- Deployment guide
- Crontab configuration examples
- Report examples (normal and alert scenarios)
- Recovery usage guide
- MIT License

---

## Upgrade Guide

### From v1.0.0 to v1.1.0

**No breaking changes!** The upgrade is seamless:

1. **Update files**:
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

2. **Optional: Create config file** (recommended):
   ```bash
   cp config.example.yaml config.yaml
   vim config.yaml
   ```

3. **Continue using as before** - All existing scripts work without changes!

**New features available**:
- Use `--show-config` to see current configuration
- Use `--validate-config` to check configuration
- Use `-c config.yaml` to specify custom config file

---

[1.1.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.1.0
[1.0.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.0.0

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-24

### Added
- 🔄 Daily snapshot backups using hard-links for space efficiency
- 📦 Monthly Git bundle archives for long-term storage
- 🔍 Smart anomaly detection (commit count and repository size monitoring)
- 🔒 Automatic protection of pre-anomaly snapshots and reports
- 📊 Comprehensive backup reports with statistics and alerts
- ⚡ Multiple recovery options (in-place, new repo, bundle export)
- 🎯 Organization/user filtering for targeted backups
- 💾 Configurable retention policies for snapshots and archives
- 📝 Detailed logging with timestamps
- 🛠️ Automatic restore script generation for each repository

### Features
- Commit decrease detection (configurable threshold, default 10%)
- Repository size monitoring (default 30% threshold)
- Protected snapshots are excluded from cleanup
- Protected reports are preserved permanently
- User-friendly restore script with interactive prompts
- Automatic permission and Git hooks fixing
- Support for case-insensitive organization name matching

### Documentation
- English and Chinese README
- Deployment guide
- Crontab configuration examples
- Report examples (normal and alert scenarios)
- Recovery usage guide
- MIT License

[1.0.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.0.0
