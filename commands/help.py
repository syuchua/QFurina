# help.py
async def handle_help_command(msg_type, number, send_msg):
        help_message = (
            "这是帮助信息：命令前请跟上/，#，或!\n"
            "1. 使用 'help' 命令获取帮助信息。\n"
            "2. 使用 'reset' 命令重置当前会话。\n"
            "3. 使用 'character' 命令获取当前系统角色信息。\n"
            "4. 发送'发一张'，'来一张'+关键词 获取指定关键词图片。\n"
            "5. 发送'来份涩图'，'来份色图'， '再来一张' 获取随机图片。\n"
            "6. 发送'画一张'，'生成一张'+关键词 获取AI绘画。\n"
            "7. 发送'语音回复'，'用声音说'，'语音说'+文本 获取语音回复。\n"
            "8. 使用 'history' 命令获取历史消息。\n"
            "9. 使用 'clear' 命令清除历史消息。\n"
        )
        await  send_msg(msg_type, number, help_message)
