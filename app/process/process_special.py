# process_special.py
import re, asyncio
from ..DB.database import db
from ..Core.decorators import async_timed, error_handler
from ..logger import logger
from ..Core.function_calling import weather_handler, handle_image_recognition, handle_image_request, handle_web_search
from .send import send_msg
from ..process.split_message import split_message
from utils.voice_service import generate_voice
from ..Core.function_calling import handle_image_request, handle_voice_request, handle_image_recognition, music_handler

def contains_special_keywords(user_input):
    keywords = ["发一张", "来一张", "再来一张", "来份涩图", "来份色图", "画一张", "生成一张", 
                "语音回复", "用声音说", "语音说", "#voice", "#draw", "#recognize", "#search",
                "点歌", "来首歌", "来首音乐", "来一首歌", "来一首音乐"]
    return any(keyword in user_input for keyword in keywords)

@async_timed()
@error_handler
async def handle_special_requests(user_input):
    # 处理图片请求
    image_url = await handle_image_request(user_input)
    if image_url:
        return f"[CQ:image,file={image_url}]"

    # 处理语音请求
    voice_url = await handle_voice_request(user_input)
    if voice_url:
        return f"[CQ:record,file={voice_url}]"
    
    # 处理音乐请求
    music_response = await music_handler.handle_music_request(user_input)
    if music_response:
        if music_response.startswith("http"):
            return f"[CQ:record,file={music_response}]"
        else:
            return music_response  # 返回错误消息

    # 处理图片识别请求   
    recognition_result = await handle_image_recognition(user_input)
    if recognition_result:
        return f"识别结果：{recognition_result}"


