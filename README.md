# Gitea Mirror Backup

[English](#english) | [中文](README_CN.md)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**Intelligent backup solution for Gitea Docker mirror repositories**

*Automatic anomaly detection • Snapshot protection • Easy recovery*

</div>

---

## ✨ Features

- 🔄 **Daily Snapshots** - Hard-link based backups, minimal storage overhead
- 📦 **Monthly Archives** - Git bundle format for long-term preservation
- 🔍 **Smart Detection** - Automatically detects force push & history rewrites (10% threshold)
- 🔒 **Auto Protection** - Critical snapshots & reports preserved permanently
- 📊 **Detailed Reports** - Comprehensive backup summaries with anomaly alerts
- ⚡ **Easy Recovery** - Multiple restore options (in-place, new repo, bundle export)
- 💾 **Space Efficient** - Hard-links minimize disk usage for unchanged files
- 🎯 **Targeted Backup** - Filter by organization/user, mirror-only option

## 🎬 Quick Start

### Prerequisites

- Python 3.6+
- Docker with Gitea container running
- Same filesystem for Gitea data and backup directory (for hard-links)

### Installation

```bash
# 1. Download the script
wget https://raw.githubusercontent.com/yourusername/gitea-mirror-backup/main/gitea_mirror_backup.py

# Or clone the repository
git clone https://github.com/yourusername/gitea-mirror-backup.git
cd gitea-mirror-backup

# 2. Make it executable
chmod +x gitea_mirror_backup.py
```

### Configuration

Edit the script and configure these key settings:

```python
class Config:
    # Docker container name
    DOCKER_CONTAINER = "gitea"
    
    # Gitea data volume path (on host)
    GITEA_DATA_VOLUME = "/var/lib/docker/volumes/gitea_data/_data"
    
    # Backup root directory
    BACKUP_ROOT = "/backup/gitea-mirrors"
    
    # Organizations to backup (empty = all)
    BACKUP_ORGANIZATIONS = ["YourOrg"]
```

### First Run

```bash
# Run manually
python3 gitea_mirror_backup.py

# Check the log
tail -f /var/log/gitea-mirror-backup.log

# View the report
cat /backup/gitea-mirrors/latest-report.md
```

### Schedule Automatic Backups

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /usr/bin/python3 /path/to/gitea_mirror_backup.py
```

## 📖 Documentation

- **[Deployment Guide](docs/deployment.md)** - Detailed setup instructions
- **[Recovery Usage Examples](examples/restore-usage-example.md)** - How to use restore scripts
- **[Crontab Examples](examples/crontab.example)** - Schedule automatic backups

## 🔍 How It Works

### Backup Strategy

```
Daily Snapshots (30 days retention)
├── Hard-link based copies
├── Near-zero space for unchanged files
└── Fast creation and deletion

Monthly Archives (12 months retention)
├── Git bundle format
├── Portable and compressed
└── Created on the 1st of each month

Automatic Protection
├── Detects anomalies (commit/size decrease)
├── Protects pre-anomaly snapshots
└── Preserves corresponding reports
```

### Anomaly Detection

The script monitors:
- **Commit count changes** - Triggers on >10% decrease (configurable)
- **Repository size changes** - Triggers on >30% decrease (auxiliary check)

When detected:
1. 🔒 Previous snapshot (normal state) is protected from cleanup
2. 📋 Current report is marked for permanent retention
3. ⚠️ Alert details are logged for review

### Storage Efficiency

Example for 100 repositories averaging 500MB each:

```
Original total:     50GB
Daily snapshots:    ~5GB (30 days, only changed files)
Monthly archives:   ~7GB (12 months, compressed bundles)
Total:             ~62GB (vs 1500GB for full copies!)
```

## 🔧 Recovery Options

The generated restore script offers three modes:

### Option 1: Restore to Original Location
```bash
/backup/gitea-mirrors/org/repo/restore.sh
# Select mode 1, choose snapshot
# ⚠️ Overwrites current repository
```

### Option 2: Export as New Repository
```bash
# Select mode 2
# Creates independent copy
# Perfect for mirror repos (original untouched)
```

### Option 3: Export as Bundle
```bash
# Select mode 3
# Portable Git bundle file
# Can be cloned anywhere
```

## 📊 Report Examples

View complete examples:
- [Normal Backup Report](examples/report-normal-example.md) - Regular backup report
- [Alert Detection Report](examples/report-alert-example.md) - Report with anomaly detection (🔒 auto-preserved)
- [Protection File Example](examples/snapshot-protected-example.txt) - Snapshot protection marker

### Alert Report Preview

```markdown
## ⚠️ Repositories Requiring Attention

### myorg/critical-repo
Commit count decreased: 45%
Previous: 567 commits → Current: 312 commits

🔒 Protected snapshot: 20260124-020000 (pre-anomaly state)
Recovery: /backup/.../myorg/critical-repo/restore.sh
```

## 🛠️ Advanced Configuration

```python
# Snapshot retention (days)
SNAPSHOT_RETENTION_DAYS = 30

# Archive retention (months)
ARCHIVE_RETENTION_MONTHS = 12

# Commit decrease threshold (%)
COMMIT_DECREASE_THRESHOLD = 10

# Size decrease threshold (%)
SIZE_DECREASE_THRESHOLD = 30

# Auto-protect abnormal snapshots
PROTECT_ABNORMAL_SNAPSHOTS = True

# Check mirror repos only
CHECK_MIRROR_ONLY = False
```

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
- 📖 [Read the Docs](docs/)

---

<div align="center">

**If this project helps you, please give it a ⭐ star!**

Made with 🐍 Python

</div>
