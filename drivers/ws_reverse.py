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
        self._api_response_futures = {}

    async def start_server(self, host: str, port: int, handler: Callable):
        self._message_handler = handler
        self._server = await websockets.serve(self.websocket_handler, host, port)
        logger.info(f"WebSocket server started on ws://{host}:{port}/ws")

    async def websocket_handler(self, websocket, path):
        self._websocket = websocket
        self._connected = True
        logger.info("Client connected")
        try:
            async for message in websocket:
                #logger.info(f"Received message: {message}")
                data = json.loads(message)
                if 'echo' in data:
                    # This is an API response
                    echo = data['echo']
                    if echo in self._api_response_futures:
                        self._api_response_futures[echo].set_result(data)
                else:
                    # This is an event
                    await self._message_handler(data)
        except websockets.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed unexpectedly: {e}")
        finally:
            self._websocket = None
            self._connected = False
            logger.info("Client disconnected")

    async def call_api(self, action, **params):
        if not self._connected:
            logger.error("WebSocket connection is not established.")
            raise ConnectionError("WebSocket connection is not established")

        echo = str(id(asyncio.current_task()))
        data = {
            "action": action,
            "params": params,
            "echo": echo
        }
        future = asyncio.get_running_loop().create_future()
        self._api_response_futures[echo] = future

        try:
            await self._websocket.send(json.dumps(data))
            # logger.info(f"Sent API call: {data}")
            response = await asyncio.wait_for(future, timeout=10)
            return response
        except asyncio.TimeoutError:
            logger.error(f"API call timed out: {data}")
            raise
        finally:
            del self._api_response_futures[echo]

    async def send_msg(self, msg_type, number, msg, use_voice=False):
        if msg_type == 'private':
            response = await self.call_api('send_private_msg', user_id=number, message=msg)
        elif msg_type == 'group':
            response = await self.call_api('send_group_msg', group_id=number, message=msg)
        else:
            raise ValueError(f"Unsupported message type: {msg_type}")
        
        logger.info(f"\nsend_{msg_type}_msg: {msg}\n")
        return response

    async def close(self):
        if self._websocket and self._connected:
            try:
                await self._websocket.close()
                logger.info("\nWebSocket connection closed\n")
            except Exception as e:
                logger.error(f"\nError closing WebSocket connection: {e}\n")
        else:
            logger.warning("\nTrying to close a non-existent or already closed WebSocket connection\n")
        self._connected = False
        self._websocket = None

