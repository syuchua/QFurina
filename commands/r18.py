import json
from app.config import Config

config = Config.get_instance()

def handle_r18_command(msg_type, recipient_id, r18_mode, send_msg):
    if r18_mode not in ['0', '1', '2']:
        send_msg(msg_type, recipient_id, "无效的r18模式。可用模式为：0（关闭），1（开启），2（随机）。")
        return
    
    try:
        with open(config.R18, 'r', encoding='utf-8') as r18_file:
            config_data = json.load(r18_file)

        config_data['r18'] = int(r18_mode)

        with open(config.R18, 'w', encoding='utf-8') as r18_file:
            json.dump(config_data, r18_file, indent=4, ensure_ascii=False)

        config.reload_config()
        send_msg(msg_type, recipient_id, f"r18模式已更新为 {r18_mode}")
    except Exception as e:
        send_msg(msg_type, recipient_id, f"更新r18模式失败: {str(e)}")