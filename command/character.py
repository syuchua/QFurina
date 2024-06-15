# character.py
from app.config import SYSTEM_MESSAGE

def handle_character_command(msg_type, number, send_msg):
    character_info = SYSTEM_MESSAGE.get("character", "未定义的角色信息。")
    send_msg(msg_type, number, character_info)