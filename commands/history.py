# *- history.py -*
"""
历史记录管理命令
"""
from app.DB.database import MongoDB

db = MongoDB()

DEFAULT_HISTORY_COUNT = 10
MAX_HISTORY_COUNT = 50
DEFAULT_CLEAR_COUNT = 10
MAX_CLEAR_COUNT = 500

async def handle_history_command(msg_type, user_info, context_type, context_id, send_msg, args):
    try:
        args_list = args.split()
        count = DEFAULT_HISTORY_COUNT
        if args_list:
            count = int(args_list[0])
            if count <= 0:
                await send_msg(msg_type, user_info["recipient_id"], "请输入一个大于0的数字。")
                return
            if count > MAX_HISTORY_COUNT:
                count = MAX_HISTORY_COUNT
                await send_msg(msg_type, user_info["recipient_id"], f"查看数量已被限制为最大值 {MAX_HISTORY_COUNT}。")

        recent_messages = db.get_recent_messages(user_id=user_info["recipient_id"], context_type=context_type, context_id=context_id, platform='onebot', limit=count)
        if recent_messages:
            message_texts = [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
            history_message = "\n".join(message_texts)
            await send_msg(msg_type, user_info["recipient_id"], f"最近的 {len(recent_messages)//2} 条消息记录：\n{history_message}")
        else:
            await send_msg(msg_type, user_info["recipient_id"], "没有找到消息记录。")
    except ValueError:
        await send_msg(msg_type, user_info["recipient_id"], "请输入一个有效的数字。")

async def handle_clear_history_command(msg_type, user_info, context_type, context_id, send_msg, args):
    try:
        args_list = args.split()
        count = DEFAULT_CLEAR_COUNT
        if args_list:
            count = int(args_list[0])
            if count <= 0:
                await send_msg(msg_type, user_info["recipient_id"], "请输入一个大于0的数字。")
                return
            if count > MAX_CLEAR_COUNT:
                count = MAX_CLEAR_COUNT
                await send_msg(msg_type, user_info["recipient_id"], f"清除数量已被限制为最大值 {MAX_CLEAR_COUNT}。")

        recent_messages = db.get_recent_messages(user_id=user_info["recipient_id"], context_type=context_type, context_id=context_id, platform='onebot', limit=count)
        if recent_messages:
            db.delete_messages(recent_messages)
            await send_msg(msg_type, user_info["recipient_id"], f"最近的 {len(recent_messages)//2} 条消息已删除。")
        else:
            await send_msg(msg_type, user_info["recipient_id"], "没有找到可以删除的消息。")
    except ValueError:
        await send_msg(msg_type, user_info["recipient_id"], "请输入一个有效的数字。")
