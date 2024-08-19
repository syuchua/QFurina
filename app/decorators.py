import asyncio
from functools import wraps
from app.logger import logger
from app.config import Config

config = Config.get_instance()

def error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行出错: {str(e)}")
            # 这里可以添加错误通知逻辑，比如发送邮件或推送消息
            raise
    return wrapper

def rate_limit(calls: int, period: float):
    semaphore = asyncio.Semaphore(calls)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                result = await func(*args, **kwargs)
                await asyncio.sleep(period / calls)
                return result
        return wrapper
    return decorator

def admin_only(func):
    @wraps(func)
    async def wrapper(msg_type, user_id, *args, **kwargs):
        if user_id != config.ADMIN_ID:
            return "对不起，您没有执行此命令的权限。"
        return await func(msg_type, user_id, *args, **kwargs)
    return wrapper

def retry(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"函数 {func.__name__} 在 {max_retries} 次尝试后仍然失败: {str(e)}")
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
        return wrapper
    return decorator

def async_timed():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = asyncio.get_event_loop().time()
            result = await func(*args, **kwargs)
            end = asyncio.get_event_loop().time()
            logger.debug(f"函数 {func.__name__} 执行时间: {end - start:.2f} 秒")
            return result
        return wrapper
    return decorator
