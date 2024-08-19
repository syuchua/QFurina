# function_calling.py
import os, re, random
from typing import Optional, List
from utils.city_codes import CITY_CODES
from utils.search import get_github_repo_info, get_webpage_content, web_search
from app.logger import logger
from utils.voice_service import generate_voice
from utils.client import client, generate_image, recognize_image, model_config
from utils.lolicon import fetch_image
from utils.weather import get_forecast, get_weather
from rapidfuzz import process, fuzz
from utils.BingArt import bing_art
from app.decorators import async_timed, error_handler, rate_limit

async def call_function(model_name: str, endpoint: str, payload: dict) -> Optional[dict]:
    try:
        response = await client.request(endpoint, payload)
        return response
    except Exception as e:
        logger.error(f"Error calling function {endpoint} on model {model_name}: {e}")
        return None

async def handle_command_request(user_input):
    COMMAND_PATTERN = re.compile(r'^[!/](help|reset|character|history|clear|model|r18|music_list|restart|shutdown)(?:\s+(.+))?')
    match = COMMAND_PATTERN.match(user_input)
    if match:
        command = match.group(1)
        command_args = match.group(2)
        full_command = f"{command} {command_args}" if command_args else command
        return full_command
    return None

import re

DRAW_PATTERN = re.compile(r"#draw\s*(.*?)[.!?]")
VOICE_PATTERN = re.compile(r"#voice\s*(.*?)[.!?]")
IMAGE_CQ_PATTERN = re.compile(r'\[CQ:image,file=(.+)\]')
RECOGNIZE_PATTERN = re.compile(r"#recognize\s*(.*)")

@async_timed()
@error_handler
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
    if model_name is None:
        for keyword in DRAW_KEYWORDS:
                if keyword in user_input:
                    prompt = user_input.replace(keyword, '').strip()
                    response = await generate_image({"prompt": prompt})
                    if response:
                        return response.get("image_url")

    draw_match = DRAW_PATTERN.search(user_input)
    if draw_match:
        prompt = draw_match.group(1).strip()
        if prompt:
            try:
                result = await bing_art.generate_images(prompt)
                if result['images']:
                    return result['images'][0]['url']
                else:
                    logger.warning("No images generated for prompt: {prompt}")
                    return None
            except Exception as e:
                logger.error(f"Error generating image: {str(e)}")
                return None
    
    return None

@async_timed()
@error_handler
async def handle_voice_request(user_input):
    VOICE_KEYWORDS = ["语音回复", "用声音说", "语音说"]

    # 检查是否包含关键词
    for keyword in VOICE_KEYWORDS:
        if keyword in user_input:
            voice_text = user_input.split(keyword, 1)[1].strip()
            audio_filename = await generate_voice(voice_text)
            if audio_filename:
                return f"http://localhost:4321/data/voice/{audio_filename}"           

    voice_match = VOICE_PATTERN.search(user_input)
    if voice_match:
        voice_text = voice_match.group(1).strip()
        audio_filename = await generate_voice(voice_text)
        if audio_filename:
            return f"http://localhost:4321/data/voice/{audio_filename}"
    
    return None

async def handle_image_recognition(user_input):
    match = IMAGE_CQ_PATTERN.search(user_input)
    if match:
        # logger.info(f"Recognize image: {match.group(0)}")
        image_cq_code = match.group(0)
        response = await recognize_image(image_cq_code)
        if response:
            return response
        
    recognize_match = RECOGNIZE_PATTERN.search(user_input)
    if recognize_match:
        # logger.info(f"Recognize image: {recognize_match.group(1)}")
        image_cq_code = recognize_match.group(1).strip()
        response = await recognize_image(image_cq_code)
        if response:
            return response

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
                    return f"http://localhost:4321/data/music/{music_name}"

        # 检查是否是点歌请求
        if "点歌" in user_input:
            song_name = user_input.split("点歌", 1)[1].strip().lower()
            # 使用模糊匹配
            matched_songs = [name for name in self.MUSIC_INFO.keys() if song_name in name]
            if matched_songs:
                chosen_song = matched_songs[0]  # 选择第一个匹配的歌曲
                return f"http://localhost:4321/data/music/{self.MUSIC_INFO[chosen_song]}"
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


class WeatherHandler:
    @staticmethod
    async def handle_request(user_input: str) -> Optional[str]:
        WEATHER_KEYWORDS = ['天气', '气温', '温度', '下雨', '阴天', '晴天', '多云', '预报']
        
        if any(keyword in user_input for keyword in WEATHER_KEYWORDS):
            city = WeatherHandler.extract_city(user_input)
            if not city:
                return "抱歉，我没有识别出您想查询的城市。请直接提供城市名，例如'北京天气'。"

            try:
                current_weather = await get_weather(city)
                forecast = await get_forecast(city)
                return f"{current_weather}\n\n{forecast}"
            except Exception as e:
                logger.error(f"Error in handle_weather_request: {e}", exc_info=True)
                return f"获取{city}的天气信息时发生错误，请稍后再试。"

        return None

    @staticmethod
    def extract_city(text: str) -> Optional[str]:
        WEATHER_KEYWORDS = ['天气', '气温', '温度', '下雨', '阴天', '晴天', '多云', '预报']
        
        logger.debug(f"Extracting city from: {text}")
        
        # 去除常见的无关词
        for keyword in WEATHER_KEYWORDS:
            text = text.replace(keyword, '')
        
        logger.debug(f"Text after removing keywords: {text}")
        
        try:
            # 使用模糊匹配找到最可能的城市名
            result = process.extractOne(text, CITY_CODES.keys(), scorer=fuzz.partial_ratio)
            
            logger.debug(f"Fuzzy matching result: {result}")
            
            if result and len(result) >= 2:
                city, score = result[0], result[1]
                logger.debug(f"Extracted city: {city}, match score: {score}")
                
                # 如果匹配度低于某个阈值，认为没有找到有效的城市名
                if score < 60:
                    logger.info(f"No valid city name found. Best match was '{city}' with score {score}")
                    return None
                
                return city
            else:
                logger.info("No city match found")
                return None
        except Exception as e:
            logger.error(f"Error in extract_city: {e}", exc_info=True)
            return None

music_handler = MusicHandler()
weather_handler = WeatherHandler()