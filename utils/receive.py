import json
from loguru import logger
import asyncio
import re
from app.database import MongoDB
from app.config import Config
from app.driver import close, start_reverse_ws_server, call_api

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
db = MongoDB()

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
    if 'post_type' not in rev_json:
        logger.warning(f"Received unexpected message format: {rev_json}")
        return

    if rev_json['post_type'] == 'message':
        user_input = rev_json.get('raw_message', '')
        user_id = rev_json.get('sender', {}).get('user_id')
        # username = rev_json.get('sender', {}).get('nickname')
        group_id = rev_json.get('group_id')
        context_type = 'private' if rev_json.get('message_type') == 'private' else 'group'
        context_id = user_id if context_type == 'private' else group_id

        if user_input:
            db.insert_chat_message(user_id, user_input, '', context_type, context_id)

            if await handle_priority_command(rev_json):
                return

            # 要屏蔽的id
            block_id = config.BLOCK_ID

            if user_id not in block_id:
                await message_queue.put(rev_json)
    
    elif rev_json['post_type'] == 'meta_event' and rev_json['meta_event_type'] == 'heartbeat':
        # 处理心跳事件
        logger.debug("Received heartbeat")
    else:
        # 处理其他类型的事件
        logger.debug(f"Received event: {rev_json['post_type']}")

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

async def start_reverse_ws():
    await start_reverse_ws_server('127.0.0.1', 8011, handle_message)
    logger.info("反向 WebSocket 服务器已启动，等待连接...")

async def close_connection():
    try:
        if config.CONNECTION_TYPE == 'http':
            # 如果有 HTTP 服务器需要关闭，在这里添加关闭逻辑
            pass
        elif config.CONNECTION_TYPE == 'ws_reverse':
            # 关闭 WebSocket 连接
            await close()
        
        # 清空消息队列
        while not message_queue.empty():
            try:
                message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info("连接已关闭")
    except Exception as e:
        logger.error(f"关闭连接时发生错误: {e}")

# 异步的消息接收函数
async def rev_msg():
    try:
        message = await message_queue.get()
        logger.debug(f"Retrieved message from queue: {message}")
        return message
    except Exception as e:
        logger.error(f"Error retrieving message from queue: {e}")
        return None

__all__ = ['message_queue', 'start_http_server', 'start_reverse_ws', 'rev_msg', 'call_api', 'close_connection']
