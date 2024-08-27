import os
import importlib
import asyncio
from typing import Dict, List, Any
from app.plugin.plugin_base import PluginBase
from app.logger import logger
from app.Core.config import Config

config = Config.get_instance()

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.enabled_plugins: Dict[str, PluginBase] = {}

    async def load_plugins(self):
        """加载所有插件"""
        plugins_dir = 'plugins'
        logger.info(f"开始加载插件,插件目录: {plugins_dir}")
        for plugin_folder in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_folder)
            if os.path.isdir(plugin_path):
                try:
                    #logger.info(f"尝试加载插件: {plugin_folder}")
                    for filename in os.listdir(plugin_path):
                        if filename.endswith('.py') and not filename.startswith('__'):
                            module_name = f"plugins.{plugin_folder}.{filename[:-3]}"
                            spec = importlib.util.spec_from_file_location(module_name, os.path.join(plugin_path, filename))
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            #logger.info(f"已加载模块: {module_name}")

                    for plugin_class in PluginBase.plugins.values():
                        plugin_instance = plugin_class()
                        self.plugins[plugin_instance.register_name] = plugin_instance
                        logger.debug(f"已加载插件: {plugin_instance.register_name} (显示名称: {plugin_instance.name})")
                except Exception as e:
                    logger.error(f"加载插件 {plugin_folder} 时发生错误: {str(e)}")
                    logger.exception(e)

        logger.info(f"插件加载完成,共加载 {len(self.plugins)} 个插件")
        logger.debug(f"已加载的插件: {', '.join(self.plugins.keys())}")
        
        # 初始化插件
        for plugin in self.plugins.values():
            try:
                await plugin.on_load()
                if plugin.register_name in config.ENABLED_PLUGINS:
                    await self.enable_plugin(plugin.register_name)
            except Exception as e:
                logger.error(f"Error initializing plugin {plugin.register_name}: {str(e)}")

    async def enable_plugin(self, plugin_name: str):
        """启用插件"""
        if plugin_name not in self.plugins:
            logger.error(f"尝试启用不存在的插件: {plugin_name}")
            return False
        if plugin_name in self.enabled_plugins:
            logger.info(f"插件 {plugin_name} 已经处于启用状态")
            return False
        plugin = self.plugins[plugin_name]
        try:
            await plugin.on_enable()
            self.enabled_plugins[plugin_name] = plugin
            logger.debug(f"已启用插件: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"启用插件 {plugin_name} 时发生错误: {str(e)}")
            logger.exception(e)
            return False

    async def disable_plugin(self, plugin_name: str):
        """禁用插件"""
        if plugin_name in self.enabled_plugins:
            plugin = self.enabled_plugins[plugin_name]
            try:
                await plugin.on_disable()
                del self.enabled_plugins[plugin_name]
                logger.info(f"Disabled plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error disabling plugin {plugin_name}: {str(e)}")

    async def unload_plugins(self):
        """卸载所有插件"""
        for plugin in self.plugins.values():
            try:
                await plugin.on_unload()
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin.register_name}: {str(e)}")
        self.plugins.clear()
        self.enabled_plugins.clear()

    async def handle_message(self, message: Dict[str, Any]) -> str:
        """处理消息，调用启用的插件"""
        for plugin in sorted(self.enabled_plugins.values(), key=lambda p: p.priority, reverse=True):
            try:
                response = await plugin.on_message(message)
                if response:
                    return response
            except Exception as e:
                logger.error(f"Error in plugin {plugin.register_name} while handling message: {str(e)}")
                logger.error(f"Message content: {message.get('content', 'N/A')}")
                logger.error(f"Full message: {message}")
                logger.exception(e)

        return None

    async def handle_command(self, command: str, args: Dict[str, Any]) -> str:
        """处理命令"""
        for plugin in self.enabled_plugins.values():
            if command in [cmd['name'] for cmd in plugin.get_commands()]:
                try:
                    return await plugin.handle_command(command, args)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.register_name} while handling command: {str(e)}")
                    return f"Error executing command in plugin {plugin.register_name}: {str(e)}"
        return f"Unknown command: {command}"

    async def call_on_file_upload(self, file_path):
        """
        调用所有启用的插件的on_file_upload方法
        """
        for plugin in self.enabled_plugins.values():
            if hasattr(plugin, 'on_file_upload'):
                try:
                    result = await plugin.on_file_upload(file_path)
                    if result:
                        return result
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name} on_file_upload: {str(e)}")
        return None

    def get_plugin_help(self, plugin_name: str) -> str:
        """获取特定插件的帮助信息"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].get_help()
        return f"Plugin '{plugin_name}' not found."

    def get_all_plugins_info(self) -> List[Dict[str, Any]]:
        """获取所有插件的信息"""
        return [
            {
                "name": plugin.name,
                "register_name": plugin.register_name,
                "version": plugin.version,
                "description": plugin.description,
                "enabled": plugin.register_name in self.enabled_plugins
            }
            for plugin in self.plugins.values()
        ]

    def get_all_plugin_commands(self):
        """获取所有启用的插件支持的命令列表"""
        commands = {}
        for plugin in self.enabled_plugins.values():
            plugin_commands = plugin.get_commands()
            for cmd in plugin_commands:
                commands[cmd['name']] = plugin
        return commands

# 创建全局插件管理器实例
plugin_manager = PluginManager()