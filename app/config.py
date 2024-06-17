import json

# 定义配置文件的路径
CONFIG_FILE_PATH = 'config/config.json'

# 加载配置文件
with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as config_file:
    config_data = json.load(config_file)

# 提取配置信息
OPENAI_API_KEY = config_data.get('openai_api_key')
MODEL = config_data.get('model')
NICKNAMES = config_data.get('nicknames', [])
SELF_ID = config_data.get('self_id')
ADMIN_ID = config_data.get('admin_id')
REPORT_SECRET = config_data.get('report_secret')
PROXY_API_BASE = config_data.get('proxy_api_base')
SYSTEM_MESSAGE = config_data.get('system_message', {})
REPLY_PROBABILITY = config_data.get('reply_probability', 1.0)
AUDIO_SAVE_PATH = config_data.get("audio_save_path")
VOICE_SERVICE_URL = config_data.get("voice_service_url")
CHA_NAME = config_data.get("cha_name")
