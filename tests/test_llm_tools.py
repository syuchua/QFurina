import asyncio
import os
import sys
import json
import time
from datetime import datetime
import base64
from PIL import Image
from io import BytesIO
import aiohttp
import ssl
from typing import Dict, Any, List, Optional, TypedDict, Literal

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qfurina.app.Core.entities import LLMResponse
from qfurina.app.logger import logger

# 硬编码配置
API_KEY = "Your-API-KEY"  # 请替换为实际的API密钥
API_BASE = "https://api.yuchu.me/v1"  # 使用官方API或你自己的API端点
MODEL_NAME = "gemini-2.0-flash"  # 或者其他你想测试的模型

# 测试设置
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_image.jpg")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# 确保结果目录存在
os.makedirs(RESULTS_DIR, exist_ok=True)

# 使用TypedDict定义工具参数结构
class SearchWebParams(TypedDict):
    query: str

class WebpageContentParams(TypedDict):
    url: str

class GitHubRepoInfoParams(TypedDict):
    url: str
    get_issues: Optional[bool]

# 工具处理器
class ToolsHandler:
    """处理LLM工具调用的类"""
    
    def __init__(self):
        # 注册可用的工具
        self.available_tools = {
            "search_web": self._handle_web_search,
            "get_webpage_content": self._handle_webpage_content,
            "get_github_repo_info": self._handle_github_repo_info,
        }
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """返回可用于LLM的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "搜索网络获取最新信息，用于查询新闻、事件、政策等互联网上的信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_webpage_content",
                    "description": "获取指定网页的内容，用于获取特定网页上的信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "网页URL"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_github_repo_info",
                    "description": "获取GitHub仓库的信息，包括描述、星标数等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "GitHub仓库URL"
                            },
                            "get_issues": {
                                "type": "boolean",
                                "description": "是否获取issues信息"
                            }
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """执行指定的工具函数"""
        if tool_name in self.available_tools:
            print(f"执行工具: {tool_name}, 参数: {args}")
            try:
                return await self.available_tools[tool_name](args)
            except Exception as e:
                error_message = f"工具执行失败: {e}"
                print(error_message)
                return error_message
        else:
            return f"未知工具: {tool_name}"
    
    async def _handle_web_search(self, args: SearchWebParams) -> str:
        """处理网络搜索请求"""
        query = args.get("query", "")
        if not query:
            return "搜索查询不能为空"
        
        # 模拟搜索结果
        print(f"模拟搜索: {query}")
        search_results = [
            {
                "title": f"关于'{query}'的最新信息",
                "url": f"https://example.com/news/{query.replace(' ', '-')}",
                "snippet": f"这里包含了关于{query}的最新报道和分析..."
            },
            {
                "title": f"{query}的官方网站",
                "url": f"https://official-{query.replace(' ', '-')}.org",
                "snippet": f"官方网站提供了{query}的详细信息和背景资料..."
            }
        ]
        
        return json.dumps({
            "query": query,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": search_results
        }, ensure_ascii=False)
    
    async def _handle_webpage_content(self, args: WebpageContentParams) -> str:
        """获取网页内容"""
        url = args.get("url", "")
        if not url:
            return "URL不能为空"
        
        # 模拟网页内容获取
        print(f"模拟获取网页内容: {url}")
        return f"这是从 {url} 获取的内容：\n\n这是一个示例网页，包含了各种信息和数据。该页面主要讨论了相关主题的最新进展..."
    
    async def _handle_github_repo_info(self, args: GitHubRepoInfoParams) -> str:
        """获取GitHub仓库信息"""
        url = args.get("url", "")
        get_issues = args.get("get_issues", False)
        
        if not url:
            return "GitHub仓库URL不能为空"
        
        # 模拟GitHub仓库信息获取
        print(f"模拟获取GitHub仓库信息: {url}, 获取issues: {get_issues}")
        
        repo_name = url.split("/")[-1] if "/" in url else "unknown-repo"
        
        repo_info = {
            "name": repo_name,
            "description": f"{repo_name}是一个优秀的开源项目，专注于...",
            "stars": 1234,
            "forks": 567,
            "last_updated": "2025-03-01"
        }
        
        if get_issues:
            repo_info["issues"] = [
                {"id": 1, "title": "功能请求：添加新的API端点", "state": "open"},
                {"id": 2, "title": "Bug：在某些环境下崩溃", "state": "closed"}
            ]
        
        return json.dumps(repo_info, ensure_ascii=False)

# 实例化工具处理器
tools_handler = ToolsHandler()

# 简单的API客户端
class SimpleAPIClient:
    def __init__(self, api_key, api_base, model_name):
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(self, messages, **kwargs):
        """简单的API调用实现"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            **kwargs
        }
        
        # 忽略SSL验证问题
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat/completions", 
                headers=self.headers,
                json=payload,
                ssl=ssl_context
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API错误 {response.status}: {error_text}")
                
                result = await response.json()
                
                # 创建LLMResponse对象
                llm_response = LLMResponse()
                
                if "choices" in result and result["choices"]:
                    choice = result["choices"][0]
                    message = choice.get("message", {})
                    
                    llm_response.role = message.get("role", "assistant")
                    llm_response.completion_text = message.get("content", "")
                    
                    # 处理工具调用
                    tool_calls = message.get("tool_calls", [])
                    if tool_calls:
                        llm_response.role = "tool"
                        for tool_call in tool_calls:
                            function_call = tool_call.get("function", {})
                            llm_response.tools_call_name.append(function_call.get("name", ""))
                            
                            try:
                                args = json.loads(function_call.get("arguments", "{}"))
                                llm_response.tools_call_args.append(args)
                            except:
                                llm_response.tools_call_args.append({})
                
                return llm_response

