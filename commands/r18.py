# commands/r18.py
import json
import os
from app.config import Config
from app.decorators import admin_only
config = Config.get_instance()

CONFIG_FILE_PATH = 'config/config.json'

@admin_only
async def handle_r18_command(msg_type, recipient_id, r18_mode, send_msg):
    if r18_mode not in ['0', '1', '2']:
        await send_msg(msg_type, recipient_id, "无效的r18模式。可用模式为：0（关闭），1（开启），2（随机）。")
        return
    
    try:
        # 读取 config.json 文件
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as config_file:
            config_data = json.load(config_file)

        # 更新 r18 设置
        config_data['r18'] = int(r18_mode)

        # 写回 config.json 文件
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as config_file:
            json.dump(config_data, config_file, indent=4, ensure_ascii=False)

        # 重新加载配置
        config.reload_config()

        await send_msg(msg_type, recipient_id, f"r18模式已更新为 {r18_mode}")
    except FileNotFoundError:
        await send_msg(msg_type, recipient_id, "错误：无法找到配置文件。")
    except json.JSONDecodeError:
        await send_msg(msg_type, recipient_id, "错误：配置文件格式不正确。")
    except Exception as e:
        await send_msg(msg_type, recipient_id, f"更新r18模式失败: {str(e)}")
