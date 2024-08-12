# function_calling.py
import os
import random
from datetime import datetime, timedelta
import aiohttp
import pytz
from zhdate import ZhDate
from utils.BingArt import bing_art
from app.logger import logger
import re
from utils.voice_service import generate_voice
from utils.common import model_config, default_config, get_client, generate_image, recognize_image
from utils.lolicon import fetch_image

MUSIC_DIRECTORY = 'data/music'
MUSIC_FILES = [f for f in os.listdir(MUSIC_DIRECTORY) if f.endswith(('.mp3', '.wav'))]
MUSIC_INFO = {os.path.splitext(f)[0]: f for f in MUSIC_FILES}

client = get_client(default_config, model_config)


async def call_function(model_name, endpoint, payload):
    try:
        response = await client.request(endpoint, payload)
        return response
    except Exception as e:
        logger.error(f"Error calling function {endpoint} on model {model_name}: {e}")
        return None

async def handle_command_request(user_input):
    COMMAND_PATTERN = re.compile(r'^[!/](help|reset|character|history|clear|model|r18|music_list)(?:\s+(.+))?')
    match = COMMAND_PATTERN.match(user_input)
    if match:
        command = match.group(1)
        command_args = match.group(2)
        full_command = f"{command} {command_args}" if command_args else command
        return full_command
    return None

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

    """
    StableDiffusion是一款利用深度学习的文生图模型，支持通过使用提示词来产生新的图像，描述要包含或省略的元素。
    我在这里引入StableDiffusion算法中的Prompt概念，又被称为提示符。
    下面的prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，如人物的外观、背景、颜色和光线效果，以及图像的主题和风格。这些prompt的格式经常包含括号内的加权数字，用于指定某些细节的重要性或强调。例如，"(masterpiece:1.5)"表示作品质量是非常重要的，多个括号也有类似作用。此外，如果使用中括号，如"{blue hair:white hair:0.3}"，这代表将蓝发和白发加以融合，蓝发占比为0.3。
    以下是用prompt帮助AI模型生成图像的例子：masterpiece,(bestquality),highlydetailed,ultra-detailed,cold,solo,(1girl),(detailedeyes),(shinegoldeneyes),(longliverhair),expressionless,(long sleeves),(puffy sleeves),(white wings),shinehalo,(heavymetal:1.2),(metaljewelry),cross-lacedfootwear (chain),(Whitedoves:1.2)

    仿照例子，给出一套详细描述以下内容的prompt。直接开始给出prompt不需要用自然语言描述
    """
    draw_pattern = re.compile(r"#draw\s*(.*?)[.!?]")
    draw_match = draw_pattern.search(user_input)
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


async def handle_voice_request(user_input):
    VOICE_KEYWORDS = ["语音回复", "用声音说", "语音说"]

    # 检查是否包含关键词
    for keyword in VOICE_KEYWORDS:
        if keyword in user_input:
            voice_text = user_input.split(keyword, 1)[1].strip()
            audio_filename = await generate_voice(voice_text)
            if audio_filename:
                return f"http://localhost:4321/data/voice/{audio_filename}"           

    # 检查是否包含 #voice 标签
    voice_pattern = re.compile(r"#voice\s*(.*?)[.!?]")
    voice_match = voice_pattern.search(user_input)
    if voice_match:
        voice_text = voice_match.group(1).strip()
        audio_filename = await generate_voice(voice_text)
        if audio_filename:
            return f"http://localhost:4321/data/voice/{audio_filename}"
    
    return None

async def handle_image_recognition(user_input):
    IMAGE_CQ_PATTERN = r'\[CQ:image,file=(.+)\]'
    match = re.search(IMAGE_CQ_PATTERN, user_input)
    if match:
        # logger.info(f"Recognize image: {match.group(0)}")
        image_cq_code = match.group(0)
        response = await recognize_image(image_cq_code)
        if response:
            return response
        
    recognize_pattern = re.compile(r"#recognize\s*(.*)")
    recognize_match = recognize_pattern.search(user_input)
    if recognize_match:
        # logger.info(f"Recognize image: {recognize_match.group(1)}")
        image_cq_code = recognize_match.group(1).strip()
        response = await recognize_image(image_cq_code)
        if response:
            return response

    return None

async def handle_music_request(user_input):
    MUSIC_KEYWORDS = ["唱一首歌", "来首歌", "来首音乐", "来一首歌", "来一首音乐"]

    for keyword in MUSIC_KEYWORDS:
        if keyword in user_input:
            music_name = random.choice(MUSIC_FILES)
            if music_name:
                return f"http://localhost:4321/data/music/{music_name}"

    # 检查是否是点歌请求
    if "点歌" in user_input:
        song_name = user_input.split("点歌", 1)[1].strip().lower()
        # 使用模糊匹配
        matched_songs = [name for name in MUSIC_INFO.keys() if song_name in name]
        if matched_songs:
            chosen_song = matched_songs[0]  # 选择第一个匹配的歌曲
            return f"http://localhost:4321/data/music/{MUSIC_INFO[chosen_song]}"
        else:
            return f"抱歉，没有找到歌曲 '{song_name}'。"

    return None


async def web_search(query):
    """
    异步搜索网络并返回结果。
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://api.openinterpreter.com/v0/browser/search',
            params={"query": query}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["result"]
            else:
                return f"搜索失败，状态码：{response.status}"

def get_current_time():
    # 设置时区为中国标准时间
    china_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(china_tz)
    
    # 格式化时间字符串
    time_str = current_time.strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 获取星期几
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][current_time.weekday()]
    
    # 判断时间段
    hour = current_time.hour
    if 5 <= hour < 12:
        period = "早上"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 22:
        period = "晚上"
    else:
        period = "深夜"
    
    return {
        "full_time": time_str,
        "weekday": weekday,
        "period": period,
        "hour": hour,
        "minute": current_time.minute
    }

def get_lunar_date_info():
    today = datetime.now()
    lunar_date = ZhDate.from_datetime(today)
    zodiac = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"][(lunar_date.lunar_year - 1900) % 12]
    
    # 简单的节日判断，可以根据需要扩展
    festivals = {
        (1, 1): "春节",
        (5, 5): "端午节",
        (7, 7): "七夕节",
        (8, 15): "中秋节",
        (9, 9): "重阳节"
    }
    festival = festivals.get((lunar_date.lunar_month, lunar_date.lunar_day), "")
    
    return {
        "lunar_date": f"{lunar_date.lunar_year}年{lunar_date.lunar_month}月{lunar_date.lunar_day}日",
        "zodiac": zodiac,
        "festival": festival
    }

def get_solar_festival(date):
    solar_festivals = {
        (1, 1): "元旦",
        (2, 14): "情人节",
        (3, 8): "妇女节",
        (4, 1): "愚人节",
        (5, 1): "劳动节",
        (6, 1): "儿童节",
        (10, 1): "国庆节",
        (12, 25): "圣诞节",
        # 可以根据需要添加更多节日
    }
    return solar_festivals.get((date.month, date.day), "")

def get_current_time_with_lunar():
    current_time = get_current_time()
    lunar_info = get_lunar_date_info()
    
    current_time.update({
        "lunar_date": lunar_info["lunar_date"],
        "zodiac": lunar_info["zodiac"],
        "festival": lunar_info["festival"]
    })
    
    return current_time