# 创建API客户端实例
api_client = SimpleAPIClient(API_KEY, API_BASE, MODEL_NAME)

# 保存测试结果的函数
def save_test_result(test_name, request, response):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "test_name": test_name,
            "timestamp": timestamp,
            "request": request,
            "response": response if isinstance(response, str) else (
                response.completion_text if hasattr(response, "completion_text") else str(response)
            )
        }, f, ensure_ascii=False, indent=2)
    
    return filepath

# 创建或获取测试图像
def prepare_test_image():
    """创建一个简单的测试图像，如果指定路径不存在的话"""
    try:
        if os.path.exists(TEST_IMAGE_PATH):
            # 尝试打开以验证有效性
            Image.open(TEST_IMAGE_PATH).close()
            return TEST_IMAGE_PATH
        
        # 创建一个简单的彩色图像
        img = Image.new('RGB', (500, 300), color=(73, 109, 137))
        img.save(TEST_IMAGE_PATH)
        print(f"创建了新的测试图像: {TEST_IMAGE_PATH}")
        return TEST_IMAGE_PATH
    except Exception as e:
        print(f"准备测试图像时出错: {e}")
        # 创建一个全新的图像，不依赖于可能损坏的文件
        new_path = os.path.join(os.path.dirname(__file__), "new_test_image.jpg")
        img = Image.new('RGB', (500, 300), color=(73, 109, 137))
        img.save(new_path)
        print(f"创建了替代测试图像: {new_path}")
        return new_path

# 图像编码函数
async def encode_image_to_base64(image_path):
    """将图片转换为base64编码"""
    try:
        # 打开并验证图像
        image = Image.open(image_path)
        # 转换为JPEG格式
        img_byte_arr = BytesIO()
        image.convert('RGB').save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        # 编码为base64
        base64_encoded = base64.b64encode(img_byte_arr).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_encoded}"
    except Exception as e:
        print(f"图像编码失败: {e}")
        return None

