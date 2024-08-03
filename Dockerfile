# 使用官方的 Python 3.11 镜像作为基础镜像
FROM python:3.11

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 MongoDB 客户端工具
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-5.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org-tools && \
    rm -rf /var/lib/apt/lists/*

# 确保配置文件夹存在并有正确的权限
RUN mkdir -p /app/config && chown -R root:root /app/config && chmod -R 755 /app/config

# 复制配置文件（如果它们不在 .dockerignore 中）
COPY config/* /app/config/

# 暴露端口
EXPOSE 3001
EXPOSE 8011

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 创建并使用非 root 用户运行应用
RUN useradd -m myuser
USER myuser

# 创建启动脚本
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 使用启动脚本
CMD ["/app/start.sh"]
