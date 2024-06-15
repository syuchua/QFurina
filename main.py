import logging
import signal
import sys
from app.message import process_group_message, process_private_message
from receive import rev_msg  

# 全局变量，用于控制循环
running = True

def signal_handler(sig, frame):
    global running
    print("收到终止信号，正在退出...")
    logging.info("收到终止信号，正在退出...")
    running = False

def main_loop():
    print("程序已启动，正在监听消息...")
    logging.info("程序已启动，正在监听消息...")
    while running:
        try:
            rev = rev_msg()  
            if rev and 'message_type' in rev:
                message_type = rev.get('message_type')
                if message_type == "private":
                    process_private_message(rev)
                elif message_type == "group":
                    process_group_message(rev)
            else:
                logging.info("没有收到消息或消息格式不正确，跳过此次循环。")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")

if __name__ == '__main__':
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main_loop()
    print("程序已停止。")
    logging.info("程序已停止。")
    sys.exit(0)