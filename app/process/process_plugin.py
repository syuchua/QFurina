# process_plugin.py
from ..plugin.plugin_manager import plugin_manager
from app.logger import logger
from ..Core.decorators import async_timed

@async_timed()
async def process_plugin_message(rev, msg_type, *args, **kwargs):
    #logger.debug(f"process_plugin_message called with: rev={rev}, msg_type={msg_type}, args={args}, kwargs={kwargs}")
    result = await plugin_manager.call_on_message(rev, msg_type, *args, **kwargs)
    #logger.debug(f"process_plugin_message result: {result}")
    return result

@async_timed()
async def process_plugin_command(command, msg_type, user_info, send_msg, context_type, context_id):
    return await plugin_manager.call_on_command(command, msg_type, user_info, send_msg, context_type, context_id)