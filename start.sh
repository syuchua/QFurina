#!/bin/bash
set -e

# 检查配置文件是否存在
if [ ! -f "/app/config/config.json" ]; then
    echo "Error: config.json not found in /app/config/"
    exit 1
fi

if [ ! -f "/app/config/model.json" ]; then
    echo "Error: model.json not found in /app/config/"
    exit 1
fi

# 打印一些调试信息
echo "Current directory: $(pwd)"
echo "Contents of /app:"
ls -la /app
echo "Contents of /app/config:"
ls -la /app/config

# 运行应用
python -u /app/main.py
