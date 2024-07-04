from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import threading
from app.logger import logger

app = Flask(__name__)
CORS(app)

@app.route('/data/voice/<filename>', methods=['GET', 'POST'])
def voice_files(filename):
    logger.info(f"用户请求文件: {filename}")
    file_path = os.path.join('data/voice', filename)
    if os.path.exists(file_path):
        logger.info(f"文件存在: {file_path}")
        return send_from_directory('data/voice', filename, as_attachment=True)
    else:
        logger.info(f"文件不存在: {file_path}")
        return 'File not found', 404
