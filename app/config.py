import json

# 定义配置文件的路径
CONFIG_FILE_PATH = 'config.json'

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
REPLY_PROBABILITY = config_data.get('reply_probability', 0.5)

# 打印配置以验证加载正确
if __name__ == '__main__':
    print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
    print(f"MODEL: {MODEL}")
    print(f"NICKNAMES: {NICKNAMES}")
    print(f"SELF_ID: {SELF_ID}")
    print(f"ADMIN_ID: {ADMIN_ID}")
    print(f"REPORT_SECRET: {REPORT_SECRET}")
    print(f"PROXY_API_BASE: {PROXY_API_BASE}")
    print(f"SYSTEM_MESSAGE: {SYSTEM_MESSAGE}")
    print(f"REPLY_PROBABILITY: {REPLY_PROBABILITY}")