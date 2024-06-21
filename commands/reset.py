import asyncio

# 定义会话超时时间（以秒为单位），例如 15 分钟
SESSION_TIMEOUT = 15 * 60

# 定义全局变量来跟踪会话的最后活动时间
last_activity_time = None

def reset_session():
    global last_activity_time
    last_activity_time = asyncio.get_event_loop().time()
    print("会话已重置。")

async def handle_reset_command(msg_type, recipient_id, send_msg):
    reset_session()
    reset_message = "当前会话已重置。"
    await send_msg(msg_type, recipient_id, reset_message)

async def session_timeout_check():
    global last_activity_time
    loop = asyncio.get_event_loop()
    while True:
        if last_activity_time is not None and loop.time() - last_activity_time >= SESSION_TIMEOUT:
            reset_session()
        await asyncio.sleep(600)  # 每10分钟检查一次
