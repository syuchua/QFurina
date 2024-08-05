import os
import signal
from app.logger import clean_old_logs, logger
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
from utils.receive import start_http_server, start_reverse_ws, rev_msg, close_connection
from commands.reset import session_timeout_check
from app.task_manger import task_manager

# 定义全局线程池
thread_pool = ThreadPoolExecutor(max_workers=10)
CONNECTION_ENABLED = threading.Event()
CONNECTION_ENABLED.set()  # 默认开启
# 定义一个事件来控制主循环
shutdown_event = asyncio.Event()

class FlaskServer:
    def __init__(self, app):
        self.server = None
        self.app = app
        self.is_running = False

    def start(self):
        self.server = make_server('127.0.0.1', 4321, self.app)
        self.server.timeout = 1
        self.is_running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        logger.info("启动 Flask 应用程序...")
        while self.is_running:
            self.server.handle_request() 

    def shutdown(self):
        logger.info("关闭 Flask 应用程序...")
        self.is_running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.thread.join(timeout=5)  # 等待最多5秒
        if self.thread.is_alive():
            logger.warning("Flask 应用程序未能在预期时间内关闭")

async def process_message(rev_message):
    if not CONNECTION_ENABLED.is_set():
        logger.debug("连接已禁用，忽略消息")
        return
    if rev_message and 'post_type' in rev_message:
        if rev_message['post_type'] == 'message':
            message_type = rev_message.get('message_type')
            if message_type == "private":
                asyncio.create_task(process_private_message(rev_message))
            elif message_type == "group":
                asyncio.create_task(process_group_message(rev_message))
        elif rev_message['post_type'] == 'meta_event':
            if rev_message['meta_event_type'] == 'heartbeat':
                logger.debug("Received heartbeat")
            elif rev_message['meta_event_type'] == 'lifecycle' and rev_message['sub_type'] == 'connect':
                logger.info("Connection established")
    else:
        logger.warning(f"Received unexpected message format: {rev_message}")

async def main_loop():
    logger.info("HTTP 轮询进程已启动，正在监听消息...")
    while not shutdown_event.is_set():
        try:
            rev_message = await asyncio.wait_for(rev_msg(), timeout=1.0)           
            await task_manager.add_task(process_message(rev_message))
            #logger.info(f"放入任务队列: {rev_message}")
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
    logger.info("HTTP 轮询进程已停止")

async def ws_process():
    while not shutdown_event.is_set():
        try:
            rev_message = await rev_msg()
            await task_manager.add_task(process_message(rev_message))
            #logger.info(f"放入任务队列: {rev_message}")
        except Exception as e:
            logger.error(f"Error in WebSocket process: {e}")
    logger.info("WebSocket 进程已停止")


# 定义定期清理任务
def schedule_jobs():
    mongo_db = MongoDB()
    exempt_users = [config.ADMIN_ID]
    exempt_groups = []

    schedule.every().day.at(config.DISABLE_TIME).do(disable_connection)
    schedule.every().day.at(config.ENABLE_TIME).do(enable_connection)


    schedule.every().day.at("02:00").do(mongo_db.clean_old_messages, days=1, exempt_user_ids=exempt_users, exempt_context_ids=exempt_groups)
    schedule.every().day.at("03:00").do(clean_old_logs, days=14)

    voice_directory = os.path.join(os.getcwd(), config.AUDIO_SAVE_PATH)
    schedule.every(60).minutes.do(clean_voice_directory, directory=voice_directory)
    
    while not shutdown_event.is_set():
        schedule.run_pending()
        time.sleep(5)  # 减少睡眠时间，以便更快地响应关闭信号

def enable_connection():
    if not CONNECTION_ENABLED.is_set():
        CONNECTION_ENABLED.set()
        logger.info("连接已启用")
    else:
        logger.debug("连接已经处于启用状态")

def disable_connection():
    if CONNECTION_ENABLED.is_set():
        CONNECTION_ENABLED.clear()
        logger.info("连接已禁用")
    else:
        logger.debug("连接已经处于禁用状态")


# 异步任务管理器
async def main():
    flask_server = FlaskServer(app)
    schedule_thread = threading.Thread(target=schedule_jobs, daemon=True)
    schedule_thread.start()

    flask_server.start()
    await task_manager.start()

    try:
        if config.CONNECTION_TYPE == 'http':
            http_server_task = asyncio.create_task(start_http_server())
        elif config.CONNECTION_TYPE == 'ws_reverse':
            ws_server_task = asyncio.create_task(start_reverse_ws())

        timeout_check_task = asyncio.create_task(session_timeout_check())

        while not shutdown_event.is_set():
            if CONNECTION_ENABLED.is_set():
                try:
                    if config.CONNECTION_TYPE == 'http':
                        rev_message = await asyncio.wait_for(rev_msg(), timeout=1.0)
                    else:  # ws_reverse
                        rev_message = await rev_msg()
                    
                    await task_manager.add_task(process_message(rev_message))
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error in message processing: {e}", exc_info=True)
                    await asyncio.sleep(1)  # 在错误发生后短暂暂停，避免rapid failing


    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        shutdown_event.set()
        if config.CONNECTION_TYPE == 'http':
            http_server_task.cancel()
        elif config.CONNECTION_TYPE == 'ws_reverse':
            ws_server_task.cancel()
        timeout_check_task.cancel()
        await close_connection()  # 确保关闭连接
        flask_server.shutdown()
        thread_pool.shutdown(wait=False)  # 关闭线程池
        logger.info("程序关闭完成")

def shutdown_handler(sig, frame):
    logger.info(f"接收到信号 {sig}, 正在关闭程序...")
    shutdown_event.set()
    # 给主循环一些时间来完成当前任务
    time.sleep(2)
    # 强制退出
    os._exit(0)
    
if __name__ == '__main__':
    config = Config.get_instance()

    # 注册信号处理程序
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main loop encountered an error: {e}")
    finally:
        logger.info("程序退出")
