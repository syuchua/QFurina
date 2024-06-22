import json
import logging
import asyncio
import re

# 用于创建日志记录
logging.basicConfig(level=logging.INFO)

# 定义监听端口
LISTEN_PORT = 3001

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
        logging.info(f"Failed to parse JSON from request: {e}")
        return None

    
# 用于接收消息的队列
message_queue = asyncio.Queue()

# 捕获并处理优先级命令
async def handle_priority_command(rev_json):
    command_pattern = re.compile(r'^[!/#](reset|character)(?:\s+(.+))?')
    user_input = rev_json.get('raw_message')
    match = command_pattern.match(user_input)
    if match:
        logging.info(f"Detected priority command: {user_input}")
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

# 异步处理连接
async def handle_client(reader, writer):
    try:
        data = await reader.read(10240)
        if not data:
            logging.info("Received empty data.")
            return  

        request = data.decode('utf-8')
        logging.info(f"Received request: {request}")

        rev_json = request_to_json(request)
        if rev_json is None:
            logging.info("Failed to parse JSON from request.")
            return  # 忽略无效请求

        # 如果是优先级命令，直接处理
        if await handle_priority_command(rev_json):
            response = HttpResponseHeader + '\r\n\r\n'
            writer.write(response.encode('utf-8'))
            await writer.drain()
            return

        await message_queue.put(rev_json)  # 将普通消息放入队列

        response = HttpResponseHeader + '\r\n\r\n'
        writer.write(response.encode('utf-8'))
        await writer.drain()
    except Exception as e:
        logging.info(f"Error during client handling: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

# 启动异步服务器
async def start_server():
    server = await asyncio.start_server(handle_client, '127.0.0.1', LISTEN_PORT)
    logging.info(f'Serving on {server.sockets[0].getsockname()}...')
    print(f'Serving on {server.sockets[0].getsockname()}...')

    async with server:
        await server.serve_forever()

# 异步的消息接收函数
async def rev_msg():
    return await message_queue.get()  # 直接从队列获取消息