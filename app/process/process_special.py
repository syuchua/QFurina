# *- process_special.py -*
"""
处理特殊请求
""" 
import re, asyncio, os
from ..DB.database import db
from ..Core.decorators import async_timed, error_handler
from ..logger import logger
from ..Core.function_calling import (
    handle_web_search, handle_image_request, 
    handle_voice_request, music_handler
)
from .send import send_msg
from utils.voice_service import generate_voice
from utils.model_request import get_chat_response
from .process_image import detect_image_in_message
from utils.client import recognize_image
from ..Core.message_utils import MessageManager

class SpecialHandler:
    def __init__(self):
        self.handlers = {
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


    async def handle_voice_synthesis(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'
        voice_pattern = re.compile(r"#voice\s*(.*)", re.DOTALL)
        voice_match = voice_pattern.search(response_text)
        if voice_match:
            voice_text = voice_match.group(1).strip()
            voice_text = voice_text.replace('\n', '.')
            voice_text = re.sub(r'\[.*?\]', '', voice_text)
            voice_text = re.sub(r'\(.*?\)', '', voice_text)
            logger.info(f"Voice synthesis request: {voice_text}")
            try:
                audio_filename = await asyncio.wait_for(generate_voice(voice_text), timeout=10)
                if audio_filename:
                    response = f"[CQ:record,file=http://my_qbot:4321/data/voice/{audio_filename}]" if is_docker else f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"
                    await send_msg(msg_type, recipient_id, response)
                    await db.insert_chat_message(user_id, response_text, response, context_type, context_id, platform='onebot')
                    return True, response
                else:
                    await send_msg(msg_type, recipient_id, "语音合成失败。")
                    return True, "语音合成失败"
            except asyncio.TimeoutError:
                await send_msg(msg_type, recipient_id, "语音合成超时，请稍后再试。")
                return True, "语音合成超时"
        return False, None

    async def handle_image_recognition_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        logger.info(f"处理图像识别请求: user_input={user_input}")
        
        # 使用 process_image.py 中的函数检测图片
        contains_image, image_cq_code, _ = await detect_image_in_message(user_input)
        
        if contains_image:
            # 使用 client.py 中的 recognize_image 函数
            recognition_result = await recognize_image(image_cq_code)
            
            if recognition_result and not any(indicator in recognition_result for indicator in [
                "无法处理图像数据", "网络连接问题", "图像识别时出现错误", 
                "当前API不支持图像识别", "图像太大"
            ]):
                response = f"识别结果：{recognition_result}"
                logger.info(f"识别结果：{recognition_result}")
                await send_msg(msg_type, recipient_id, response)
                await db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
                return True, response
        
        # 当未找到图片或识别失败时，给出提示
        await send_msg(msg_type, recipient_id, "未找到要识别的图片，请确保您发送了图片。")
        return False, None

    async def handle_search_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        search_pattern = re.compile(r"#search\s*(.*)")
        
        # 首先尝试在 user_input 中匹配
        search_match = search_pattern.search(user_input)
        if not search_match:
            # 如果在 user_input 中未找到，再在 response_text 中匹配
            search_match = search_pattern.search(response_text)
        
        if search_match:
            search_query = search_match.group(1).strip()
            if not search_query:
                # 如果未提供搜索关键词，给出提示
                await send_msg(msg_type, recipient_id, "请在 #search 后面提供搜索关键词。")
                return True, None
            try:
                await send_msg(msg_type, recipient_id, f"正在搜索：{search_query}")
                search_result = await handle_web_search(search_query)
                if search_result:
                    is_github = search_query.startswith("https://github.com/")
                    
                    # 获取用户信息和聊天上下文
                    username = await db.get_username(user_id)
                    
                    # 使用 MessageManager 创建消息上下文
                    context_messages, _ = await MessageManager.create_message_context(
                        "", user_id, username, context_type, context_id
                    )
                    
                    # 获取最近的几条对话作为上下文
                    recent_messages = await db.get_recent_messages(
                        user_id=recipient_id, 
                        context_type=context_type, 
                        context_id=context_id, 
                        platform='onebot', 
                        limit=5
                    )
                    
                    # 构建完整的提示信息，包含系统人设和上下文
                    ai_response = await self.generate_search_response_with_context(
                        search_query, 
                        search_result, 
                        is_github,
                        context_messages + recent_messages
                    )
                    
                    # 直接发送生成的回复
                    await send_msg(msg_type, recipient_id, ai_response)
                    await db.insert_chat_message(user_id, search_query, ai_response, context_type, context_id, platform='onebot')
                    return True, ai_response
                else:
                    logger.error("搜索没有返回结果。")
                    await send_msg(msg_type, recipient_id, "抱歉，搜索没有返回结果。")
                    return True, "抱歉，搜索没有返回结果。"
            except Exception as e:
                logger.error(f"搜索过程中出现错误: {e}")
                await send_msg(msg_type, recipient_id, "搜索过程中出现错误，请稍后再试。")
                return True, "搜索过程中出现错误，请稍后再试。"
        return False, None

    async def generate_search_response_with_context(self, query: str, search_results: str, is_github: bool = False, context_messages=None) -> str:
        """根据搜索结果和上下文生成AI回复"""
        
        # 从配置中获取系统人设
        from ..Core.config import config
        system_message = config.SYSTEM_MESSAGE.get("role", "你是一个智能助手")
        
        # 构建带有上下文的系统提示
        system_prompt = f"""
        {system_message}
        
        用户搜索查询: "{query}"
        
        搜索结果:
        {search_results}
        
        请根据以上搜索结果和聊天上下文，生成一个信息丰富且符合你的人设的回复。回复应该：
        1. 总结搜索结果的主要信息
        2. 保持与你的人设一致的语气和风格
        3. 提供对查询的直接回答（如果可能）
        4. 如果搜索结果中包含多个观点，请简要说明不同的观点
        5. 与之前的对话保持连贯性
        {"6. 重点介绍GitHub项目的主要功能和特点" if is_github else ""}
        
        请以对话的方式回复，就像你在与用户直接交谈一样。回复应该是中文的。
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加上下文消息
        if context_messages:
            # 只保留最近的几条消息作为上下文
            context_slice = context_messages[-5:] if len(context_messages) > 5 else context_messages
            messages.extend(context_slice)
            
        # 添加最终的用户查询
        messages.append({"role": "user", "content": f"请根据搜索结果回答关于'{query}'的问题，保持你的人设风格。"})
        
        response = await get_chat_response(messages)
        return response.strip()

    async def handle_image_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        image_url = await handle_image_request(user_input)
        if image_url:
            response = f"[CQ:image,file={image_url}]"
            await send_msg(msg_type, recipient_id, response)
            await db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
            return True, response
        return False, None

    async def handle_voice_request(self, user_input, response_text, msg_type, recipient_id, user_id, context_type, context_id):
        voice_url = await handle_voice_request(user_input)
        if voice_url:
            response = f"[CQ:record,file={voice_url}]"
            await send_msg(msg_type, recipient_id, response)
            await db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
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
            await db.insert_chat_message(user_id, user_input, response, context_type, context_id, platform='onebot')
            return True, response
        return False, None

special_handler = SpecialHandler()
