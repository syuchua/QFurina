# command.py
from commands.help import handle_help_command
from commands.history import handle_clear_history_command, handle_history_command
from commands.music_list import handle_music_list_command
from commands.reset import handle_reset_command
from commands.character import handle_character_command
from commands.model import handle_model_command
from commands.r18 import handle_r18_command
from commands.switch import handle_switch_command  
from commands.plugin import (
    handle_enable_plugin,
    handle_disable_plugin,
    handle_list_plugins,
    handle_reload_plugin,
    handle_plugin_info
)

async def handle_command(command, msg_type, user_info, send_msg, context_type, context_id):
    parts = command.split(' ', 1)
    main_command = parts[0].lstrip('/#!')  # 移除触发符号
    args = parts[1] if len(parts) > 1 else ''

    try:
        if main_command == 'help':
            await handle_help_command(msg_type, user_info, send_msg)
        elif main_command == 'enable_plugin':
            await handle_enable_plugin(msg_type, user_info, args, send_msg)
        elif main_command == 'disable_plugin':
            await handle_disable_plugin(msg_type, user_info, args, send_msg)
        elif main_command == 'list_plugins':
            await handle_list_plugins(msg_type, user_info, send_msg)
        elif main_command == 'reload_plugin':
            await handle_reload_plugin(msg_type, user_info, args, send_msg)
        elif main_command == 'plugin_info':
            await handle_plugin_info(msg_type, user_info, args, send_msg)
        elif main_command == 'model':
            if not args:
                raise ValueError("缺少模型参数")
            await handle_model_command(msg_type, user_info, args, send_msg)
        elif main_command == 'r18':
            if not args or args not in ['0', '1', '2']:
                raise ValueError("无效的R18模式参数")
            await handle_r18_command(msg_type, user_info, args, send_msg)
        elif main_command == 'reset':
            await handle_reset_command(msg_type, user_info, send_msg)
        elif main_command == 'character':
            await handle_character_command(msg_type, user_info, send_msg)
        elif main_command == 'music_list':
            await handle_music_list_command(msg_type, user_info, send_msg)
        elif main_command == 'shutdown':
            await handle_switch_command(msg_type, user_info, 'shutdown', send_msg)
        elif main_command == 'restart':
            await handle_switch_command(msg_type, user_info, 'restart', send_msg)
        elif main_command == 'history':
            count = None
            if args:
                try:
                    count = int(args)
                except ValueError:
                    await send_msg(msg_type, user_info["recipient_id"], "请在 history 后输入一个有效的数字。")
                    return
            await handle_history_command(msg_type, user_info, context_type, context_id, send_msg, count)
        elif main_command == 'clear':
            count = None
            if args:
                try:
                    count = int(args)
                except ValueError:
                    await send_msg(msg_type, user_info["recipient_id"], "请在 clear 后输入一个有效的数字。")
                    return
            await handle_clear_history_command(msg_type, user_info, context_type, context_id, send_msg, count)
        else:
            raise ValueError(f"未知的命令: {main_command}")
    except ValueError as e:
        error_message = f"命令错误: {str(e)}\n使用 'help' 命令获取帮助信息。"
        await send_msg(msg_type, user_info["recipient_id"], error_message)
    except Exception as e:
        error_message = f"执行命令时发生错误: {str(e)}\n请稍后再试或联系管理员。"
        await send_msg(msg_type, user_info["recipient_id"], error_message)