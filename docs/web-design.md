# Web 管理界面设计文档

## 📋 项目概述

**版本**: v1.5  
**技术栈**: FastAPI + Vue 3 + TypeScript  
**目标**: 提供可视化的备份管理界面

---

## 🎯 核心功能

### 1. 仪表板 (Dashboard)
- 📊 备份统计概览
  - 总仓库数
  - 总快照数
  - 磁盘使用情况
  - 最近备份时间
- 📈 趋势图表
  - 备份成功率
  - 磁盘使用趋势
  - 备份耗时统计
- ⚠️ 异常告警
  - 最近异常列表
  - 失败备份提醒

### 2. 仓库管理 (Repositories)
- 📚 仓库列表
  - 仓库名称、描述
  - 最后备份时间
  - 快照数量
  - 磁盘占用
- 🔍 搜索和过滤
- 🎯 单个仓库详情
  - 快照历史
  - 备份日志
  - 异常记录
- ⚡ 操作
  - 立即备份
  - 删除快照
  - 查看差异

### 3. 快照管理 (Snapshots)
- 📸 快照列表
  - 时间、大小、状态
  - 文件数量、提交数
- 🔄 快照操作
  - 查看详情
  - 下载快照
  - 删除快照
  - 恢复测试
- 📊 快照对比
  - 文件差异
  - 大小变化

### 4. 报告查看 (Reports)
- 📝 报告列表
  - 按时间排序
  - 成功/失败状态
- 📄 报告详情
  - Markdown 渲染
  - 下载报告
- 🔍 日志查看
  - 实时日志
  - 历史日志

### 5. 配置管理 (Settings)
- ⚙️ 基础配置
  - Gitea 连接
  - 备份路径
  - 定时任务
- 🔔 通知配置
  - 邮件通知
  - Webhook
  - 企业微信/钉钉
- 🔐 安全设置
  - 用户管理
  - API Token
  - 访问日志

### 6. 任务管理 (Tasks)
- ⏱️ 定时任务
  - Cron 表达式配置
  - 启用/禁用
- 📋 任务历史
  - 执行记录
  - 成功/失败状态
- ▶️ 手动执行
  - 立即运行
  - 查看进度

---

## 🏗️ 技术架构

### 后端 (FastAPI)

```
web/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── models.py            # 数据模型
│   ├── database.py          # 数据库连接
│   └── routers/
│       ├── __init__.py
│       ├── dashboard.py     # 仪表板 API
│       ├── repositories.py  # 仓库管理 API
│       ├── snapshots.py     # 快照管理 API
│       ├── reports.py       # 报告 API
│       ├── settings.py      # 配置 API
│       ├── tasks.py         # 任务 API
│       └── auth.py          # 认证 API
├── services/
│   ├── __init__.py
│   ├── backup_service.py    # 备份服务
│   ├── snapshot_service.py  # 快照服务
│   ├── report_service.py    # 报告服务
│   └── task_service.py      # 任务服务
├── utils/
│   ├── __init__.py
│   ├── auth.py              # 认证工具
│   └── helpers.py           # 辅助函数
└── requirements.txt
```

### 前端 (Vue 3)

