import asyncio, random
from functools import wraps
from utils.model_request import get_chat_response
from ..DB.database import db
from utils.current_time import get_current_time, get_lunar_date_info
from ..Core.config import config
from ..logger import logger
from ..process.split_message import split_message
from ..Core.command import handle_command
from ..Core.function_calling import handle_command_request
from .process_festival import should_include_festival, should_include_lunar
from .process_special import process_special_responses, handle_special_requests, contains_special_keywords
from .send import send_msg
from .process_plugin import process_plugin_command, process_plugin_message

def get_dialogue_response(user_input):
    for dialogue in config.DIALOGUES:
        if dialogue["user"] == user_input:
            return dialogue["assistant"]
    return None

def process_chat_message(msg_type):
    def decorator(func):
        @wraps(func)
        async def wrapper(rev, *args, **kwargs):
            try:
                user_input = rev['raw_message']
                user_id = rev['sender']['user_id']
                username = rev['sender']['nickname']
                recipient_id = rev['sender']['user_id'] if msg_type == 'private' else rev['group_id']
                context_type = 'private' if msg_type == 'private' else 'group'
                context_id = recipient_id

                user_info = {
                    "user_id": user_id,
                    "username": username,
                    "group_id": rev['group_id'] if msg_type == 'group' else None,
                    "recipient_id": recipient_id
                }
                db.insert_user_info(user_info)

                # 调用原始函数，可能会修改 user_input 或执行其他特定逻辑
                modified_input = await func(rev, *args, **kwargs)
                if modified_input is None:
                    return  # 如果返回 None，表示不需要回复，直接返回
                if modified_input is not None:
                    user_input = modified_input

                # 检查是否需要包含农历信息和节日信息
                include_lunar = should_include_lunar(user_input)
                include_festival = should_include_festival(user_input)

                # 获取时间信息
                time_info = get_current_time()
                if include_lunar:
                    lunar_info = get_lunar_date_info()
                    time_info.update(lunar_info)

                # 构建时间信息字符串
                time_str = (f"今天是：{time_info['full_time']}，{time_info['weekday']}，"
                            f"现在是{time_info['period']}，具体时间是{time_info['hour']}点{time_info['minute']}分。")
                
                if include_lunar:
                    time_str += f"\n农历：{time_info['lunar_date']}，生肖：{time_info['zodiac']}"
                    if time_info['festival']:
                        time_str += f"，今天是{time_info['festival']}"
                
                if include_festival and time_info['solar_festival']:
                    time_str += f"\n今天是{time_info['solar_festival']}"
                elif include_festival:
                    time_str += "\n今天没有特殊的公历节日"

                # 调用插件的on_message方法并获取响应
                #logger.info("calling process_plugin_message")
                plugin_response = await process_plugin_message(rev, msg_type, *args, **kwargs)
                #logger.debug(f"process_plugin_message returned: {plugin_response}")

                if plugin_response:
                    # 如果有插件响应,直接发送插件的响应
                    #logger.info(f"Plugin response received: {plugin_response}")
                    await send_msg(msg_type, recipient_id, plugin_response)
                    return  # 如果插件处理了消息,就不再进行后续的AI处理

                # 如果没有插件响应,在继续AI处理之前
                if not plugin_response:
                    logger.debug("No plugin responses, continuing with AI processing")

                # 检测命令
                full_command = await handle_command_request(user_input)
                if full_command:
                    # 调用插件的on_command方法
                    plugin_response = await process_plugin_command(full_command, msg_type, user_info, send_msg, context_type, context_id)
                    if not plugin_response:
                        await handle_command(full_command, msg_type, user_info, send_msg, context_type, context_id)
                    return

                # 处理特殊请求
                if contains_special_keywords(user_input):
                    special_response = await handle_special_requests(user_input)
                    if special_response:
                        await send_msg(msg_type, recipient_id, special_response)
                        db.insert_chat_message(user_id, user_input, special_response, context_type, context_id)
                        return

                # 获取最近的10条消息
                recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=10)

                # 检查最近消息中是否包含当前用户的消息
                user_in_recent = any(msg['role'] == 'user' and msg['content'].startswith(f"{username}:") for msg in recent_messages)
                
                if not user_in_recent:
                    # 如果最近消息中没有当前用户的消息，获取用户的历史消息
                    user_historical = db.get_user_historical_messages(user_id=user_id, context_type=context_type, context_id=context_id, limit=3)
                    
                    # 将用户的历史消息插入到最近消息的适当位置
                    insert_index = len(recent_messages) // 2  # 插入到中间位置
                    recent_messages = recent_messages[:insert_index] + user_historical + recent_messages[insert_index:]
                    
                    # 如果插入后消息数量超过10轮，裁剪掉最早的消息
                    if len(recent_messages) > 20:  # 10轮对话是20条消息（每轮包含用户输入和机器人回复）
                        recent_messages = recent_messages[-20:]

                system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
                if user_id == config.ADMIN_ID:
                    admin_title = random.choice(config.ADMIN_TITLES)
                    user_input = "[impression]这是老爹说的话："f"{admin_title}: {user_input}"
                else:
                    user_input = "[impression]这不是老爹说的话:"f"{username}: {user_input}"
                messages = [
                    {"role": "system", "content": system_message_text},
                    {"role": "system", "content": time_str}
                ] + recent_messages + [{"role": "user", "content": user_input}]

                #logger.info(f"Messages for chat response: {messages}")

                response_text = get_dialogue_response(user_input) if user_id == config.ADMIN_ID else None
                if response_text is None:
                    response_text = await get_chat_response(messages)

                if response_text:
                    db.insert_chat_message(user_id, user_input, response_text, context_type, context_id)
                    # 添加一个参数来指示是否处理特殊响应
                    process_special = not user_input.startswith(('!history', '/history', '#history'))
                    await process_special_responses(response_text, msg_type, recipient_id, user_id, user_input, context_type, context_id, process_special=process_special)

                if user_id == config.ADMIN_ID:                    
                    response_with_username = response_text
                else:
                    response_with_username = f"{username}，{response_text}"

                # 使用消息截断器发送最终响应
                response_parts = split_message(response_with_username)
                for part in response_parts:
                    await send_msg(msg_type, recipient_id, part)
                    await asyncio.sleep(0.3)

                # 直接发送完整消息，不使用消息截断器
                #await send_msg(msg_type, recipient_id, response_with_username)

            except Exception as e:
                logger.error(f"Error in process_chat_message: {e}")
                await send_msg(msg_type, recipient_id, "阿巴阿巴，出错了。")
        
        return wrapper
    return decorator


