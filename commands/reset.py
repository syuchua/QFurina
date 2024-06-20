# reset.py
import time
import threading

# 定义会话超时时间（以秒为单位），例如 15 分钟
SESSION_TIMEOUT = 15 * 60

# 定义全局变量来跟踪会话的最后活动时间
last_activity_time = time.time()

def reset_session():
    global last_activity_time
    last_activity_time = time.time()
    print("会话已重置。")

def handle_reset_command(msg_type, number, send_msg):
    reset_session()
    reset_message = "当前会话已重置。"
    send_msg(msg_type, number, reset_message)

def session_timeout_check():
    global last_activity_time
    while True:
        if time.time() - last_activity_time >= SESSION_TIMEOUT:
            reset_session()
        time.sleep(600)  # 每10分钟检查一次

# 在模块导入时启动会话超时检查线程
threading.Thread(target=session_timeout_check, daemon=True).start()