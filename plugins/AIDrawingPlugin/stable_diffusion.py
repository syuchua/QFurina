# AIDrawingPlugin.py
import os, time, aiohttp, base64
import re
from io import BytesIO
from PIL import Image
from app.Core.message_utils import MessageManager
from app.plugin.plugin_base import PluginBase
from app.logger import logger
from app.process.process_plugin import upload_file_for_plugin
from utils.model_request import get_chat_response

@PluginBase.register("ai_drawing")
class AIDrawingPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "AI Drawing Plugin"
        self.register_name = "ai_drawing"
        self.version = "1.4.0"
        self.description = "使用Cloudflare Worker进行AI绘画"
        self.priority = 2
        self.tmp_folder = os.path.join(os.path.dirname(__file__), 'tmp')
        self.prompt_generation_system_message = """
        您是一位 Stable Diffusion 提示词专家，擅长从简单描述创建详细的图像生成提示。请按照以下指南创建提示：

        1. 提示结构：前缀 + 主题 + 场景
           - 前缀：质量标签 + 风格词 + 效果器
           - 主题：图像的主要焦点
           - 场景：背景和环境

        2. 使用常见词汇，按重要性排序，用逗号分隔。避免使用"-"或"."，但可以使用空格和自然语言。避免词汇重复。

        3. 强调关键词：
           - 使用括号增加权重：(word)增加1.1倍，((word))增加1.21倍，(((word)))增加1.331倍
           - 使用精确权重：(word:1.5)将权重增加1.5倍
           - 仅为重要标签增加权重

        4. 前缀指南：
           - 质量标签：如 "masterpiece", "best quality", "4k" 等提高图像细节
           - 风格词：如 "illustration", "digital art" 等定义图像风格
           - 效果器：如 "best lighting", "lens flare", "depth of field" 等影响光照和深度

        5. 主题指南：
           - 详细描述主题以确保图像丰富详细
           - 对于角色，描述面部、头发、身体、服装、姿势等特征
           - 增加主题的权重以增强其清晰度

        6. 场景指南：
           - 描述环境以丰富背景
           - 使用如 "flower field", "sunlight", "river" 等环境词

        请根据用户的简单描述，创建一个详细、结构化的 Stable Diffusion 提示词。确保提示词全面、有序，并突出关键元素。

        示例：
        用户输入：一只可爱的小猫
        您的输出：(masterpiece, best quality, 4k), (digital art:1.2), soft lighting, depth of field, (adorable kitten:1.3), fluffy fur, big curious eyes, (tiny pink nose), whiskers, (playful pose:1.1), (cozy living room:1.2), warm sunlight, comfortable sofa, scattered toys
        """
        os.makedirs(self.tmp_folder, exist_ok=True)

    async def on_load(self):
        self.worker_url = self.config.get('worker_url', "https://yourworker.dev")
        self.models = self.config.get('models', {
            "v1": "dreamshaper-8-lcm",
            "v2": "stable-diffusion-xl-base-1.0",
            "v3": "stable-diffusion-xl-lightning"
        })
        self.save_config()
        #logger.info(f"{self.name} v{self.version} loaded")

    async def on_enable(self):
        await super().on_enable()
        logger.debug(f"{self.name} enabled")

    async def on_disable(self):
        await super().on_disable()
        logger.info(f"{self.name} disabled")

    async def on_unload(self):
        logger.info(f"{self.name} unloaded")

    def get_commands(self):
        return [
            {"name": "draw-v1", "description": "使用 dreamshaper-8-lcm 模型绘画"},
            {"name": "draw-v2", "description": "使用 stable-diffusion-xl-base-1.0 模型绘画"},
            {"name": "draw-v3", "description": "使用 stable-diffusion-xl-lightning 模型绘画"}
        ]

    async def handle_command(self, command, args):
        if command.startswith("draw-v"):
            logger.info(f"decated command: {command}")
            version = command[-1]
            return await self.draw_command(args, version)
        return await super().handle_command(command, args)

    async def draw_command(self, args, version):
        if not args:
            return self.get_help_message()

        user_prompt = " ".join(args)
        optimized_prompt = await self.generate_optimized_prompt(user_prompt)
        model = self.models.get(f"{version}")
        if not model:
            return f"未知的模型版本: {version}"
        
        try:
            image_data = await self.generate_image(optimized_prompt, model)
            if image_data:
                image_path = self.save_image(image_data)
                file_url = await upload_file_for_plugin(image_path, 'image')
                if file_url:
                    cq_code = f"[CQ:image,file={file_url}]"
                    return {
                        "type": "node",
                        "data": {
                            "name": "AI绘画",
                            "uin": "2854196310",
                            "content": f"{cq_code}\n已生成图片，原始提示词: {user_prompt}\n优化后的提示词: {optimized_prompt}\n使用模型: {model}"
                        }
                    }
                else:
                    return "上传图片失败，请稍后再试。"
            else:
                return "生成图片失败，请稍后再试。"
        except Exception as e:
            logger.error(f"生成图片时发生错误: {str(e)}")
            return f"生成图片时发生错误: {str(e)}"

    async def generate_image(self, prompt, model):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.worker_url, json={"prompt": prompt, "model": model}, timeout=60) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Worker返回错误: {response.status}, {await response.text()}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"请求Worker时发生错误: {str(e)}")
                return None

    def save_image(self, image_data):
        try:
            img = Image.open(BytesIO(image_data))
            filename = f"generated_image_{int(time.time())}.png"
            file_path = os.path.join(self.tmp_folder, filename)
            img.save(file_path)
            logger.info(f"图片已保存到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存图片时发生错误: {str(e)}")
            raise

    async def on_message(self, message):
        content = message.get('content', '')
        if isinstance(content, str):
            for version in self.models.keys():
                if content.lower().startswith(f"/draw-{version} "):
                    args = content[len(f"/draw-{version} "):].split()
                    return await self.draw_command(args, version)
        return None

    async def on_file_upload(self, file_path):
        """
        文件上传钩子
        如果需要自定义上传逻辑，可以在这里实现
        """
        # 例如，如果你想为AI绘画的图片使用不同的URL前缀：
        if file_path.startswith(self.tmp_folder):
            filename = os.path.basename(file_path)
            return f"http://your-custom-domain.com/ai-drawings/{filename}"
        return None

    def get_help_message(self):
        return (
            "AI绘画插件使用说明:\n"
            "/draw-v1 <提示词> - 使用 dreamshaper-8-lcm 模型\n"
            "/draw-v2 <提示词> - 使用 stable-diffusion-xl-base-1.0 模型\n"
            "/draw-v3 <提示词> - 使用 stable-diffusion-xl-lightning 模型"
        )
    async def generate_optimized_prompt(self, user_input):
        messages = MessageManager.insert_or_replace_system_message([], self.prompt_generation_system_message)
        messages.append({"role": "user", "content": user_input})
        logger.debug(f"messages: {messages}")
        response = await get_chat_response(messages)
        return self.optimize_prompt(response)

    def optimize_prompt(self, prompt):
        # 移除所有非英文、非数字、非基本标点的字符
        prompt = re.sub(r'[^a-zA-Z0-9\s\.,!?():-]', '', prompt)
        # 移除多余的空白字符
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        # 确保括号的使用正确
        prompt = re.sub(r'\(+', '(((', prompt)
        prompt = re.sub(r'\)+', ')))', prompt)
        return prompt
