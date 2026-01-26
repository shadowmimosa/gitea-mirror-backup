# Gitea Mirror Backup Web 管理界面 - 使用指南

## 🚀 快速开始

### 方式一：开发模式（推荐用于测试）

#### 1. 启动后端 API

```bash
cd web
python run.py
```

后端将在 http://localhost:8000 启动

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

#### 2. 启动前端界面

打开新终端：

```bash
cd web/frontend
pnpm install  # 首次运行需要安装依赖
pnpm dev
```

前端将在 http://localhost:5173 启动

#### 3. 访问界面

打开浏览器访问：http://localhost:5173

**默认账号**：
- 用户名：`admin`
- 密码：`admin123`

---

### 方式二：生产模式（Docker）

#### 1. 使用 Docker Compose（推荐）

```bash
# 启动 Web 服务（会自动构建前端）
docker-compose up -d gitea-backup-web

# 查看日志
docker-compose logs -f gitea-backup-web

# 停止服务
docker-compose stop gitea-backup-web
```

访问：http://localhost:8000

#### 2. 手动构建（可选）

如果你想手动构建前端：

```bash
# 构建前端
cd web/frontend
pnpm install
pnpm build

# 构建 Docker 镜像
docker build -f Dockerfile.web -t gitea-backup-web .

# 运行容器
docker run -d \
  --name gitea-backup-web \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/backup:/app/backup \
  -v $(pwd)/web/data:/app/data \
  -e SECRET_KEY="your-secret-key" \
  gitea-backup-web
```

---

## 📖 功能使用

### 1. 登录系统

1. 打开 http://localhost:5173
2. 输入用户名：`admin`
3. 输入密码：`admin123`
4. 点击"登录"按钮

登录成功后会自动跳转到仪表板。

### 2. 仪表板

仪表板显示系统概览：

- **总仓库数**：已备份的 Git 仓库总数
- **总快照数**：所有快照的总数
- **磁盘使用**：备份占用的磁盘空间
- **成功率**：备份成功率百分比
- **最近备份时间**：最后一次备份的时间

### 3. 仓库管理

#### 查看仓库列表

1. 点击左侧菜单"仓库管理"
2. 查看所有已备份的仓库
3. 点击仓库名称查看详情

#### 立即备份仓库

1. 进入仓库详情页
2. 点击"立即备份"按钮
3. 系统会启动备份任务

### 4. 快照管理

#### 查看快照列表

1. 点击左侧菜单"快照管理"
2. 查看所有快照信息
   - 快照 ID
   - 所属仓库
   - 文件大小
   - 创建时间
   - 状态

#### 删除快照

1. 在快照列表中找到要删除的快照
2. 点击"删除"按钮
3. 确认删除操作

⚠️ **注意**：删除快照后无法恢复！

### 5. 报告查看

#### 查看备份报告

1. 点击左侧菜单"报告查看"
2. 查看所有备份报告列表
3. 点击报告查看详细内容

报告包含：
- 备份时间
- 备份的仓库列表
- 快照信息
- 异常检测结果
- 磁盘使用统计

### 6. 系统设置

1. 点击左侧菜单"系统设置"
2. 查看系统信息
3. 配置系统参数（开发中）

---

## 🔧 配置说明

### 后端配置

创建 `web/.env` 文件：

```env
# 安全密钥（生产环境必须修改！）
SECRET_KEY=your-secret-key-change-in-production

# 数据库路径
DATABASE_URL=sqlite:///./data/web.db

# 备份数据路径
BACKUP_BASE_PATH=./backup

# CORS 允许的源
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 前端配置

编辑 `web/frontend/vite.config.ts`：

```typescript
export default defineConfig({
  server: {
    port: 5173,  // 前端端口
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // 后端地址
        changeOrigin: true
      }
    }
  }
})
```

---

## 🐳 Docker 部署

### 完整的 docker-compose.yml

```yaml
version: '3.8'

services:
  # 备份服务
  gitea-backup:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: gitea-backup
    environment:
      - TZ=Asia/Shanghai
      - BACKUP_ROOT=/shared/backup
    volumes:
      - gitea-data:/shared
      - ./config:/app/config
    restart: unless-stopped

  # Web 管理界面
  gitea-backup-web:
    build:
      context: .
      dockerfile: Dockerfile.web
    container_name: gitea-backup-web
    ports:
      - "8000:8000"
    environment:
      - TZ=Asia/Shanghai
      - SECRET_KEY=${SECRET_KEY:-change-this-in-production}
      - DATABASE_URL=sqlite:///data/web.db
      - BACKUP_BASE_PATH=/shared/backup
    volumes:
      - gitea-data:/shared
      - ./config:/app/config:ro
      - ./web/data:/app/data
    depends_on:
      - gitea-backup
    restart: unless-stopped

