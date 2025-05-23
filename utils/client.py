# client.py

from functools import wraps
from utils.cqimage import get_cq_image_base64, decode_cq_code
from app.logger import logger
import aiohttp, json, os, ssl
from app.Core.config import config
from app.Core.decorators import async_timed, error_handler, rate_limit, retry



class ModelClient:
    def __init__(self, api_key, base_url, timeout=120):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

        # 创建自定义的 SSL 上下文，禁用 SSL 证书验证
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def request(self, endpoint, payload):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            async with session.post(f"{self.base_url}/{endpoint}", json=payload, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return await response.json()
                elif 'text/plain' in content_type:
                    return await response.text()
                else:
                    raise ValueError(f"Unexpected content type: {content_type}")

class OpenAIClient(ModelClient):
    @error_handler
    @retry(max_retries=3, delay=1.0)
    #@rate_limit(calls=10, period=60) # 限速装饰器，每分钟10条
    async def chat_completion(self, model, messages, **kwargs):
        payload = {
            'model': model,
            'messages': messages
        }
        payload.update(kwargs)
        return await self.request('chat/completions', payload)

    @error_handler
    @async_timed()
    async def image_generation(self, model, prompt, **kwargs):
        payload = {
            'model': model,
            'prompt': prompt,
            'max_tokens': 1024
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

# 单例装饰器: 用于确保在多线程环境中只有一个实例
def singleton(func):
    instances = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        if func not in instances:
            instances[func] = func(*args, **kwargs)
        return instances[func]
    return wrapper

@singleton
def get_client(default_config, model_config):
    """获取大模型请求实例"""
    
    model_name = config.MODEL_NAME
    supports_image_recognition = model_config.get('vision', False) 

    if model_name:
        for model_key, settings in model_config.get('models', {}).items():
            if model_name in settings.get('available_models', []):
                api_key = settings['api_key']
                base_url = settings['base_url']
                timeout = settings.get('timeout', 120)
                client = OpenAIClient(api_key, base_url, timeout)
                logger.debug(f"Using model '{model_name}' with base_url: {base_url}")
                return client, supports_image_recognition
        logger.warning(f"Model '{model_name}' not found in available models. Using default config.json settings.")
    else:
        logger.warning(f"Model is not specified in model.json. Using default config.json settings.")
    
    # 使用默认配置
    api_key = default_config.get('api_key')
    base_url = default_config.get('base_url', 'https://api.openai.com/v1') 
    timeout = 120
    client = OpenAIClient(api_key, base_url, timeout) 
    logger.info(f"Using default settings with base_url: {base_url}")
    # 如果使用默认配置，仍然检查模型名称是否以 "gpt-4" 开头
    if not supports_image_recognition:
        supports_image_recognition = default_config.get("model", "").startswith("gpt-4")
    return client, supports_image_recognition


async def generate_image(prompt):
    """
    使用DALL-E 2模型生成图像。
    
    参数:
    prompt (str): 用于生成图像的文本描述。
    
    返回:
    str: 生成图像的URL。
    
    异常:
    Exception: 如果图像生成过程中出现错误。
    """
    try:
        response = await client.image_generation(
            model="dalle-2",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response['data'][0]['url']
    except Exception as e:
        raise Exception(f"图像生成API请求过程中出现错误: {e}")

async def recognize_image(cq_code):
    """
    识别CQ码中的图像内容。

    参数:
    cq_code (str): 包含图像信息的CQ码。

    返回:
    str: 图像识别的结果文本。

    异常:
    Exception: 如果API不支持图像识别或识别过程中出现错误。
    """
    # 检查是否支持图像识别
    if not supports_image_recognition:
        raise Exception("API does not support image recognition.")
        
    try:
        # 从CQ码中提取图片base64编码
        image_data = await get_cq_image_base64(cq_code)
        if not image_data:
            raise ValueError("Failed to get image data from CQ code.")
        
        logger.info(f"Sending image for recognition")
        
        # 准备请求，直接传递图像数据
        messages = f"识别图片并用中文回复，图片base64编码:{image_data}"
        
        # 使用支持图像识别的API请求
        from .model_request import get_chat_response
        response_text = await get_chat_response(messages)
        
        return response_text
    except Exception as e:
        logger.error(f"Error during image recognition: {e}")
        return "图像识别时出现错误，请稍后重试。"
    
default_config, model_config = load_config()
client, supports_image_recognition = get_client(default_config, model_config)
