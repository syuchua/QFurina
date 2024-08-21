from abc import ABC, abstractmethod

class PluginBase(ABC):
    plugins = {}

    @classmethod
    def register(cls, name):
        def decorator(plugin_class):
            cls.plugins[name] = plugin_class
            return plugin_class
        return decorator

    def __init__(self):
        self.name = ""
        self.version = ""
        self.description = ""
        self.enabled = True
        self.event_handlers = {}
        self.priority = 0  # 默认优先级

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        self._priority = value

    def register_event_handler(self, event_name, handler):
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)

    async def trigger_event(self, event_name, *args, **kwargs):
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                await handler(*args, **kwargs)

    @abstractmethod
    async def on_load(self):
        """当插件被加载时调用"""
        pass

    @abstractmethod
    async def on_message(self, message):
        """当收到消息时调用"""
        pass

    @abstractmethod
    async def on_command(self, command, args):
        """当收到命令时调用"""
        pass

    @abstractmethod
    async def on_unload(self):
        """当插件被卸载时调用"""
        pass

    @abstractmethod
    async def on_receive(self, message):
        """当接收到消息时调用"""
        pass

    @abstractmethod
    async def on_send(self, message):
        """当发送消息时调用"""
        pass

    @abstractmethod
    async def on_file_upload(self, file_info):
        """当文件上传时调用"""
        pass

    @abstractmethod
    async def on_plugin_command(self, command, args):
        """当收到插件特定命令时调用"""
        pass

    @abstractmethod
    async def on_enable(self):
        pass

    @abstractmethod
    async def on_disable(self):
        pass

    @abstractmethod
    async def on_reload(self):
        pass