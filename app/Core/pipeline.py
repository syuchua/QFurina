from functools import wraps
from typing import Callable, Any, Dict
from ..process.process_msg import process_chat_message, handle_telegram_message
from ..logger import logger
from ..process.send import send_msg

def pipeline(platform: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(message: Dict[str, Any], *args, **kwargs):
            try:
                if platform == 'onebot':
                    msg_type = 'private' if message['message_type'] == 'private' else 'group'
                    return await process_chat_message(msg_type)(func)(message, *args, **kwargs)
                elif platform == 'telegram':
                    logger.info(f"Received Telegram message: {message}")
                    return await handle_telegram_message(message)
                else:
                    raise ValueError(f"Unsupported platform: {platform}")
            except Exception as e:
                logger.error(f"Error in pipeline for {platform}: {e}", exc_info=True)
                if platform == 'onebot':
                    recipient_id = message['user_id'] if message['message_type'] == 'private' else message['group_id']
                    await send_msg(message['message_type'], recipient_id, "阿巴阿巴，出错了。")
                elif platform == 'telegram':
                    await send_msg('telegram', message['chat']['id'], "阿巴阿巴，出错了。")

        return wrapper
    return decorator
