import os
import time
import random
import aiofiles
import aiohttp
import requests
from app.logger import logger
from app.config import Config

# 获取配置实例
config = Config.get_instance()

async def generate_voice(text, cha_name=None):
    if cha_name is None:
        cha_name = config.CHA_NAME

    tts_data = {
        "cha_name": cha_name,
        "text": text.replace("...", "…").replace("…", ","),
        "character_emotion": random.choice(['default', '平常的', '慢速病娇', '傻白甜', '平静的', '疯批', '聊天'])
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=config.VOICE_SERVICE_URL, json=tts_data) as response:
                response.raise_for_status()
                content = await response.read()
    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP error occurred: {e.status} - {e.message}")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Request exception occurred: {e}")
        return None

    filename = '%stts%d.wav' % (time.strftime('%F') + '-' + time.strftime('%T').replace(':', '-'), random.randrange(10000, 99999))
    file_path = os.path.join(config.AUDIO_SAVE_PATH, filename)

    try:
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(content)
        logger.info("语音文件生成成功")
    except IOError as e:
        logger.error(f"IO error occurred while writing file {file_path}: {e}")
        return None

    return filename
