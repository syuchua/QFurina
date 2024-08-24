# * - message.py - *
from app.logger import logger
import re, random
from .config import config
from ..process.process_msg import process_chat_message
from app.Core.onebotv11 import (
    is_group_message, is_private_message, 
    get_user_id, get_group_id, get_message_content,
    GroupMessageEvent, PrivateMessageEvent
)



@process_chat_message('private')
async def process_private_message(event: PrivateMessageEvent):
    user_id = get_user_id(event)
    content = get_message_content(event)
    logger.info(f"\nReceived private message from user {user_id}: {content}\n")
    return content

@process_chat_message('group')
async def process_group_message(event: GroupMessageEvent):
    user_id = get_user_id(event)
    group_id = get_group_id(event)
    content = get_message_content(event)
    logger.info(f"\nReceived group message from user {user_id} in group {group_id}: {content}\n")

    block_id = config.BLOCK_ID
    contains_nickname = any(nickname in content for nickname in config.NICKNAMES)
    is_sender_blocked = user_id in block_id
    at_bot_message = r'\[CQ:at,qq={},name=[^\]]+\]'.format(config.SELF_ID)
    is_at_bot = re.search(at_bot_message, content)

    is_restart_command = content.strip().lower().startswith('/restart')

    if is_at_bot:
        content = re.sub(at_bot_message, '', content).strip()

    if (contains_nickname or is_at_bot or is_restart_command) and not is_sender_blocked:
        if is_restart_command:
            return '/restart'
        return content

    if random.random() <= config.REPLY_PROBABILITY and not is_sender_blocked:
        return content

    return None