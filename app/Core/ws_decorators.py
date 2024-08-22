from ..Core.driver import driver_instance as ws_driver
from ..Core.config import Config
from app.logger import logger
import aiohttp
import asyncio
from functools import wraps
from ..Core.decorators import async_timed

config = Config.get_instance()


def select_connection_method(func):
    @wraps(func)
    @async_timed()
    async def wrapper(msg_type, number, msg, use_voice=False, *args, **kwargs):
        # logger.info(f"\nPreparing to send {msg_type} message: {msg}\n")

        if config.CONNECTION_TYPE == 'http':
            return await func(msg_type, number, msg, use_voice, *args, **kwargs)
        elif config.CONNECTION_TYPE == 'ws_reverse':
            try:
                response = await ws_driver.send_msg(msg_type, number, msg, use_voice)
                logger.info(f"\nsend_{msg_type}_msg: {msg}\n")
                logger.debug(f"WebSocket API response: {response}")
                return response
            except Exception as e:
                logger.error(f"WebSocket error occurred: {e}")
                if isinstance(e, asyncio.TimeoutError):
                    error_msg = "阿巴阿巴，出错了。"
                elif isinstance(e, aiohttp.ClientConnectorError):
                    error_msg = "阿巴阿巴，出错了。"
                elif hasattr(e, 'status') and e.status == 404:
                    error_msg = "资源未找到 (404 错误)。"
                elif hasattr(e, 'status') and e.status == 429:
                    error_msg = "阿巴阿巴，出错了。"
                
                try:
                    await ws_driver.send_msg(msg_type, number, error_msg)
                except Exception:
                    logger.error("Failed to send error message via WebSocket")
                
                return None  # 或者你可以选择抛出异常

    return wrapper


