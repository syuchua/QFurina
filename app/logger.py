from loguru import logger
import os
import sys

# 获取日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志文件
log_file_path = os.path.join(log_dir, 'app.log')

# 移除默认的日志处理器
logger.remove()

# 控制台日志格式（不包含文件名和函数名）
console_format_str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level}</level> | - "
    "<level>{message}</level>"
)

# 文件日志格式（包含文件名和函数名）
file_format_str = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# 添加控制台日志处理器，带有颜色，设置为 INFO 级别
logger.add(
    sys.stdout,
    format=console_format_str,
    level="INFO",
    colorize=True
)

# 添加文件日志处理器，保持 DEBUG 级别以记录更详细的信息
logger.add(
    log_file_path,
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
    format=file_format_str,
    encoding="utf8"
)

def clean_old_logs(days=30):
    """清理指定天数之前的日志文件"""
    from datetime import datetime, timedelta
    current_time = datetime.now()
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if current_time - file_modification_time > timedelta(days=days):
            os.remove(file_path)
            logger.info(f"Removed old log file: {filename}")

# 导出 log_dir 和 clean_old_logs 函数
__all__ = ['logger', 'log_dir', 'clean_old_logs']
