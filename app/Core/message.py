# * - message.py - *
from functools import wraps
import asyncio, re, random
from .config import config
from .pipeline import pipeline
from ..logger import logger
from .adapter.tgbot import TelegramBot
from .adapter.onebotv11 import (
    is_group_message, is_private_message, 
    get_user_id, get_group_id, get_message_content,
    GroupMessageEvent, PrivateMessageEvent
)

# 初始化 Telegram Bot
tg_bot = TelegramBot(config.TELEGRAM_BOT_TOKEN)

@pipeline('onebot')
async def process_private_message(event: PrivateMessageEvent):
    """处理私聊消息"""
    user_id = get_user_id(event)
    content = get_message_content(event)
    logger.info(f"\nReceived private message from user {user_id}: {content}\n")
    return content

@pipeline('onebot')
async def process_group_message(event: GroupMessageEvent):
    """处理群聊消息"""
    user_id = get_user_id(event)
    group_id = get_group_id(event)
    content = get_message_content(event)
    logger.info(f"\nReceived group message from user {user_id} in group {group_id}: {content}\n")

    block_id = config.BLOCK_ID
    contains_nickname = any(nickname in content for nickname in config.NICKNAMES)
    is_sender_blocked = user_id in block_id
    at_bot_message = r'\[CQ:at,qq={0}.*?\]'.format(config.SELF_ID)
    is_at_bot = re.search(at_bot_message, content)
    is_restart_command = content.strip().lower().startswith('/restart')

    if is_at_bot:
        logger.info(f"\nDetected at_bot message: {content}\n")
        content = re.sub(at_bot_message, '', content).strip()
        # logger.info(f"\nProcessed at_bot message: {content}\n")

    if (contains_nickname or is_at_bot or is_restart_command) and not is_sender_blocked:
        if is_restart_command:
            return '/restart'
        return content

    if random.random() <= config.REPLY_PROBABILITY and not is_sender_blocked:
        return content

    return None

@pipeline('telegram')
async def process_telegram_message(message):
    """处理 Telegram 消息"""
    user_id = message['from']['id']
    chat_id = message['chat']['id']
    content = message.get('text', '')
    chat_type = message['chat']['type']
    
    if chat_type == 'private':
        logger.info(f"\nReceived Telegram private message from user {user_id}: {content}\n")
    else:
        logger.info(f"\nReceived Telegram group message from user {user_id} in chat {chat_id}: {content}\n")

    return message
