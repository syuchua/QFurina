# switch.py
from functools import wraps
from app.config import Config
from app.decorators import admin_only

config = Config.get_instance()

@admin_only
async def handle_switch_command(msg_type, number, new_state, send_msg):
    from utils.boot import shutdown_gracefully, restart_main_loop, BOT_ACTIVE
    if new_state == 'restart':
        if not BOT_ACTIVE.is_set():
            await restart_main_loop()
            await send_msg(msg_type, number, "机器人已唤醒")
        else:
            await send_msg(msg_type, number, "机器人已经处于活跃状态")
    elif new_state == 'shutdown':
        if BOT_ACTIVE.is_set():
            await shutdown_gracefully()
            await send_msg(msg_type, number, "机器人已进入睡眠状态")
        else:
            await send_msg(msg_type, number, "机器人已经处于睡眠状态")

