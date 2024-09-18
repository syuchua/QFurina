from typing import Dict, Any, List, Callable, Optional

from .config import Config
from .adapter.onebotv11 import (
    get_user_id, get_group_id, get_message_content, get_username,
    is_group_message, is_private_message
)
from .message_utils import MessageManager
from ..DB.database import MongoDB
from ..process.process_time import get_time_info
from ..process.send import send_msg
from ..process.process_plugin import process_plugin_command, process_plugin_message, upload_file_for_plugin
from ..plugin.plugin_manager import PluginManager
from utils.model_request import get_chat_response


class Application:
    def __init__(self):
        self.config: Config = Config.get_instance()
        self.message_manager: MessageManager = MessageManager()
        self.db: MongoDB = MongoDB()
        self.plugin_manager: PluginManager = PluginManager()

    async def send_message(self, msg_type: str, recipient_id: int, content: str):
        """
        发送消息
        """
        await send_msg(msg_type, recipient_id, content)

    async def get_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """
        获取聊天响应
        """
        return await get_chat_response(messages)

    def get_time_info(self) -> str:
        """
        获取时间信息
        """
        return get_time_info()

    async def process_plugin_message(self, message: Dict[str, Any]):
        """
        处理插件消息
        """
        return await process_plugin_message(message)

    async def process_plugin_command(self, command: str, msg_type: str, user_info: Dict[str, Any], 
                                     send_func: Callable, context_type: str, context_id: int):
        """
        处理插件命令
        """
        return await process_plugin_command(command, msg_type, user_info, send_func, context_type, context_id)

    async def upload_file_for_plugin(self, file_path: str, file_type: str = 'image'):
        """
        上传文件
        """
        return await upload_file_for_plugin(file_path, file_type)

    def get_user_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取用户信息
        """
        return {
            "user_id": get_user_id(event),
            "group_id": get_group_id(event) if is_group_message(event) else None,
            "username": get_username(event),
            "message_content": get_message_content(event)
        }

    def create_message_context(self, user_input: str, user_id: int, username: str, 
                               context_type: str, context_id: int) -> List[Dict[str, str]]:
        """
        创建消息上下文
        """
        return self.message_manager.create_message_context(user_input, user_id, username, context_type, context_id)

    def insert_or_replace_system_message(self, messages: List[Dict[str, str]], 
                                         new_system_message: str) -> List[Dict[str, str]]:
        """
        插入或替换系统消息
        """
        return self.message_manager.insert_or_replace_system_message(messages, new_system_message)


    # 数据库操作方法
    def insert_user_info(self, user_info: Dict[str, Any]):
        """
        插入用户信息
        """
        return self.db.insert_user_info(user_info)

    def insert_chat_message(self, user_id: int, user_input: str, response_text: str, 
                            context_type: str, context_id: str, platform: str):
        """
        插入聊天消息
        """
        return self.db.insert_chat_message(user_id, user_input, response_text, context_type, context_id, platform)

    def get_recent_messages(self, user_id: int, context_type: str, context_id: str, limit: int = 10):
        """
        获取最近的消息
        """
        return self.db.get_recent_messages(user_id, context_type, context_id, limit)

    def get_user_historical_messages(self, user_id: int, context_type: str, context_id: str, limit: int = 5):
        """
        获取用户历史消息
        """
        return self.db.get_user_historical_messages(user_id, context_type, context_id, limit)

    def clean_old_messages(self, days: int = 1, exempt_user_ids: Optional[List[int]] = None, 
                           exempt_context_ids: Optional[List[str]] = None):
        """
        清理旧消息
        """
        return self.db.clean_old_messages(days, exempt_user_ids, exempt_context_ids)

    def delete_message(self, message_id: str):
        """
        删除消息
        """
        return self.db.delete_message(message_id)

    def delete_messages(self, messages_list: List[Dict[str, Any]]):
        """
        删除消息
        """
        return self.db.delete_messages(messages_list)

    def get_message_count(self, start_time: Optional[float] = None, end_time: Optional[float] = None, 
                          user_id: Optional[int] = None, context_type: Optional[str] = None, 
                          context_id: Optional[str] = None):
        """
        获取消息数量
        """
        return self.db.get_message_count(start_time, end_time, user_id, context_type, context_id)

    def get_daily_message_count(self, days: int = 7, user_id: Optional[int] = None, 
                                context_type: Optional[str] = None, context_id: Optional[str] = None):
        """
        获取每日消息数量
        """
        return self.db.get_daily_message_count(days, user_id, context_type, context_id)
