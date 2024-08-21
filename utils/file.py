from flask import Flask, send_file
from flask_cors import CORS
import os
from app.plugin.plugin_manager import PluginManager
from app.logger import logger

plugin_manager = PluginManager()
app = Flask(__name__)
CORS(app)

@app.route('/data/voice/<filename>', methods=['GET', 'POST'])
def voice_files(filename):
    logger.info(f"用户请求文件: {filename}")
    currend_work_dir = os.getcwd()
    logger.debug(f"当前工作目录: {currend_work_dir}")
    file_path = os.path.join(f'{currend_work_dir}/data/voice', filename)
    if os.path.exists(file_path):
        logger.info(f"文件存在: {file_path}")
        # 调用插件的on_file_upload方法
        #await plugin_manager.call_on_file_upload(file_path)
        return send_file(file_path,as_attachment=True)
    else:
        logger.info(f"文件不存在: {file_path}")
        return 'File not found', 404

@app.route('/data/music/<filename>', methods=['GET', 'POST'])
def music_files(filename):
    logger.info(f"用户请求文件: {filename}")
    currend_work_dir = os.getcwd()
    logger.debug(f"当前工作目录: {currend_work_dir}")
    file_path = os.path.join(f'{currend_work_dir}/data/music', filename)
    if os.path.exists(file_path):
        logger.info(f"文件存在: {file_path}")
        # 调用插件的on_file_upload方法
        #await plugin_manager.call_on_file_upload(file_path)
        return send_file(file_path,as_attachment=True)
    else:
        logger.info(f"文件不存在: {file_path}")
        return 'File not found', 404