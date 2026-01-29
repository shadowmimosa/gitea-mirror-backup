# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.3] - 2026-01-29

### Fixed

- 🐛 **Web Service Path Configuration Issue**
  - Fixed Web service unable to correctly read backup data
  - Unified configuration loading logic for backup, cron, and web services
  - Web service now also uses `ConfigLoader` to read `config.yaml`
  - Configuration priority: environment variables > config.yaml > defaults

### Added

- ✨ **Configurable Default Admin Account**
  - Support configuring default admin account via environment variables
  - New environment variables: `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_EMAIL`
  - Create admin account using configuration on first startup
  - Automatically update password if non-default password is configured for existing user

- 🔄 **Automatic Version Retrieval**
  - New system info API: `GET /api/system/info`
  - Frontend Settings page automatically retrieves version from API
  - Version number maintained centrally in `web/api/config.py`
  - No need to manually update version in multiple places

### Changed

- 🔧 **Web Configuration System Refactoring**
  - `web/api/config.py` integrated with `ConfigLoader`
  - `BACKUP_ROOT` changed to dynamic property, supporting multi-level configuration
  - Maintains completely consistent configuration logic with backup service

- 📝 **Environment Variable Documentation Update**
  - `env.example` added admin account configuration instructions
  - Added security recommendations and configuration examples

### Security

- 🔐 Support custom admin account, avoid using default account
- 🔐 Automatic password update mechanism for easy password management
- 🔐 Production environments must change default password

### Upgrade Notes

Configure in `.env` file:
```bash
DEFAULT_ADMIN_USERNAME=myadmin
DEFAULT_ADMIN_PASSWORD=MySecurePassword123
DEFAULT_ADMIN_EMAIL=admin@mydomain.com
```

Update steps:
```bash
git pull
docker compose build web
docker compose up -d web
docker compose logs web
```

## [1.4.2] - 2026-01-28

### Changed

- 🔧 **Configuration System Refactoring** - Unified configuration management
  - Unified all services (backup, web, cron) to use the same configuration approach
  - Configuration priority: environment variables > config.yaml > defaults
  - Removed hard-coded environment variables from docker-compose.yml
  - All services now use `.env` + `config.yaml` configuration

- 📝 **Configuration Template Optimization**
  - Added `config.docker.yaml` - Docker deployment configuration template (container paths)
  - Added `config.example.yaml` - Direct deployment configuration template (host paths)
  - Clear distinction between container paths (/shared/gitea) and host paths (/opt/gitea)
  - Simplified configuration file structure, removed unnecessary `config/` directory hierarchy

- 🔔 **Notification Configuration Enhancement**
  - Added 10 notification-related environment variable mappings
  - Support overriding all notification configurations via environment variables
  - Environment variables: WECOM_WEBHOOK_URL, DINGTALK_WEBHOOK_URL, DINGTALK_SECRET, EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USE_TLS, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM, EMAIL_TO

- 📚 **Comprehensive Documentation Updates**
  - Added `docs/CONFIG-FILES.md` - Configuration file usage guide
  - Added `docs/ENV-VARIABLES.md` - Complete environment variables reference
  - Added `docs/MIGRATION-GUIDE.md` - Configuration migration guide
  - Updated `README.md` and `README_CN.md` - Simplified configuration instructions
  - Updated `docs/docker.md` - Docker deployment configuration instructions
  - Updated `docs/configuration.md` - Detailed configuration system documentation
  - Updated `docs/notifications.md` - Notification configuration instructions
  - Updated `env.example` - Complete environment variables example

### Fixed

- 🐛 **Configuration Consistency Fixes**
  - Fixed Web service using hard-coded environment variables
  - Fixed notification environment variables unable to override config.yaml
  - Fixed configuration file path confusion (container paths vs host paths)
  - Fixed inconsistent configuration approaches between services

### Added

- ✨ **Configuration Management Tools**
  - `.gitignore` now includes `.env` and `config.yaml` (prevent sensitive information leakage)
  - Provided two sets of configuration templates for different deployment scenarios

### Removed

