# commands/history.py
from app.database import MongoDB

db = MongoDB()

DEFAULT_HISTORY_COUNT = 10
MAX_HISTORY_COUNT = 50
DEFAULT_CLEAR_COUNT = 10
MAX_CLEAR_COUNT = 50

async def handle_history_command(msg_type, recipient_id, context_type, context_id, send_msg, count=None):
    try:
        if count is not None:
            count = int(count)
            if count <= 0:
                await send_msg(msg_type, recipient_id, "请输入一个大于0的数字。")
                return
            if count > MAX_HISTORY_COUNT:
                count = MAX_HISTORY_COUNT
                await send_msg(msg_type, recipient_id, f"查看数量已被限制为最大值 {MAX_HISTORY_COUNT}。")
        else:
            count = DEFAULT_HISTORY_COUNT

        recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=count)
        if recent_messages:
            message_texts = [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
            history_message = "\n".join(message_texts)
            await send_msg(msg_type, recipient_id, f"最近的 {len(recent_messages)//2} 条消息记录：\n{history_message}")
        else:
            await send_msg(msg_type, recipient_id, "没有找到消息记录。")
    except ValueError:
        await send_msg(msg_type, recipient_id, "请输入一个有效的数字。")

async def handle_clear_history_command(msg_type, recipient_id, context_type, context_id, send_msg, count=None):
    try:
        if count is not None:
            count = int(count)
            if count <= 0:
                await send_msg(msg_type, recipient_id, "请输入一个大于0的数字。")
                return
            if count > MAX_CLEAR_COUNT:
                count = MAX_CLEAR_COUNT
                await send_msg(msg_type, recipient_id, f"清除数量已被限制为最大值 {MAX_CLEAR_COUNT}。")
        else:
            count = DEFAULT_CLEAR_COUNT

        recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=count)
        if recent_messages:
            db.delete_messages(recent_messages)
            await send_msg(msg_type, recipient_id, f"最近的 {len(recent_messages)//2} 条消息已删除。")
        else:
            await send_msg(msg_type, recipient_id, "没有找到可以删除的消息。")
    except ValueError:
        await send_msg(msg_type, recipient_id, "请输入一个有效的数字。")