# 模拟get_chat_response函数
async def get_chat_response(messages, tools=None, use_tools=False):
    """简化版的chat response函数，直接使用api_client"""
    try:
        # 准备额外参数
        extra_params = {}
        if tools:
            # 处理不同API格式的工具
            if isinstance(tools, list) and tools and "type" in tools[0] and tools[0].get("type") == "function":
                # 新格式工具
                extra_params["tools"] = tools
                extra_params["tool_choice"] = "auto"
            else:
                # 旧格式函数
                extra_params["functions"] = tools
                extra_params["function_call"] = "auto"
        
        # 如果启用工具处理
        if use_tools:
            return await process_with_tools(messages, tools or tools_handler.get_tools_definition())
            
        # 调用API
        response = await api_client.chat_completion(messages, **extra_params)
        return response
    except Exception as e:
        print(f"API调用出错: {e}")
        # 返回带有错误信息的响应对象
        error_response = LLMResponse("err", f"调用API错误: {e}")
        return error_response

async def process_with_tools(messages, tools=None):
    """
    使用工具处理消息并返回结果
    
    工作流程:
    1. 将消息和工具定义发送给LLM
    2. 如果LLM决定使用工具，则执行工具调用
    3. 将工具执行结果添加到消息中
    4. 将更新后的消息再次发送给LLM获取最终回复
    """
    print("启动工具处理流程...")
    
    # 获取工具定义
    if tools is None:
        tools = tools_handler.get_tools_definition()
    
    # 第一次调用LLM，带有工具定义
    response = await api_client.chat_completion(messages, tools=tools)
    
    # 如果不是工具调用，直接返回结果
    if not hasattr(response, "is_tool_call") or not response.is_tool_call():
        print("LLM选择不使用工具，直接返回结果")
        return response
    
    # 处理工具调用
    tool_calls = response.get_all_tool_calls()
    tool_results = []
    
    print(f"需要执行 {len(tool_calls)} 个工具调用")
    
    # 执行每个工具调用
    for tool_name, tool_args in tool_calls:
        result = await tools_handler.execute_tool(tool_name, tool_args)
        tool_results.append({
            "tool_name": tool_name,
            "tool_args": tool_args,
            "result": result
        })
        print(f"工具 {tool_name} 执行结果: {result[:100]}..." if len(result) > 100 else f"工具 {tool_name} 执行结果: {result}")
    
    # 构建更新后的消息
    updated_messages = messages.copy()
    
    # 添加助手的工具调用消息
    tool_calls_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": []
    }
    
    for i, (tool_name, tool_args) in enumerate(tool_calls):
        tool_calls_message["tool_calls"].append({
            "id": f"call_{i}",
            "type": "function",
            "function": {
                "name": tool_name,
                "arguments": json.dumps(tool_args, ensure_ascii=False)
            }
        })
    
    updated_messages.append(tool_calls_message)
    
    # 为每个工具调用添加工具响应消息
    for i, result in enumerate(tool_results):
        tool_response_message = {
            "role": "tool",
            "tool_call_id": f"call_{i}",
            "name": result["tool_name"],
            "content": result["result"]
        }
        updated_messages.append(tool_response_message)
    
    print("将工具结果发送回LLM获取最终回复...")
    
    # 再次调用LLM获取最终回复
    final_response = await api_client.chat_completion(updated_messages)
    return final_response

# 测试函数
async def test_text_completion():
    """测试基本文本完成功能"""
    print("\n测试基本文本完成...")
    
    # 简单的提示
    messages = [{"role": "user", "content": "你好，请用中文介绍一下自己"}]
    
    # 调用API
    start_time = time.time()
    response = await get_chat_response(messages)
    end_time = time.time()
    
    # 处理响应
    if hasattr(response, "completion_text"):
        response_text = response.completion_text
    else:
        response_text = str(response)
    
    print(f"文本完成响应: {response_text[:100]}...")
    print(f"响应时间: {end_time - start_time:.2f} 秒")
    
    # 保存结果
    result_file = save_test_result("text_completion", messages, response)
    print(f"结果已保存到: {result_file}")
    
    # 检查错误
    if hasattr(response, "role") and response.role == "err":
        print(f"错误: {response_text}")
        return False
    
    return "正常" in response_text or "你好" in response_text or "AI" in response_text