- 🗑️ **Cleanup Redundant Documentation**
  - Removed `docs/configuration-analysis.md` (temporary analysis document)
  - Removed `docs/DOCS-UPDATE-SUMMARY.md` (temporary update record)
  - Removed `docs/REFACTOR-SUMMARY.md` (temporary refactoring record)

### Technical Details

**Configuration Priority**:
```
Environment Variables > config.yaml > Code Defaults
```

**Configuration File Selection**:
- Docker deployment: Use `config.docker.yaml` (container paths like /shared/gitea)
- Direct deployment: Use `config.example.yaml` (host paths like /opt/gitea)

**Environment Variable Mappings** (newly added):
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

**Impact Scope**:
- All Docker deployment users need to update configuration files
- Recommended to reconfigure using new configuration templates
- Old configurations are still compatible, but migration is recommended

### Upgrade Notes

#### Docker Deployment Users

1. **Backup existing configuration**:
   ```bash
   cp config.yaml config.yaml.backup
   cp .env .env.backup
   ```

2. **Use new template**:
   ```bash
   cp config.docker.yaml config.yaml
   vim config.yaml  # Adjust according to actual situation
   ```

3. **Update docker-compose.yml**:
   ```bash
   docker compose down
   docker compose pull
   docker compose up -d
   ```

4. **Verify configuration**:
   ```bash
   docker compose logs backup
   ```

#### Direct Deployment Users

1. **Use new template**:
   ```bash
   cp config.example.yaml config.yaml
   vim config.yaml  # Adjust according to actual situation
   ```

2. **Verify configuration**:
   ```bash
   python src/gitea_mirror_backup.py --show-config
   ```

For detailed migration guide, please refer to: `docs/MIGRATION-GUIDE.md`

---

## [1.4.1] - 2026-01-28

### Fixed

- 🐛 **Cron Service Environment Variable Passing Issue**
  - Fixed cron scheduled tasks unable to read container environment variables
  - Added `. /etc/environment` in cron tasks to load environment variables
  - Ensured cron tasks use correct configuration paths (`/shared/gitea` and `/shared/backup`)
  - Fixed Python command path in cron tasks (`python` → `python3`)

- 🔧 **Docker Compose Configuration Optimization**
  - Removed outdated `version: '3.8'` configuration (avoid warning messages)
  - Optimized cron service environment variable export mechanism

### Changed

- 📝 **Documentation Updates**
  - Unified use of new `docker compose` command (replacing old `docker-compose`)
  - Updated all command examples in README.md, README_CN.md and docs/docker.md

### Technical Details

**Root Cause**:
- Cron daemon runs tasks in a minimal environment and doesn't automatically inherit container environment variables
- This caused the program to read default paths from config.yaml instead of environment variable configured paths

**Solution**:
```bash
# Export environment variables to /etc/environment on container startup
printenv | grep -v 'no_proxy' >> /etc/environment

# Load environment variables before cron task execution
. /etc/environment && cd /app && /usr/local/bin/python3 gitea_mirror_backup.py
```

**Impact Scope**:
- Only affects scheduled task service started with `docker compose up -d cron`
- Manual execution (`docker compose run --rm backup`) and Web service are not affected

### Upgrade Notes

If you are using the cron service, restart to apply the fix:

```bash
docker compose down cron
docker compose up -d cron
```

---

## [1.4.0] - 2026-01-27

### Added

- 🌐 **Web Management Interface** - Modern web management system based on FastAPI + Vue 3
  - User authentication system (JWT Token)
  - Dashboard - Real-time statistics and trend charts
  - Repository management - View all backup repository information
  - Repository details page - View all snapshots of a single repository
  - Snapshot management - Browse and delete snapshots
  - Report viewing - Markdown format report display
  - Dark theme interface design

- 📊 **Dashboard Features**
  - Total repositories, snapshots, disk usage statistics
  - Last backup time display
  - Backup success rate calculation
  - Anomaly repository count statistics

- 🗂️ **Repository Management Features**
  - Display repository full name (owner/repo format)
  - Display commit count, snapshot count, protected snapshot count
  - Display disk usage and last backup time
  - Anomaly status indicator (⚠️ Has anomalies)
  - Click repository name to jump to details page

