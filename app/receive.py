import json
from loguru import logger
import asyncio
import re
from app.database import MongoDB
from app.config import Config
from app.driver import receive_msg, send_msg, close, start_reverse_ws_server

config = Config.get_instance()

# 定义HTTP响应头
HttpResponseHeader = '''HTTP/1.1 200 OK
Content-Type: text/html
'''

# 解析请求内容为JSON
def request_to_json(msg):
    try:
        dicstrmsg = msg.split("\r\n\r\n")[-1]
        return json.loads(dicstrmsg)
    except json.JSONDecodeError as e:
        logger.info(f"Failed to parse JSON from request: {e}")
        return None

    
# 用于接收消息的队列
message_queue = asyncio.Queue(maxsize=config.MESSAGE_QUEUE_SIZE)
db=MongoDB()

# 捕获并处理优先级命令
async def handle_priority_command(rev_json):
    command_pattern = re.compile(r'^[!/#](reset|character|clear)(?:\s+(.+))?')
    user_input = rev_json.get('raw_message')
    match = command_pattern.match(user_input)
    if match:
        logger.info(f"Detected priority command: {user_input}")
        queue_with_priority = asyncio.Queue()
        queue_with_priority.put_nowait(rev_json)  # 将优先级命令放入新队列的最前端
        while not message_queue.empty():
            msg = message_queue.get_nowait()
            queue_with_priority.put_nowait(msg)
        while not queue_with_priority.empty():
            msg = queue_with_priority.get_nowait()
            await message_queue.put(msg)
        return True
    return False

async def handle_message(rev_json):
    user_input = rev_json.get('raw_message', '')
    user_id = rev_json.get('sender', {}).get('user_id')
    username = rev_json.get('sender', {}).get('nickname')
    group_id = rev_json.get('group_id')
    context_type = 'private' if rev_json.get('message_type') == 'private' else 'group'
    context_id = user_id if context_type == 'private' else group_id

    if user_input:
        db.insert_chat_message(user_id, user_input, '', context_type, context_id, username)

        if await handle_priority_command(rev_json):
            return

        await message_queue.put(rev_json)
    
    # logger.debug(f"Received message: {rev_json}")

async def start_http_server():
    async def handle_client(reader, writer):
        try:
            data = await reader.read(10240)
            if not data:
                logger.info("Received empty data.")
                return  

            request = data.decode('utf-8')
            rev_json = request_to_json(request)
            if rev_json is None:
                logger.info("Failed to parse JSON from request.")
                return  # 忽略无效请求

            await handle_message(rev_json)

            response = HttpResponseHeader + '\r\n\r\n'
            writer.write(response.encode('utf-8'))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handle_client, '127.0.0.1', port=3001)
    logger.info(f'Serving on {server.sockets[0].getsockname()}...')
    async with server:
        await server.serve_forever()

# 修改后的 start_reverse_ws 函数
async def start_reverse_ws():
    await start_reverse_ws_server('127.0.0.1', 8011, handle_message)  # 传递host和port参数
    logger.info("反向 WebSocket 服务器已启动，等待连接...")

# 异步的消息接收函数
async def rev_msg():
    return await message_queue.get()  # 直接从队列获取消息

__all__ = ['message_queue', 'start_http_server', 'start_reverse_ws', 'rev_msg']
