# process.py
import asyncio, random
from functools import wraps
from ..plugin.plugin_manager import plugin_manager
from utils.model_request import get_chat_response
from ..DB.database import db
from ..Core.config import config
from ..logger import logger
from ..process.split_message import split_message
from ..Core.command import handle_command
from ..Core.function_calling import handle_command_request
from .process_time import get_time_info
from .process_special import special_handler
from .send import send_msg
from .process_plugin import process_plugin_command, process_plugin_message
from ..Core.decorators import async_timed
from app.Core.onebotv11 import (
    get_user_id, get_group_id, get_message_content, get_username
)

# 自定义回复
def get_dialogue_response(user_input):
    for dialogue in config.DIALOGUES:
        if dialogue["user"] == user_input:
            return dialogue["assistant"]
    return None

@async_timed()
async def timed_get_chat_response(messages):
    return await get_chat_response(messages)


def process_chat_message(msg_type):
    def decorator(func):
        @wraps(func)
        async def wrapper(rev, *args, **kwargs):
            try:
                user_input = get_message_content(rev)
                user_id = get_user_id(rev)
                username = get_username(rev)
                recipient_id = get_user_id(rev) if msg_type == 'private' else get_group_id(rev)
                context_type = 'private' if msg_type == 'private' else 'group'
                context_id = recipient_id

                user_info = {
                    "user_id": user_id,
                    "username": username,
                    "group_id": get_group_id(rev) if msg_type == 'group' else None,
                    "recipient_id": recipient_id
                }
                db.insert_user_info(user_info)

                # 调用原始函数，可能会修改 user_input 或执行其他特定逻辑
                modified_input = await func(rev, *args, **kwargs)
                if modified_input is None:
                    return  # 如果返回 None，表示不需要回复，直接返回
                if modified_input is not None:
                    user_input = modified_input

                # 获取时间信息
                time_str = get_time_info(user_input)

                # 构建消息对象
                message = {
                    "content": user_input,
                    "user_id": user_id,
                    "username": username,
                    "recipient_id": recipient_id,
                    "context_type": context_type,
                    "context_id": context_id,
                    "time_str": time_str
                }

                # 处理插件消息
                plugin_response = await process_plugin_message(message)
                if plugin_response:
                    await send_msg(msg_type, recipient_id, plugin_response)
                    return

                # 检查用户输入中的特殊请求
                handled, result = await special_handler.process_special(user_input, "", msg_type, recipient_id, user_id, context_type, context_id)
                if handled:
                    return result

                # 检查是否为命令
                full_command = await handle_command_request(user_input)
                if full_command:
                    plugin_commands = plugin_manager.get_all_plugin_commands()
                    command = full_command.split()[0].lower()
                    
                    if command in plugin_commands:
                        # 如果是插件命令,调用插件的处理函数
                        plugin_response = await process_plugin_command(full_command, msg_type, user_info, send_msg, context_type, context_id)
                        return
                    else:
                        # 如果不是插件命令,则处理为系统命令
                        await handle_command(full_command, msg_type, user_info, send_msg, context_type, context_id)
                        return

                # 获取最近的消息
                recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=10)
                user_in_recent = any(msg['role'] == 'user' and msg['content'].startswith(f"{username}:") for msg in recent_messages)  

                if not user_in_recent:
                    user_historical = db.get_user_historical_messages(user_id=user_id, context_type=context_type, context_id=context_id, limit=3)
                    insert_index = len(recent_messages) // 2
                    recent_messages = recent_messages[:insert_index] + user_historical + recent_messages[insert_index:]
                    if len(recent_messages) > 20:
                        recent_messages = recent_messages[-20:]

                system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
                if user_id == config.ADMIN_ID:
                    admin_title = random.choice(config.ADMIN_TITLES)
                    user_input = f"[impression]这是老爹说的话：{admin_title}: {user_input}"
                else:
                    user_input = f"[impression]这不是老爹说的话:{username}: {user_input}"
                messages = [
                    {"role": "system", "content": system_message_text},
                    {"role": "system", "content": time_str}
                ] + recent_messages + [{"role": "user", "content": user_input}]

                response_text = get_dialogue_response(user_input) if user_id == config.ADMIN_ID else None
                if response_text is None:
                    response_text = await timed_get_chat_response(messages)

                if response_text:
                    db.insert_chat_message(user_id, user_input, response_text, context_type, context_id)
                    
                    # 检查 AI 响应中的特殊处理
                    handled, result = await special_handler.process_special(user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id)
                    if handled:
                        return result
                    
                    # 如果没有特殊处理，继续正常的消息处理流程
                    if user_id == config.ADMIN_ID:                    
                        response_with_username = response_text
                    else:
                        response_with_username = f"{username}，{response_text}"

                    # 使用消息截断器发送最终响应
                    response_parts = split_message(response_with_username)
                    for part in response_parts:
                        await send_msg(msg_type, recipient_id, part)
                        await asyncio.sleep(0.3)

            except Exception as e:
                logger.error(f"Error in process_chat_message: {e}", exc_info=True)
                await send_msg(msg_type, recipient_id, "阿巴阿巴，出错了。")
        
        return wrapper
    return decorator