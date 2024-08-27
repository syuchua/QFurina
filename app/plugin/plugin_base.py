import os, json
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.logger import logger
from app.Core.config import Config

config = Config.get_instance()

class PluginBase(ABC):
    plugins: Dict[str, Any] = {}

    @classmethod
    def register(cls, name):
        def decorator(plugin_class):
            cls.plugins[name] = plugin_class
            plugin_class.register_name = name # 设置插件的注册名称
            return plugin_class
        return decorator

    def __init__(self):
        self.name = "Base Plugin"
        self.version = "1.0.0"
        self.description = "Base plugin class"
        self.enabled = False
        self.priority = 0
        self.register_name = getattr(self.__class__, 'register_name', self.name.lower().replace(' ', '_'))
        self.plugin_dir = os.path.dirname(os.path.abspath(self.__class__.__module__))
        self.config_file = os.path.join(self.plugin_dir, 'config.json')
        self.ensure_config()
        self.load_config()

    def ensure_config(self):
        """确保插件配置文件存在"""
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

    def get_plugin_path(self, filename: str) -> str:
        """获取插件文件的完整路径"""
        return os.path.join(self.plugin_dir, filename)

    def load_config(self):
        """加载插件配置"""

        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def save_config(self):
        """保存插件配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    
    @abstractmethod
    async def on_load(self):
        """当插件被加载时调用"""
        pass

    @abstractmethod
    async def on_unload(self):
        """当插件被卸载时调用"""
        pass

    async def on_enable(self):
        """当插件被启用时调用"""
        self.enabled = True

    async def on_disable(self):
        """当插件被禁用时调用"""
        self.enabled = False

    async def on_message(self, message: Dict[str, Any]) -> str:
        """当收到消息时调用"""
        return None

    async def on_file_upload(self, file_path: str):
        """当文件被上传时调用"""
        pass

    def get_commands(self) -> List[Dict[str, str]]:
        """获取插件支持的命令列表"""
        return []

    async def handle_command(self, command: str, args: Dict[str, Any]) -> str:
        """处理插件命令"""
        return f"Command '{command}' not implemented for {self.name}"

    def get_help(self) -> str:
        """获取插件帮助信息"""
        commands = self.get_commands()
        if not commands:
            return f"{self.name} v{self.version}\n{self.description}\n该插件没有可用的命令。"
        
        help_text = f"{self.name} v{self.version}\n{self.description}\n\n可用命令:\n"
        for cmd in commands:
            help_text += f"/{cmd['name']} - {cmd['description']}\n"
        return help_text

    @classmethod
    def get_all_plugins(cls) -> Dict[str, Any]:
        """获取所有注册的插件"""
        return cls.plugins