- 📸 **Snapshot Management Features**
  - View all snapshots or filter by repository
  - Display snapshot size, creation time, protection status
  - Single delete and batch delete snapshots
  - Protected snapshots cannot be deleted (automatically disabled)
  - Batch operations automatically skip protected snapshots

- 🔍 **Repository Details Page**
  - Display complete repository information (commit count, snapshot count, disk usage, etc.)
  - List all snapshots of the repository
  - Support multi-select and batch delete snapshots
  - Visual indicator for protected snapshots (🔒)

- 📝 **Report Viewing Features**
  - Markdown format report rendering
  - Dark theme adaptation
  - Display report creation time and size
  - Protected report indicator

- 🐳 **Docker Deployment Support**
  - Dockerfile.web - Multi-stage build optimization
  - docker-compose.web.yml - Web service orchestration
  - Frontend and backend integrated deployment
  - Data persistence configuration

### Changed

- 🏗️ **Project Structure Optimization**
  - Added `web/` directory for web application code
  - `web/api/` - FastAPI backend code
  - `web/frontend/` - Vue 3 frontend code
  - `web/services/` - Business logic services
  - `web/models/` - Database models
  - `web/utils/` - Utility functions

- 🔧 **BackupService Adaptation**
  - Adapted to actual backup directory structure ({owner}/{repo_name}/snapshots/)
  - Read `.commit_tracking` to get commit count
  - Read `.size_tracking` to get repository size
  - Detect `.protected` file to determine snapshot protection status
  - Detect `.alerts` file to determine repository anomaly status

- 🎨 **Frontend Experience Optimization**
  - Use Naive UI component library for dark theme implementation
  - Responsive layout design
  - Unified pagination and table styles
  - Friendly error prompts and confirmation dialogs
  - Smart prompts for batch operations

### Fixed

- 🐛 **Directory Structure Compatibility Fixes**
  - Fixed mismatch between web interface expected directory structure and actual backup structure
  - Fixed dashboard statistics showing 0
  - Fixed snapshot delete API missing repository parameter

- 🔒 **Protected Resource Handling**
  - Protected snapshots cannot be selected and deleted
  - Batch delete automatically skips protected snapshots
  - Clear protection status visual indicators

### Technical Details

**Backend Tech Stack:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM database operations
- JWT - User authentication
- bcrypt - Password encryption
- Pydantic - Data validation

**Frontend Tech Stack:**
- Vue 3 - Progressive JavaScript framework
- TypeScript - Type safety
- Vite - Fast build tool
- Naive UI - Vue 3 component library
- Pinia - State management
- Vue Router - Routing management
- Axios - HTTP client
- Marked - Markdown rendering

**Deployment:**
```bash
# Build and start web service
docker-compose -f docker-compose.web.yml up -d

# Access web interface
http://localhost:8000

# Default account
Username: admin
Password: admin123
```

### Documentation

- 📖 Added `docs/web-usage.md` - Web management interface usage documentation
- 📖 Updated README with web management interface description

### Security

- 🔐 JWT Token authentication mechanism
- 🔐 Password bcrypt encryption storage
- 🔐 Administrator permission control (delete operations require admin privileges)
- 🔐 Protected resource deletion protection

---

## [1.3.3] - 2026-01-27

### Added

- 📄 **Markdown Report Rendering Support**
  - Added Markdown report display capability
  - Adapted to dark theme with dark Markdown styles
  - Report area background transparent, consistent with system theme

- 👁️ **Repository and Snapshot Operation Enhancement**
  - Support pagination size selection (10 / 20 / 50 / 100)
  - Added snapshot protection status display
  - Added total snapshot count display for more complete information

### Fixed

- 🐛 **Pagination and Data Display Fixes**
  - Fixed snapshot list pagination display anomaly
  - Fixed repository details page pagination logic inconsistency
  - Fixed partial snapshot data display errors on repository details page
  - Fixed multiple TypeScript type errors and UI interaction issues

