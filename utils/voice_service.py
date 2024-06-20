import os
import time
import random
import requests
import logging
from app.config import Config

# 获取配置实例
config = Config.get_instance()

def generate_voice(text, cha_name=None):
    if cha_name is None:
        cha_name = config.CHA_NAME
    
    tts_data = {
        "cha_name": cha_name,
        "text": text.replace("...", "…").replace("…", ","),
        "character_emotion": random.choice(['default', '平常的', '慢速病娇', '傻白甜', '平静的', '疯批', '聊天'])
    }
    
    try:
        response = requests.post(url=config.VOICE_SERVICE_URL, json=tts_data)
        response.raise_for_status()  # 确保请求成功
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception occurred: {e}")
        return None

    filename = '%stts%d.wav' % (time.strftime('%F') + '-' + time.strftime('%T').replace(':', '-'), random.randrange(10000, 99999))
    file_path = os.path.join(config.AUDIO_SAVE_PATH, filename)
    
    try:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print("语音文件生成成功")
    except IOError as e:
        logging.error(f"IO error occurred while writing file {file_path}: {e}")
        return None

    return filename