import json
from app.config import Config
config = Config.get_instance()

async def handle_model_command(msg_type, number, new_model, send_msg):
    try:
        with open(config.MODEL_NAME, 'r', encoding='utf-8') as model_file:
            model_config_data = json.load(model_file)

        model_config_data['model'] = new_model

        with open(config.MODEL_NAME, 'w', encoding='utf-8') as model_file:
            json.dump(model_config_data, model_file, indent=4, ensure_ascii=False)

        config.reload_config()

        await send_msg(msg_type, number, f"Model updated to {new_model} and configuration reloaded successfully.")
    except Exception as e:
        await send_msg(msg_type, number, f"Failed to update model: {str(e)}")