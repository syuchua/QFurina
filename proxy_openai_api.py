# openai.py
import json
from openai import OpenAI

# 读取配置文件
with open('config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)

# 从配置文件中读取OpenAI API密钥和反代URL
OPENAI_API_KEY = config['openai_api_key']
PROXY_API_BASE = config.get('proxy_api_base', 'https://api.openai.com/v1')
MODEL = config['model']

# 初始化 OpenAI 客户端
client = OpenAI(api_key=OPENAI_API_KEY, base_url=PROXY_API_BASE)

def get_chat_response(messages):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
            top_p=0.95,
            presence_penalty=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Error during OpenAI API request: {e}")

def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        raise Exception(f"Error during DALL·E API request: {e}")