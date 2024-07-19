# app/decorators.py

from app.driver import driver_instance
from app.config import Config
from app.logger import logger
import aiohttp
import asyncio

config = Config.get_instance()

def select_connection_method(func):
    async def wrapper(*args, **kwargs):
        msg_type = kwargs.get('msg_type')
        number = kwargs.get('number')
        msg = kwargs.get('msg')
        use_voice = kwargs.get('use_voice', False)

        if config.CONNECTION_TYPE == 'http':
            await func(*args, **kwargs)
        elif config.CONNECTION_TYPE == 'ws_reverse':
            try:
                await driver_instance.send_msg(msg_type, number, msg, use_voice)
            except Exception as e:
                logger.error(f"WebSocket error occurred: {e}")
                await func(*args, **kwargs)  # Fallback to HTTP if WebSocket fails

    return wrapper
