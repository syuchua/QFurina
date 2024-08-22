from app.plugin.plugin_base import PluginBase
from app.logger import logger

@PluginBase.register("example_plugin")
class ExamplePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "example_plugin"
        self.version = "1.0"
        self.description = "这是一个示例插件"

    async def on_load(self):
        logger.debug("示例插件已加载")

    async def on_message(self, rev, msg_type, *args, **kwargs):
        logger.debug(f"ExamplePlugin.on_message called with: rev={rev}, msg_type={msg_type}, args={args}, kwargs={kwargs}")
        
        message = rev.get('raw_message', '')
        #logger.debug(f"Raw message: {message}")

        if isinstance(message, list):
            #logger.debug("Message is a list, extracting text content")
            text = ' '.join([m['data']['text'] for m in message if m['type'] == 'text'])
        else:
            text = message

        #logger.debug(f"Processed text: {text}")

        if 'hello plugin' in text.lower():
            return "Hello! This is an example plugin response."
        
        return None

    async def on_unload(self):
        logger.debug("示例插件已卸载")

    async def on_command(self, command, msg_type, user_info, send_msg, context_type, context_id):
        parts = command.split()
        main_command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if main_command == "plugin_example":
            if not args:
                return "这是示例插件命令。使用方法：plugin_example <参数>"
            return f"示例插件收到命令：{' '.join(args)}"
        return None

    async def on_enable(self):
        logger.info("示例插件已启用")

    async def on_disable(self):
        logger.info("示例插件已禁用")