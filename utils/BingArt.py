import re
import time
import asyncio
from urllib.parse import urlencode
import aiohttp
import browser_cookie3 as bc
from app.logger import logger
from typing import List, Dict
import json, os, random, psutil

class AuthCookieError(Exception):
    pass

class PromptRejectedError(Exception):
    pass

class CookieManager:
    def __init__(self, cookie_file: str = 'cookies.json'):
        self.cookie_file = os.path.join(os.getcwd(), cookie_file)
        self.cookies: List[Dict[str, str]] = self.load_cookies()
        self.last_used: Dict[int, float] = {}
        self.cooldown = 3600  # 1 hour cooldown

    def load_cookies(self) -> List[Dict[str, str]]:
        try:
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
            if isinstance(cookies, dict):  # 如果是单个 cookie
                cookies = [cookies]  # 将其转换为列表
            logger.info(f"Loaded {len(cookies)} cookies from {self.cookie_file}")
            return cookies
        except FileNotFoundError:
            logger.warning(f"Cookie file not found: {self.cookie_file}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in cookie file: {self.cookie_file}")
            return []

    def save_cookies(self):
        with open(self.cookie_file, 'w') as f:
            json.dump(self.cookies, f)

    def get_cookie(self) -> Dict[str, str]:
        if not self.cookies:
            raise ValueError("No cookies available")
        
        if len(self.cookies) == 1:
            return self.cookies[0]
        
        current_time = time.time()
        available_cookies = [
            i for i, last_used in self.last_used.items()
            if current_time - last_used > self.cooldown
        ]
        
        if not available_cookies:
            if len(self.cookies) > len(self.last_used):
                available_cookies = list(set(range(len(self.cookies))) - set(self.last_used.keys()))
            else:
                cookie_index = min(self.last_used, key=self.last_used.get)
        else:
            cookie_index = random.choice(available_cookies)
        
        self.last_used[cookie_index] = current_time
        return self.cookies[cookie_index]

    def remove_cookie(self, cookie: Dict[str, str]):
        self.cookies = [c for c in self.cookies if c != cookie]
        self.save_cookies()

    def is_cookie_valid(self, cookie: Dict[str, str]) -> bool:
        return '_U' in cookie and 'KievRPSSecAuth' in cookie

class BingArt:
    browser_procs = {
        bc.chrome: 'chrome.exe',
        bc.firefox: 'firefox.exe',
        bc.edge: 'msedge.exe',
        bc.opera: 'launcher.exe',
        bc.opera_gx: 'launcher.exe'
    }

    def __init__(self, cookie_manager: CookieManager):
        self.cookie_manager = cookie_manager
        self.base_url = 'https://www.bing.com/images/create'

    def _prepare_headers(self, cookie: Dict[str, str]):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': self.base_url,
            'Accept-Language': 'en-US,en;q=0.9',
            'Cookie': '; '.join([f"{name}={value}" for name, value in cookie.items()])
        }

    async def _get_balance(self, session):
        async with session.get(self.base_url) as response:
            text = await response.text()
            try:
                match = re.search(r'bal" aria-label="(\d+) ', text)
                if match:
                    coins = int(match.group(1))
                else:
                    logger.warning("Unable to find coin balance in the response. Setting coins to 0.")
                    coins = 0
            except (AttributeError, ValueError) as e:
                logger.error(f"Error parsing coin balance: {e}")
                coins = 0
        return coins  # 确保返回 coins 值


    async def _fetch_images(self, session, encoded_query, ID, IG):
        images = []
        while True:
            async with session.get(
                f'{self.base_url}/async/results/{ID}?{encoded_query}&IG={IG}&IID=images.as'.replace('&amp;nfy=1', '')
            ) as response:
                text = await response.text()
                if 'text/css' in text:
                    src_urls = re.findall(r'src="([^"]+)"', text)
                    for src_url in src_urls:
                        if '?' in src_url:
                            clean_url = src_url.split('?')[0] + '?pid=ImgGn'
                            images.append({'url': clean_url})
                    return images
            await asyncio.sleep(5)

    async def generate_images(self, query):
        try:
            cookie = self.cookie_manager.get_cookie()
        except ValueError as e:
            print(f"Failed to get cookie: {e}")
            raise
        headers = self._prepare_headers(cookie)
        encoded_query = urlencode({'q': query})

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                coins = await self._get_balance(session)
                rt = '4' if coins > 0 else '3'
                creation_url = f'{self.base_url}?{encoded_query}&rt={rt}&FORM=GENCRE'

                async with session.post(creation_url, data={'q': query}) as response:
                    text = await response.text()

                try:
                    ID = re.search(';id=([^"]+)"', text).group(1)
                    IG = re.search('IG:"([^"]+)"', text).group(1)
                except AttributeError:
                    raise PromptRejectedError('Error! Your prompt has been rejected for ethical reasons.')

                images = await self._fetch_images(session, encoded_query, ID, IG)
                return {'images': images, 'prompt': query}
        except AuthCookieError:
            print("Auth cookie failed, removing from pool")
            self.cookie_manager.remove_cookie(cookie)
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    

# 初始化
cookie_manager = CookieManager('cookies.json')
bing_art = BingArt(cookie_manager)
