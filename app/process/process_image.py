"""
处理图像识别和自动图像分析
"""
import re
from ..logger import logger
from utils.client import recognize_image
from ..Core.function_calling import IMAGE_CQ_PATTERN
from utils.model_request import get_chat_response
from ..Core.decorators import async_timed

async def detect_image_in_message(user_input):
    """
    检测消息中是否包含图片，并返回CQ码
    
    参数:
    user_input (str): 用户输入消息
    
    返回:
    tuple: (是否包含图片, 图片CQ码, 纯文本内容)
    """
    image_match = IMAGE_CQ_PATTERN.search(user_input)
    if not image_match:
        return False, None, user_input
        
    image_cq_code = image_match.group(0)
    text_content = re.sub(r'\[CQ:[^\]]+\]', '', user_input).strip()
    
    return True, image_cq_code, text_content

# 修改 process_image 函数，直接返回完整响应
@async_timed()
async def process_image(user_input, auto_recognize=True):
    """
    处理用户消息中的图片并直接返回响应
    
    参数:
    user_input (str): 用户输入消息
    auto_recognize (bool): 是否自动识别图片
    
    返回:
    tuple: (是否已处理, 最终响应文本, 纯文本内容)
    """
    contains_image, image_cq_code, text_content = await detect_image_in_message(user_input)
    
    if not contains_image or "#recognize" in user_input:
        return False, None, user_input
        
    if auto_recognize and contains_image:
        logger.info(f"自动识别图片: {image_cq_code}")
        try:
            recognition_result = await recognize_image(image_cq_code)
            
            # 检查结果有效性
            error_indicators = [
                "无法处理图像数据", 
                "网络连接问题", 
                "图像识别时出现错误",
                "当前API不支持图像识别",
                "图像太大"
            ]
            
            if recognition_result and not any(indicator in recognition_result for indicator in error_indicators):
                # 如果用户同时提供了文字，生成带有图片上下文的响应
                if text_content:
                    messages = [
                        {"role": "system", "content": "用户发送了一张图片和一段文字。请根据图片内容和文字进行回复。"},
                        {"role": "system", "content": f"图片内容描述: {recognition_result}"},
                        {"role": "user", "content": text_content}
                    ]
                else:
                    # 如果用户只发送了图片，直接使用识别结果
                    return True, recognition_result, text_content
                    
                # 只有在有额外文本时才需要额外处理
                final_response = await get_chat_response(messages)
                return True, final_response, text_content
            else:
                logger.warning(f"图像识别失败: {recognition_result}")
                return False, None, user_input
        except Exception as e:
            logger.error(f"图像处理异常: {e}")
            return False, None, user_input
            
    return False, None, user_input

