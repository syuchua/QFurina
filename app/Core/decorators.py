import asyncio
from functools import wraps
from ..logger import logger
from ..Core.config import Config
from .filters import word_filter

config = Config.get_instance()

def error_handler(func):
    """捕获错误并记录日志的装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            错误消息 = f"函数 {func.__name__} 执行出错: {str(e)}"
            logger.error(错误消息)
            raise
    return wrapper

def rate_limit(calls: int, period: float):
    """限速装饰器"""

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
    """管理员权限检查装饰器"""

    @wraps(func)
    async def wrapper(msg_type, user_info, *args, **kwargs):
        user_id = user_info['user_id']
        logger.info(f"Checking admin status for user: {user_id}")
        
        if str(user_id) != str(config.ADMIN_ID):
            logger.warning(f"Non-admin user {user_id} attempted to use admin command")
            return "对不起，您没有执行此命令的权限。"
        logger.info(f"Admin command executed by user: {user_id}")
        return await func(msg_type, user_info, *args, **kwargs)
    return wrapper

def retry(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    
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
    """计算函数执行时间的装饰器"""
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

def filter_message(func):
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        if isinstance(message, dict):
            content = message.get('text', '')
            # 检查是否为 system_message，如果是则跳过检查
            if message.get('role') == 'system':
                return await func(message, *args, **kwargs)
        else:
            content = str(message)

        blocked_word = word_filter.contains_blocked_word(content)
        if blocked_word:
            logger.warning(f"Blocked message containing inappropriate content. Triggered word: '{blocked_word}'. Message: {content}")
            return None  # 或者返回一个特定的错误消息

        return await func(message, *args, **kwargs)

    return wrapper
