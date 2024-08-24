# AIDrawingPlugin.py
import os, time, aiohttp, base64
from io import BytesIO
from PIL import Image
from app.plugin.plugin_base import PluginBase
from app.logger import logger
from app.process.process_plugin import upload_file_for_plugin
from utils.file import upload_file  # 导入上传文件的函数

@PluginBase.register("ai_drawing")
class AIDrawingPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "AI Drawing Plugin"
        self.register_name = "ai_drawing"
        self.version = "1.3.0"
        self.description = "使用Cloudflare Worker进行AI绘画"
        self.priority = 2
        self.tmp_folder = os.path.join(os.path.dirname(__file__), 'tmp')
        os.makedirs(self.tmp_folder, exist_ok=True)

    async def on_load(self):
        self.worker_url = self.config.get('worker_url', "https://your-worker.dev") #你的worker地址
        self.models = self.config.get('models', {
            "v1": "dreamshaper-8-lcm",
            "v2": "stable-diffusion-xl-base-1.0",
            "v3": "stable-diffusion-xl-lightning"
        })
        self.save_config()
        #logger.info(f"{self.name} v{self.version} loaded")

    async def on_enable(self):
        await super().on_enable()
        logger.info(f"{self.name} enabled")

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
            version = command[-1]
            return await self.draw_command(args, version)
        return await super().handle_command(command, args)

    async def draw_command(self, args, version):
        if not args:
            return self.get_help_message()

        prompt = " ".join(args)
        model = self.models.get(f"{version}")
        if not model:
            return f"未知的模型版本: {version}"
        
        try:
            image_data = await self.generate_image(prompt, model)
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
                            "content": f"{cq_code}\n已生成图片，提示词: {prompt}\n使用模型: {model}"
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
