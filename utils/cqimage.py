from app.logger import logger
import re
import ssl
from urllib.parse import parse_qs, urlparse
import aiohttp
import requests
import base64
from io import BytesIO
from PIL import Image

def decode_cq_code(cq_code):
    """
    从CQ码中提取URL
    """
    parts = cq_code.split(',')
    url_part = next((part for part in parts if part.startswith('url=')), None)
    if url_part:
        url_match = re.search(r'url=([^,]+)', url_part)
        if url_match:
            return url_match.group(1).replace('&amp;', '&')
    return None

async def download_image(image_url):
    """
    从URL下载图像，并转换为PIL图像对象
    """
    parsed = urlparse(image_url)
    query = parse_qs(parsed.query)
    
    # Flatten the query dictionary
    query = {k: v[0] for k, v in query.items()}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(trust_env=False) as session:
        async with session.get(
            f"http://{parsed.netloc}{parsed.path}",
            params=query,
            ssl=ssl_context
        ) as resp:
            try:
                resp.raise_for_status()  # 检查HTTP错误
                file_bytes = await resp.read()
                image = Image.open(BytesIO(file_bytes))
                return image
            except aiohttp.ClientError as e:
                logger.error(f"Error downloading the image: {e}")
                return None
            except IOError as e:
                logger.error(f"Error opening the image: {e}")
                return None

def detect_image_format(image):
    """
    检测图像格式
    
    参数:
    image (PIL.Image): PIL图像对象
    
    返回:
    str: 检测到的图像格式 (jpeg, png, etc.)
    """
    format_lower = image.format.lower() if image.format else "jpeg"
    if format_lower == "jpg":
        format_lower = "jpeg"
    return format_lower

def image_to_base64(image):
    """
    将图像转换为base64编码，保留原始格式
    """
    format_lower = detect_image_format(image)
    buffered = BytesIO()
    image.save(buffered, format=format_lower.upper())
    return base64.b64encode(buffered.getvalue()).decode(), format_lower

async def get_cq_image_base64(cq_code):
    """
    异步提取CQ码图片，并转换为Base64编码
    
    返回:
    tuple: (image_base64, image_format) 图像的base64编码和格式
    """
    image_url = decode_cq_code(cq_code)
    if image_url:
        logger.info(f"Image URL: {image_url}")
        image = await download_image(image_url)
        if image:
            image_base64, image_format = image_to_base64(image)
            return image_base64, image_format
        else:
            raise ValueError("无法下载或打开图像")
    else:
        raise ValueError("CQ码中未找到有效的图像URL")
