FROM python:3.9-slim-bullseye

LABEL maintainer="your-email@example.com"
LABEL description="Gitea Mirror Backup - Intelligent backup solution for Gitea mirror repositories"
LABEL version="1.3.0"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY gitea_mirror_backup.py .
COPY config.example.yaml .

# 创建必要的目录
RUN mkdir -p /backup /logs

# 设置权限
RUN chmod +x gitea_mirror_backup.py

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 入口点
ENTRYPOINT ["python", "gitea_mirror_backup.py"]

# 默认命令（可被覆盖）
CMD []