async def test_image_recognition():
    """测试图像识别功能"""
    print("\n测试图像识别...")
    
    # 准备测试图像
    image_path = prepare_test_image()
    base64_image = await encode_image_to_base64(image_path)
    
    if not base64_image:
        print("图像编码失败，跳过测试")
        return False
        
    # 构建多模态消息
    messages = [
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "这张图片展示了什么内容？请用中文详细描述。"},
                {"type": "image_url", "image_url": {"url": base64_image}}
            ]
        }
    ]
    
    # 调用API
    start_time = time.time()
    response = await get_chat_response(messages)
    end_time = time.time()
    
    # 处理响应
    if hasattr(response, "completion_text"):
        response_text = response.completion_text
    else:
        response_text = str(response)
    
    print(f"图像识别响应: {response_text[:100]}...")
    print(f"响应时间: {end_time - start_time:.2f} 秒")
    
    # 保存结果
    result_file = save_test_result("image_recognition", {"image": "base64_encoded_image", "query": "这张图片展示了什么内容？"}, response)
    print(f"结果已保存到: {result_file}")
    
    # 检查错误
    if hasattr(response, "role") and response.role == "err":
        print(f"错误: {response_text}")
        return False
    
    # 判断是否包含图像描述相关内容
    success_indicators = ["图片", "图像", "显示", "展示", "color", "颜色", "背景"]
    return any(indicator in response_text for indicator in success_indicators)

async def test_tool_calling():
    """测试工具调用功能"""
    print("\n测试基础工具调用...")
    
    # 构建测试消息
    messages = [
        {"role": "system", "content": "当用户询问需要搜索或查询网页内容的问题时，使用适当的工具。"},
        {"role": "user", "content": "请帮我查询一下最近中国的人工智能政策。"}
    ]
    
    print("发送带有工具定义的消息给LLM...")
    
    # 获取工具定义
    tools = tools_handler.get_tools_definition()
    
    # 调用API
    start_time = time.time()
    response = await get_chat_response(messages, tools)
    end_time = time.time()
    
    # 检查是否是工具调用响应
    is_tool_call = hasattr(response, "is_tool_call") and response.is_tool_call()
    
    if is_tool_call:
        tool_name, tool_args = response.get_first_tool_call()
        print(f"工具调用成功: {tool_name}, 参数: {tool_args}")
    else:
        print("工具调用未触发，API返回了纯文本响应")
    
    # 保存结果
    result_file = save_test_result("tool_calling", {"messages": messages, "tools": tools}, response)
    print(f"结果已保存到: {result_file}")
    
    # 检查错误
    if hasattr(response, "role") and response.role == "err":
        print(f"错误: {response.completion_text}")
        return False
    
    return is_tool_call

async def test_complex_conversation():
    """测试复杂对话流程"""
    print("\n测试复杂对话流程...")
    
    # 构建多轮对话
    conversation = [
        {"role": "system", "content": "你是一个有用的AI助手，今天是2025年3月5日。"},
        {"role": "user", "content": "今天天气怎么样？"},
        {"role": "assistant", "content": "我无法知道具体的天气情况，因为我没有实时获取天气数据的能力。建议您查看天气预报应用或网站获取最准确的天气信息。"},
        {"role": "user", "content": "你能帮我总结一下关于人工智能的最新研究方向吗？"}
    ]
    
    # 调用API
    start_time = time.time()
    response = await get_chat_response(conversation)
    end_time = time.time()
    
    # 处理响应
    if hasattr(response, "completion_text"):
        response_text = response.completion_text
    else:
        response_text = str(response)
    
    print(f"对话响应: {response_text[:100]}...")
    print(f"响应时间: {end_time - start_time:.2f} 秒")
    
    # 保存结果
    result_file = save_test_result("complex_conversation", conversation, response)
    print(f"结果已保存到: {result_file}")
    
    # 检查错误
    if hasattr(response, "role") and response.role == "err":
        print(f"错误: {response_text}")
        return False
    
    # 检查响应是否包含相关关键词
    success_indicators = ["人工智能", "AI", "机器学习", "研究", "方向"]
    return any(indicator in response_text for indicator in success_indicators)

