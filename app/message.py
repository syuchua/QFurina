import logging
import re
import time
import aiohttp
import random
import asyncio
from app.config import Config
from utils.voice_service import generate_voice
from app.command import handle_command
from utils.lolicon import fetch_image
from utils.model_request import get_chat_response, generate_image

config = Config.get_instance()

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
                logging.info(f"Message sent successfully: {msg}")
                try:
                    print(f"send_{msg_type}_msg: {msg}", await res.json())
                except aiohttp.ClientResponseError:
                    print(f"send_{msg_type}_msg: {msg}", await res.text())
    except aiohttp.ClientError as e:
        logging.error(f"HTTP error occurred: {e}")

async def send_image(msg_type, number, img_url):
    try:
        image_msg = f"[CQ:image,file={img_url}]"
        await send_msg(msg_type, number, image_msg)
        logging.info(f"Image sent to {number}.")
    except aiohttp.ClientError as e:
        logging.error(f"Failed to send image due to HTTP error: {e}")
        # 向用户反馈具体的错误详情
        await send_msg(msg_type, number, "发送图片失败，请检查网络或稍后再试。")
    except asyncio.TimeoutError as e:
        logging.error(f"Failed to send image due to timeout: {e}")
        # 向用户反馈具体的错误详情
        await send_msg(msg_type, number, "发送图片超时，请稍后再试。")
    except Exception as e:
        logging.error(f"Failed to send image due to an unexpected error: {e}")
        # 向用户反馈具体的错误详情
        await send_msg(msg_type, number, "出现了一些意外情况，图片发送失败。")

# 特殊字符命令
COMMAND_PATTERN = re.compile(r'^[!/#](help|reset|character)(?:\s+(.+))?')
# 图片关键词和绘画关键词
IMAGE_KEYWORDS = ["发一张", "来一张"]
RANDOM_IMAGE_KEYWORDS = ["再来一张", "来份涩图", "来份色图"]
DRAW_KEYWORDS = ["画一张", "生成一张"]
# 添加语音关键词
VOICE_KEYWORDS = ["语音回复", "用声音说", "语音说"]

async def process_chat_message(rev, msg_type):
    user_input = rev['raw_message']
    recipient_id = rev['sender']['user_id'] if msg_type == 'private' else rev['group_id']

    # 检查是否是特殊字符命令
    match = COMMAND_PATTERN.match(user_input)
    if match:
        command = match.group(1)
        command_args = match.group(2)
        full_command = f"{command} {command_args}" if command_args else command
        await handle_command(full_command, msg_type, recipient_id, send_msg)
        return

    # 检查是否是图片关键词
    for keyword in IMAGE_KEYWORDS:
        if keyword in user_input:
            keyword_value = user_input.split(keyword, 1)[1].strip() if keyword in user_input else ""
            image_url = await fetch_image(keyword_value)
            await send_image(msg_type, recipient_id, image_url)
            return

    for keyword in RANDOM_IMAGE_KEYWORDS:
        if keyword in user_input:
            image_url = await fetch_image("")
            await send_image(msg_type, recipient_id, image_url)
            return

    # 检查是否是 DALL-E 绘画关键词
    for keyword in DRAW_KEYWORDS:
        if keyword in user_input:
            prompt = user_input.replace(keyword, '').strip()
            image_url = await generate_image(prompt)
            await send_image(msg_type, recipient_id, image_url)
            return

    # 检查是否是语音合成关键词
    for keyword in VOICE_KEYWORDS:
        if keyword in user_input:
            voice_text = user_input.replace(keyword, '').strip()
            await send_msg(msg_type, recipient_id, voice_text, use_voice=True)
            return

    # 不匹配以上关键词时处理普通消息
    system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
    messages = [
        {"role": "system", "content": system_message_text},
        {"role": "user", "content": user_input}
    ]
    try:
        response_text = await get_chat_response(messages)
        await send_msg(msg_type, recipient_id, response_text)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await send_msg(msg_type, recipient_id, "阿巴阿巴，出错了。")

async def process_private_message(rev):
    print(f"Received private message from user {rev['sender']['user_id']}: {rev['raw_message']}")
    await process_chat_message(rev, 'private')

async def process_group_message(rev):
    print(f"Received group message in group {rev['group_id']}: {rev['raw_message']}")
    user_input = rev['raw_message']
    group_id = rev['group_id']
    msg_type = 'group'

    # 检查消息是否包含 @ 机器人的 CQ 码
    at_bot_message = r'\[CQ:at,qq={}\]'.format(config.SELF_ID)
    if re.search(at_bot_message, user_input):
        # 去除 @ 机器人的CQ码
        user_input = re.sub(at_bot_message, '', user_input).strip()
        await process_chat_message(rev, 'group')
        return

    if any(nickname in user_input for nickname in config.NICKNAMES) or re.match(r'^\[CQ:at,qq={}\]$'.format(config.SELF_ID), user_input):
        await process_chat_message(rev, 'group')
    else:
        if random.random() <= config.REPLY_PROBABILITY:
            system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
            messages = [
                {"role": "system", "content": system_message_text},
                {"role": "user", "content": user_input}
            ]
            response_text = await get_chat_response(messages)
            await send_msg('group', group_id, response_text)