# lolicon.py
import json
import os
import aiohttp
import requests

from app.Core.config import Config
config = Config.get_instance()

API_URL = "https://api.lolicon.app/setu/v2"

async def fetch_image(keyword: str) -> str:
    params = {
        'r18': config.R18,
        'tag': keyword, 
        'num': 1,
        'size': 'regular',
        'proxy': 'i.pixiv.re',
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()

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
    
    except aiohttp.ClientError as e:
        raise Exception(f"请求图片信息时发生网络错误: {e}")