```
web/frontend/
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/
│   │   └── index.ts
│   ├── stores/              # Pinia 状态管理
│   │   ├── auth.ts
│   │   ├── dashboard.ts
│   │   └── repositories.ts
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Repositories.vue
│   │   ├── Snapshots.vue
│   │   ├── Reports.vue
│   │   ├── Settings.vue
│   │   └── Tasks.vue
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.vue
│   │   │   ├── Header.vue
│   │   │   └── Footer.vue
│   │   ├── charts/
│   │   │   ├── LineChart.vue
│   │   │   └── PieChart.vue
│   │   └── common/
│   │       ├── Table.vue
│   │       ├── Card.vue
│   │       └── Modal.vue
│   ├── api/
│   │   └── client.ts        # API 客户端
│   └── assets/
│       └── styles/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 🎨 UI 设计

### 设计风格
- **主题**: 深色主题（可切换）
- **字体**: 
  - 标题: `Outfit` (Google Fonts)
  - 正文: `Inter` (Google Fonts)
  - 代码: `JetBrains Mono`
- **配色方案**:
  ```css
  --primary: #3b82f6      /* 蓝色 */
  --success: #10b981      /* 绿色 */
  --warning: #f59e0b      /* 橙色 */
  --danger: #ef4444       /* 红色 */
  --dark: #1e293b         /* 深色背景 */
  --light: #f8fafc        /* 浅色背景 */
  ```

### 组件库
- **选择**: Element Plus / Naive UI
- **图表**: ECharts / Chart.js
- **图标**: Heroicons / Lucide Icons

### 布局
```
┌─────────────────────────────────────────┐
│  Header (Logo, 用户信息, 通知)           │
├──────┬──────────────────────────────────┤
│      │                                  │
│ Side │  Main Content Area               │
│ bar  │                                  │
│      │                                  │
│      │                                  │
└──────┴──────────────────────────────────┘
```

---

## 🔌 API 设计

### 认证
```
POST   /api/auth/login       # 登录
POST   /api/auth/logout      # 登出
GET    /api/auth/me          # 当前用户信息
```

### 仪表板
```
GET    /api/dashboard/stats  # 统计数据
GET    /api/dashboard/trends # 趋势数据
GET    /api/dashboard/alerts # 告警信息
```

### 仓库
```
GET    /api/repositories              # 仓库列表
GET    /api/repositories/{id}         # 仓库详情
POST   /api/repositories/{id}/backup  # 立即备份
GET    /api/repositories/{id}/logs    # 备份日志
```

### 快照
```
GET    /api/snapshots                 # 快照列表
GET    /api/snapshots/{id}            # 快照详情
DELETE /api/snapshots/{id}            # 删除快照
GET    /api/snapshots/{id}/download   # 下载快照
POST   /api/snapshots/compare         # 对比快照
```

### 报告
```
GET    /api/reports                   # 报告列表
GET    /api/reports/{id}              # 报告详情
GET    /api/reports/{id}/download     # 下载报告
```

### 配置
```
GET    /api/settings                  # 获取配置
PUT    /api/settings                  # 更新配置
POST   /api/settings/test-connection  # 测试连接
```

### 任务
```
GET    /api/tasks                     # 任务列表
POST   /api/tasks                     # 创建任务
PUT    /api/tasks/{id}                # 更新任务
DELETE /api/tasks/{id}                # 删除任务
POST   /api/tasks/{id}/run            # 执行任务
GET    /api/tasks/{id}/logs           # 任务日志
```

---

## 💾 数据存储

### SQLite 数据库

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务表
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    cron_expression TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT 1,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务执行记录
CREATE TABLE task_runs (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    status TEXT,  -- running, success, failed
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    log_file TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- 配置表
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔐 安全性

### 认证方式
- JWT Token 认证
- Session 过期时间: 24 小时
- 密码加密: bcrypt

### 权限控制
- 管理员: 所有权限
- 普通用户: 只读权限

### API 安全
- CORS 配置
- Rate Limiting
- HTTPS 强制（生产环境）

---

## 🚀 部署方案

### Docker 部署

```yaml
# docker-compose.yml 扩展
services:
  gitea-backup:
    # ... 现有配置 ...
  
  gitea-backup-web:
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
    depends_on:
      - gitea-backup
```

---

## 📝 开发计划

### Phase 1: 后端基础 (2-3 小时)
- [ ] FastAPI 项目搭建
- [ ] 数据库模型设计
- [ ] 基础 API 实现
- [ ] 认证系统

### Phase 2: 核心功能 (3-4 小时)
- [ ] 仪表板 API
- [ ] 仓库管理 API
- [ ] 快照管理 API
- [ ] 报告 API

### Phase 3: 前端开发 (4-5 小时)
- [ ] Vue 3 项目搭建
- [ ] 布局和路由
- [ ] 仪表板页面
- [ ] 仓库管理页面
- [ ] 配置页面

### Phase 4: 集成和优化 (2-3 小时)
- [ ] 前后端联调
- [ ] Docker 集成
- [ ] 性能优化
- [ ] 文档完善

**总预计时间**: 11-15 小时

---

## 🎯 MVP 功能（最小可行产品）

为了快速交付，第一版只实现核心功能：

1. ✅ 仪表板（基础统计）
2. ✅ 仓库列表和详情
3. ✅ 快照列表和查看
4. ✅ 报告查看
5. ✅ 基础配置管理
6. ✅ 简单认证（单用户）

**后续版本再添加**:
- 多用户管理
- 高级图表
- 实时日志
- 任务调度界面
- 快照对比
- 下载功能

---

## 💡 技术选型理由

### 为什么选 FastAPI？
- ⚡ 高性能（基于 Starlette 和 Pydantic）
- 📝 自动生成 API 文档（Swagger UI）
- 🔒 内置数据验证
- 🐍 现代 Python 特性（async/await）
- 🛠️ 易于集成现有代码

### 为什么选 Vue 3？
- 🚀 性能优秀
- 📦 组合式 API（Composition API）
- 🔧 TypeScript 支持好
- 🎨 生态丰富（Vite, Pinia, Vue Router）
- 📚 学习曲线平缓

---

## 🤔 待讨论

1. **前端框架**: Vue 3 还是 React？
2. **UI 组件库**: Element Plus, Naive UI, 还是 Ant Design Vue？
3. **图表库**: ECharts 还是 Chart.js？
4. **认证方式**: JWT 还是 Session？
5. **数据库**: SQLite 还是 PostgreSQL？

---

## 📌 下一步

1. 确认技术选型
2. 创建项目结构
3. 开始后端开发