volumes:
  gitea-data:
    driver: local
```

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 只启动 Web 服务
docker-compose up -d gitea-backup-web

# 查看日志
docker-compose logs -f gitea-backup-web

# 重启服务
docker-compose restart gitea-backup-web

# 停止服务
docker-compose stop gitea-backup-web

# 删除服务
docker-compose down
```

---

## 🔐 安全建议

### 1. 修改默认密码

首次登录后立即修改默认密码：

```bash
# 使用 API 修改密码（开发中）
# 或者直接修改数据库
```

### 2. 生成安全的 SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

将生成的密钥写入 `.env` 文件。

### 3. 使用 HTTPS

生产环境建议使用 Nginx 反向代理并配置 SSL：

```nginx
server {
    listen 443 ssl http2;
    server_name backup.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 限制访问

使用防火墙限制只允许特定 IP 访问：

```bash
# 只允许内网访问
iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

---

## 🐛 故障排查

### 问题 1：无法连接后端 API

**症状**：前端显示"获取数据失败"

**解决方案**：
1. 检查后端是否运行：`curl http://localhost:8000/health`
2. 检查防火墙设置
3. 查看后端日志

### 问题 2：登录失败

**症状**：提示"用户名或密码错误"

**解决方案**：
1. 确认使用默认账号：`admin` / `admin123`
2. 检查数据库是否正确初始化
3. 删除数据库重新初始化：`rm web/data/web.db`

### 问题 3：前端页面空白

**症状**：浏览器显示空白页面

**解决方案**：
1. 打开浏览器控制台查看错误
2. 检查前端是否正确构建
3. 清除浏览器缓存

### 问题 4：Docker 容器无法启动

**症状**：`docker-compose up` 失败

**解决方案**：
1. 查看日志：`docker-compose logs gitea-backup-web`
2. 检查端口是否被占用：`netstat -ano | findstr :8000`
3. 检查卷挂载路径是否正确

---

## 📊 性能优化

### 1. 前端构建优化

```bash
# 生产构建
pnpm build

# 分析构建产物
pnpm build --mode analyze
```

### 2. 后端性能

```python
# 增加 worker 数量
uvicorn web.api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### 3. 数据库优化

```bash
# 定期清理旧数据
sqlite3 web/data/web.db "VACUUM;"
```

---

## 📝 API 使用示例

### 使用 curl 调用 API

```bash
# 登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 获取仪表板统计
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/dashboard/stats

# 获取仓库列表
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/repositories

# 立即备份仓库
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/repositories/my-repo/backup
```

### 使用 Python 调用 API

```python
import requests

# 登录
response = requests.post('http://localhost:8000/api/auth/login', 
    json={'username': 'admin', 'password': 'admin123'})
token = response.json()['access_token']

# 设置请求头
headers = {'Authorization': f'Bearer {token}'}

# 获取统计数据
stats = requests.get('http://localhost:8000/api/dashboard/stats', 
    headers=headers).json()
print(stats)

# 获取仓库列表
repos = requests.get('http://localhost:8000/api/repositories', 
    headers=headers).json()
print(repos)
```

---

## 🎯 最佳实践

### 1. 定期备份数据库

```bash
# 备份 Web 数据库
cp web/data/web.db web/data/web.db.backup.$(date +%Y%m%d)
```

### 2. 监控日志

```bash
# 实时查看日志
tail -f logs/gitea-mirror-backup.log
```

### 3. 定期清理

```bash
# 清理旧快照（根据保留策略）
# 清理旧报告
# 清理旧日志
```

### 4. 备份验证

定期验证备份的完整性和可恢复性。

---

## 📞 获取帮助

- **API 文档**：http://localhost:8000/docs
- **项目文档**：查看 `docs/` 目录
- **问题反馈**：提交 Issue

---

## 🎉 总结

现在你已经学会了：

✅ 如何启动 Web 管理界面  
✅ 如何使用各项功能  
✅ 如何配置和部署  
✅ 如何排查问题  
✅ 如何调用 API  

开始使用 Gitea Mirror Backup Web 管理界面吧！🚀

