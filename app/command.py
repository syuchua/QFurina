# app/command.py

from command.help import handle_help_command
from command.reset import handle_reset_command
from command.character import handle_character_command

def handle_command(command, msg_type, number, send_msg):
    if command == 'help':
        handle_help_command(msg_type, number, send_msg)
    elif command == 'reset':
        handle_reset_command(msg_type, number, send_msg)
    elif command == 'character':
        handle_character_command(msg_type, number, send_msg)
    else:
        send_msg(msg_type, number, "未知的命令。使用 'help' 命令获取帮助信息。")