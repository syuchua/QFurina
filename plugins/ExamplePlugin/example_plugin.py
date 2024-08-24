# ExamplePlugin.py
from app.plugin.plugin_base import PluginBase
from app.logger import logger

@PluginBase.register("example")
class ExamplePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "Example Plugin"
        self.register_name = "example"
        self.version = "1.0.0"
        self.description = "This is an example plugin"
        self.priority = 1

    async def on_load(self):
        self.config['count'] = self.config.get('count', 0)
        self.save_config()
        logger.info(f"{self.name} loaded. Count: {self.config['count']}")

    async def on_enable(self):
        await super().on_enable()
        logger.info(f"{self.name} enabled")

    async def on_disable(self):
        await super().on_disable()
        logger.info(f"{self.name} disabled")

    async def on_unload(self):
        logger.info(f"{self.name} unloaded. Final count: {self.config['count']}")

    async def on_message(self, message):
        content = message.get('content', '')
        if isinstance(content, str):
            if "hello plugin" in content.lower():
                return f"Hello from {self.name}! I've been called {self.config['count']} times."
        return None

    def get_commands(self):
        return [
            {"name": "count", "description": "显示插件被调用的次数"},
            {"name": "reset", "description": "重置计数器"}
        ]

    async def handle_command(self, command, args):
        if command == "count":
            self.config['count'] += 1
            self.save_config()
            return f"This plugin has been called {self.config['count']} times."
        elif command == "reset":
            self.config['count'] = 0
            self.save_config()
            return "Counter has been reset to 0."
        return await super().handle_command(command, args)

    async def on_file_upload(self, file_path):
        logger.info(f"{self.name} received file upload notification: {file_path}")