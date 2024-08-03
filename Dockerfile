# 使用官方的 Python 3.11 镜像作为基础镜像
FROM python:3.11

# 设置工作目录
WORKDIR /app

# 将当前目录下所有文件复制到工作目录
COPY . /app

# 列出 /app 目录内容（用于调试）
RUN ls -la /app

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

# 暴露端口3001用于接收QQ上报的http消息
EXPOSE 3001
# 暴露端口8011用于WebSocket连接
EXPOSE 8011

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 再次列出 /app 目录内容（用于调试）
RUN ls -la /app

# 启动应用
CMD ["python", "/app/main.py"]
