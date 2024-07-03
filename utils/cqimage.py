import logging
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
