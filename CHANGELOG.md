# Changelog

All notable changes to this project will be documented in this file.

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
