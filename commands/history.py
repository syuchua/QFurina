# commands/history.py
from app.database import MongoDB

db = MongoDB()

async def handle_history_command(msg_type, recipient_id, context_type, context_id, send_msg):
    recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=10)
    if recent_messages:
        message_texts = [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
        history_message = "\n".join(message_texts)
    else:
        history_message = "没有找到最近的消息记录。"
    await send_msg(msg_type, recipient_id, history_message)

async def handle_clear_history_command(msg_type, recipient_id, context_type, context_id, send_msg):
    recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=10)
    db.delete_messages(recent_messages)
    await send_msg(msg_type, recipient_id, "最近的十条消息已删除。")
