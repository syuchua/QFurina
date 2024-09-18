# process.py
import asyncio, random
from functools import wraps
from ..Core.decorators import filter_message
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
from ..Core.adapter.onebotv11 import (
    get_user_id, get_group_id, get_message_content, get_username
)

# 自定义回复
def get_dialogue_response(user_input):
    for dialogue in config.DIALOGUES:
        if dialogue["user"] == user_input:
            return dialogue["assistant"]
    return None

@async_timed()
@filter_message
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

                # 构建消息对象
                message = {
                    "content": user_input,
                    "user_id": user_id,
                    "username": username,
                    "recipient_id": recipient_id,
                    "context_type": context_type,
                    "context_id": context_id
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

                # 使用 MessageManager 创建消息上下文
                messages, user_input = MessageManager.create_message_context(
                    user_input, user_id, username, context_type, context_id
                )

                # 获取最近的消息
                recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, platform='onebot', limit=10)
                user_in_recent = any(msg['role'] == 'user' and msg['content'].startswith(f"{username}:") for msg in recent_messages)  

                if not user_in_recent:
                    user_historical = db.get_user_historical_messages(user_id=user_id, context_type=context_type, context_id=context_id, limit=3)
                    insert_index = len(recent_messages) // 2
                    recent_messages = recent_messages[:insert_index] + user_historical + recent_messages[insert_index:]
                    if len(recent_messages) > 20:
                        recent_messages = recent_messages[-20:]

                messages.extend(recent_messages)
                messages.append({"role": "user", "content": user_input})

                response_text = get_dialogue_response(user_input) if user_id == config.ADMIN_ID else None
                if response_text is None:
                    response_text = await timed_get_chat_response(messages)

                if response_text:
                    db.insert_chat_message(user_id, user_input, response_text, context_type, context_id, platform='onebot')
                    
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

async def handle_telegram_message(message):
    try:
        user_input = message.get('text', '')
        user_id = message['from']['id']
        username = message['from'].get('username', 'Unknown')
        chat_id = message['chat']['id']
        context_type = 'private' if message['chat']['type'] == 'private' else 'group'
        context_id = chat_id

        # 构建消息对象
        message_obj = {
            "content": user_input,
            "user_id": user_id,
            "username": username,
            "recipient_id": chat_id,
            "context_type": context_type,
            "context_id": context_id
        }

        # 处理插件消息
        plugin_response = await process_plugin_message(message_obj)
        if plugin_response:
            await send_msg('telegram', chat_id, plugin_response)
            return message

        # 检查是否为命令
        full_command = await handle_command_request(user_input)
        if full_command:
            plugin_commands = plugin_manager.get_all_plugin_commands()
            command = full_command.split()[0].lower()
            
            if command in plugin_commands:
                await process_plugin_command(full_command, context_type, message_obj, lambda rid, msg: send_msg('telegram', rid, msg), context_type, context_id)
                return message
            else:
                await handle_command(full_command, context_type, message_obj, lambda rid, msg: send_msg('telegram', rid, msg), context_type, context_id)
                return message

        # 使用 MessageManager 创建消息上下文
        messages, user_input = MessageManager.create_message_context(
            user_input, user_id, username, context_type, context_id
        )

        # 获取最近的消息
        recent_messages = db.get_recent_messages(user_id=chat_id, context_type=context_type, context_id=context_id, platform='telegram', limit=10)
        messages.extend(recent_messages)
        messages.append({"role": "user", "content": user_input})

        response_text = await timed_get_chat_response(messages)

        if response_text:
            db.insert_chat_message(user_id, user_input, response_text, context_type, context_id, platform='telegram')
            
            # 检查 AI 响应中的特殊处理
            handled, result = await special_handler.process_special(user_input, response_text, 'telegram', chat_id, user_id, context_type, context_id)
            if handled:
                await send_msg('telegram', chat_id, result)
                return message
            
            # 如果没有特殊处理,继续正常的消息处理流程
            response_with_username = f"{username},{response_text}" if user_id != config.ADMIN_ID else response_text

            # 使用消息截断器发送最终响应
            response_parts = split_message(response_with_username)
            for part in response_parts:
                await send_msg('telegram', chat_id, part)
                await asyncio.sleep(0.3)

        # 将响应添加到原始消息对象中
        message['response'] = response_text

        return message # 返回修改后的消息对象
    
    except Exception as e:
        logger.error(f"Error in handle_telegram_message: {e}", exc_info=True)
        await send_msg('telegram', chat_id, "阿巴阿巴,出错了。")
        return message
    
async def handle_telegram_updates(bot):
    offset = 0
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            logger.debug(f"Received Telegram updates: {updates}")

            if not isinstance(updates, list):
                logger.error(f"Unexpected updates type: {type(updates)}")
                await asyncio.sleep(5)
                continue

            for update in updates:
                if not isinstance(update, dict):
                    logger.error(f"Unexpected update type: {type(update)}")
                    continue

                update_id = update.get('update_id')
                if update_id is None:
                    logger.error("Update missing 'update_id'")
                    continue

                offset = update_id + 1

                message = update.get('message')
                if message is None:
                    logger.debug(f"Update {update_id} has no 'message'")
                    continue

                if not isinstance(message, dict):
                    logger.error(f"Unexpected message type: {type(message)}")
                    continue

                # 处理消息
                response = await handle_telegram_message(message)
                
                # 检查 response 是否为字符串（来自 get_chat_response）
                if isinstance(response, str):
                    # 如果是字符串，直接发送响应
                    chat_id = message['chat']['id']
                    await bot.send_message(chat_id=chat_id, text=response)
                elif isinstance(response, dict):
                    # 如果是字典，可能包含了原始消息和响应
                    if 'response' in response:
                        chat_id = message['chat']['id']
                        await bot.send_message(chat_id=chat_id, text=response['response'])
                else:
                    logger.error(f"Unexpected response type from process_telegram_message: {type(response)}")

        except Exception as e:
            logger.error(f"Error in handle_telegram_updates: {e}", exc_info=True)

        await asyncio.sleep(1)