# message.py 

import random
from app.Core.config import config
from ..process.process_time import get_time_info


class MessageManager:
    @staticmethod
    def get_system_message():
        """获取系统消息"""
        return "\n".join(config.SYSTEM_MESSAGE.values())

    @staticmethod
    def create_message_context(user_input, user_id, username, context_type, context_id):
        """创建消息上下文"""
        system_message_text = MessageManager.get_system_message()
        time_str = get_time_info(user_input)

        if user_id == config.ADMIN_ID:
            admin_title = random.choice(config.ADMIN_TITLES)
            user_input = f"[impression]这是老爹说的话：{admin_title}: {user_input}"
        else:
            user_input = f"[impression]这不是老爹说的话:{username}: {user_input}"

        messages = [
            {"role": "system", "content": system_message_text},
            {"role": "system", "content": time_str}
        ]

        return messages, user_input

    @staticmethod
    def insert_or_replace_system_message(messages, new_system_message):
        """插入或替换系统消息"""
        if messages and messages[0]['role'] == 'system':
            messages[0]['content'] = new_system_message
        else:
            messages.insert(0, {"role": "system", "content": new_system_message})
        return messages
