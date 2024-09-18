from app.Core.filters import WordFilter
from app.Core.decorators import admin_only

@admin_only
async def handle_block_word_command(msg_type, user_info, args, send_msg):
    if len(args) < 2:
        await send_msg(msg_type, user_info['recipient_id'], "使用方法：/block_word add/remove 词语")
        return

    action, word = args[0], ' '.join(args[1:])

    if action == 'add':
        WordFilter.add_blocked_word(word)
        await send_msg(msg_type, user_info['recipient_id'], f"已添加屏蔽词：{word}")
    elif action == 'remove':
        WordFilter.remove_blocked_word(word)
        await send_msg(msg_type, user_info['recipient_id'], f"已移除屏蔽词：{word}")
    else:
        await send_msg(msg_type, user_info['recipient_id'], "无效的操作。请使用 'add' 或 'remove'。")