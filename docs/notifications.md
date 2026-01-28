# 通知系统配置指南

## 📧 邮件通知

### 配置方式 1: 使用 config.yaml

```yaml
notifications:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    smtp_user: "your-email@gmail.com"
    smtp_password: "your-app-password"
    from_addr: "backup@example.com"
    to_addrs:
      - "admin@example.com"
      - "team@example.com"
    notify_on: "on_alert"  # always/on_error/on_alert
```

### 配置方式 2: 使用环境变量

```bash
# .env 文件
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDR=backup@example.com
EMAIL_TO_ADDRS=admin@example.com,team@example.com
```

然后在 `config.yaml` 中启用：

```yaml
notifications:
  email:
    enabled: true
    notify_on: "on_alert"
```

### 配置方式 3: 混合使用（推荐）

```yaml
# config.yaml（基础配置）
notifications:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    from_addr: "backup@example.com"
    to_addrs:
      - "admin@example.com"
    notify_on: "on_alert"
```

```bash
# .env（敏感信息）
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
```

### Gmail 配置

1. 启用两步验证
2. 生成应用专用密码：https://myaccount.google.com/apppasswords
3. 使用应用密码作为 `smtp_password`

### 其他邮箱

- **QQ邮箱**: `smtp.qq.com:587`
- **163邮箱**: `smtp.163.com:465`
- **Outlook**: `smtp.office365.com:587`

## 🔗 Webhook 通知

### 配置示例

```yaml
notifications:
  webhook:
    enabled: true
    url: "https://your-server.com/webhook"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer your-token"
    notify_on: "on_alert"
```

### 请求格式

```json
{
  "title": "备份报告标题",
  "message": "备份详细信息",
  "level": "info",
  "timestamp": "2024-01-26T10:00:00",
  "details": {
    "total_repos": 10,
    "has_alerts": false
  }
}
```

## 💬 企业微信通知

### 配置步骤

1. 登录企业微信管理后台
2. 进入「应用管理」→「群机器人」
3. 创建机器人，获取 Webhook URL
4. 配置通知

### 配置方式 1: 使用 config.yaml

```yaml
notifications:
  wecom:
    enabled: true
    webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    notify_on: "on_alert"
```

### 配置方式 2: 使用环境变量（推荐）

```bash
# .env 文件
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

然后在 `config.yaml` 中启用：

```yaml
notifications:
  wecom:
    enabled: true
    notify_on: "on_alert"
```

> 💡 **推荐使用环境变量**：Webhook URL 包含密钥，不应提交到版本控制

### 消息格式

企业微信会收到文本消息：

```
✅ Gitea 备份报告 - 全部正常

备份时间: 2024-01-26 10:00:00
备份仓库数: 10
总提交数: 5,000
快照总数: 300
占用空间: 1024 MB
```

## 📱 钉钉通知

### 配置步骤

1. 打开钉钉群聊
2. 群设置 → 智能群助手 → 添加机器人 → 自定义
3. 设置安全设置（推荐使用加签）
4. 获取 Webhook URL 和加签密钥

### 配置方式 1: 基础配置（config.yaml）

```yaml
notifications:
  dingtalk:
    enabled: true
    webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    notify_on: "on_alert"
```

### 配置方式 2: 使用环境变量（推荐）

```bash
# .env 文件
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
DINGTALK_SECRET=SECxxxxxxxxxxxx
```

然后在 `config.yaml` 中启用：

```yaml
notifications:
  dingtalk:
    enabled: true
    notify_on: "on_alert"
```

### 配置方式 3: 加签配置（最安全）

```yaml
# config.yaml
notifications:
  dingtalk:
    enabled: true
    notify_on: "on_alert"
```

```bash
# .env（敏感信息）
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
DINGTALK_SECRET=SECxxxxxxxxxxxx
```

> 💡 **推荐使用环境变量 + 加签**：提高安全性，密钥不会泄露

## 🔔 通知条件

### notify_on 选项

- **`always`** - 每次备份后都发送通知
- **`on_error`** - 仅在备份失败时发送通知
- **`on_alert`** - 仅在检测到异常时发送通知（推荐）

### 示例

```yaml
# 邮件：仅异常时通知
notifications:
  email:
    enabled: true
    notify_on: "on_alert"

# 企业微信：总是通知
notifications:
  wecom:
    enabled: true
    notify_on: "always"

# 钉钉：仅错误时通知
notifications:
  dingtalk:
    enabled: true
    notify_on: "on_error"
```

## 🧪 测试通知

运行测试脚本验证配置：

```bash
python test_notifier.py
```

测试脚本会：
1. 加载配置
2. 初始化通知管理器
3. 发送测试通知
4. 发送测试备份报告
5. 发送测试异常报告

## 🔍 故障排查

### 邮件通知失败

**问题**: `SMTPAuthenticationError`
- 检查用户名和密码是否正确
- Gmail 需要使用应用专用密码
- 检查是否启用了"允许不够安全的应用"

**问题**: `Connection refused`
- 检查 SMTP 服务器地址和端口
- 检查防火墙设置
- 尝试使用 SSL 端口（465）

### Webhook 通知失败

**问题**: `Connection timeout`
- 检查 URL 是否正确
- 检查网络连接
- 检查服务器是否可访问

**问题**: `401 Unauthorized`
- 检查 Authorization header
- 检查 API token 是否有效

### 企业微信/钉钉通知失败

**问题**: `invalid webhook url`
- 检查 Webhook URL 是否完整
- 检查 key/access_token 是否正确

**问题**: 钉钉加签失败
- 检查 secret 是否正确
- 确保系统时间准确（加签对时间敏感）

## 📝 最佳实践

1. **使用加签** - 钉钉机器人建议启用加签，提高安全性
2. **合理设置通知条件** - 避免通知过于频繁
3. **测试配置** - 配置后先运行测试脚本验证
4. **多渠道备份** - 可以同时启用多个通知渠道
5. **保护敏感信息** - 不要将配置文件提交到公开仓库

## 🔐 安全建议

1. **邮箱密码** - 使用应用专用密码，不要使用主密码
2. **Webhook Token** - 定期更换 API token
3. **使用环境变量** - 敏感信息使用环境变量而非配置文件

```bash
# .env 文件（不要提交到 Git）
EMAIL_SMTP_PASSWORD=your-password
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
DINGTALK_SECRET=your-secret
```

4. **配置文件权限** - 设置适当的文件权限

```bash
chmod 600 config.yaml
chmod 600 .env
```

5. **.gitignore** - 确保敏感文件不被提交

```
# .gitignore
.env
config.yaml
config/config.yaml
```

## 📋 环境变量完整列表

所有通知相关的环境变量：

```bash
# 企业微信
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 钉钉
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxxxxxxxxxxx

# 邮件
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDR=backup@example.com
EMAIL_TO_ADDRS=admin@example.com,team@example.com

# 通用 Webhook
WEBHOOK_URL=https://your-webhook-endpoint.com/notify
```

详细说明请参考：[环境变量文档](ENV-VARIABLES.md)

## 📞 获取帮助

如有问题，请：
1. 查看日志文件：`/var/log/gitea-mirror-backup.log`
2. 运行测试脚本：`python test_notifier.py`
3. 提交 Issue：https://github.com/yourusername/gitea-mirror-backup/issues

