import json
from app.logger import logger
import os
import aiohttp
from app.config import Config
from utils.cqimage import decode_cq_code

config = Config.get_instance()

class ModelClient:
    def __init__(self, api_key, base_url, timeout=120):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    async def request(self, endpoint, payload):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/{endpoint}", json=payload, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                return await response.json()

class OpenAIClient(ModelClient):
    async def chat_completion(self, model, messages, **kwargs):
        payload = {
            'model': model,
            'messages': messages
        }
        payload.update(kwargs)
        return await self.request('chat/completions', payload)

    async def image_generation(self, model, prompt, **kwargs):
        payload = {
            'model': model,
            'prompt': prompt
        }
        payload.update(kwargs)
        return await self.request('images/generate', payload)

# 读取配置文件
def load_config():
    config_dir = os.path.join(os.path.dirname(__file__), '../config')
    
    with open(os.path.join(config_dir, 'config.json'), 'r', encoding='utf-8') as config_file:
        default_config = json.load(config_file)
    
    with open(os.path.join(config_dir, 'model.json'), 'r', encoding='utf-8') as model_file:
        model_config = json.load(model_file)
    
    return default_config, model_config

def get_client(default_config, model_config):
    global supports_image_recognition
    model_name = config.MODEL_NAME

    if model_name:  # 如果 model.json 中指定了 model
        for model_key, settings in model_config.get('models', {}).items():
            if model_name in settings.get('available_models', []):
                api_key = settings['api_key']
                base_url = settings['base_url']
                timeout = settings.get('timeout', 120)  # 使用模型配置中的 timeout，默认为 120
                client = OpenAIClient(api_key, base_url, timeout)
                logger.info(f"Using model '{model_name}' with base_url: {base_url}")
                # 检查是否支持图像识别
                supports_image_recognition = settings.get('vision', False)
                return client
        # 如果指定的 model 没有找到可用模型
        logger.warning(f"Model '{model_name}' not found in available models. Using default config.json settings.")
        supports_image_recognition = False

    else:
        logger.warning(f"Model is not specified in model.json. Using default config.json settings.")
        supports_image_recognition = False
    
    # 使用默认配置
    api_key = default_config.get('openai_api_key')
    base_url = default_config.get('proxy_api_base', 'https://api.openai.com/v1') 
    timeout = 120
    client = OpenAIClient(api_key, base_url, timeout)
    logger.info(f"Using default settings with base_url: {base_url}")
    supports_image_recognition = True if default_config.get("model", "").startswith("gpt-4") else False
    return client

# 确保只调用一次
if 'client' not in globals():
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
            model="glm-4",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response['data'][0]['url']
    except Exception as e:
        raise Exception(f"Error during DALL·E API request: {e}")

async def recognize_image(cq_code):
    # 检查是否支持图像识别
    if not supports_image_recognition:
        raise Exception("API does not support image recognition.")
        
    try:
        # 解析CQ码中的图像URL
        image_url = decode_cq_code(cq_code)
        if not image_url:
            raise ValueError("No valid image URL found in CQ code")
        
        # 准备消息
        message_content = f"识别图片：图像URL:{image_url}"
        logger.info(f"Sending image for recognition: {message_content}")
        messages = [{"role": "user", "content": message_content}]
        
        # 使用 get_chat_response 函数获取聊天响应
        response_text = await get_chat_response(messages)
        
        return response_text
    except Exception as e:
        raise Exception(f"Error during image recognition: {e}")
