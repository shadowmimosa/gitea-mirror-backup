# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2024-01-26

### 新增功能 (Added)

- ✨ **配置文件支持** - 支持 YAML 格式配置文件
  - 自动查找配置文件（当前目录、用户目录、系统目录）
  - 支持通过 `-c` 参数指定配置文件路径
  - 完整的配置验证和错误提示
  
- 🔧 **环境变量覆盖** - 支持通过环境变量动态调整配置
  - 支持所有主要配置项的环境变量覆盖
  - 自动类型转换（字符串、整数、布尔、列表）
  - 优先级：环境变量 > 配置文件 > 默认值

- 📋 **新增命令行选项**
  - `--config/-c`: 指定配置文件路径
  - `--show-config`: 显示当前生效的配置
  - `--validate-config`: 验证配置文件正确性
  - `--help`: 显示详细帮助信息

- 📚 **完善文档**
  - 新增配置指南 (`docs/configuration.md`)
  - 新增使用指南 (`USAGE.md`)
  - 新增配置说明 (`README_CONFIG.md`)
  - 更新示例配置文件 (`config.example.yaml`)

- 🧪 **测试支持**
  - 新增配置加载器测试脚本 (`test_config.py`)
  - 覆盖默认配置、YAML 加载、环境变量、类型转换等场景

### 改进 (Changed)

- 🔄 **重构配置系统**
  - 将硬编码配置迁移到配置加载器
  - 保持向后兼容，旧代码无需修改
  - 使用属性访问器实现透明的配置访问

- 📝 **改进日志系统**
  - 支持配置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
  - 支持自定义日志格式和日期格式
  - 延迟初始化日志，支持配置文件控制

- 🎯 **优化命令行界面**
  - 使用 argparse 提供更好的参数解析
  - 添加详细的帮助信息和使用示例
  - 改进错误提示和用户反馈

### 依赖变更 (Dependencies)

- ➕ 新增依赖：`PyYAML>=6.0` - 用于 YAML 配置文件解析

### 向后兼容 (Backward Compatibility)

- ✅ 完全向后兼容旧版本
- ✅ 如果不提供配置文件，使用默认配置
- ✅ 保持原有的 Config 类接口不变
- ✅ 所有旧脚本和 cron 任务无需修改

### 文档更新 (Documentation)

- 📖 新增详细的配置指南
- 📖 新增使用教程和最佳实践
- 📖 新增配置迁移指南
- 📖 更新 README 和示例

---

## [1.0.0] - 2024-01-20

### 初始版本

- 基本的 Gitea 镜像仓库备份功能
- 快照和归档管理
- 异常检测和自动保护
- 恢复脚本生成
- 备份报告生成

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
