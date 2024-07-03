from app.logger import logger
import signal
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import os
import subprocess
from wsgiref.simple_server import make_server
from utils.file import run_flask_app
import schedule
from app.message import process_group_message, process_private_message
from app.config import Config
from app.database import MongoDB
from utils.receive import start_server, rev_msg
from commands.reset import session_timeout_check

# 全局变量用于控制循环
running = True

# 启动 MongoDB 服务
def start_mongodb():
    logger.info("启动 MongoDB 服务...")
    mongodb_command = ['mongod', '--dbpath', 'D:\\MongoDB\\data', '--logpath', 'D:\\MongoDB\\log\\mongodb.log', '--logappend']
    subprocess.Popen(mongodb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 信号处理函数
def signal_handler(sig, frame):
    global running
    logger.info("收到终止信号，正在退出...")
    running = False

# 异步消息处理逻辑
async def main_loop():
    global running
    logger.info("程序已启动，正在监听消息...")

    while running:
        try:
            rev = await rev_msg()  
            if rev and 'message_type' in rev:
                message_type = rev.get('message_type')
                if message_type == "private":
                    await process_private_message(rev)  
                elif message_type == "group":
                    await process_group_message(rev)  
                else:
                    pass  # 忽略未识别的消息类型
            else:
                pass  # 忽略没有收到消息或消息格式不正确的情况

        except Exception as e:
            logger.error(f"Error in main loop: {e}")

# 定义定期清理任务
def schedule_jobs():
    mongo_db = MongoDB()
    exempt_users = [config.ADMIN_ID]  # 需要替换成实际管理员用户ID
    exempt_groups = []  # 需要替换成实际需要豁免的群聊ID
    schedule.every().day.at("02:00").do(mongo_db.clean_old_messages, days=1, exempt_user_ids=exempt_users, exempt_context_ids=exempt_groups)

    
    while running:
        schedule.run_pending()
        time.sleep(60)  # 休眠60秒

# 异步任务管理器
async def main():
    global running

    try:

        # 启动 MongoDB 服务
        start_mongodb()

        # 启动 Flask 应用
        flask_thread = threading.Thread(target=run_flask_app)
        flask_thread.start()

        # 启动定时任务线程
        schedule_thread = threading.Thread(target=schedule_jobs)
        schedule_thread.start()

        # 启动消息服务器、异步消息接收循环和会话超时检查任务
        await asyncio.gather(
            start_server(),  # 启动异步服务器并等待
            main_loop(),  # 启动主循环处理消息
            session_timeout_check()  # 启动会话超时检查任务
        )
        # 启动 session_timeout_check 函数进行定时检查
        asyncio.create_task(session_timeout_check())
    finally:
        # 等待所有任务完成后关闭 Flask 应用
        #flask_server.shutdown()
        print("关闭 Flask 应用程序...")
        logger.info("关闭 Flask 应用程序...")

if __name__ == '__main__':
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 读取配置
    config = Config.get_instance()

    try:
        # 运行主异步任务
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main loop encountered an error: {e}")

    logger.info("程序已停止。")

    sys.exit(0)