- 🧩 **Cross-platform Compatibility Fixes**
  - Fixed snapshot size calculation anomaly on Windows systems
  - Windows environment automatically falls back to Python recursive calculation

### Changed

- ⚡ **Performance and Architecture Optimization**
  - Snapshot list changed to server-side pagination, query performance improved 10-100x
  - Added total snapshot count API to support frontend pagination calculation
  - Snapshot size changed to on-demand calculation, only counting current page data
  - Linux/Unix environments use `du` command to calculate snapshot size, replacing Python recursive traversal

- 🎨 **Frontend Experience and Layout Optimization**
  - Refactored pagination logic, using independent paginator component for unified UI style
  - Improved overall readability and operation consistency

### Technical Details

- Pagination mechanism:
  - Both snapshot list and repository details support server-side pagination
  - API supports `page` and `pageSize` parameters
- Snapshot size calculation strategy:
  - Linux: Prioritize using `du` command
  - Windows: Automatically downgrade to Python recursive statistics
- No new third-party dependencies introduced in this update

---

## [1.3.2] - 2026-01-27

### Fixed

- 🌙 **Markdown Dark Theme Adaptation**
  - Switched Markdown style from `github-markdown-light.css` to `github-markdown-dark.css`
  - Fixed background inconsistency in dark theme (background changed to transparent)
  - Fixed readability issues of tables and code blocks in dark mode
    - Table borders use semi-transparent white
    - Code block background uses semi-transparent white
    - Table zebra stripes use semi-transparent background
  - Markdown report area now perfectly integrates with system dark theme

- 📐 **Dashboard Layout Issue Fixes**
  - Removed `max-width: 1400px` and `margin: 0 auto` layout restrictions
  - Removed local `padding: 20px` (unified control by outer layout)
  - Fixed width inconsistency between dashboard page and repository management, snapshot management pages

### Added

- 👁️ **Repository Management View Entry Added**
  - Repository list added "Actions" column
  - Added "View" button using `EyeOutline` icon
  - Support one-click jump to repository details page
  - Improved operability and intuitiveness of repository list

### Changed

- 🎨 **Frontend Visual Consistency Optimization**
  - Unified width and spacing strategy between dashboard and other management pages
  - Improved overall UI consistency and readability in dark theme

### Technical Details

- Markdown style adaptation:
  - Use `github-markdown-dark.css`
  - Custom override styles for seamless dark theme integration
- Repository list actions column:
  - Added icon button component, no additional dependencies required
- No new third-party dependencies in this update (`marked` and `github-markdown-css` were introduced in previous versions)

---

## [1.3.1] - 2026-01-26

### Fixed

- 🐛 **Docker Environment Fixes**
  - Fixed Docker container timezone configuration (added TZ environment variable)
  - Fixed cron service startup issue (Debian uses `cron` instead of `crond`)
  - Fixed cross-filesystem hard link failure (automatically downgrade to regular copy)
  - Fixed symlink using absolute path causing host inaccessibility (changed to relative path)

- 🔗 **Hard Link Optimization**
  - Added shared volume configuration strategy (mount parent directory for same filesystem hard links)
  - Added detailed hard link configuration documentation (docs/docker-hardlink.md)
  - Added hard link troubleshooting documentation (docs/docker-hardlink-fix.md)
  - Hard link success can save 90%+ disk space

### Changed

- 📝 **Documentation Improvements**
  - Updated docker-compose.yml configuration examples
  - Added hard link configuration best practices
  - Added timezone configuration instructions

### Technical Details

- Cross-filesystem detection: Catch `OSError: [Errno 18] Invalid cross-device link`
- Auto-downgrade strategy: Use `cp -a` to preserve file attributes when hard link fails
- Symlink relative path: `latest_report.symlink_to(report_file.relative_to(latest_report.parent))`
- Shared volume strategy: Mount `/shared` parent directory, all data on same filesystem

---

## [1.3.0] - 2026-01-26

### Added

- 🐳 **Docker Containerization Support**
  - Dockerfile - Lightweight image based on python:3.9-slim
  - docker-compose.yml - Quick deployment configuration
  - Support all configuration options (environment variables + config file)
  - Health checks and resource limits
  - Scheduled task service (optional)
  - Complete volume mount configuration

