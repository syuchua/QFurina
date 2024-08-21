import inspect
import os
import importlib
from app.plugin.plugin_base import PluginBase
from app.logger import logger
from app.config import Config
from app.plugin.PluginDependencyManager import PluginDependencyManager
from app.decorators import async_timed, error_handler

config = Config.get_instance()

class PluginConfig:
    def __init__(self):
        self.enabled_plugins = config.ENABLED_PLUGINS

    def enable_plugin(self, plugin_name):
        if plugin_name not in self.enabled_plugins:
            self.enabled_plugins.append(plugin_name)
            config.save_config()

    def disable_plugin(self, plugin_name):
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_name)
            config.save_config()

class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.config = Config.get_instance()
        self.dependency_manager = PluginDependencyManager()

    async def load_plugins(self):
        plugin_dir = "plugins"
        #logger.info(f"Searching for plugins in directory: {plugin_dir}")
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_name = filename[:-3]
                try:
                    module = importlib.import_module(f"{plugin_dir}.{plugin_name}")
                    #logger.info(f"Successfully imported plugin module: {plugin_name}")
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, PluginBase) and obj != PluginBase:
                            #logger.info(f"Found plugin class: {name} in module {plugin_name}")
                            pass
                except Exception as e:
                    logger.error(f"Error importing plugin {plugin_name}: {e}")

        #logger.info(f"Registered plugins: {PluginBase.plugins.keys()}")
        #logger.info(f"Enabled plugins in config: {self.config.ENABLED_PLUGINS}")

        for name, plugin_class in PluginBase.plugins.items():
            if name in self.config.ENABLED_PLUGINS:
                try:
                    plugin = plugin_class()
                    if not hasattr(plugin, 'on_message') or not callable(getattr(plugin, 'on_message')):
                        logger.error(f"Plugin {name} does not have a valid on_message method")
                        continue
                    await plugin.on_load()
                    self.plugins[name] = plugin
                    #logger.info(f"Loaded and enabled plugin: {name}")
                except Exception as e:
                    logger.error(f"Error loading plugin {name}: {e}")

        #logger.info(f"Total loaded and enabled plugins: {len(self.plugins)}")

    async def load_plugin(self, plugin_name):
        try:
            module = importlib.import_module(f"plugins.{plugin_name}")
            plugin_class = getattr(module, f"{plugin_name.capitalize()}Plugin")
            plugin = plugin_class()
            await plugin.on_load()
            self.plugins[plugin_name] = plugin
            logger.info(f"Dynamically loaded plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")

    async def unload_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            await plugin.on_unload()
            del self.plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")

    async def reload_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            await self.unload_plugin(plugin_name)
        await self.load_plugin(plugin_name)
        logger.info(f"Reloaded plugin: {plugin_name}")

    async def enable_plugin(self, plugin_name):
        if plugin_name not in self.plugins and plugin_name in PluginBase.plugins:
            plugin = PluginBase.plugins[plugin_name]()
            await plugin.on_load()
            self.plugins[plugin_name] = plugin
            if plugin_name not in self.config.ENABLED_PLUGINS:
                self.config.ENABLED_PLUGINS.append(plugin_name)
                self.config.save_config()  # 保存更新后的配置
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
        return False

    async def disable_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            await self.plugins[plugin_name].on_unload()
            del self.plugins[plugin_name]
            if plugin_name in self.config.ENABLED_PLUGINS:
                self.config.ENABLED_PLUGINS.remove(plugin_name)
                self.config.save_config()  # 保存更新后的配置
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
        return False

    def sort_plugins(self):
        self.plugins = dict(sorted(self.plugins.items(), key=lambda x: x[1].priority, reverse=True))

    @error_handler
    async def call_on_message(self, message):
        logger.debug(f"Calling on_message for {len(self.plugins)} plugins")
        sorted_plugins = sorted(self.plugins.values(), key=lambda x: x.priority, reverse=True)
        responses = []
        for plugin in sorted_plugins:
            logger.info(f"Checking plugin: {plugin.name}, enabled: {plugin.enabled}")
            if plugin.enabled:
                logger.info(f"Calling on_message for plugin: {plugin.name}")
                try:
                    response = await plugin.on_message(message)
                    logger.info(f"Response from {plugin.name}: {response}")
                    if response:
                        responses.append(response)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name} on_message: {e}", exc_info=True)
        #logger.info(f"Total responses from plugins: {len(responses)}")
        return responses

    async def call_on_command(self, command, args):
        responses = []
        sorted_plugins = sorted(self.plugins.values(), key=lambda x: x.priority, reverse=True)
        for plugin in sorted_plugins:
            if plugin.enabled:
                response = await plugin.on_command(command, args)
                if response:
                    responses.append(response)
        return responses

    async def call_on_receive(self, message):
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    await plugin.on_receive(message)
                    logger.info(f"plugin received message: {message}")
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name} on_receive: {e}")

    async def call_on_send(self, message):
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    await plugin.on_send(message)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name} on_send: {e}")

    async def call_on_file_upload(self, file_info):
        for plugin in self.plugins.values():
            if plugin.enabled:
                await plugin.on_file_upload(file_info)

    async def call_on_plugin_command(self, plugin_name, command, args):
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            if plugin.enabled:
                return await plugin.on_plugin_command(command, args)
        return None