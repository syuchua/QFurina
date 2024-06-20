import logging
import signal
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from wsgiref.simple_server import make_server
from flask import app
from app.message import process_group_message, process_private_message
from app.config import Config
from utils.receive import start_server, rev_msg  # 调整为导入 start_server 和 rev_msg

# 全局变量用于控制循环
running = True

# 信号处理函数
def signal_handler(sig, frame):
    global running
    print("收到终止信号，正在退出...")
    logging.info("收到终止信号，正在退出...")
    running = False

# 运行 Flask 应用线程池以保持与原逻辑一致
class FlaskServer:
    def __init__(self, app):
        self.server = None
        self.app = app

    def start(self):
        self.server = make_server('127.0.0.1', 4321, self.app)
        self.server.timeout = 1
        self.thread = ThreadPoolExecutor().submit(self.run)

    def run(self):
        logging.info("启动 Flask 应用程序...")
        while running:
            self.server.handle_request()

    def shutdown(self):
        logging.info("关闭 Flask 应用程序...")
        self.server.server_close()

# 异步消息处理逻辑
async def main_loop():
    global running
    print("程序已启动，正在监听消息...")
    logging.info("程序已启动，正在监听消息...")

    while running:
        try:
            rev = await rev_msg()  # 使用异步版本的消息接收函数
            if rev and 'message_type' in rev:
                message_type = rev.get('message_type')
                if message_type == "private":
                    await process_private_message(rev)  # 假设这个函数已经异步定义了
                elif message_type == "group":
                    await process_group_message(rev)  # 假设这个函数已经异步定义了
            else:
                logging.info("没有收到消息或消息格式不正确，跳过此次循环。")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")

async def main():
    global running
    flask_server = FlaskServer(app)

    try:
        # 启动 Flask 应用
        flask_server.start()

        # 启动消息服务器和异步消息接收循环
        await asyncio.gather(
            start_server(),  # 启动异步服务器并等待
            main_loop()  # 启动主循环处理消息
        )
    finally:
        # 确保 Flask 应用被关闭
        flask_server.shutdown()

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
        logging.error("Main loop encountered an error: {}".format(e))

    print("程序已停止。")
    logging.info("程序已停止。")

    sys.exit(0)