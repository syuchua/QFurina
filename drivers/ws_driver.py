import aiohttp
from app.logger import logger

class WebSocketDriver:
    def __init__(self):
        self.websocket = None

    async def connect(self):
        url = "ws://127.0.0.1:8010/ws"
        try:
            self.websocket = await aiohttp.ClientSession().ws_connect(url)
        except aiohttp.ClientError as e:
            logger.error(f"WebSocket connection error: {e}")

    async def receive_msg(self, handler):
        if not self.websocket:
            logger.error("WebSocket connection is not established.")
            return
        async for message in self.websocket:
            await handler(message.data)

    async def send_msg(self, msg_type, number, msg, use_voice=False):
        if not self.websocket:
            logger.error("WebSocket connection is not established.")
            return

        params = {
            'message': msg,
            **({'group_id': number} if msg_type == 'group' else {'user_id': number})
        }

        try:
            await self.websocket.send_str(params)
        except aiohttp.ClientError as e:
            logger.error(f"WebSocket error occurred: {e}")

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")
        else:
            logger.warning("Trying to close a non-existent WebSocket connection")
