# help.py
def handle_help_command(msg_type, number, send_msg):
    help_message = (
        "这是帮助信息：你知道的太多了\n"
        "1. 使用 'help' 命令获取帮助信息。\n"
        "2. 使用 'reset' 命令重置当前会话。\n"
        "3. 使用 'character' 命令获取当前系统角色信息。\n"
    )
    send_msg(msg_type, number, help_message)