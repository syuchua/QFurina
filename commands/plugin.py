from app.plugin.plugin_manager import PluginManager
from app.plugin.plugin_base import PluginBase
from app.decorators import admin_only
from app.logger import logger

plugin_manager = PluginManager()

@admin_only
async def handle_enable_plugin(msg_type, user_info, plugin_name, send_msg):
    try:
        if await plugin_manager.enable_plugin(plugin_name):
            await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 已启用")
        else:
            await send_msg(msg_type, user_info['recipient_id'], f"无法启用插件 {plugin_name}")
    except Exception as e:
        logger.error(f"启用插件 {plugin_name} 时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], f"启用插件 {plugin_name} 时发生错误")

@admin_only
async def handle_disable_plugin(msg_type, user_info, plugin_name, send_msg):
    try:
        if await plugin_manager.disable_plugin(plugin_name):
            await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 已禁用")
        else:
            await send_msg(msg_type, user_info['recipient_id'], f"无法禁用插件 {plugin_name}")
    except Exception as e:
        logger.error(f"禁用插件 {plugin_name} 时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], f"禁用插件 {plugin_name} 时发生错误")

@admin_only
async def handle_list_plugins(msg_type, user_info, send_msg):
    try:
        enabled_plugins = ", ".join(plugin_manager.plugins.keys())
        disabled_plugins = ", ".join(set(PluginBase.plugins.keys()) - set(plugin_manager.plugins.keys()))
        plugin_list = f"已启用的插件: {enabled_plugins}\n已禁用的插件: {disabled_plugins}"
        await send_msg(msg_type, user_info['recipient_id'], plugin_list)
    except Exception as e:
        logger.error(f"列出插件时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], "列出插件时发生错误")

@admin_only
async def handle_reload_plugin(msg_type, user_info, plugin_name, send_msg):
    try:
        await plugin_manager.reload_plugin(plugin_name)
        await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 已重新加载")
    except Exception as e:
        logger.error(f"重新加载插件 {plugin_name} 时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], f"重新加载插件 {plugin_name} 时发生错误")