@async_timed()
@error_handler
async def process_special_responses(response_text, msg_type, recipient_id, user_id, user_input, context_type, context_id, process_special=True):
    if not process_special:
        return False

    WEATHER_KEYWORDS = ['天气', '气温', '温度', '下雨', '阴天', '晴天', '多云', '预报']

    if any(keyword in user_input for keyword in WEATHER_KEYWORDS):
        logger.info("Weather request detected")
        try:
            weather_response = await weather_handler.handle_request(user_input)
            logger.debug(f"Weather response type: {type(weather_response)}, content: {weather_response}")
            if weather_response:
                await send_msg(msg_type, recipient_id, weather_response)
                db.insert_chat_message(user_id, user_input, weather_response, context_type, context_id)
            else:
                await send_msg(msg_type, recipient_id, "抱歉，无法获取天气信息。")
            return True
        except Exception as e:
            logger.error(f"Error in weather request handling: {e}", exc_info=True)
            await send_msg(msg_type, recipient_id, "获取天气信息时发生错误，请稍后再试。")
            return True



    if process_special and '#voice' in response_text:
        logger.info("Voice request detected")
        voice_pattern = re.compile(r"#voice\s*(.*)", re.DOTALL)
        voice_match = voice_pattern.search(response_text)
        if voice_match:
            voice_text = voice_match.group(1).strip()
            voice_text = voice_text.replace('\n', '.')
            voice_text = re.sub(r'\[.*?\]', '', voice_text) # 移除方括号内的内容
            voice_text = re.sub(r'\(.*?\)', '', voice_text) # 移除圆括号内的内容
            logger.info(f"Voice text: {voice_text}")
            try:
                audio_filename = await asyncio.wait_for(generate_voice(voice_text), timeout=10)
                logger.info(f"Audio filename: {audio_filename}")
                if (audio_filename):
                    await send_msg(msg_type, recipient_id, f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]")
                    db.insert_chat_message(user_id, user_input, f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]", context_type, context_id)
                else:
                    await send_msg(msg_type, recipient_id, "语音合成失败。")
                return
            except asyncio.TimeoutError:
                await send_msg(msg_type, recipient_id, "语音合成超时，请稍后再试。")
                return
    elif process_special and '#recognize' in response_text:
        recognition_result = await handle_image_recognition(response_text[10:].strip())
        if recognition_result:
            await send_msg(msg_type, recipient_id, f"识别结果：{recognition_result}")
            db.insert_chat_message(user_id, user_input, f"识别结果：{recognition_result}", context_type, context_id)
        return
    elif process_special and '#draw' in response_text:
        logger.info("Draw request detected")
        draw_pattern = re.compile(r"#draw\s*(.*)", re.DOTALL)
        draw_match = draw_pattern.search(response_text)
        if draw_match:
            draw_prompt = draw_match.group(1).strip()
            # 清理 prompt
            draw_prompt = draw_prompt.replace('\n', ' ')  # 将换行符替换为空格
            draw_prompt = re.sub(r'\[.*?\]', '', draw_prompt)  # 移除方括号内的内容
            draw_prompt = draw_prompt.replace('()', '') # 移除圆括号
            draw_prompt = re.sub(r'[,，。.…]+', ' ', draw_prompt)  # 替换逗号、句号、省略号为空格
            draw_prompt = re.sub(r'\s+', ',', draw_prompt)  # 将多个空格替换为逗号           
            draw_prompt = ''.join([char for char in draw_prompt if not is_chinese(char)])  # 移除中文字符         
            draw_prompt = draw_prompt.strip()  # 去除首尾空格
            # draw_prompt = re.sub(r'\s+', ',', draw_prompt)  # 将空格替换为逗号
            draw_prompt = draw_prompt[:-2] # 移除前三个字符
            draw_prompt = re.sub(r'^[,.。... ! ?\s]+|[,.。... ! ?\s]+$', '', draw_prompt) # 移除开头和结尾的标点符号和空格
            logger.info(f"Draw prompt: {draw_prompt}")
        try:
            draw_result = await handle_image_request(response_text)
            if draw_result:
                await send_msg(msg_type, recipient_id, f"[CQ:image,file={draw_result}]")
                db.insert_chat_message(user_id, user_input, f"[CQ:image,file={draw_result}]", context_type, context_id)
            else:
                await send_msg(msg_type, recipient_id, "抱歉，我无法生成这个图片。可能是提示词不够清晰或具体。")
        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            await send_msg(msg_type, recipient_id, "图片生成过程中出现错误，请稍后再试。")
        return
    
    elif process_special and '#search' in response_text:
        logger.info("Search request detected")
        search_pattern = re.compile(r"#search\s*(.*)")  # 修改正则表达式以捕获整个URL
        search_match = search_pattern.search(response_text)
        if search_match:
            search_query = search_match.group(1).strip()
            logger.info(f"Search query: {search_query}")
            try:
                await send_msg(msg_type, recipient_id, f"正在搜索：{search_query}")
                search_result = await handle_web_search(search_query)
                logger.info(f"Raw search result: {search_result}")  # 记录完整的搜索结果
                if search_result:
                    if search_query.startswith("https://github.com/"):
                        # 对于 GitHub 仓库，分两部分发送
                        result_preview = search_result[:500] if len(search_result) > 500 else search_result
                        await send_msg(msg_type, recipient_id, f"Search result: {result_preview}...")
                        
                        # 查找 "#search" 的位置，从这里开始发送剩余部分
                        remaining_start = search_result.find("#search")
                        if remaining_start != -1:
                            remaining_text = search_result[remaining_start:]
                            await send_msg(msg_type, recipient_id, remaining_text)
                        
                    else:
                        # 对于其他搜索结果，使用消息截断器
                        result_parts = split_message(search_result, max_length=1000)
                        for part in result_parts:
                            await send_msg(msg_type, recipient_id, part)
                            await asyncio.sleep(0.5)
                    
                    # 将完整的搜索结果保存到数据库
                    db.insert_chat_message(user_id, user_input, search_result, context_type, context_id)
                else:
                    await send_msg(msg_type, recipient_id, "抱歉，搜索没有返回结果。")
            except Exception as e:
                logger.error(f"Error during web search: {e}")
                await send_msg(msg_type, recipient_id, "搜索过程中出现错误，请稍后再试。")
            return
        

def is_chinese(char):
    """检查一个字符是否是中文"""
    return '\u4e00' <= char <= '\u9fff'