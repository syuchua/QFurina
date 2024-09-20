# *- blocked.py -*
"""
屏蔽词管理命令
"""
from app.Core.filters import word_filter
from app.Core.decorators import admin_only
from app.logger import logger

@admin_only
async def handle_block_word_command(msg_type, user_info, args, send_msg):
    args_list = args.split()
    if len(args_list) < 2:
        await send_msg(msg_type, user_info['recipient_id'], "使用方法：/block_word add/remove 词语")
        return

    action = args_list[0]
    word = ' '.join(args_list[1:])

    try:
        if action == 'add':
            word_filter.add_blocked_word(word)
            await send_msg(msg_type, user_info['recipient_id'], f"已添加屏蔽词：{word}")
            logger.info(f"Added blocked word: {word}")
        elif action == 'remove':
            word_filter.remove_blocked_word(word)
            await send_msg(msg_type, user_info['recipient_id'], f"已移除屏蔽词：{word}")
            logger.info(f"Removed blocked word: {word}")
        else:
            await send_msg(msg_type, user_info['recipient_id'], "无效的操作。请使用 'add' 或 'remove'。")
    except Exception as e:
        error_message = f"处理屏蔽词时发生错误: {str(e)}"
        logger.error(error_message)
        await send_msg(msg_type, user_info['recipient_id'], error_message)