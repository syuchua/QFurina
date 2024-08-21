# 使用官方的 Python 3.11 镜像作为基础镜像
FROM python:3.11

# 设置工作目录
WORKDIR /app

# 将当前目录下所有文件复制到工作目录
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口3001用于接收QQ上报的http消息
EXPOSE 3001
# 暴露端口8011用于WebSocket连接
EXPOSE 8011

# 设置环境变量
ENV IS_DOCKER=true
ENV MONGO_URI=mongodb://mongo:27017
ENV MONGO_DB_NAME=chatbot_db

# 启动应用
CMD ["python", "main.py"]