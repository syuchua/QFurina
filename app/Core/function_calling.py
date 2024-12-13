# function_calling.py
import os, re, random
from typing import Optional, List
from utils.search import get_github_repo_info, get_webpage_content, web_search
from app.logger import logger
from utils.voice_service import generate_voice
from utils.client import client, generate_image, recognize_image, model_config
from utils.lolicon import fetch_image
from ..Core.decorators import async_timed, rate_limit

is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'

async def call_function(model_name: str, endpoint: str, payload: dict) -> Optional[dict]:
    try:
        response = await client.request(endpoint, payload)
        return response
    except Exception as e:
        logger.error(f"Error calling function {endpoint} on model {model_name}: {e}")
        return None

async def handle_command_request(user_input):
    COMMAND_PATTERN = re.compile(r'^[!/](help|reset|character|history|clear|model|r18|music_list|restart|shutdown|enable_plugin|disable_plugin|list_plugins|reload_plugin|plugin|block_word)(?:\s+(.+))?')
    match = COMMAND_PATTERN.match(user_input)
    if match:
        command = match.group(1)
        command_args = match.group(2)
        full_command = f"{command} {command_args}" if command_args else command
        return full_command
    return None

import re

VOICE_PATTERN = re.compile(r"#voice\s*(.*?)[.!?]")
IMAGE_CQ_PATTERN = re.compile(r'\[CQ:image,file=(.+)\]')
RECOGNIZE_PATTERN = re.compile(r"#recognize\s*(.*)")

@rate_limit(calls=5, period=60)
async def handle_image_request(user_input):

    IMAGE_KEYWORDS = ["发一张", "来一张"]
    RANDOM_IMAGE_KEYWORDS = ["再来一张", "来份涩图", "来份色图"]
    DRAW_KEYWORDS = ["画一张", "生成一张"]

    for keyword in IMAGE_KEYWORDS:
        if keyword in user_input:
            keyword_value = user_input.split(keyword, 1)[1].strip() if keyword in user_input else ""
            image_url = await fetch_image(keyword_value)
            return image_url

    for keyword in RANDOM_IMAGE_KEYWORDS:
        if keyword in user_input:
            image_url = await fetch_image("")
            return image_url

    model_name = model_config.get('model')
    if model_name is not None and model_name.startswith("gpt"):
        for keyword in DRAW_KEYWORDS:
                if keyword in user_input:
                    prompt = user_input.replace(keyword, '').strip()
                    response = await generate_image({"prompt": prompt})
                    if response:
                        return response.get("image_url")


async def handle_voice_request(user_input):
    VOICE_KEYWORDS = ["语音回复", "用声音说", "语音说"]

    # 检查是否包含关键词
    for keyword in VOICE_KEYWORDS:
        if keyword in user_input:
            voice_text = user_input.split(keyword, 1)[1].strip()
            audio_filename = await generate_voice(voice_text)
            if audio_filename:
                return f"http://my_qbot:4321/data/voice/{audio_filename}" if is_docker else f"http://localhost:4321/data/voice/{audio_filename}"           

    voice_match = VOICE_PATTERN.search(user_input)
    if voice_match:
        voice_text = voice_match.group(1).strip()
        audio_filename = await generate_voice(voice_text)
        if audio_filename:
            return f"http://my_qbot:4321/data/voice/{audio_filename}" if is_docker else f"http://localhost:4321/data/voice/{audio_filename}"
    
    return None

async def handle_image_recognition(user_input):
    logger.debug(f"Handling image recognition: user_input={user_input}")
    match = IMAGE_CQ_PATTERN.search(user_input)
    if match:
        logger.info(f"Recognize image: {match.group(0)}")
        image_cq_code = match.group(0)
        response = await recognize_image(image_cq_code)
        if response:
            return response
    # 处理未匹配的情况
    logger.warning("No image found in user input for recognition.")
    return None

class MusicHandler:
    def __init__(self):
        self.MUSIC_DIRECTORY = os.getenv('MUSIC_DIRECTORY', 'data/music')
        self.MUSIC_FILES = [f for f in os.listdir(self.MUSIC_DIRECTORY) if f.endswith(('.mp3', '.wav'))]
        self.MUSIC_INFO = {os.path.splitext(f)[0]: f for f in self.MUSIC_FILES}

    async def handle_music_request(self, user_input:str) -> Optional[str]:
        MUSIC_KEYWORDS = ["唱一首歌", "来首歌", "来首音乐", "来一首歌", "来一首音乐"]

        for keyword in MUSIC_KEYWORDS:
            if keyword in user_input:
                music_name = random.choice(self.MUSIC_FILES)
                if music_name:
                    return f"http://my_qbot:4321/data/music/{music_name}" if is_docker else f"http://localhost:4321/data/music/{music_name}"

        # 检查是否是点歌请求
        if "点歌" in user_input:
            song_name = user_input.split("点歌", 1)[1].strip().lower()
            # 使用模糊匹配
            matched_songs = [name for name in self.MUSIC_INFO.keys() if song_name in name]
            if matched_songs:
                chosen_song = matched_songs[0]  # 选择第一个匹配的歌曲
                return f"http://my_qbot:4321/data/music/{self.MUSIC_INFO[chosen_song]}" if is_docker else f"http://localhost:4321/data/music/{self.MUSIC_INFO[chosen_song]}"
            else:
                return f"抱歉，没有找到歌曲 '{song_name}'。"

        return None

@async_timed()
async def handle_web_search(query):
    # 检查是否是 GitHub 仓库 URL
    if query.startswith("https://github.com/") and "/blob/" not in query:
        return await get_github_repo_info(query)
    
    # 原有的搜索逻辑
    search_result = await web_search(query)
    if not search_result:
        return "无法获取搜索结果。"

    # 从搜索结果中提取URL
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', search_result)

    enhanced_result = search_result + "\n\n额外内容:\n"

    for url in urls[:3]:  # 限制处理的URL数量
        content = await get_webpage_content(url)
        enhanced_result += f"\n链接: {url}\n内容摘要: {content}\n"

    return enhanced_result


music_handler = MusicHandler()