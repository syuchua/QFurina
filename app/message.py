# * - message.py - *
from functools import wraps
from app.logger import logger
import re, random, time, asyncio, aiohttp
from app.config import Config
from app.command import handle_command
from app.ws_decorators import select_connection_method
from utils.voice_service import generate_voice
from utils.model_request import get_chat_response
from app.function_calling import handle_command_request, handle_image_request, handle_voice_request, handle_image_recognition, music_handler, weather_handler, handle_web_search
from app.database import db
from app.split_message import split_message
from utils.current_time import get_current_time, get_lunar_date_info
from app.decorators import async_timed, error_handler, rate_limit, retry

config = Config.get_instance()

# 超时重试装饰器
def retry_on_timeout(retries=1, timeout=10):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on attempt {attempt + 1}/{retries}. Retrying...")
                    await asyncio.sleep(timeout)
            raise asyncio.TimeoutError("Max retries reached")
        return wrapper
    return decorator

@retry_on_timeout(retries=3, timeout=10)
async def send_http_request(url, json):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=json) as res:
            res.raise_for_status()
            response = await res.json()
            return response


@select_connection_method
@error_handler
@rate_limit(calls=10, period=60)
async def send_msg(msg_type, number, msg, use_voice=False, is_error_message=False): # 使用限速器
    if use_voice:
        try:
            audio_filename = await generate_voice(msg)
            if audio_filename:
                msg = f"[CQ:record,file=http://localhost:4321/data/voice/{audio_filename}]"
        except asyncio.TimeoutError:
            msg = "语音合成超时，请稍后再试。"

    params = {
        'message': msg,
        **({'group_id': number} if msg_type == 'group' else {'user_id': number})
    }
    if config.CONNECTION_TYPE == 'http':
        url = f"http://127.0.0.1:3000/send_{msg_type}_msg"
        try:
            response = await send_http_request(url, params)
            if 'status' in response and response['status'] == 'failed':
                error_msg = response.get('message', response.get('wording', 'Unknown error'))
                logger.error(f"Failed to send {msg_type} message: {error_msg}")
                if not is_error_message:
                    await send_msg(msg_type, number, f"发送消息失败: {error_msg}", is_error_message=True)
            else:
                logger.info(f"\nsend_{msg_type}_msg: {msg}\n")
                logger.debug(f"API response: {response}")
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.error(f"Resource not found: {e}")
                await send_msg(msg_type, number, "资源未找到 (404 错误)。", is_error_message=True)
            else:
                logger.error(f"HTTP error occurred: {e}")
                await send_msg(msg_type, number, f"HTTP 错误: {e}", is_error_message=True)
        except asyncio.TimeoutError:
            logger.error("Request timed out after retries")
            await send_msg(msg_type, number, "请求超时，请稍后再试。", is_error_message=True)
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error occurred: {e}")
            await send_msg(msg_type, number, f"HTTP 错误: {e}", is_error_message=True)


def get_dialogue_response(user_input):
    for dialogue in config.DIALOGUES:
        if dialogue["user"] == user_input:
            return dialogue["assistant"]
    return None

def should_include_lunar(user_input):
    lunar_keywords = ["农历", "阴历", "节日", "生肖", "春节", "元宵", "端午", "中秋", "重阳"]
    return any(keyword in user_input for keyword in lunar_keywords)

def should_include_festival(user_input):
    festival_keywords = ["元旦", "情人节", "妇女节", "愚人节", "劳动节", "儿童节", "国庆节", "圣诞节"]
    return any(keyword in user_input for keyword in festival_keywords)


