import streamlit as st
import json
import os
import sys
from app.Core.config import Config

#st.set_option('browser.gatherUsageStats', False)

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def run_streamlit_app():
    st.set_page_config(page_title="QFurina 配置", layout="wide")
    st.title('QFurina 配置')

    # 获取Config实例
    config_instance = Config.get_instance()

    # 加载配置
    config = load_config('config/config.json')
    model_config = load_config('config/model.json')

    # 创建侧边栏用于切换不同的配置部分
    section = st.sidebar.radio("选择配置部分", ["基础配置", "模型配置", "系统消息", "插件配置"])

    if section == "基础配置":
        st.header("基础配置")
        st.info("注意：如果使用 GPT 系列模型，请在此处填写 API Key，并忽略模型配置部分。")
        
        col1, col2 = st.columns(2)
        with col1:
            config['api_key'] = st.text_input("API Key", config.get('api_key', ''))
            config['model'] = st.text_input("模型名称(可选，默认gpt-3.5-turbo)", config.get('model', 'gpt-3.5-turbo'))
            config['self_id'] = st.number_input("Self ID（机器人QQ号）", value=config.get('self_id', 0))
        with col2:
            config['admin_id'] = st.number_input("Admin ID（管理员QQ号）", value=config.get('admin_id', 0))
            config['reply_probability'] = st.slider("回复概率（越接近1，回复概率越高，1为必定回复，0为必定不回复）", 0.0, 1.0, config.get('reply_probability', 0.024))
        
        config['r18'] = st.select_slider("色图接口R18 级别（0为非R18，1为允许R18，2为随机）", options=[0, 1, 2], value=config.get('r18', 2))
        
        st.info("默认的 base_url 是 https://api.openai.com/v1")
        config['base_url'] = st.text_input("Base URL (可选)", config.get('base_url', 'https://api.openai.com/v1'))

    elif section == "模型配置":
        st.header("模型配置")
        st.info("这里的配置适用于非 GPT 系列模型。如果使用 GPT 模型，请在基础配置中设置。")
        
        model_types = list(model_config.get('models', {}).keys())
        selected_model_type = st.selectbox("选择模型类型", model_types)
        
        if selected_model_type:
            st.subheader(f"{selected_model_type} 配置")
            model_details = model_config['models'][selected_model_type]
            
            col1, col2 = st.columns(2)
            with col1:
                model_details['api_key'] = st.text_input(f"{selected_model_type} API Key", model_details.get('api_key', ''))
            with col2:
                model_details['base_url'] = st.text_input(f"{selected_model_type} Base URL", model_details.get('base_url', ''))
            
            available_models = model_details.get('available_models', [])
            selected_model = st.selectbox(f"选择 {selected_model_type} 模型", available_models, index=0 if available_models else None)
            if selected_model:
                model_details['model'] = selected_model

    elif section == "系统消息":
        st.header("系统消息")
        config['system_message'] = config.get('system_message', {})
        config['system_message']['character'] = st.text_area("角色设定", config['system_message'].get('character', ''), height=300)
        st.info("在这里设置 AI 的角色和行为规则。这将影响 AI 的回复风格和内容。")

    elif section == "插件配置":
        st.header("插件配置")
        all_plugins = config.get('enabled_plugins', [])
        enabled_plugins = st.multiselect("启用的插件", all_plugins, default=all_plugins)
        config['enabled_plugins'] = enabled_plugins
        st.info("选择要启用的插件。这些插件将增强 AI 的功能。")

    # 保存按钮
    if st.button('保存配置'):
        save_config(config, 'config/config.json')
        save_config(model_config, 'config/model.json')
        
        # 重新加载配置
        config_instance.reload_config()
        
        st.success('配置已保存并重新加载')

if __name__ == "__main__":
    run_streamlit_app()