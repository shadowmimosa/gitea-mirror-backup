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

```yaml
gitea:
  docker_container: "gitea"              # Your container name
  data_volume: "/opt/gitea/gitea"        # Data volume path

backup:
  root: "/opt/backup/gitea-mirrors"      # Backup storage path
```

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

#### 1. YAML Config File (Recommended)

```yaml
gitea:
  docker_container: "gitea"
  docker_git_user: "git"
  data_volume: "/opt/gitea/gitea"
  repos_path: "git/repositories"

backup:
  root: "/opt/backup/gitea-mirrors"
  organizations:                    # Specify orgs, empty = all
    - "MyOrg"
  check_mirror_only: false          # true = mirror repos only
  retention:
    snapshots_days: 30              # Snapshot retention days
    archives_months: 12             # Archive retention months
    reports_days: 30                # Report retention days

alerts:
  commit_decrease_threshold: 10     # Commit decrease threshold (%)
  size_decrease_threshold: 30       # Size decrease threshold (%)
  protect_abnormal_snapshots: true  # Auto-protect abnormal snapshots

logging:
  file: "/var/log/gitea-mirror-backup.log"
  level: "INFO"                     # DEBUG/INFO/WARNING/ERROR

# Notification configuration (optional)
notifications:
  # Method 1: Webhook (recommended, supports WeChat Work)
  webhook:
    enabled: true
    url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    method: "POST"
    notify_on: "on_alert"           # always/on_error/on_alert
  
  # Method 2: Email notification
  email:
    enabled: false
    smtp_host: "smtp.example.com"
    smtp_port: 587
    smtp_user: "user@example.com"
    smtp_password: "password"
    from_addr: "backup@example.com"
    to_addrs:
      - "admin@example.com"
    notify_on: "on_alert"
  
  # Method 3: WeChat Work bot
  wecom:
    enabled: false
    webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    notify_on: "on_alert"
  
  # Method 4: DingTalk bot
  dingtalk:
    enabled: false
    webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: ""                      # Optional, signature secret
    notify_on: "on_alert"
```

#### 2. Environment Variables

```bash
export GITEA_DOCKER_CONTAINER="gitea"
export BACKUP_ROOT="/backup/gitea"
export BACKUP_ORGANIZATIONS="Org1,Org2"
export LOG_LEVEL="DEBUG"

python gitea_mirror_backup.py
```

#### 3. Code Configuration (Backward Compatible)

Directly modify the `Config` class in `gitea_mirror_backup.py`.

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

Each repository has an auto-generated restore script:

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

```bash
# Run restore script
./restore.sh

# Select recovery mode
Choose restore method [1]: 2

# Select snapshot
Choose snapshot number [1]: 1

# Enter new repo name
Enter new repository name: my-repo-restored
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

- **[Deployment Guide](docs/deployment.md)** - Detailed deployment instructions
- **[Notification Guide](docs/notifications.md)** - Notification system configuration
- **[Examples](examples/)** - Configuration and report examples
- **[Changelog](CHANGELOG.md)** - Version history

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
