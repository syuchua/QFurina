import os


MUSIC_DIRECTORY = 'data/music'
MUSIC_FILES = [f for f in os.listdir(MUSIC_DIRECTORY) if f.endswith(('.mp3', '.wav'))]
MUSIC_INFO = {os.path.splitext(f)[0]: f for f in MUSIC_FILES}

async def handle_music_list_command(msg_type, user_info, send_msg):
    if MUSIC_INFO:
        song_list = "\n".join(MUSIC_INFO.keys())
        await send_msg(msg_type, user_info["recipient_id"], f"可用的歌曲列表：\n{song_list}")
    else:
        await send_msg(msg_type, user_info["recipient_id"], "当前没有可用的歌曲。")
