# * - message.py - *
from app.logger import logger
import re, random
from .config import config
from ..process.process_msg import process_chat_message

@process_chat_message('private')
async def process_private_message(rev):
    logger.info(f"\nReceived private message from user {rev['sender']['user_id']}: {rev['raw_message']}\n")
    user_input = rev['raw_message']

    return user_input


@process_chat_message('group')
async def process_group_message(rev):
    logger.info(f"\nReceived group message from user {rev['sender']['user_id']} in group {rev['group_id']}: {rev['raw_message']}\n")

    user_input = rev['raw_message']
    group_id = rev['group_id']
    user_id = rev['sender']['user_id']


    block_id = config.BLOCK_ID
    contains_nickname = any(nickname in user_input for nickname in config.NICKNAMES)
    is_sender_blocked = user_id in block_id
    # 更新 at_bot_message 正则表达式以匹配新格式
    at_bot_message = r'\[CQ:at,qq={},name=[^\]]+\]'.format(config.SELF_ID)
    is_at_bot = re.search(at_bot_message, user_input)

    # 简化的重启命令检查
    is_restart_command = user_input.strip().lower().startswith('/restart')

    if is_at_bot:
        # 移除 @ 消息，包括可能的名字部分
        user_input = re.sub(at_bot_message, '', user_input).strip()

    if (contains_nickname or is_at_bot or is_restart_command) and not is_sender_blocked:
        if is_restart_command:
            # 如果是重启命令，只返回 '/restart'
            return '/restart'
        return user_input  # 返回处理后的 user_input

    if random.random() <= config.REPLY_PROBABILITY and not is_sender_blocked:
        return user_input  # 随机回复的情况

    return None  # 明确表示不需要回复

