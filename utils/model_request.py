import json
import logging
import os
import requests


class OpenAIClient:
    def __init__(self, api_key, base_url, timeout=120):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def chat_completion(self, model, messages, **kwargs):
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
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def image_generation(self, model, prompt, **kwargs):
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

        response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

# 读取配置文件
def load_config():
    config_dir = os.path.join(os.path.dirname(__file__), '../config')
    
    with open(os.path.join(config_dir, 'config.json'), 'r', encoding='utf-8') as config_file:
        default_config = json.load(config_file)
    
    with open(os.path.join(config_dir, 'model.json'), 'r', encoding='utf-8') as model_file:
        model_config = json.load(model_file)
    
    return default_config, model_config

def get_client(default_config, model_config):
    # 检查 model 是否为空
    model_name = model_config.get('model')
    if not model_name:
        logging.warning(f"Model is not specified in model.json. Using default config.json settings.")
        model_name = default_config.get('model', 'gpt-3.5-turbo')

    # 根据 model 确定使用的模型配置
    for model_key, settings in model_config['models'].items():
        if model_name in settings.get('available_models', []):
            api_key = settings['api_key']
            base_url = settings['base_url']
            timeout = settings['timeout']
            return OpenAIClient(api_key, base_url, timeout)
    
    # 如果没有找到匹配的模型，则使用默认配置
    logging.warning(f"Model '{model_name}' not found in available models. Using default config.json settings.")
    api_key = default_config.get('openai_api_key')
    base_url = default_config.get('proxy_api_base', 'https://api.openai.com/v1')
    timeout = 120
    return OpenAIClient(api_key, base_url, timeout)


default_config, model_config = load_config()
client = get_client(default_config, model_config)

def get_chat_response(messages):
    system_message = model_config.get('system_message', {}).get('character', '') or default_config.get('system_message', {}).get('character', '')
    if system_message:
        messages.insert(0, {"role": "system", "content": system_message})

    try:
        response = client.chat_completion(
            model=model_config.get('model') or default_config.get('model', 'gpt-3.5-turbo'),
            messages=messages,
            max_tokens=1000,
            top_p=0.95,
            presence_penalty=0
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise Exception(f"Error during OpenAI API request: {e}")

def generate_image(prompt):
    try:
        response = client.image_generation(
            model="dall-e-2",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response['data'][0]['url']
    except Exception as e:
        raise Exception(f"Error during DALL·E API request: {e}")