- 📝 **Docker Documentation**
  - docs/docker.md - Complete Docker deployment guide
  - Quick start guide
  - Configuration instructions and examples
  - Scheduled task configuration (3 methods)
  - Monitoring and maintenance guide
  - Troubleshooting guide
  - Production environment deployment recommendations

### Changed

- 📚 **Documentation Updates**
  - README.md / README_CN.md added Docker quick start
  - Recommended Docker deployment method

- 🔧 **Project Structure**
  - Added .dockerignore to optimize build context
  - Independent development dependency management

### Docker Features

- ✅ Lightweight image (estimated 150-200MB)
- ✅ Support environment variable configuration
- ✅ Support config file mounting
- ✅ Automatic health checks
- ✅ Resource limit configuration
- ✅ Log management
- ✅ Scheduled task support
- ✅ Docker Compose one-click deployment

### Deployment

```bash
# Quick start
docker-compose up -d

# View logs
docker-compose logs -f gitea-backup

# Manual execution
docker-compose run --rm gitea-backup
```

---

## [1.2.0] - 2026-01-26

### Added

- 📧 **Notification System** - Support multiple notification methods
  - Email notification (SMTP, supports HTML format)
  - Webhook notification (generic HTTP POST/GET, auto-detect WeCom format)
  - WeCom bot notification
  - DingTalk bot notification (supports signature verification)
  - Flexible notification conditions (always/on_error/on_alert)
  - Detailed backup reports and anomaly alerts

- 🏗️ **Project Structure Refactoring**
  - Modular directory structure (src/tests/docs/examples)
  - Source code moved to `src/` directory
  - Test files moved to `tests/` directory
  - Documentation organized in `docs/` directory
  - Example files categorized in `examples/` subdirectories
  - Added `.gitignore` file

- 📝 **Documentation Improvements**
  - Added notification configuration guide (docs/notifications.md)
  - Added recovery operation guide (docs/recovery.md)
  - Added project structure description (PROJECT_STRUCTURE.md)
  - Updated Chinese and English README with notification system description

- 🧪 **Test Files**
  - tests/test_config.py - Configuration system tests
  - tests/test_notifier.py - Notification system tests
  - tests/test_notification.py - Quick notification test script

### Changed

- 🔧 **Dependency Updates**
  - Added `requests>=2.28.0` for HTTP notifications

- 🔄 **Import Paths**
  - Updated all import paths to adapt to new directory structure
  - Maintained backward compatibility

### Fixed

- Fixed Windows platform encoding issues
- Optimized configuration loading logic

---

## [1.1.0] - 2026-01-26

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
  - New configuration loader test script (test_config.py)
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

### From v1.1.0 to v1.2.0

**No breaking changes!** The upgrade is simple:

1. **Update code**:
   ```bash
   git pull
   ```

2. **Install new dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure notifications (optional)**:
   ```bash
   vim config.yaml  # Configure notifications section
   ```

4. **Test notifications**:
   ```bash
   python tests/test_notification.py
   ```

**New features**:
- Multi-channel notification system
- Modular project structure
- Comprehensive test suite

### From v1.0.0 to v1.1.0

**No breaking changes!** The upgrade is seamless:

1. **Update files**:
   ```bash
   git pull
   pip install -r requirements.txt
   ```

2. **Optional: Create config file** (recommended):
   ```bash
   cp config.example.yaml config.yaml
   vim config.yaml
   ```
3. **Continue using as before** - All existing scripts work without changes!

**New features**:
- Use `--show-config` to see current configuration
- Use `--validate-config` to check configuration
- Use `-c config.yaml` to specify custom config file

---

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[1.4.2]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.4.2
[1.4.1]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.4.1
[1.4.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.4.0
[1.3.3]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.3.3
[1.3.2]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.3.2
[1.3.1]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.3.1
[1.3.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.3.0
[1.2.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.2.0
[1.1.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.1.0
[1.0.0]: https://github.com/yourusername/gitea-mirror-backup/releases/tag/v1.0.0


