# adapter/tgbot.py

import aiohttp
from typing import Optional, List, Union, Dict, Any

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"

    async def _make_request(self, method: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url + method, json=data) as response:
                return await response.json()

    async def get_me(self) -> Dict[str, Any]:
        return await self._make_request("getMe")

    async def send_message(self, chat_id: Union[int, str], text: str, 
                           parse_mode: Optional[str] = None, 
                           reply_to_message_id: Optional[int] = None) -> Dict[str, Any]:
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_to_message_id": reply_to_message_id
        }
        return await self._make_request("sendMessage", data)

    async def send_photo(self, chat_id: Union[int, str], photo: Union[str, bytes], 
                         caption: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption
        }
        return await self._make_request("sendPhoto", data)

    async def send_document(self, chat_id: Union[int, str], document: Union[str, bytes], 
                            caption: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "chat_id": chat_id,
            "document": document,
            "caption": caption
        }
        return await self._make_request("sendDocument", data)

    async def get_updates(self, offset: Optional[int] = None, 
                          limit: Optional[int] = None, 
                          timeout: Optional[int] = None) -> List[Dict[str, Any]]:
        data = {
            "offset": offset,
            "limit": limit,
            "timeout": timeout
        }
        return await self._make_request("getUpdates", data)

    async def set_webhook(self, url: str) -> Dict[str, Any]:
        data = {"url": url}
        return await self._make_request("setWebhook", data)

    # 可以继续添加其他需要的方法...

# 定义消息类型枚举（如果需要）
class MessageType:
    TEXT = "text"
    PHOTO = "photo"
    DOCUMENT = "document"
    # 可以继续添加其他消息类型...

# 定义事件类型枚举（如果需要）
class EventType:
    MESSAGE = "message"
    EDITED_MESSAGE = "edited_message"
    CALLBACK_QUERY = "callback_query"
    # 可以继续添加其他事件类型...

# 可以添加其他辅助函数或类...
