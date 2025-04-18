# help.py
async def handle_help_command(msg_type, user_info, send_msg):
        help_message = (
            "这是帮助信息：命令前请跟上/，#，或!\n"
            "1. 使用 'help' 命令获取帮助信息。\n"
            "2. 使用 'reset' 命令重置当前会话。\n"
            "3. 使用 'character' 命令获取当前系统角色信息。\n"
            "4. 发送 '发一张'，'来一张'+关键词 获取指定关键词图片。\n"
            "5. 发送 '来份涩图'，'来份色图'， '再来一张' 获取随机图片。\n"
            "6. 发送 '画一张'，'生成一张'+关键词 获取AI绘画。\n"
            "7. 发送 '语音回复'，'用声音说'，'语音说'+文本 获取语音回复。\n"
            "8. 发送 '点歌'+歌曲名 点歌。\n"
            "9. 使用 'history' 命令获取历史消息，默认十条，可接数字。\n"
            "10. 使用 'clear' 命令清除历史消息，默认十条，可接数字。\n"
            "11. 使用 'music_list'命令获取可用的音乐列表。\n"
            "12. 使用 'r18'+[0, 1, 2]命令切换涩图接口r18模式。0为关闭r18，1为开启，2为随机\n"
            "13. 使用 'model'+模型名命令切换AI模型。对应模型需先再model.json中配置好。\n"
            "14. 使用 'shutdown'命令关闭机器人。\n"
            "15. 使用 'restart'命令重启\n"
            "16. 使用 'block_word'命令+add/remove管理屏蔽词。\n"
            "17. 使用 'enable_plugin'命令+插件名 启用插件。\n"
            "18. 使用 'disable_plugin'命令+插件名 禁用插件。\n"
            "19. 使用 'list_plugins'命令获取所有插件列表。\n"
            "20. 使用 'plugin_info'命令+插件名 获取指定插件信息。\n"
            "21. 使用 'plugin'命令+GitHub仓库URL 下载指定插件。\n"
        )
        await  send_msg(msg_type, user_info["recipient_id"], help_message)
