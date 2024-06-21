import json
import logging
import asyncio

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
    dicstrmsg = msg.split("\r\n\r\n")[-1]
    return json.loads(dicstrmsg)

# 用于接收消息的队列
message_queue = asyncio.Queue()

# 异步处理连接
async def handle_client(reader, writer):
    try:
        data = await reader.read(10240)
        request = data.decode('utf-8')
        logging.info(f"Received request: {request}")

        rev_json = request_to_json(request)
        await message_queue.put(rev_json)  # 将消息放入队列

        response = HttpResponseHeader + '\r\n\r\n'
        writer.write(response.encode('utf-8'))
        await writer.drain()
    except Exception as e:
        logging.error(f"Error during client handling: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

# 启动异步服务器
async def start_server():
    server = await asyncio.start_server(handle_client, '127.0.0.1', LISTEN_PORT)
    logging.info(f'Serving on {server.sockets[0].getsockname()}')

    async with server:
        await server.serve_forever()

# 异步的消息接收函数
async def rev_msg():
    return await message_queue.get()  # 直接从队列获取消息