from app.logger import logger
import re
import time
import aiohttp
import random
import asyncio
from app.config import Config
from app.command import handle_command
from utils.voice_service import generate_voice
from utils.model_request import get_chat_response
from app.function_calling import handle_image_request, handle_voice_request, handle_image_recognition, handle_command_request
from app.database import MongoDB

config = Config.get_instance()

# 添加数据库连接实例
db = MongoDB()

async def send_msg(msg_type, number, msg, use_voice=False):
    if use_voice:
        try:
            audio_filename = await generate_voice(msg)
            if audio_filename:
                msg = f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"
        except asyncio.TimeoutError:
            msg = "语音合成超时，请稍后再试。"

    params = {
        'message': msg,
        **({'group_id': number} if msg_type == 'group' else {'user_id': number})
    }
    if config.CONNECTION_TYPE == 'http':
        url = f"http://127.0.0.1:3000/send_{msg_type}_msg"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as res:
                    res.raise_for_status()
                    response = await res.json()
                    try:
                        if 'status' in response and response['status'] == 'failed':
                            error_msg = response.get('msg', 'Unknown error')
                            logger.error(f"Failed to send {msg_type} message: {error_msg}")
                            await send_msg(msg_type, number, f"发送消息失败: {error_msg}")
                        else:
                            logger.info(f"\nsend_{msg_type}_msg: {msg}\n", response)
                    except aiohttp.ClientResponseError:
                        error_msg = await res.text()
                        logger.error(f"Client response error: {error_msg}")
                        await send_msg(msg_type, number, f"客户端响应错误: {error_msg}")
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.error(f"Resource not found: {e}")
                await send_msg(msg_type, number, "资源未找到 (404 错误)。")
            else:
                logger.error(f"HTTP error occurred: {e}")
                await send_msg(msg_type, number, f"HTTP 错误: {e}")
        except asyncio.TimeoutError:
            logger.error("Request timed out")
            await send_msg(msg_type, number, "请求超时，请稍后再试。")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error occurred: {e}")
            await send_msg(msg_type, number, f"HTTP 错误: {e}")
    elif config.CONNECTION_TYPE == 'ws_reverse':
        from app.driver import driver_instance
        await driver_instance.send_msg(msg_type, number, msg)


def get_dialogue_response(user_input):
    for dialogue in config.DIALOGUES:
        if dialogue["user"] == user_input:
            return dialogue["assistant"]
    return None

