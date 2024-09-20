# *- file.py -*
"""
文件上传模块
"""
import os
from flask import Flask, send_file, request
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from app.logger import logger
from app.plugin.plugin_manager import plugin_manager

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取项目根目录
DATA_DIR = os.path.join(BASE_DIR, 'data')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/data/<path:filename>', methods=['GET'])
def handle_file(filename):
    logger.info(f"用户请求文件: {filename}")
    file_path = os.path.join(DATA_DIR, filename)
    file_path = os.path.normpath(file_path)  # 规范化路径
    
    logger.info(f"尝试访问文件路径: {file_path}")
    if os.path.exists(file_path):
        logger.info(f"文件存在: {file_path}")
        return send_file(file_path, as_attachment=True)
    else:
        logger.info(f"文件不存在: {file_path}")
        return 'File not found', 404

@app.route('/upload', methods=['POST', 'GET'])
async def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_type = request.form.get('file_type', 'file')
        file_dir = os.path.join(DATA_DIR, file_type)
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, filename)
        file.save(file_path)
        is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'
        
        # 调用插件的on_file_upload方法
        upload_result = await plugin_manager.call_on_file_upload(file_path)
        
        # 如果插件返回了自定义的URL，使用插件返回的URL
        if upload_result and isinstance(upload_result, str):
            return upload_result, 200
        
        # 否则使用默认的URL
        return f'http://my_qbot:4321/data/{file_type}/{filename}' if is_docker else f'http://localhost:4321/data/{file_type}/{filename}' , 200
    else:
        return 'File type not allowed', 400

# 确保在 Flask 应用启动时创建必要的目录
os.makedirs(DATA_DIR, exist_ok=True)