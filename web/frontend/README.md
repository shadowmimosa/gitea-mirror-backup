# Gitea Backup Web Frontend

基于 Vue 3 + TypeScript + Naive UI 的现代化 Web 管理界面。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vite** - 快速的构建工具
- **Naive UI** - 优雅的 Vue 3 组件库
- **Vue Router** - 路由管理
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端

## 开发

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
```

## 功能特性

- ✅ 用户登录认证
- ✅ 仪表板统计
- ✅ 仓库管理
- ✅ 快照管理
- ✅ 报告查看
- ✅ 系统设置
- ✅ 响应式设计
- ✅ 深色主题

## 项目结构

```
src/
├── api/          # API 客户端
├── assets/       # 静态资源
├── components/   # 公共组件
├── layouts/      # 布局组件
├── router/       # 路由配置
├── stores/       # 状态管理
├── views/        # 页面组件
├── App.vue       # 根组件
└── main.ts       # 入口文件
```

## 环境要求

- Node.js >= 16
- pnpm >= 8 (推荐) 或 npm >= 8

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

⚠️ **首次登录后请立即修改默认密码！**

