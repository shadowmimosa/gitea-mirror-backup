#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 Web 服务器
"""
import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("=" * 60)
    print("Gitea Mirror Backup Web Server")
    print("=" * 60)
    print("访问地址: http://localhost:8000")
    print("API 文档: http://localhost:8000/docs")
    print("默认账号: admin / admin123")
    print("=" * 60)
    print("")

    uvicorn.run(
        "web.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