def process_chat_message(msg_type):
    def decorator(func):
        @wraps(func)
        async def wrapper(rev, *args, **kwargs):
            try:
                user_input = rev['raw_message']
                user_id = rev['sender']['user_id']
                username = rev['sender']['nickname']
                recipient_id = rev['sender']['user_id'] if msg_type == 'private' else rev['group_id']
                context_type = 'private' if msg_type == 'private' else 'group'
                context_id = recipient_id

                user_info = {"user_id": user_id, "username": username}
                db.insert_user_info(user_info)

                # 调用原始函数，可能会修改 user_input 或执行其他特定逻辑
                modified_input = await func(rev, *args, **kwargs)
                if modified_input is None:
                    return  # 如果返回 None，表示不需要回复，直接返回
                if modified_input is not None:
                    user_input = modified_input

                # 检查是否需要包含农历信息和节日信息
                include_lunar = should_include_lunar(user_input)
                include_festival = should_include_festival(user_input)

                # 获取时间信息
                time_info = get_current_time()
                if include_lunar:
                    lunar_info = get_lunar_date_info()
                    time_info.update(lunar_info)

                # 构建时间信息字符串
                time_str = (f"今天是：{time_info['full_time']}，{time_info['weekday']}，"
                            f"现在是{time_info['period']}，具体时间是{time_info['hour']}点{time_info['minute']}分。")
                
                if include_lunar:
                    time_str += f"\n农历：{time_info['lunar_date']}，生肖：{time_info['zodiac']}"
                    if time_info['festival']:
                        time_str += f"，今天是{time_info['festival']}"
                
                if include_festival and time_info['solar_festival']:
                    time_str += f"\n今天是{time_info['solar_festival']}"
                elif include_festival:
                    time_str += "\n今天没有特殊的公历节日"

                # 检测命令
                full_command = await handle_command_request(user_input)
                if full_command:
                    await handle_command(full_command, msg_type, recipient_id, send_msg, context_type, context_id)
                    return

                # 处理特殊请求
                if contains_special_keywords(user_input):
                    special_response = await handle_special_requests(user_input)
                    if special_response:
                        await send_msg(msg_type, recipient_id, special_response)
                        db.insert_chat_message(user_id, user_input, special_response, context_type, context_id)
                        return

                # 获取最近的10条消息
                recent_messages = db.get_recent_messages(user_id=recipient_id, context_type=context_type, context_id=context_id, limit=10)

                # 检查最近消息中是否包含当前用户的消息
                user_in_recent = any(msg['role'] == 'user' and msg['content'].startswith(f"{username}:") for msg in recent_messages)
                
                if not user_in_recent:
                    # 如果最近消息中没有当前用户的消息，获取用户的历史消息
                    user_historical = db.get_user_historical_messages(user_id=user_id, context_type=context_type, context_id=context_id, limit=3)
                    
                    # 将用户的历史消息插入到最近消息的适当位置
                    insert_index = len(recent_messages) // 2  # 插入到中间位置
                    recent_messages = recent_messages[:insert_index] + user_historical + recent_messages[insert_index:]
                    
                    # 如果插入后消息数量超过10轮，裁剪掉最早的消息
                    if len(recent_messages) > 20:  # 10轮对话是20条消息（每轮包含用户输入和机器人回复）
                        recent_messages = recent_messages[-20:]

                system_message_text = "\n".join(config.SYSTEM_MESSAGE.values())
                if user_id == config.ADMIN_ID:
                    admin_title = random.choice(config.ADMIN_TITLES)
                    user_input = "[impression]这是老爹说的话："f"{admin_title}: {user_input}"
                else:
                    user_input = "[impression]这不是老爹说的话:"f"{username}: {user_input}"
                messages = [
                    {"role": "system", "content": system_message_text},
                    {"role": "system", "content": time_str}
                ] + recent_messages + [{"role": "user", "content": user_input}]

                #logger.info(f"Messages for chat response: {messages}")

                response_text = get_dialogue_response(user_input) if user_id == config.ADMIN_ID else None
                if response_text is None:
                    response_text = await get_chat_response(messages)

                if response_text:
                    db.insert_chat_message(user_id, user_input, response_text, context_type, context_id)
                    # 添加一个参数来指示是否处理特殊响应
                    process_special = not user_input.startswith(('!history', '/history', '#history'))
                    await process_special_responses(response_text, msg_type, recipient_id, user_id, user_input, context_type, context_id, process_special=process_special)

                if user_id == config.ADMIN_ID:                    
                    response_with_username = response_text
                else:
                    response_with_username = f"{username}，{response_text}"

                # 使用消息截断器发送最终响应
                # response_parts = split_message(response_with_username)
                # for part in response_parts:
                #     await send_msg(msg_type, recipient_id, part)
                #     await asyncio.sleep(0.3)

                # 直接发送完整消息，不使用消息截断器
                await send_msg(msg_type, recipient_id, response_with_username)

            except Exception as e:
                logger.error(f"Error in process_chat_message: {e}")
                await send_msg(msg_type, recipient_id, "阿巴阿巴，出错了。")
        
        return wrapper
    return decorator

def contains_special_keywords(user_input):
    keywords = ["发一张", "来一张", "再来一张", "来份涩图", "来份色图", "画一张", "生成一张", 
                "语音回复", "用声音说", "语音说", "#voice", "#draw", "#recognize", "#search"]
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


def is_chinese(char):
    """检查一个字符是否是中文"""
    return '\u4e00' <= char <= '\u9fff'

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

@process_chat_message('private')
async def process_private_message(rev):
    logger.info(f"\nReceived private message from user {rev['sender']['user_id']}: {rev['raw_message']}\n")
    return rev['raw_message']

@process_chat_message('group')
async def process_group_message(rev):
    logger.info(f"\nReceived group message in group {rev['group_id']}: {rev['raw_message']}\n")

    user_input = rev['raw_message']
    group_id = rev['group_id']
    user_id = rev['sender']['user_id']

    block_id = config.BLOCK_ID
    contains_nickname = any(nickname in user_input for nickname in config.NICKNAMES)
    is_sender_blocked = user_id in block_id
    # 更新 at_bot_message 正则表达式以匹配新格式
    at_bot_message = r'\[CQ:at,qq={},name=[^\]]+\]'.format(config.SELF_ID)
    is_at_bot = re.search(at_bot_message, user_input)

    # 简化的重启命令检查
    is_restart_command = user_input.strip().lower().startswith('/restart')

    if is_at_bot:
        # 移除 @ 消息，包括可能的名字部分
        user_input = re.sub(at_bot_message, '', user_input).strip()

    if (contains_nickname or is_at_bot or is_restart_command) and not is_sender_blocked:
        if is_restart_command:
            # 如果是重启命令，只返回 '/restart'
            return '/restart'
        return user_input  # 返回处理后的 user_input

    if random.random() <= config.REPLY_PROBABILITY and not is_sender_blocked:
        return user_input  # 随机回复的情况

    return None  # 明确表示不需要回复

