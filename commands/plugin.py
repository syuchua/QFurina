from app.plugin.plugin_manager import plugin_manager
from app.Core.decorators import admin_only
from app.logger import logger
from app.Core.config import Config

config = Config.get_instance()

@admin_only
async def handle_enable_plugin(msg_type, user_info, plugin_name, send_msg):
    try:
        if await plugin_manager.enable_plugin(plugin_name):
            config.ENABLED_PLUGINS.append(plugin_name)
            config.save_config()
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
            config.ENABLED_PLUGINS.remove(plugin_name)
            config.save_config()
            await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 已禁用")
        else:
            await send_msg(msg_type, user_info['recipient_id'], f"无法禁用插件 {plugin_name}")
    except Exception as e:
        logger.error(f"禁用插件 {plugin_name} 时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], f"禁用插件 {plugin_name} 时发生错误")

@admin_only
async def handle_list_plugins(msg_type, user_info, send_msg):
    try:
        all_plugins = plugin_manager.get_all_plugins_info()
        enabled_plugins = [f"{p['register_name']} ({p['name']})" for p in all_plugins if p['enabled']]
        disabled_plugins = [f"{p['register_name']} ({p['name']})" for p in all_plugins if not p['enabled']]
        
        plugin_list = "已启用的插件:\n" + "\n".join(enabled_plugins)
        plugin_list += "\n\n已禁用的插件:\n" + "\n".join(disabled_plugins)
        
        await send_msg(msg_type, user_info['recipient_id'], plugin_list)
    except Exception as e:
        logger.error(f"列出插件时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], "列出插件时发生错误")

@admin_only
async def handle_reload_plugin(msg_type, user_info, plugin_name, send_msg):
    try:
        if plugin_name in plugin_manager.plugins:
            await plugin_manager.disable_plugin(plugin_name)
            await plugin_manager.unload_plugins()
            await plugin_manager.load_plugins()
            if plugin_name in config.ENABLED_PLUGINS:
                await plugin_manager.enable_plugin(plugin_name)
            await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 已重新加载")
        else:
            await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 不存在")
    except Exception as e:
        logger.error(f"重新加载插件 {plugin_name} 时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], f"重新加载插件 {plugin_name} 时发生错误")

@admin_only
async def handle_plugin_info(msg_type, user_info, plugin_name, send_msg):
    try:
        plugin_info = next((p for p in plugin_manager.get_all_plugins_info() if p['register_name'] == plugin_name), None)
        if plugin_info:
            info_text = f"插件名称: {plugin_info['name']}\n"
            info_text += f"版本: {plugin_info['version']}\n"
            info_text += f"描述: {plugin_info['description']}\n"
            info_text += f"状态: {'已启用' if plugin_info['enabled'] else '已禁用'}"
            await send_msg(msg_type, user_info['recipient_id'], info_text)
        else:
            await send_msg(msg_type, user_info['recipient_id'], f"插件 {plugin_name} 不存在")
    except Exception as e:
        logger.error(f"获取插件 {plugin_name} 信息时发生错误: {str(e)}")
        await send_msg(msg_type, user_info['recipient_id'], f"获取插件 {plugin_name} 信息时发生错误")