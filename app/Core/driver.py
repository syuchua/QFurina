from typing import Callable
from ..Core.config import Config

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
    if msg_type == 'private':
        await driver_instance.call_api('send_private_msg', user_id=number, message=msg)
    elif msg_type == 'group':
        await driver_instance.call_api('send_group_msg', group_id=number, message=msg)
    else:
        raise ValueError(f"Unsupported message type: {msg_type}")

async def call_api(api, **params):
    return await driver_instance.call_api(api, **params)

async def close():
    await driver_instance.close()
