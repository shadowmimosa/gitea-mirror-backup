# Gitea Mirror Backup

[English](#english) | [中文](README_CN.md)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**Intelligent backup solution for Gitea Docker mirror repositories**

*Automatic anomaly detection • Snapshot protection • Easy recovery • Flexible configuration*

</div>

---

## ✨ Features

- 🔄 **Daily Snapshots** - Hard-link based backups, minimal storage overhead
- 📦 **Monthly Archives** - Git bundle format for long-term preservation
- 🔍 **Smart Detection** - Automatically detects force push & history rewrites
- 🔒 **Auto Protection** - Critical snapshots & reports preserved permanently
- 📊 **Detailed Reports** - Comprehensive backup summaries with anomaly alerts
- ⚡ **Easy Recovery** - Multiple restore options (in-place, new repo, bundle export)
- 💾 **Space Efficient** - Hard-links minimize disk usage for unchanged files
- 🎯 **Targeted Backup** - Filter by organization, mirror-only option
- ⚙️ **Flexible Config** - YAML config file + environment variables support
- 📧 **Notification System** - Email/Webhook/WeChat Work/DingTalk notifications

## 🎬 Quick Start

### Method 1: Docker (Recommended)

```bash
# Using Docker Compose
docker compose up -d

# View logs
docker compose logs -f gitea-backup
```

See [Docker Deployment Guide](docs/docker.md) for details.

### Method 2: Direct Installation

#### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/gitea-mirror-backup.git
cd gitea-mirror-backup

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create configuration file
cp config.example.yaml config.yaml
vim config.yaml
```

### Minimal Configuration

Edit `config.yaml` with at least these three settings:

**Direct Deployment**:
```yaml
gitea:
  docker_container: "gitea"              # Your container name
  data_volume: "/opt/gitea"              # Host path

backup:
  root: "/opt/backup/gitea-mirrors"      # Host path
```

**Docker Deployment**:
```yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"           # Container path

backup:
  root: "/shared/backup"                 # Container path
```

> 💡 **Tip**: For Docker deployment, use `config.docker.yaml` as template

### Run

```bash
# Validate configuration
python gitea_mirror_backup.py --validate-config

# Execute backup
python gitea_mirror_backup.py

# View report
cat /opt/backup/gitea-mirrors/latest-report.md
```

### Schedule Automatic Backups

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/gitea-mirror-backup && python gitea_mirror_backup.py
```

## ⚙️ Configuration

### Configuration Methods

Three configuration methods supported (priority: environment variables > config file > defaults):

#### 1. Hybrid Configuration (Recommended)

Base configuration in `config.yaml`, sensitive data in `.env`:

```yaml
# config/config.yaml
gitea:
  docker_container: "gitea"
  data_volume: "/shared/gitea"

backup:
  root: "/shared/backup"
  organizations: []
  
notifications:
  wecom:
    enabled: true
    notify_on: "on_alert"
```

```bash
# .env (sensitive data, not committed to Git)
SECRET_KEY=your-random-secret-key
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
EMAIL_SMTP_PASSWORD=your-password
```

#### 2. Pure YAML Configuration

```yaml
# config.yaml
gitea:
  docker_container: "gitea"
  data_volume: "/opt/gitea/gitea"

backup:
  root: "/opt/backup/gitea-mirrors"
  organizations: ["MyOrg"]
  check_mirror_only: false
  retention:
    snapshots_days: 30
    archives_months: 12

alerts:
  commit_decrease_threshold: 10
  protect_abnormal_snapshots: true

logging:
  level: "INFO"

# Notifications (use environment variables for sensitive data)
notifications:
  wecom:
    enabled: false
    webhook_url: ""  # Use WECOM_WEBHOOK_URL env var
  email:
    enabled: false
    smtp_password: ""  # Use EMAIL_SMTP_PASSWORD env var
```

#### 3. Environment Variables

```bash
# Basic config
export GITEA_DOCKER_CONTAINER="gitea"
export BACKUP_ROOT="/backup/gitea"
export LOG_LEVEL="INFO"

# Notifications (sensitive data)
export WECOM_WEBHOOK_URL="https://qyapi.weixin.qq.com/..."
export EMAIL_SMTP_PASSWORD="your-password"

python gitea_mirror_backup.py
```

### Supported Environment Variables

**Basic**: `GITEA_DOCKER_CONTAINER`, `BACKUP_ROOT`, `BACKUP_ORGANIZATIONS`, `LOG_LEVEL`

**Notifications**: `WECOM_WEBHOOK_URL`, `DINGTALK_WEBHOOK_URL`, `DINGTALK_SECRET`, `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_USER`, `EMAIL_SMTP_PASSWORD`, `EMAIL_FROM_ADDR`, `EMAIL_TO_ADDRS`, `WEBHOOK_URL`

See [Environment Variables Documentation](docs/ENV-VARIABLES.md) for complete list.

### Command Line Options

```bash
python gitea_mirror_backup.py --help              # Show help
python gitea_mirror_backup.py -c config.yaml     # Specify config file
python gitea_mirror_backup.py --show-config      # Display current config
python gitea_mirror_backup.py --validate-config  # Validate configuration
python gitea_mirror_backup.py --report           # Generate report only
python gitea_mirror_backup.py --cleanup          # Cleanup old reports
```

### Common Configuration Scenarios

**Scenario 1: Backup all repositories**
```yaml
backup:
  organizations: []           # Empty list
  check_mirror_only: false
```

**Scenario 2: Mirror repos from specific organizations only**
```yaml
backup:
  organizations: ["mirrors", "upstream"]
  check_mirror_only: true
```

**Scenario 3: Long-term retention**
```yaml
backup:
  retention:
    snapshots_days: 90
    archives_months: 24
```

## 🔍 How It Works

### Backup Strategy

```
Daily Snapshots (30 days retention)
├── Hard-link based, minimal extra space
├── Fast creation and deletion
└── Auto-cleanup expired snapshots

Monthly Archives (12 months retention)
├── Git bundle format
├── Portable and compressed
└── Auto-created on 1st of each month

Anomaly Detection & Protection
├── Monitor commit count and repo size
├── Auto-protect snapshots on anomaly
└── Preserve corresponding reports
```

### Anomaly Detection

Monitoring metrics:
- **Commit count decrease** > 10% (configurable)
- **Repository size decrease** > 30% (auxiliary check)

When triggered:
1. 🔒 Protect pre-anomaly snapshot (normal state)
2. 📋 Mark report for permanent retention
3. ⚠️ Log detailed alert information

### Storage Efficiency

Example: 100 repos × 500MB each

```
Original size:  50GB
Snapshots 30d:  ~5GB  (hard-links, only changes)
Archives 12m:   ~7GB  (compressed bundles)
Total:         ~62GB (vs 1500GB for full copies)
```

## 🔧 Recovery Operations

Each repository has auto-generated restore scripts.

### Docker Deployment

The backup image entrypoint runs the Python backup program. **Do not run `restore.sh` directly on the host** (paths inside the script are container paths like `/shared/backup/...`).

```bash
# Option 1: restore helper service (recommended)
docker compose run --rm -it restore \
  /shared/backup/org/repo/restore.sh

# Option 2: backup service with entrypoint override
docker compose run --rm -it --entrypoint bash backup \
  /shared/backup/org/repo/restore.sh

# Option 3: wrapper script in the repo directory
/shared/backup/org/repo/restore-via-docker.sh
```

Regenerate all restore scripts:

```bash
docker compose run --rm --entrypoint python backup \
  gitea_mirror_backup.py --regenerate-restore-scripts
```

### Direct Deployment

```bash
/opt/backup/gitea-mirrors/org/repo/restore.sh
```

### Three Recovery Modes

**Mode 1: Restore to Original Location**
- Overwrites current repository
- Auto-backup current state
- Fix permissions and hooks

**Mode 2: Export as New Repository**
- Create independent copy
- Original repo untouched
- Requires manual adoption in Gitea

**Mode 3: Export as Bundle**
- Portable Git bundle file
- Can be cloned anywhere
- Suitable for transfer and archival

### Recovery Example

**Docker:**

```bash
docker compose run --rm -it restore /shared/backup/org/repo/restore.sh
```

**Direct deployment:**

```bash
cd /opt/backup/gitea-mirrors/org/repo && ./restore.sh
```

## 📊 Report Examples

### Normal Report

```markdown
## 📊 Overall Statistics
- Backed up repositories: 15
- Total commits: 45,678 commits
- Total snapshots: 450
- Disk usage: 8.5 GB

## ✅ All Normal
No anomalies detected in this cycle.
```

### Alert Report (Auto-Protected)

```markdown
## ⚠️ Repositories Requiring Attention

### myorg/critical-repo
Commit count decreased: 45%
Previous: 567 commits → Current: 312 commits
Possible cause: force push, branch deletion, or history rewrite

🔒 Protected snapshot: 20260124-020000 (pre-anomaly state)
Recovery: /backup/.../myorg/critical-repo/restore.sh
```

View complete examples: [examples/](examples/)

## 🛠️ Advanced Usage

### Multi-Environment Configuration

```bash
# Production environment
python gitea_mirror_backup.py -c config.prod.yaml

# Test environment
python gitea_mirror_backup.py -c config.test.yaml
```

### Manage Protected Resources

```bash
# View all protected snapshots
find /opt/backup -name ".protected"

# View protection reason
cat /path/to/snapshot/.protected

# Remove protection (allow auto-cleanup)
rm /path/to/snapshot/.protected
```

### Monitoring and Maintenance

```bash
# View logs
tail -f /var/log/gitea-mirror-backup.log

# Check disk usage
du -sh /opt/backup/gitea-mirrors

# Manual cleanup old reports
python gitea_mirror_backup.py --cleanup
```

## 📖 Documentation

- **[Configuration Guide](docs/configuration.md)** - Detailed configuration guide
- **[Environment Variables](docs/ENV-VARIABLES.md)** - Complete environment variables list
- **[Notifications](docs/notifications.md)** - Notification system setup
- **[Docker Deployment](docs/docker.md)** - Docker deployment guide
- **[Migration Guide](docs/MIGRATION-GUIDE.md)** - Configuration migration guide
- **[Examples](examples/)** - Configuration and report examples
- **[Changelog](CHANGELOG_EN.md)** - Version history ([中文版](CHANGELOG.md))

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Designed for [Gitea](https://gitea.io/) self-hosted Git service
- Inspired by the need for reliable mirror repository backups
- Built with ❤️ for the self-hosting community

## 📮 Support

- 🐛 [Report Issues](https://github.com/yourusername/gitea-mirror-backup/issues)
- 💡 [Request Features](https://github.com/yourusername/gitea-mirror-backup/issues/new)

---

<div align="center">

**If this project helps you, please give it a ⭐ star!**

Made with 🐍 Python

</div>
