# search.py
import re, aiohttp
from bs4 import BeautifulSoup

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

async def get_webpage_content(url):
    """
    使用 DuckDuckGo 获取网页内容
    """
    ddg_url = f"https://html.duckduckgo.com/html/?q={url}"
    async with aiohttp.ClientSession() as session:
        async with session.get(ddg_url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                # 尝试提取主要内容
                main_content = soup.find('div', {'id': 'links'})
                if main_content:
                    paragraphs = main_content.find_all('p')
                    content = ' '.join([p.text for p in paragraphs])
                    return content[:1000]  # 限制内容长度
                else:
                    return "无法提取页面内容。"
            else:
                return f"无法获取页面内容，状态码：{response.status}"

async def get_github_repo_info(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 获取仓库名称
                repo_name = soup.find('strong', {'itemprop': 'name'})
                repo_name = repo_name.text.strip() if repo_name else "Unknown"
                
                # 获取仓库描述
                description = soup.find('p', {'class': 'f4 mb-3'})
                description = description.text.strip() if description else "No description available."
                
                # 获取语言信息
                languages = []
                language_div = soup.find('div', {'class': 'Layout-main'}).find('h2', string='Languages')
                if language_div:
                    language_items = language_div.find_next('ul').find_all('li')
                    for item in language_items:
                        lang_name = item.find('span', class_='color-fg-default')
                        lang_percent = item.find('span', class_='color-fg-muted')
                        if lang_name and lang_percent:
                            languages.append(f"{lang_name.text.strip()} {lang_percent.text.strip()}")
                
                main_language = languages[0].split()[0] if languages else "Not specified"
                all_languages = ", ".join(languages) if languages else "Not specified"
                
                # 获取最后更新时间
                last_updated = soup.find('relative-time')
                last_updated = last_updated['datetime'] if last_updated else "Unknown"
                
                # 获取默认分支
                default_branch = soup.find('span', {'class': 'css-truncate-target', 'data-menu-button': ''})
                if not default_branch:
                    default_branch = soup.find('summary', {'class': 'btn css-truncate'})
                default_branch = default_branch.text.strip() if default_branch else "Unknown"
                
                # 获取 README 内容
                readme = soup.find('article', {'class': 'markdown-body entry-content container-lg'})
                readme_text = readme.get_text(strip=True)[:500] + "..." if readme else "No README available."
                
                return  f"仓库地址: {url}\n" \
                        f"仓库名称: {repo_name}\n" \
                        f"项目描述: {description}\n" \
                        f"主要语言: {main_language}\n" \
                        f"默认分支: {default_branch}\n" \
                        f"最后更新时间: {last_updated}\n" \
                        f"\nREADME预览:\n{readme_text}"

            else:
                return f"无法获取 GitHub 仓库信息，状态码：{response.status}"
