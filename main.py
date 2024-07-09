import os
import signal
from app.logger import logger
from utils.voice_service import clean_voice_directory
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from wsgiref.simple_server import make_server
from utils.file import app
import schedule
from app.message import process_group_message, process_private_message
from app.config import Config
from app.database import MongoDB
from utils.receive import start_server, rev_msg
from commands.reset import session_timeout_check

# 定义全局线程池
thread_pool = ThreadPoolExecutor(max_workers=10)

# 确认程序是否要关停
def isMainThreadAlive():
    return threading.main_thread().is_alive()

# 运行 Flask 应用线程池以保持与原逻辑一致
class FlaskServer:
    def __init__(self, app):
        self.server = None
        self.app = app

    def start(self):
        self.server = make_server('127.0.0.1', 4321, self.app)
        self.server.timeout = 1
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        logger.info("启动 Flask 应用程序...")
        while isMainThreadAlive():
            self.server.handle_request() 

    def shutdown(self):
        logger.info("关闭 Flask 应用程序...")
        if self.server:
            self.server.shutdown()
            self.server.server_close()

# 同步包装函数
def sync_process_private_message(rev):
    asyncio.run(process_private_message(rev))

def sync_process_group_message(rev):
    asyncio.run(process_group_message(rev))

# 异步消息处理逻辑
async def main_loop():
    logger.info("程序已启动，正在监听消息...")

    while isMainThreadAlive():
        try:
            rev_message = await rev_msg()  # 直接接收单个消息对象
            if rev_message and 'message_type' in rev_message:
                message_type = rev_message.get('message_type')
                if message_type == "private":
                    await asyncio.get_event_loop().run_in_executor(thread_pool, sync_process_private_message, rev_message)
                elif message_type == "group":
                    await asyncio.get_event_loop().run_in_executor(thread_pool, sync_process_group_message, rev_message)
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

    # 每小时检查一次语音文件夹
    voice_directory = os.path.join(os.getcwd(), config.AUDIO_SAVE_PATH)
    schedule.every(60).minutes.do(clean_voice_directory, directory=voice_directory)
    
    while isMainThreadAlive():
        schedule.run_pending()
        time.sleep(60)  # 休眠60秒

# 异步任务管理器
async def main():
    flask_server = FlaskServer(app)
    schedule_thread = threading.Thread(target=schedule_jobs, daemon=True)
    schedule_thread.start()
    try:
        # 启动 Flask 应用
        flask_server.start()
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
        flask_server.shutdown()
        logger.info("关闭 Flask 应用程序...")
        raise SystemExit(0)

def shutdown_handler(sig, frame):
    logger.info(f"接收到信号 {sig}, 正在关闭程序...")
    asyncio.create_task(main_shutdown())

async def main_shutdown():
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    # 读取配置
    config = Config.get_instance()

    # 注册信号处理程序
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        # 运行主异步任务
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main loop encountered an error: {e}")