async def test_complete_tool_flow():
    """测试完整的工具调用流程（包括执行工具并获取最终结果）"""
    print("\n测试完整工具处理流程...")
    
    messages = [
        {"role": "system", "content": "你是一个有用的AI助手，今天是2025年3月5日。当用户询问需要搜索或查询最新信息时，使用适当的搜索工具。"},
        {"role": "user", "content": "请告诉我最近中国人工智能产业有哪些新政策？"}
    ]
    
    # 调用API，启用工具处理
    start_time = time.time()
    response = await get_chat_response(messages, use_tools=True)
    end_time = time.time()
    
    # 处理响应
    if hasattr(response, "completion_text"):
        response_text = response.completion_text
    else:
        response_text = str(response)
    
    print(f"完整工具流程响应: {response_text[:150]}...")
    print(f"总响应时间: {end_time - start_time:.2f} 秒")
    
    # 保存结果
    result_file = save_test_result("complete_tool_flow", messages, response)
    print(f"结果已保存到: {result_file}")
    
    # 检查是否成功
    success_indicators = ["政策", "人工智能", "AI", "中国", "发展"]
    return any(indicator in response_text for indicator in success_indicators)
    
async def test_github_repo_info_tool():
    """测试GitHub仓库信息工具"""
    print("\n测试GitHub仓库信息工具...")
    
    messages = [
        {"role": "system", "content": "当用户询问关于GitHub项目的信息时，使用适当的工具。"},
        {"role": "user", "content": "请帮我查看一下FastChat这个GitHub项目的基本信息，包括star数量和issues。"}
    ]
    
    # 调用API，启用工具处理
    start_time = time.time()
    response = await get_chat_response(messages, use_tools=True)
    end_time = time.time()
    
    # 处理响应
    if hasattr(response, "completion_text"):
        response_text = response.completion_text
    else:
        response_text = str(response)
    
    print(f"GitHub工具响应: {response_text[:150]}...")
    print(f"响应时间: {end_time - start_time:.2f} 秒")
    
    # 保存结果
    result_file = save_test_result("github_repo_info", messages, response)
    print(f"结果已保存到: {result_file}")
    
    # 检查是否成功
    success_indicators = ["GitHub", "FastChat", "stars", "星", "issue", "问题"]
    return any(indicator in response_text for indicator in success_indicators)

# 主测试函数
async def run_integration_tests():
    """运行所有集成测试"""
    print("=== 开始LLM API集成测试 ===")
    print(f"使用模型: {MODEL_NAME}")
    print(f"API基础URL: {API_BASE}")
    print(f"API密钥: {API_KEY[:5]}...{API_KEY[-4:] if len(API_KEY) > 8 else ''}")
    
    # 运行测试并收集结果
    results = {}
    
    try:
        results["基本文本完成"] = await test_text_completion()
    except Exception as e:
        print(f"基本文本完成测试失败: {e}")
        results["基本文本完成"] = False
    
    try:
        results["图像识别"] = await test_image_recognition()
    except Exception as e:
        print(f"图像识别测试失败: {e}")
        results["图像识别"] = False
    
    try:
        results["基础工具调用"] = await test_tool_calling()
    except Exception as e:
        print(f"基础工具调用测试失败: {e}")
        results["基础工具调用"] = False
    
    try:
        results["复杂对话"] = await test_complex_conversation()
    except Exception as e:
        print(f"复杂对话测试失败: {e}")
        results["复杂对话"] = False
    
    try:
        results["完整工具流程"] = await test_complete_tool_flow()
    except Exception as e:
        print(f"完整工具流程测试失败: {e}")
        results["完整工具流程"] = False
        
    try:
        results["GitHub仓库工具"] = await test_github_repo_info_tool()
    except Exception as e:
        print(f"GitHub仓库工具测试失败: {e}")
        results["GitHub仓库工具"] = False
    
    # 打印总结
    print("\n=== 测试结果总结 ===")
    for test_name, passed in results.items():
        status = "通过" if passed else "失败"
        print(f"{test_name}: {status}")
    
    overall = all(results.values())
    print(f"\n总体结果: {'所有测试通过' if overall else '部分测试失败'}")
    
    return overall

# 运行测试
if __name__ == "__main__":
    asyncio.run(run_integration_tests())