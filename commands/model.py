# *- model.py -*
"""
模型管理命令
"""
import json
import os
from app.Core.config import Config
from app.Core.decorators import admin_only
config = Config.get_instance()


@admin_only
async def handle_model_command(msg_type, user_info, new_model, send_msg):
    try:
        # 构建 model.json 的路径
        model_json_path = os.path.join('config', 'model.json')

        # 读取 model.json 文件
        with open(model_json_path, 'r', encoding='utf-8') as model_file:
            model_config_data = json.load(model_file)

        # 检查新模型是否在可用模型列表中
        available_models = []
        for model_type in model_config_data['models']:
            available_models.extend(model_config_data['models'][model_type]['available_models'])

        if new_model not in available_models:
            await send_msg(msg_type, user_info["recipient_id"], f"错误：'{new_model}' 不是可用的模型。可用的模型有：{', '.join(available_models)}")
            return

        # 更新模型
        model_config_data['model'] = new_model

        # 写回 model.json 文件
        with open(model_json_path, 'w', encoding='utf-8') as model_file:
            json.dump(model_config_data, model_file, indent=4, ensure_ascii=False)

        # 重新加载配置
        config.reload_config()

        await send_msg(msg_type, user_info["recipient_id"], f"模型已更新为 {new_model} 并且配置已成功重新加载。")
    except FileNotFoundError:
        await send_msg(msg_type, user_info["recipient_id"], "错误：无法找到 model.json 文件。")
    except json.JSONDecodeError:
        await send_msg(msg_type, user_info["recipient_id"], "错误：model.json 文件格式不正确。")
    except Exception as e:
        await send_msg(msg_type, user_info["recipient_id"], f"更新模型失败：{str(e)}")
