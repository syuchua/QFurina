# model_requuest.py
import base64
import json
import httpx
from app.logger import logger
import os
import aiohttp
from utils.common import model_config, default_config, client
from app.function_calling import get_current_time, get_lunar_date_info

# 从配置文件中读取默认配置和模型配置
async def get_chat_response(messages):
    system_message = model_config.get('system_message', {}).get('character', '') or default_config.get('system_message', {}).get('character', '')

    if system_message:
        messages.insert(0, {"role": "system", "content": system_message})

    try:
        response = await client.chat_completion(
            model=model_config.get('model') or default_config.get('model', 'gpt-3.5-turbo'),
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
            top_p=0.95,
            stream=False,
            stop=None,
            presence_penalty=0
        )
        return response['choices'][0]['message']['content'].strip()
    except aiohttp.ClientConnectorError as e:
        logger.error(f"Network connection error during API request: {e}")
        raise Exception(f"网络连接错误，请检查网络状态后重试: {e}")
    except Exception as e:
        logger.error(f"Error during API request: {e}")
        raise Exception(f"API 请求出错: {e}")

