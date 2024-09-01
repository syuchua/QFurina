# send.py
import asyncio, aiohttp, os
from ..Core.ws_decorators import select_connection_method
from ..Core.decorators import error_handler, rate_limit
from utils.voice_service import generate_voice
from ..logger import logger
from ..Core.config import config
from ..process.split_message import split_message

# 超时重试装饰器
def retry_on_timeout(retries=1, timeout=10):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on attempt {attempt + 1}/{retries}. Retrying...")
                    await asyncio.sleep(timeout)
            raise asyncio.TimeoutError("Max retries reached")
        return wrapper
    return decorator

@retry_on_timeout(retries=3, timeout=10)
async def send_http_request(url, json):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=json) as res:
            res.raise_for_status()
            response = await res.json()
            return response


@select_connection_method
@error_handler
#@rate_limit(calls=10, period=60) # 限速装饰器，每分钟10条
async def send_msg(msg_type, number, msg, use_voice=False, is_error_message=False): # 使用限速器
    if use_voice:
        is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'
        try:
            audio_filename = await generate_voice(msg)
            if audio_filename:
                msg = f"[CQ:record,file=http://my_qbot:4321/data/voice/{audio_filename}]" if is_docker else f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"
        except asyncio.TimeoutError:
            msg = "语音合成超时，请稍后再试。"

    # 使用消息截断器
    message_parts = split_message(msg)
    for part in message_parts:
        params = {
            'message': part,
            **({'group_id': number} if msg_type == 'group' else {'user_id': number})
        }

    # params = {
    #     'message': msg,
    #     **({'group_id': number} if msg_type == 'group' else {'user_id': number})
    # }
        if config.CONNECTION_TYPE == 'http':
            url = f"http://127.0.0.1:3000/send_{msg_type}_msg"
            try:
                response = await send_http_request(url, params)
                if 'status' in response and response['status'] == 'failed':
                    error_msg = response.get('message', response.get('wording', 'Unknown error'))
                    logger.error(f"Failed to send {msg_type} message: {error_msg}")
                    if not is_error_message:
                        await send_msg(msg_type, number, f"发送消息失败: {error_msg}", is_error_message=True)
                else:
                    logger.info(f"\nsend_{msg_type}_msg: {msg}\n")
                    logger.debug(f"API response: {response}")
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    logger.error(f"Resource not found: {e}")
                    await send_msg(msg_type, number, "资源未找到 (404 错误)。", is_error_message=True)
                else:
                    logger.error(f"HTTP error occurred: {e}")
                    await send_msg(msg_type, number, f"HTTP 错误: {e}", is_error_message=True)
            except asyncio.TimeoutError:
                logger.error("Request timed out after retries")
                await send_msg(msg_type, number, "请求超时，请稍后再试。", is_error_message=True)
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error occurred: {e}")
                await send_msg(msg_type, number, f"HTTP 错误: {e}", is_error_message=True)

        await asyncio.sleep(0.3) # 等待0.3秒,防止发送过快