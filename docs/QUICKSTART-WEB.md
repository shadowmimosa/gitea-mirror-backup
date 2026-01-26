# 快速开始 - Web 管理界面

## 🚀 5 分钟快速上手

### 步骤 1：启动后端

```bash
cd web
python run.py
```

看到这个输出表示成功：
```
============================================================
Gitea Mirror Backup Web Server
============================================================
访问地址: http://localhost:8000
API 文档: http://localhost:8000/docs
默认账号: admin / admin123
============================================================
```

### 步骤 2：启动前端

**新开一个终端**，运行：

```bash
cd web/frontend
pnpm install  # 首次运行需要
pnpm dev
```

看到这个输出表示成功：
```
VITE v5.4.21  ready in 826 ms

➜  Local:   http://localhost:5173/
```

### 步骤 3：登录使用

1. 打开浏览器访问：http://localhost:5173
2. 输入账号：`admin`
3. 输入密码：`admin123`
4. 点击登录

完成！🎉

---

## 📱 界面功能

### 仪表板
- 查看备份统计
- 查看磁盘使用
- 查看成功率

### 仓库管理
- 查看所有仓库
- 立即备份仓库
- 查看仓库详情

### 快照管理
- 查看所有快照
- 删除快照

### 报告查看
- 查看备份报告
- 查看详细内容

---

## 🐳 Docker 一键部署

```bash
# 启动服务
docker-compose up -d gitea-backup-web

# 访问
http://localhost:8000
```

---

## ⚠️ 注意事项

1. **首次登录后请修改默认密码**
2. **生产环境请修改 SECRET_KEY**
3. **建议使用 HTTPS**

---

## 🆘 遇到问题？

### 后端无法启动
```bash
# 检查端口是否被占用
netstat -ano | findstr :8000

# 查看错误日志
python web/run.py
```

### 前端无法启动
```bash
# 重新安装依赖
cd web/frontend
rm -rf node_modules
npm install
```

### 无法登录
```bash
# 重置数据库
rm web/data/web.db
python web/run.py
```

---

更多详细信息请查看：[完整使用指南](./web-usage.md)

