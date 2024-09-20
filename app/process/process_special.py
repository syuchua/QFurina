# *- process_special.py -*
"""
处理特殊请求
""" 
import re, asyncio, os
from ..DB.database import db
from ..Core.decorators import async_timed, error_handler
from ..logger import logger
from ..Core.function_calling import (
    handle_web_search, handle_image_recognition, handle_image_request, 
    handle_voice_request, music_handler
)
from .send import send_msg
from ..process.split_message import split_message
from utils.voice_service import generate_voice

class SpecialHandler:
    def __init__(self):
        self.handlers = {
            #r'(天气|气温|温度|下雨|阴天|晴天|多云|预报)': self.handle_weather_request,
            r'#voice': self.handle_voice_synthesis,
            r'#recognize': self.handle_image_recognition_request,
            r'#search': self.handle_search_request,
            r'(发一张|来一张|再来一张|来份涩图|来份色图|画一张|生成一张)': self.handle_image_request,
            r'(语音回复|用声音说|语音说)': self.handle_voice_request,
            r'(点歌|来首歌|来首音乐|来一首歌|来一首音乐)': self.handle_music_request
        }

    @async_timed()
    @error_handler
    async def process_special(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id, process_special=True):
        if not process_special:
            return False, None

        # 先检查用户输入
        for pattern, handler in self.handlers.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.info(f"Detected special request in user input: {pattern}")
                try:
                    handled, result = await handler(user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id)
                    if handled:
                        return True, result
                except Exception as e:
                    logger.error(f"Error in special handling: {e}", exc_info=True)
                    return True, f"处理特殊请求时发生错误: {str(e)}"

        # 然后检查AI响应
        for pattern, handler in self.handlers.items():
            if re.search(pattern, response_text, re.IGNORECASE):
                logger.info(f"Detected special response in AI output: {pattern}")
                try:
                    handled, result = await handler(user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id)
                    if handled:
                        return True, result
                except Exception as e:
                    logger.error(f"Error in special handling: {e}", exc_info=True)
                    return True, f"处理特殊响应时发生错误: {str(e)}"

        return False, None

    # async def handle_weather_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
    #     try:
    #         weather_response = await weather_handler.handle_request(response_text)
    #         if weather_response:
    #             await send_msg(msg_type, recipient_id, weather_response)
    #             db.insert_chat_message(user_id, response_text, weather_response, context_type, context_id)
    #             return True, weather_response
    #         else:
    #             await send_msg(msg_type, recipient_id, "抱歉，无法获取天气信息。")
    #             return True, "无法获取天气信息"
    #     except Exception as e:
    #         logger.error(f"Error in weather request handling: {e}", exc_info=True)
    #         await send_msg(msg_type, recipient_id, "获取天气信息时发生错误，请稍后再试。")
    #         return True, "天气信息获取错误"

    async def handle_voice_synthesis(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'
        voice_pattern = re.compile(r"#voice\s*(.*)", re.DOTALL)
        voice_match = voice_pattern.search(response_text)
        if voice_match:
            voice_text = voice_match.group(1).strip()
            voice_text = voice_text.replace('\n', '.')
            voice_text = re.sub(r'\[.*?\]', '', voice_text)
            voice_text = re.sub(r'\(.*?\)', '', voice_text)
            try:
                audio_filename = await asyncio.wait_for(generate_voice(voice_text), timeout=10)
                if audio_filename:
                    response = f"[CQ:record,file=http://my_qbot:4321/data/voice/{audio_filename}]" if is_docker else f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"
                    await send_msg(msg_type, recipient_id, response)
                    db.insert_chat_message(user_id, response_text, response, context_type, context_id, platform='onebot')
                    return True, response
                else:
                    await send_msg(msg_type, recipient_id, "语音合成失败。")
                    return True, "语音合成失败"
            except asyncio.TimeoutError:
                await send_msg(msg_type, recipient_id, "语音合成超时，请稍后再试。")
                return True, "语音合成超时"
        return False, None

    async def handle_image_recognition_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        recognition_result = await handle_image_recognition(response_text[10:].strip())
        if recognition_result:
            response = f"识别结果：{recognition_result}"
            await send_msg(msg_type, recipient_id, response)
            db.insert_chat_message(user_id, response_text, response, context_type, context_id, platform='onebot')
            return True, response
        return False, None

    async def handle_search_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        search_pattern = re.compile(r"#search\s*(.*)")
        search_match = search_pattern.search(response_text)
        if search_match:
            search_query = search_match.group(1).strip()
            try:
                await send_msg(msg_type, recipient_id, f"正在搜索：{search_query}")
                search_result = await handle_web_search(search_query)
                if search_result:
                    if search_query.startswith("https://github.com/"):
                        await self.send_github_result(search_result, msg_type, recipient_id)
                        db.insert_chat_message(user_id, response_text, search_result, context_type, context_id, platform='onebot')
                        return True, search_result
                    else:
                        await self.send_search_result(search_result, msg_type, recipient_id)
                        db.insert_chat_message(user_id, response_text, search_result, context_type, context_id, platform='onebot')
                        return True, search_result
                else:
                    await send_msg(msg_type, recipient_id, "抱歉，搜索没有返回结果。")
                    return True, "搜索无结果"
            except Exception as e:
                logger.error(f"Error during web search: {e}")
                await send_msg(msg_type, recipient_id, "搜索过程中出现错误，请稍后再试。")
                return True, "搜索错误"
            return True, None
        return False, None

    async def handle_image_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        image_url = await handle_image_request(user_input)
        if image_url:
            response = f"[CQ:image,file={image_url}]"
            await send_msg(msg_type, recipient_id, response)
            db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
            return True, response
        return False, None

    async def handle_voice_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        voice_url = await handle_voice_request(user_input)
        if voice_url:
            response = f"[CQ:record,file={voice_url}]"
            await send_msg(msg_type, recipient_id, response)
            db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
            return True, response
        return False, None

    async def handle_music_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        music_response = await music_handler.handle_music_request(user_input)
        if music_response:
            if music_response.startswith("http"):
                response = f"[CQ:record,file={music_response}]"
            else:
                response = music_response
            await send_msg(msg_type, recipient_id, response)
            db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
            return True, response
        return False, None

    # @staticmethod
    # def clean_draw_prompt(prompt):
    #     prompt = prompt.replace('\n', ' ')
    #     prompt = re.sub(r'\[.*?\]', '', prompt)
    #     prompt = prompt.replace('()', '')
    #     prompt = re.sub(r'[,，。.…]+', ' ', prompt)
    #     prompt = re.sub(r'\s+', ',', prompt)
    #     prompt = ''.join([char for char in prompt if not SpecialHandler.is_chinese(char)])
    #     prompt = prompt.strip()
    #     prompt = re.sub(r'^[,.。... ! ?\s]+|[,.。... ! ?\s]+$', '', prompt)
    #     return prompt

    @staticmethod
    def is_chinese(char):
        return '\u4e00' <= char <= '\u9fff'

    @staticmethod
    async def send_github_result(result, msg_type, recipient_id):
        result_preview = result[:500] if len(result) > 500 else result
        await send_msg(msg_type, recipient_id, f"Search result: {result_preview}...")
        remaining_start = result.find("#search")
        if remaining_start != -1:
            remaining_text = result[remaining_start:]
            await send_msg(msg_type, recipient_id, remaining_text)

    @staticmethod
    async def send_search_result(result, msg_type, recipient_id):
        result_parts = split_message(result, max_length=1000)
        for part in result_parts:
            await send_msg(msg_type, recipient_id, part)
            await asyncio.sleep(0.5)

special_handler = SpecialHandler()