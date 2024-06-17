# lolicon.py
import json
import os
import requests

API_URL = "https://api.lolicon.app/setu/v2"
config_dir = os.path.join(os.path.dirname(__file__), '../config')
    
with open(os.path.join(config_dir, 'config.json'), 'r', encoding='utf-8') as config_file:
    config_data = json.load(config_file)
R18=config_data.get("r18")
def fetch_image(keyword):
    params = {
        'r18': R18,
        'tag': keyword,
        'num': 1,
        'size': 'regular',
        'proxy': 'i.pixiv.re',
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # 检查错误信息
        if data.get('error'):
            raise Exception(f"API请求失败: {data.get('error')}")

        images = data.get('data', [])
        if images:
            image_info = images[0]
            image_url = image_info.get('urls', {}).get('regular')
            if image_url:
                return image_url
            else:
                raise Exception("没有找到相关的图片。")
        else:
            raise Exception("没有找到相关的图片。")
    
    except requests.RequestException as e:
        raise Exception(f"请求图片信息时发生网络错误: {e}")