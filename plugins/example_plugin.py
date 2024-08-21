from app.plugin.plugin_base import PluginBase
from app.decorators import async_timed, error_handler
from app.logger import logger

@PluginBase.register("example_plugin")
class Example_pluginPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "example_plugin"
        self.version = "1.0"
        self.description = "This is an example plugin"

    async def on_load(self):
        logger.debug("Example plugin loaded")

    async def on_message(self, message):
        if "hello plugin" in message.lower():
            logger.info("Example plugin responding to 'hello plugin'")
            return "Hello from the example plugin!"
        logger.info("Example plugin not responding to this message")
        return None

    async def on_command(self, command, args):
        if command == "plugin_example":
            return "This is an example plugin command"

    async def on_unload(self):
        logger.info("Example plugin unloaded")

    async def on_receive(self, message):
        logger.info(f"Example plugin received message: {message}")

    async def on_send(self, message):
        print(f"Sending message: {message}")

    async def on_file_upload(self, file_info):
        print(f"File uploaded: {file_info}")

    async def on_plugin_command(self, command, args):
        if command == "hello":
            return f"Hello from example plugin! Args: {args}"
        return None

    async def on_enable(self):
        print("Example plugin enabled")

    async def on_disable(self):
        print("Example plugin disabled")

    async def on_reload(self):
        print("Example plugin reloaded")