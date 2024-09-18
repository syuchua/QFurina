# *- boot.py -*
import asyncio, threading, os, time, schedule
from app.process.task_manger import task_manager
from app.Core.config import config
from app.logger import clean_old_logs, logger
from app.DB.database import MongoDB
from app.Core.message import process_group_message, process_private_message, process_telegram_message
from commands.reset import session_timeout_check
from app.Core.decorators import error_handler
from utils.receive import close_connection, rev_msg, start_http_server, start_reverse_ws
from app.Core.thread_pool import get_thread_pool
from utils.voice_service import clean_voice_directory
from utils.file import app
from wsgiref.simple_server import make_server
from app.plugin.plugin_manager import plugin_manager
from app.Core.adapter.onebotv11 import EventType, is_group_message, is_private_message
from app.Core.adapter.tgbot import TelegramBot
from functools import partial

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
        self.server = make_server('0.0.0.0', 4321, self.app)
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
    is_restart_command = rev_message.get('raw_message', '').strip().lower().startswith('/restart')
    
    if not BOT_ACTIVE.is_set() and not is_restart_command:
        logger.debug("机器人处于睡眠状态，忽略非重启命令")
        return
    
    if rev_message and 'post_type' in rev_message:
        if rev_message['post_type'] == EventType.MESSAGE.value:
            if is_group_message(rev_message):
                await asyncio.create_task(process_group_message(rev_message))
            elif is_private_message(rev_message):
                await asyncio.create_task(process_private_message(rev_message))
        elif rev_message['post_type'] == EventType.META_EVENT.value:

            if rev_message['meta_event_type'] == 'heartbeat':
                logger.debug("Received heartbeat")
            elif rev_message['meta_event_type'] == 'lifecycle' and rev_message['sub_type'] == 'connect':
                logger.info("Connection established")
    elif 'message' in rev_message:
        await asyncio.create_task(process_telegram_message(rev_message))
    else:
        logger.warning(f"Received unexpected message format: {rev_message}")



@error_handler
async def message_loop():
    """消息处理循环"""
    
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
    schedule.every().day.at(config.DISABLE_TIME).do(shutdown_gracefully)
    schedule.every().day.at(config.ENABLE_TIME).do(restart_main_loop)

    # 定时清理任务
    schedule.every().day.at("02:00").do(partial(mongo_db.clean_old_messages, days=1, exempt_user_ids=exempt_users, exempt_context_ids=exempt_groups))
    schedule.every().day.at("03:00").do(partial(clean_old_logs, days=14))

    voice_directory = os.path.join(os.getcwd(), config.AUDIO_SAVE_PATH)
    schedule.every(60).minutes.do(partial(clean_voice_directory, directory=voice_directory))
    
    while not shutdown_event.is_set():
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Error in scheduled job: {e}", exc_info=True)
        time.sleep(5)

def shutdown_gracefully():
    """进入睡眠状态"""
    logger.info("开始执行睡眠...")
    BOT_ACTIVE.clear()
    logger.info("机器人已进入睡眠状态")

def restart_main_loop():
    """从睡眠状态唤醒"""
    logger.info("开始唤醒机器人...")
    BOT_ACTIVE.set()
    logger.info("机器人已唤醒，恢复正常运行")

# 处理 Telegram 更新
async def handle_telegram_updates(bot):
    offset = 0
    while not shutdown_event.is_set():
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                offset = update['update_id'] + 1
                if 'message' in update:
                    await task_manager.add_task(process_message(update['message']))
        except Exception as e:
            logger.error(f"Error in handle_telegram_updates: {e}")
        await asyncio.sleep(1)

def is_telegram_enabled():
    return config.ENABLE_TELEGRAM and config.TELEGRAM_BOT_TOKEN

# 异步任务管理器
async def task():
    flask_server = FlaskServer(app)
    schedule_thread = threading.Thread(target=schedule_jobs, daemon=True)
    schedule_thread.start()

    flask_server.start()
    await task_manager.start()

    # 加载插件
    await plugin_manager.load_plugins()

    try:
        tasks = [session_timeout_check()]
        if config.CONNECTION_TYPE == 'http':
            tasks.append(start_http_server())
        elif config.CONNECTION_TYPE == 'ws_reverse':
            tasks.append(start_reverse_ws())

        if BOT_ACTIVE.is_set():
            tasks.append(message_loop())

        if is_telegram_enabled():
            tg_bot = TelegramBot(config.TELEGRAM_BOT_TOKEN)
            tasks.append(handle_telegram_updates(tg_bot))

        await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        shutdown_event.set()
        await close_connection()
        await plugin_manager.unload_plugins()
        flask_server.shutdown()
        get_thread_pool().shutdown(wait=False)
        logger.info("程序关闭完成")

def shutdown_handler(sig, frame):
    logger.info(f"接收到信号 {sig}, 正在关闭程序...")
    shutdown_event.set()
    # 给主循环一些时间来完成当前任务
    time.sleep(5)
    # 强制退出
    os._exit(0)