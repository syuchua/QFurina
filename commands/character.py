# character.py
from app.config import Config
from app.decorators import admin_only
config = Config.get_instance()


@admin_only
async def handle_character_command(msg_type, number, send_msg):
    character_info = config.SYSTEM_MESSAGE.get("character", "未定义的角色信息。")
    await send_msg(msg_type, number, character_info)
