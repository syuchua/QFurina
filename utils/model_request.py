import json
import logging
import os
import requests
import aiohttp
import asyncio

from app.config import Config
config = Config.get_instance()

class OpenAIClient:
    def __init__(self, api_key, base_url, timeout=120):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    async def chat_completion(self, model, messages, **kwargs):
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model,
            'messages': messages
        }
        payload.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                return await response.json()

    async def image_generation(self, model, prompt, **kwargs):
        endpoint = f"{self.base_url}/images/generate"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model,
            'prompt': prompt
        }
        payload.update(kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                return await response.json()


# 读取配置文件
def load_config():
    config_dir = os.path.join(os.path.dirname(__file__), '../config')
    
    with open(os.path.join(config_dir, 'config.json'), 'r', encoding='utf-8') as config_file:
        default_config = json.load(config_file)
    
    with open(os.path.join(config_dir, 'model.json'), 'r', encoding='utf-8') as model_file:
        model_config = json.load(model_file)
    
    return default_config, model_config

def get_client(default_config, model_config):
    model_name = config.MODEL_NAME
    base_url = None

    if model_name:  # 如果 model.json 中指定了 model
        for model_key, settings in model_config.get('models', {}).items():
            if model_name in settings.get('available_models', []):
                api_key = settings['api_key']
                base_url = settings['base_url']
                timeout = settings.get('timeout', 120)  # 使用模型配置中的 timeout，默认为 120
                client = OpenAIClient(api_key, base_url, timeout)
                logging.info(f"Using model '{model_name}' with base_url: {base_url}")
                return client
        # 如果指定的 model 没有找到可用模型
        logging.warning(f"Model '{model_name}' not found in available models. Using default config.json settings.")

    else:
        logging.warning(f"Model is not specified in model.json. Using default config.json settings.")

    # 使用默认配置
    api_key = default_config.get('openai_api_key')
    base_url = default_config.get('proxy_api_base', 'https://api.openai.com/v1')
    timeout = 120
    client = OpenAIClient(api_key, base_url, timeout)
    logging.info(f"Using default settings with base_url: {base_url}")
    return client


default_config, model_config = load_config()
client = get_client(default_config, model_config)

async def get_chat_response(messages):
    system_message = model_config.get('system_message', {}).get('character', '') or default_config.get('system_message', {}).get('character', '')
    if system_message:
        messages.insert(0, {"role": "system", "content": system_message})

    try:
        response = await client.chat_completion(
            model=model_config.get('model') or default_config.get('model', 'gpt-3.5-turbo'),
            messages=messages,
            max_tokens=1000,
            top_p=0.95,
            presence_penalty=0
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise Exception(f"Error during OpenAI API request: {e}")

async def generate_image(prompt):
    try:
        response = await client.image_generation(
            model="dall-e-2",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response['data'][0]['url']
    except Exception as e:
        raise Exception(f"Error during DALL·E API request: {e}")