async def process_chat_message(rev, msg_type):

    user_input = rev['raw_message']
    user_id = rev['sender']['user_id']
    username = rev['sender']['nickname']  # 获取群友的昵称
    recipient_id = rev['sender']['user_id'] if msg_type == 'private' else rev['group_id']

    # 确定 context_type 和 context_id
    context_type = 'private' if msg_type == 'private' else 'group'
    context_id = recipient_id


    # 存储用户信息
    user_info = {
        "user_id": user_id,
        "username": username,
    }
    db.insert_user_info(user_info)


    # 处理命令
    full_command =await handle_command_request(user_input)
    if full_command:
        await handle_command(full_command, msg_type, recipient_id, send_msg, context_type, context_id)
        return
        
    # 处理特殊请求
    async def handle_special_requests(user_input):

        image_url = await handle_image_request(user_input)
        if image_url:
            return f"[CQ:image,file={image_url}]"

        voice_url = await handle_voice_request(user_input)
        if voice_url:
            return f"[CQ:record,file={voice_url}]"

        recognition_result = await handle_image_recognition(user_input)
        if recognition_result:
            return f"识别结果：{recognition_result}"

        return None

    special_response = await handle_special_requests(user_input)
    if special_response:
        await send_msg(msg_type, recipient_id, special_response)
        db.insert_chat_message(user_id, user_input, special_response, context_type, context_id, username)
        return

    # 获取最近的对话记录
    recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=10)
    # logger.info(f"Recent messages: {recent_messages}")

    # 构建上下文消息列表
    system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
    messages = [
        {"role": "system", "content": system_message_text}
    ] + recent_messages + [
        {"role": "user", "content": user_input}
    ]

    # 从对话记录中获取预定回复（仅限管理员触发）
    response_text = get_dialogue_response(user_input) if user_id == config.ADMIN_ID else None
    if response_text is None:
        try:
            response_text = await get_chat_response(messages)
            if response_text:  # 确保机器人产生的回复不为空
                db.insert_chat_message(user_id, user_input, response_text, context_type, context_id, username)

                if '#voice' in response_text:
                    logger.info("Voice request detected")
                    voice_pattern = re.compile(r"#voice\s*(.*?)(?<!\.\.\.)[.!?！？]")
                    voice_match = voice_pattern.search(response_text)
                    if voice_match:
                        voice_text = voice_match.group(1).strip()
                        logger.info(f"Voice text: {voice_text}")
                        try:
                            audio_filename = await asyncio.wait_for(generate_voice(voice_text), timeout=10)  # 设置超时时间为10秒
                            logger.info(f"Audio filename: {audio_filename}")
                            if audio_filename:
                                await send_msg(msg_type, recipient_id, f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]")
                                db.insert_chat_message(user_id, user_input, f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]", context_type, context_id, username)
                            else:
                                await send_msg(msg_type, recipient_id, "语音合成失败。")
                            return
                        except asyncio.TimeoutError:
                            await send_msg(msg_type, recipient_id, "语音合成超时，请稍后再试。")
                            return


                elif response_text.startswith('#recognize'):
                    recognition_result = await handle_image_recognition(response_text[10:].strip())
                    if recognition_result:
                        await send_msg(msg_type, recipient_id, f"识别结果：{recognition_result}")
                        db.insert_chat_message(user_id, user_input, f"识别结果：{recognition_result}", context_type, context_id, username)
                    return
            else:
                logger.warning(f"No response generated for user input '{user_input}'. Skipping database insertion.")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await send_msg(msg_type, recipient_id, "阿巴阿巴，出错了。")
            return

        


    # 替换管理员称呼
    if user_id == config.ADMIN_ID:
        admin_title = random.choice(config.ADMIN_TITLES)
        response_with_username = f"{admin_title}，{response_text}"
        await send_msg(msg_type, recipient_id, response_with_username)
    else:
        response_with_username = f"{username}，{response_text}"
        await send_msg(msg_type, recipient_id, response_with_username)


async def process_private_message(rev):
    logger.info(f"\nReceived private message from user {rev['sender']['user_id']}: {rev['raw_message']}\n")
    await process_chat_message(rev, 'private')

async def process_group_message(rev):
    logger.info(f"\nReceived group message in group {rev['group_id']}: {rev['raw_message']}\n")
    user_input = rev['raw_message']
    group_id = rev['group_id']
    user_id = rev['sender']['user_id']
    username = rev['sender']['nickname']  # 获取群友的昵称
    msg_type = 'group'

    # 确定 context_type 和 context_id
    context_type = 'group'
    context_id = group_id

    # 要屏蔽的id
    block_id = [3780469992,3542896617,3758919058]

     # 检查消息是否包含特定的昵称
    contains_nickname = any(nickname in user_input for nickname in config.NICKNAMES)

    # 检查发送者是否在屏蔽列表中
    is_sender_blocked = user_id in block_id

    # 检查消息是否包含 @ 机器人的 CQ 码
    at_bot_message = r'\[CQ:at,qq={}\]'.format(config.SELF_ID)
    is_at_bot = re.search(at_bot_message, user_input)
    if re.search(at_bot_message, user_input):
        # 去除 @ 机器人的CQ码
        user_input = re.sub(at_bot_message, '', user_input).strip()
        await process_chat_message(rev, 'group')
        return
    

    if (contains_nickname or is_at_bot) and not is_sender_blocked:

        await process_chat_message(rev, 'group')
    else:
        if random.random() <= config.REPLY_PROBABILITY:
            system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
            messages = [
                {"role": "system", "content": system_message_text},
                {"role": "user", "content": user_input}
            ]
            response_text = await get_chat_response(messages)
            # 替换管理员称呼
            if user_id == config.ADMIN_ID:
                admin_title = random.choice(config.ADMIN_TITLES)
                response_with_username = f"{admin_title}，{response_text}"
            else:
                response_with_username = f"{username}，{response_text}"

            await send_msg('group', group_id, response_with_username)

            # 存储聊天记录到数据库
            db.insert_chat_message(user_id, user_input, response_text, context_type, context_id, username)
