# Gitea Mirror Backup - Web 管理界面

基于 FastAPI 的 Web 管理界面，提供可视化的备份管理功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd web
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，修改配置（特别是 SECRET_KEY）
```

### 3. 启动服务

```bash
python run.py
```

或使用 uvicorn：

```bash
uvicorn web.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问界面

- **Web 界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **默认账号**: `admin` / `admin123`

⚠️ **首次登录后请立即修改默认密码！**

## 📚 API 文档

启动服务后访问 http://localhost:8000/docs 查看完整的 API 文档（Swagger UI）。

### 主要接口

#### 认证
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/register` - 注册新用户（管理员）

#### 仪表板
- `GET /api/dashboard/stats` - 获取统计数据
- `GET /api/dashboard/trends` - 获取趋势数据

#### 仓库管理
- `GET /api/repositories` - 仓库列表
- `GET /api/repositories/{id}` - 仓库详情
- `POST /api/repositories/{id}/backup` - 立即备份

#### 快照管理
- `GET /api/snapshots` - 快照列表
- `GET /api/snapshots/{id}` - 快照详情
- `DELETE /api/snapshots/{id}` - 删除快照

#### 报告
- `GET /api/reports` - 报告列表
- `GET /api/reports/{id}` - 报告详情

#### 配置
- `GET /api/settings` - 获取配置
- `PUT /api/settings` - 更新配置

## 🔐 安全配置

### 修改默认密码

首次登录后，请立即修改默认管理员密码：

```bash
# 使用 API 或 Web 界面修改
```

### 生成安全的 SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

将生成的密钥写入 `.env` 文件的 `SECRET_KEY` 配置项。

### HTTPS 配置

生产环境建议使用 HTTPS：

```bash
# 使用 Nginx 反向代理
# 或使用 uvicorn 的 SSL 配置
uvicorn web.api.main:app --host 0.0.0.0 --port 8000 \
    --ssl-keyfile=/path/to/key.pem \
    --ssl-certfile=/path/to/cert.pem
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -f Dockerfile.web -t gitea-backup-web .
```

### 运行容器

```bash
docker run -d \
    --name gitea-backup-web \
    -p 8000:8000 \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/backup:/app/backup \
    -v $(pwd)/web/data:/app/data \
    -e SECRET_KEY="your-secret-key" \
    gitea-backup-web
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./backup:/app/backup
      - ./web/data:/app/data
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=sqlite:///data/web.db
    restart: unless-stopped
```

## 📊 功能特性

### 已实现
- ✅ 用户认证（JWT）
- ✅ 仪表板统计
- ✅ API 文档（Swagger）
- ✅ 数据库管理（SQLite）

### 开发中
- 🚧 仓库管理
- 🚧 快照管理
- 🚧 报告查看
- 🚧 配置管理
- 🚧 前端界面

### 计划中
- 📋 任务调度
- 📈 高级图表
- 🔔 实时通知
- 👥 多用户管理

## 🛠️ 开发

### 项目结构

```
web/
├── api/
│   ├── main.py          # FastAPI 应用
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库
│   ├── models.py        # 数据模型
│   ├── schemas.py       # Pydantic 模式
│   └── routers/         # 路由
│       ├── auth.py
│       └── dashboard.py
├── services/            # 业务逻辑
├── utils/               # 工具函数
│   └── auth.py
├── frontend/            # 前端（Vue 3）
├── requirements.txt     # 依赖
├── .env.example         # 环境变量示例
└── run.py              # 启动脚本
```

### 添加新路由

1. 在 `web/api/routers/` 创建新文件
2. 定义路由和处理函数
3. 在 `web/api/routers/__init__.py` 导出
4. 在 `web/api/main.py` 注册路由

### 数据库迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 🐛 故障排查

### 数据库错误

```bash
# 删除数据库重新初始化
rm -rf web/data/web.db
python web/run.py
```

### 端口被占用

```bash
# 修改端口
uvicorn web.api.main:app --port 8001
```

### 导入错误

确保项目根目录在 Python 路径中：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

