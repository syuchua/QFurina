from app.driver import driver_instance
from app.config import Config
from app.logger import logger
import aiohttp
import asyncio
from functools import wraps

config = Config.get_instance()



def select_connection_method(func):
    @wraps(func)
    async def wrapper(msg_type, number, msg, use_voice=False, *args, **kwargs):
        # logger.info(f"\nPreparing to send {msg_type} message: {msg}\n")

        if config.CONNECTION_TYPE == 'http':
            return await func(msg_type, number, msg, use_voice, *args, **kwargs)
        elif config.CONNECTION_TYPE == 'ws_reverse':
            try:
                response = await driver_instance.send_msg(msg_type, number, msg, use_voice)
                logger.debug(f"WebSocket API response: {response}")
                return response
            except Exception as e:
                logger.error(f"WebSocket error occurred: {e}")
                return await func(msg_type, number, msg, use_voice, *args, **kwargs)  # Fallback to HTTP if WebSocket fails

    return wrapper


