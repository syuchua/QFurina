from typing import Callable
from app.config import Config

config = Config.get_instance()

if config.CONNECTION_TYPE == 'http':
    from drivers.http_driver import HttpDriver as Driver
elif config.CONNECTION_TYPE == 'ws':
    from drivers.ws_driver import WebSocketDriver as Driver
elif config.CONNECTION_TYPE == 'ws_reverse':
    from drivers.ws_reverse import WsReverseDriver as Driver
else:
    raise ValueError("Unsupported connection type")

driver_instance = Driver()

async def start_reverse_ws_server(host: str, port: int, handler: Callable):
    await driver_instance.start_server(host, port, handler)

async def receive_msg(handler):
    await driver_instance.receive_msg(handler)

async def send_msg(msg_type, number, msg, use_voice=False):
    await driver_instance.send_msg(msg_type, number, msg, use_voice)

async def close():
    await driver_instance.close()
