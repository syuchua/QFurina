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
from app.function_calling import handle_image_request, handle_voice_request, handle_image_recognition
from app.database import MongoDB

config = Config.get_instance()

# 添加数据库连接实例
db = MongoDB()

async def send_msg(msg_type, number, msg, use_voice=False):
    if use_voice:
        audio_filename = await generate_voice(msg)
        if audio_filename:
            msg = f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"

    params = {
        'message': msg,
        **({'group_id': number} if msg_type == 'group' else {'user_id': number})
    }
    url = f"http://127.0.0.1:3000/send_{msg_type}_msg"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as res:
                res.raise_for_status()
                # logger.info(f"Message sent successfully")
                try:
                    logger.info(f"\nsend_{msg_type}_msg: {msg}\n", await res.json())
                except aiohttp.ClientResponseError:
                    logger.info(f"\nsend_{msg_type}_msg: {msg}\n", await res.text())
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error occurred: {e}")

async def send_image(msg_type, number, img_url):
    try:
        image_msg = f"[CQ:image,file={img_url}]"
        await send_msg(msg_type, number, image_msg)
        logger.info(f"Image sent to {number}.")
    except aiohttp.ClientError as e:
        logger.error(f"Failed to send image due to HTTP error: {e}")
        await send_msg(msg_type, number, "发送图片失败，请检查网络或稍后再试。")
    except asyncio.TimeoutError as e:
        logger.error(f"Failed to send image due to timeout: {e}")
        await send_msg(msg_type, number, "发送图片超时，请稍后再试。")
    except Exception as e:
        logger.error(f"Failed to send image due to an unexpected error: {e}")
        await send_msg(msg_type, number, "出现了一些意外情况，图片发送失败。")

async def send_voice(msg_type, number, voice_text):
    try:
        audio_filename = await generate_voice(voice_text)
        if audio_filename:
            voice_msg = f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"
            await send_msg(msg_type, number, voice_msg)
            logger.info(f"Voice message sent to {number}.")
        else:
            logger.error(f"Failed to generate voice message for text: {voice_text}")
            await send_msg(msg_type, number, "语音合成失败，请稍后再试。")
    except aiohttp.ClientError as e:
        logger.error(f"Failed to send voice message due to HTTP error: {e}")
        await send_msg(msg_type, number, "发送语音失败，请检查网络或稍后再试。")

def get_dialogue_response(user_input):
    for dialogue in config.DIALOGUES:
        if dialogue["user"] == user_input:
            return dialogue["assistant"]
    return None

COMMAND_PATTERN = re.compile(r'^[!/#](help|reset|character|history|clear|model|r18)(?:\s+(.+))?')

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

    # 处理命令请求
    # 检查是否是特殊字符命令
    match = COMMAND_PATTERN.match(user_input)
    if match:
        command = match.group(1)
        command_args = match.group(2)
        full_command = f"{command} {command_args}" if command_args else command
        await handle_command(full_command, msg_type, recipient_id, send_msg, context_type, context_id)
        
        
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

    response = await handle_special_requests(user_input)
    if response:
        await send_msg(msg_type, recipient_id, response)
        return

    # 从对话记录中获取最近的消息以进行上下文理解
    recent_messages = db.get_recent_messages(user_id if msg_type == 'private' else 'group', context_type, context_id)
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
                db.insert_chat_message(user_id, user_input, response_text, context_type, context_id)
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
    context_id = user_id

    # 要屏蔽的id
    block_id = [3780469992, 3542896617]

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
            db.insert_chat_message(user_id, user_input, response_text, context_type, context_id)
