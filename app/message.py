import json
import logging
import os
import re
import time
import requests
import random
from app.config import  NICKNAMES, REPLY_PROBABILITY, SELF_ID, SYSTEM_MESSAGE
from utils.voice_service import generate_voice
from app.command import handle_command
from utils.lolicon import fetch_image 
from utils.model_request import get_chat_response, generate_image

def send_msg(msg_type, number, msg, use_voice=False):

    if use_voice:
        audio_filename = generate_voice(msg)
        if audio_filename:
            msg = f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"

    params = {
        'message': msg,
        **({'group_id': number} if msg_type == 'group' else {'user_id': number})
    }
    url = f"http://127.0.0.1:3000/send_{msg_type}_msg"

    try:
        res = requests.post(url, json=params)
        res.raise_for_status()
        logging.info(f"Message sent successfully: {msg}")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred: {e.response.status_code} - {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception occurred: {e}")

    try:
        print(f"send_{msg_type}_msg: {msg}", json.loads(res.content))
    except json.JSONDecodeError:
        print(f"send_{msg_type}_msg: {msg}", res.content)

def send_image(msg_type, number, img_url):
    try:
        # 尝试发送图片消息
        image_msg = f"[CQ:image,file={img_url}]"
        send_msg(msg_type, number, image_msg)
        logging.info(f"图片已发送至 {number}。")
    except requests.exceptions.RequestException as e:
        logging.error(f"发送图片失败: {e}")
        send_msg(msg_type, number, "哎呀，图片找不到了")


def send_voice(msg_type, number, voice_text):
    try:
        # 尝试发送语音消息
        send_msg(msg_type, number, voice_text, use_voice=True)
        logging.info(f"语音消息已发送至 {number}。")
    except requests.exceptions.RequestException as e:
        logging.error(f"发送语音消息失败: {e}")
        send_msg(msg_type, number, "哎呀，语音消息无法发送")

# 特殊字符命令
COMMAND_PATTERN = re.compile(r'^[!/#](help|reset|character)(?:\s+(.+))?')
# 图片关键词和绘画关键词
IMAGE_KEYWORDS = ["发一张", "来一张"]
RANDOM_IMAGE_KEYWORDS = ["再来一张", "来份涩图", "来份色图"]
DRAW_KEYWORDS = ["画一张", "生成一张"]
# 添加语音关键词
VOICE_KEYWORDS = ["语音回复", "用声音说", "语音说"]

def process_chat_message(rev, msg_type):
    global last_activity_time
    last_activity_time = time.time()  # 每次处理消息时重新计时

    user_input = rev['raw_message']
    recipient_id = rev['sender']['user_id'] if msg_type == 'private' else rev['group_id']

    # 检查是否是特殊字符命令
    match = COMMAND_PATTERN.match(user_input)
    if match:
        command = match.group(1)
        handle_command(command, msg_type, recipient_id, send_msg)
        return

    # 检查是否是图片关键词
    for keyword in IMAGE_KEYWORDS:
        if keyword in user_input:
            keyword_value = user_input.split(keyword, 1)[1].strip() if keyword in user_input else ""
            image_url = fetch_image(keyword_value)
            send_image(msg_type, recipient_id, image_url)
            return

    for keyword in RANDOM_IMAGE_KEYWORDS:
        if keyword in user_input:
            image_url = fetch_image("")
            send_image(msg_type, recipient_id, image_url)
            return

    # 检查是否是 DALL-E 绘画关键词
    for keyword in DRAW_KEYWORDS:
        if keyword in user_input:
            prompt = user_input.replace(keyword, '').strip()
            image_url = generate_image(prompt)
            send_image(msg_type, recipient_id, image_url)
            return

    # 检查是否是语音合成关键词
    for keyword in VOICE_KEYWORDS:
        if keyword in user_input:
            voice_text = user_input.replace(keyword, '').strip()
            send_msg(msg_type, recipient_id, voice_text, use_voice=True)
            return

    # 不匹配以上关键词时处理普通消息
    system_message_text = "\n".join(SYSTEM_MESSAGE.values())
    messages = [
        {"role": "system", "content": system_message_text},
        {"role": "user", "content": user_input}
    ]
    try:
        response_text = get_chat_response(messages)
        send_msg(msg_type, recipient_id, response_text)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        send_msg(msg_type, recipient_id, "阿巴阿巴，出错了。")

def process_private_message(rev):
    print(f"Received private message from user {rev['sender']['user_id']}: {rev['raw_message']}")
    process_chat_message(rev, 'private')

def process_group_message(rev):
    print(f"Received group message in group {rev['group_id']}: {rev['raw_message']}")
    user_input = rev['raw_message']
    group_id = rev['group_id']
    msg_type = 'group'

    # 检查消息是否包含 @ 机器人的 CQ 码
    at_bot_message = r'\[CQ:at,qq={}\]'.format(SELF_ID)
    if re.search(at_bot_message, user_input):
        # 去除 @ 机器人的CQ码
        user_input = re.sub(at_bot_message, '', user_input).strip()
        process_chat_message(rev, 'group')
        return

    if any(nickname in user_input for nickname in NICKNAMES) or re.match(r'^\[CQ:at,qq={}\]$'.format(SELF_ID), user_input):
        process_chat_message(rev, 'group')
    else:
        if random.random() <= REPLY_PROBABILITY:
            system_message_text = "\n".join(SYSTEM_MESSAGE.values())
            messages = [
                {"role": "system", "content": system_message_text},
                {"role": "user", "content": user_input}
            ]
            response_text = get_chat_response(messages)
            send_msg('group', group_id, response_text)