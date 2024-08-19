# *- boot.py -*
import asyncio, threading, os, time, schedule
from app.task_manger import task_manager
from app.config import Config
from app.logger import clean_old_logs, logger
from app.database import MongoDB
from app.message import process_group_message, process_private_message
from commands.reset import session_timeout_check
from app.decorators import error_handler
from utils.receive import close_connection, rev_msg, start_http_server, start_reverse_ws
from concurrent.futures import ThreadPoolExecutor
from utils.voice_service import clean_voice_directory
from utils.file import app
from wsgiref.simple_server import make_server

config = Config.get_instance()

# 定义全局线程池
thread_pool = ThreadPoolExecutor(max_workers=10)
BOT_ACTIVE = threading.Event()
BOT_ACTIVE.set()  # 默认为激活状态


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
    is_restart_command = rev_message['raw_message'].strip().lower().startswith('/restart')
    
    if not BOT_ACTIVE.is_set() and not is_restart_command:
        logger.debug("机器人处于睡眠状态，忽略非重启命令")
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



@error_handler
async def message_loop():
    logger.info("消息处理循环已启动...")
    while not shutdown_event.is_set():
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
            await asyncio.sleep(1) 
    logger.info("消息处理循环已停止")


def schedule_jobs():
    mongo_db = MongoDB()
    exempt_users = [config.ADMIN_ID]
    exempt_groups = []

    # 定时开关机
    schedule.every().day.at(config.DISABLE_TIME).do(asyncio.run, shutdown_gracefully())
    schedule.every().day.at(config.ENABLE_TIME).do(asyncio.run, restart_main_loop())

    # 定时清理任务
    schedule.every().day.at("02:00").do(mongo_db.clean_old_messages, days=1, exempt_user_ids=exempt_users, exempt_context_ids=exempt_groups)
    schedule.every().day.at("03:00").do(clean_old_logs, days=14)

    voice_directory = os.path.join(os.getcwd(), config.AUDIO_SAVE_PATH)
    schedule.every(60).minutes.do(clean_voice_directory, directory=voice_directory)
    
    while not shutdown_event.is_set():
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Error in scheduled job: {e}", exc_info=True)
        time.sleep(5)

async def shutdown_gracefully():
    """进入睡眠状态"""
    logger.info("开始执行睡眠...")
    BOT_ACTIVE.clear()
    logger.info("机器人已进入睡眠状态")

async def restart_main_loop():
    """从睡眠状态唤醒"""
    logger.info("开始唤醒机器人...")
    BOT_ACTIVE.set()
    logger.info("机器人已唤醒，恢复正常运行")

# 异步任务管理器
async def task():
    flask_server = FlaskServer(app)
    schedule_thread = threading.Thread(target=schedule_jobs, daemon=True)
    schedule_thread.start()

    flask_server.start()
    await task_manager.start()

    try:
        tasks = [session_timeout_check()]
        if config.CONNECTION_TYPE == 'http':
            tasks.append(start_http_server())
        elif config.CONNECTION_TYPE == 'ws_reverse':
            tasks.append(start_reverse_ws())

        if BOT_ACTIVE.is_set():
            tasks.append(message_loop())

        await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        shutdown_event.set()
        await close_connection()
        flask_server.shutdown()
        thread_pool.shutdown(wait=False)
        logger.info("程序关闭完成")

def shutdown_handler(sig, frame):
    logger.info(f"接收到信号 {sig}, 正在关闭程序...")
    shutdown_event.set()
    # 给主循环一些时间来完成当前任务
    time.sleep(2)
    # 强制退出
    os._exit(0)