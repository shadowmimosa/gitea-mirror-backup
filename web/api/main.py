"""
FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from .config import settings
from .database import init_db, get_db, SessionLocal
from .models import User
from .routers import (
    auth_router,
    dashboard_router,
    repositories_router,
    snapshots_router,
    reports_router,
)
from ..utils.auth import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("=" * 60)
    print("初始化数据库...")
    init_db()

    # 创建默认管理员用户
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("创建默认管理员用户...")
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            print("默认管理员用户已创建")
            print("   用户名: admin")
            print("   密码: admin123")
            print("   警告: 请立即修改默认密码！")
    finally:
        db.close()

    print("应用启动完成")
    print("=" * 60)

    yield

    # 关闭时执行
    print("应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Gitea 镜像备份 Web 管理界面",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(repositories_router, prefix=settings.API_PREFIX)
app.include_router(snapshots_router, prefix=settings.API_PREFIX)
app.include_router(reports_router, prefix=settings.API_PREFIX)


# 挂载前端静态文件（生产环境）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets"
    )

    @app.get("/")
    async def serve_frontend():
        """提供前端页面"""
        from fastapi.responses import FileResponse

        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """处理前端路由"""
        # 如果是 API 路由，跳过
        if full_path.startswith("api/"):
            return JSONResponse({"error": "Not found"}, status_code=404)

        # 检查是否是静态文件
        file_path = frontend_dist / full_path
        if file_path.is_file():
            from fastapi.responses import FileResponse

            return FileResponse(str(file_path))

        # 否则返回 index.html（SPA 路由）
        from fastapi.responses import FileResponse

        return FileResponse(str(frontend_dist / "index.html"))

else:

    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "message": "Frontend not built. Please run 'cd web/frontend && pnpm build'",
        }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
