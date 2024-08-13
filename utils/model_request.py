# model_requuest.py
import json
from app.logger import logger
import aiohttp
from utils.common import model_config, default_config, client

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
        # 处理响应
        if isinstance(response, str):
            # 如果响应是字符串，尝试解析 JSON
            try:
                response_json = json.loads(response)
            except json.JSONDecodeError:
                # 如果不是 JSON，直接返回字符串
                return response.strip()
        elif isinstance(response, dict):
            response_json = response
        else:
            logger.error(f"Unexpected response type: {type(response)}")
            raise Exception("API 返回了意外的响应类型")

        # 处理解析后的 JSON
        if 'choices' in response_json and len(response_json['choices']) > 0:
            content = response_json['choices'][0]['message']['content']
            # 检查是否包含错误信息
            if "error" in content.lower():
                logger.error(f"API returned an error: {content}")
                raise Exception(f"API 返回错误: {content}")
            return content.strip()
        else:
            # 如果响应不符合预期格式，但是是一个字符串，直接返回
            if isinstance(response, str):
                return response.strip()
            logger.error(f"Unexpected response format: {response_json}")
            raise Exception("API 返回了意外的响应格式")

    except aiohttp.ClientConnectorError as e:
        logger.error(f"Network connection error during API request: {e}")
        raise Exception(f"网络连接错误，请检查网络状态后重试: {e}")
    except Exception as e:
        logger.error(f"Error during API request: {e}")
        raise Exception(f"API 请求出错: {e}")