import aiohttp
from app.logger import logger

class HttpDriver:
    async def connect(self):
        pass  # HTTP 不需要专门的连接方法

    async def receive_msg(self, handler):
        pass  # HTTP 不需要这个方法

    async def send_msg(self, msg_type, number, msg, use_voice=False):
        params = {
            'message': msg,
            **({'group_id': number} if msg_type == 'group' else {'user_id': number})
        }
        url = f"http://127.0.0.1:3000/send_{msg_type}_msg"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as res:
                    res.raise_for_status()
                    try:
                        logger.info(f"\nsend_{msg_type}_msg: {msg}\n", await res.json())
                    except aiohttp.ClientResponseError:
                        logger.info(f"\nsend_{msg_type}_msg: {msg}\n", await res.text())
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error occurred: {e}")

    async def close(self):
        pass  # HTTP 不需要专门的关闭方法
