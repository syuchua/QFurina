# process_plugin.py
from app.plugin.plugin_manager import plugin_manager
from app.logger import logger
from app.Core.decorators import async_timed
from utils.file import DATA_DIR, allowed_file
import os


@async_timed()
async def process_plugin_message(message):
    """处理插件消息"""
    try:
        plugin_result = await plugin_manager.handle_message(message)
        return plugin_result
    except Exception as e:
        logger.error(f"Error in process_plugin_message: {str(e)}")
        return None

@async_timed()
async def process_plugin_command(user_input, message):
    """处理插件命令"""
    try:
        for plugin in plugin_manager.enabled_plugins.values():
            command_response = await plugin.handle_command(user_input, message)
            if command_response:
                return command_response
        return None
    except Exception as e:
        logger.error(f"Error in process_plugin_command: {str(e)}")
        return None

@async_timed()
async def upload_file_for_plugin(file_path, file_type='image'):
    """
    为插件提供的文件上传函数
    """
    filename = os.path.basename(file_path)
    if allowed_file(filename):
        dest_dir = os.path.join(DATA_DIR, file_type)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        os.rename(file_path, dest_path)
        
        # 调用插件的on_file_upload方法
        upload_result = await plugin_manager.call_on_file_upload(dest_path)
        
        # 如果插件返回了自定义的URL，使用插件返回的URL
        if upload_result and isinstance(upload_result, str):
            return upload_result
        
        # 否则使用默认的URL
        return f'http://localhost:4321/data/{file_type}/{filename}'
    else:
        return None