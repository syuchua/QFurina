import asyncio
import json
import websockets
from app.logger import logger
from typing import Callable

class WsReverseDriver:
    def __init__(self):
        self._websocket = None
        self._server = None
        self._connected = False
        self._message_handler = None

    async def start_server(self, host: str, port: int, handler: Callable):
        self._message_handler = handler
        self._server = await websockets.serve(self.websocket_handler, host, port, subprotocols=["ws"])
        logger.info(f"WebSocket server started on ws://{host}:{port}/ws")

    async def websocket_handler(self, websocket, path):
        self._websocket = websocket
        self._connected = True
        logger.info("Client connected")
        try:
            async for message in websocket:
                if self._message_handler:
                    await self._message_handler(json.loads(message))
        except websockets.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed unexpectedly: {e}")
        finally:
            self._websocket = None
            self._connected = False
            logger.info("Client disconnected")

    async def send_msg(self, msg_type, number, msg, use_voice=False):
        if not self._connected:
            logger.error("WebSocket connection is not established.")
            return

        params = json.dumps( {
            'message': msg,
            **({'group_id': number} if msg_type == 'group' else {'user_id': number})
        })

        try:
            await self._websocket.send(params)
            logger.info(f"Send message: {params}")
        except websockets.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed unexpectedly: {e}")

    async def close(self):
        if self._websocket and self._connected:
            await self._websocket.close()
            logger.info("WebSocket connection closed")
        else:
            logger.warning("Trying to close a non-existent or already closed WebSocket connection")
