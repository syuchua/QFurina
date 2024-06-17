import logging
import signal
import sys
import threading
from wsgiref.simple_server import make_server

from flask import app
from waitress import serve
from app.message import process_group_message, process_private_message
from utils.receive import rev_msg  

# 全局变量，用于控制循环
running = True

def signal_handler(sig, frame):
    global running
    print("收到终止信号，正在退出...")
    logging.info("收到终止信号，正在退出...")
    running = False

class ServerThread(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 4321, app)
        self.srv.timeout = 1
        self._is_shut_down = threading.Event()
        self._shutdown_request = False

    def run(self):
        logging.info("启动 Flask 应用程序...")
        while not self._shutdown_request:
            self.srv.handle_request()
        self._is_shut_down.set()

    def shutdown(self):
        logging.info("关闭 Flask 应用程序...")
        self._shutdown_request = True
        self._is_shut_down.wait()

def run_flask_app():
    server = ServerThread(app)
    server.start()
    return server

def main_loop():
    print("程序已启动，正在监听消息...")
    logging.info("程序已启动，正在监听消息...")
    while running:
        try:
            rev = rev_msg()  # 假设这个函数已经定义了
            if rev and 'message_type' in rev:
                message_type = rev.get('message_type')
                if message_type == "private":
                    process_private_message(rev)  # 假设这个函数已经定义了
                elif message_type == "group":
                    process_group_message(rev)  # 假设这个函数已经定义了
            else:
                logging.info("没有收到消息或消息格式不正确，跳过此次循环。")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")

if __name__ == '__main__':
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动 Flask 应用的线程
    server = run_flask_app()

    # 进入主循环
    main_loop()
    print("程序已停止。")
    logging.info("程序已停止。")

    # 确保 Flask 服务停止
    if server.is_alive():
        server.shutdown()
        server.join()

    sys.exit(0)