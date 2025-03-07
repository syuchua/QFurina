# process.py
import asyncio
from functools import wraps
from ..Core.message_utils import MessageManager
from ..plugin.plugin_manager import plugin_manager
from utils.model_request import get_chat_response
from ..DB.database import db
from ..Core.config import config
from ..logger import logger
from ..process.split_message import split_message
from ..Core.command import handle_command
from ..Core.function_calling import handle_command_request
from .process_special import special_handler
from .send import send_msg
from .process_plugin import process_plugin_command, process_plugin_message
from ..Core.decorators import async_timed
from .memory_generator import memory_generator
from ..Core.adapter.onebotv11 import (
    get_user_id, get_group_id, get_message_content, get_username
)
from .process_image import process_image

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
    """
    处理消息
    这个装饰器用于处理接收到的消息，包括消息的预处理、插件处理、命令处理、记忆生成和最终响应发送。
    处理流程：
    1. 获取消息内容、用户ID、用户名、接收者ID、上下文类型和上下文ID。
    2. 构建消息对象。
    3. 将用户消息添加到记忆生成器。
    4. 处理插件消息。
    5. 检查用户输入中的特殊请求。
    6. 检查是否为命令。
    7. 使用 MessageManager 创建消息上下文。
    8. 获取记忆。
    9. 将记忆添加到上下文。
    10. 获取最近的消息。
    11. 如果用户消息不在最近消息中，则添加用户历史消息。
    12. 将最近消息添加到上下文。
    13. 将用户消息和上下文一起发送给 AI 模型。
    14. 获取 AI 响应。
    15. 检查 AI 响应中的特殊处理。
    16. 如果没有特殊处理，继续正常的消息处理流程。
    17. 使用消息截断器发送最终响应。
    18. 将响应添加到原始消息对象中。
    19. 返回修改后的消息对象。
    """
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
                await db.insert_user_info(user_info)

                # 调用原始函数，可能会修改 user_input 或执行其他特定逻辑
                modified_input = await func(rev, *args, **kwargs)
                if modified_input is None:
                    return  # 如果返回 None，表示不需要回复，直接返回
                if modified_input is not None:
                    user_input = modified_input

                # 构建消息对象
                message = {
                    "content": user_input,
                    "user_id": user_id,
                    "username": username,
                    "recipient_id": recipient_id,
                    "context_type": context_type,
                    "context_id": context_id
                }

                #添加用户消息到记忆生成器
                await memory_generator.add_message({
                    "role": "user",
                    "content": user_input
                },context_type,context_id)

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

                # 处理图像识别
                auto_recognition_enabled = config.AUTO_IMAGE_RECOGNITION
                if auto_recognition_enabled:
                    image_handled, image_response, processed_input = await process_image(user_input)
                    logger.info(f"Image handled: {image_handled}, Image response: {image_response}, Processed input: {processed_input}")
                    if image_handled and image_response:
                        await send_msg(msg_type, recipient_id, image_response)
                        await db.insert_chat_message(user_id, user_input, image_response, context_type, context_id, platform='onebot')
                        
                        # 添加到记忆生成器
                        await memory_generator.add_message({
                            "role": "assistant",
                            "content": image_response
                        }, context_type, context_id)
                        
                        return  # 图片已处理，无需继续

                # 使用 MessageManager 创建消息上下文
                messages, user_input = MessageManager.create_message_context(
                    user_input, user_id, username, context_type, context_id
                )

                # 获取记忆
                memories = memory_generator.get_memories()
                # 将记忆添加到上下文
                if memories["short_term"]:
                    messages.append({"role": "system", "content": f"Short-term memory: {memories['short_term']}"})
                if memories["mid_term"]:
                    messages.append({"role": "system", "content": f"Mid-term memory: {memories['mid_term']}"})

                # 获取最近的消息
                recent_messages = await db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, platform='onebot', limit=10)
                user_in_recent = any(msg['role'] == 'user' and msg['content'].startswith(f"{username}:") for msg in recent_messages)  

                # 如果用户消息不在最近消息中，则添加用户历史消息
                if not user_in_recent:
                    user_historical = await db.get_user_historical_messages(user_id=user_id, context_type=context_type, context_id=context_id, limit=3)
                    insert_index = len(recent_messages) // 2
                    recent_messages = recent_messages[:insert_index] + user_historical + recent_messages[insert_index:]
                    if len(recent_messages) > 20:
                        recent_messages = recent_messages[-20:]

                # 将最近消息添加到上下文
                messages.extend(recent_messages)
                messages.append({"role": "user", "content": user_input})

                response_text = get_dialogue_response(user_input) if user_id == config.ADMIN_ID else None
                if response_text is None:
                    response_text = await timed_get_chat_response(messages)

                if response_text:
                    await db.insert_chat_message(user_id, user_input, response_text, context_type, context_id, platform='onebot')
                    
                    # 将 AI 响应添加到记忆生成器
                    await memory_generator.add_message({
                        "role": "assistant",
                        "content": response_text
                    },context_type,context_id)

                    # 检查 AI 响应中的特殊处理
                    handled, result = await special_handler.process_special(user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id)
                    if handled:
                        return result
                    
                    # 如果没有特殊处理，继续正常的消息处理流程
                    if user_id != config.ADMIN_ID:                    
                        response_with_username = f"{username},{response_text}"
                    else:
                        response_with_username = response_text

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
