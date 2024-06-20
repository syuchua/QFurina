from commands.help import handle_help_command
from commands.reset import handle_reset_command
from commands.character import handle_character_command
from commands.model import handle_model_command
from commands.r18 import handle_r18_command  

def handle_command(command, msg_type, recipient_id, send_msg):
    parts = command.split(' ', 1)
    main_command = parts[0]
    args = parts[1] if len(parts) > 1 else ''

    if main_command == 'help':
        handle_help_command(msg_type, recipient_id, send_msg)
    elif main_command == 'reset':
        handle_reset_command(msg_type, recipient_id, send_msg)
    elif main_command == 'character':
        handle_character_command(msg_type, recipient_id, send_msg)
    elif main_command == 'model':
        if args:  # model 命令需要一个额外的参数
            new_model = args
            handle_model_command(msg_type, recipient_id, new_model, send_msg)
        else:
            send_msg(msg_type, recipient_id, "Usage: !model <new_model>")
    elif main_command == 'r18':
        if args:  # r18 命令需要一个额外的参数
            r18_mode = args
            handle_r18_command(msg_type, recipient_id, r18_mode, send_msg)
        else:
            send_msg(msg_type, recipient_id, "Usage: /r18 <mode>，其中 <mode> 可以是 0, 1 或 2")
    else:
        send_msg(msg_type, recipient_id, "未知的命令。使用 'help' 命令获取帮助信息。")