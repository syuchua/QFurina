# memory_generator.py 记忆生成器
"""
记忆生成器 (MemoryGenerator)

这个模块实现了一个动态的记忆生成系统，用于总结和管理聊天机器人的对话历史。
系统分为短期记忆和中期记忆两个层次，通过定期生成摘要来保持对话的上下文理解。

主要特点和工作原理：

1. 双层记忆系统：
   - 短期记忆：关注最近的对话，更新频率较高。
   - 中期记忆：覆盖更长时间的对话历史，提供更广泛的上下文。

2. 动态更新机制：
   - 基于时间和消息数量的混合触发机制。
   - 设置最小消息数量阈值，防止在消息稀少时过于频繁地生成摘要。
   - 设置最大时间间隔，确保即使在低活跃度时期也能定期更新记忆。

3. 防刷屏机制：
   - 消息数量不作为独立的触发条件，而是作为时间判断的辅助条件。
   - 这样可以防止用户通过短时间内发送大量消息来强制触发记忆生成。

4. 记忆生成条件：
   短期记忆：
   - 距离上次更新已过去10分钟，且至少有10条新消息；或
   - 距离上次更新已过去1小时（最长间隔）。
   
   中期记忆：
   - 距离上次更新已过去1小时，且至少有50条新消息；或
   - 距离上次更新已过去24小时（最长间隔）。

5. 缓冲区管理：
   - 使用固定大小的缓冲区（deque）来存储最近的消息。
   - 短期记忆缓冲区大小为20条消息，中期记忆缓冲区大小为200条消息。
   - 当生成摘要时，只使用最近的最小消息数量（短期10条，中期50条）。

6. 摘要生成：
   - 使用外部的AI模型（通过get_chat_response函数）来生成对话摘要。
   - 摘要生成时会考虑消息的角色（如用户或助手）以保持上下文的连贯性。

使用说明：
- 实例化MemoryGenerator类。
- 对每条新消息调用add_message方法。
- 使用get_memories方法获取当前的记忆摘要。

注意事项：
- 确保正确配置和实现get_chat_response函数以与AI模型交互。
- 可以根据具体需求调整时间间隔、消息数量阈值等参数。
- 日志记录功能有助于监控和调试记忆生成过程。

"""

from collections import deque
from typing import List, Dict
from app.Core.config import Config
from utils.model_request import get_chat_response
from app.logger import logger
from ..Core.decorators import async_timed
import time

config = Config.get_instance()

class MemoryGenerator:
    """记忆生成器"""
    def __init__(self):
        self.short_term_buffer = deque(maxlen=20)  # 增加缓冲区大小以适应新策略
        self.mid_term_buffer = deque(maxlen=200)   # 增加缓冲区大小以适应新策略
        self.short_term_memory = ""
        self.mid_term_memory = ""
        self.last_short_term_update = time.time()
        self.last_mid_term_update = time.time()
        self.SHORT_TERM_INTERVAL = 600  # 10分钟
        self.MID_TERM_INTERVAL = 3600  # 1小时
        self.MAX_SHORT_TERM_INTERVAL = 3600  # 最长1小时
        self.MAX_MID_TERM_INTERVAL = 86400  # 最长24小时
        self.MIN_SHORT_TERM_MESSAGES = 20
        self.MIN_MID_TERM_MESSAGES = 150

    async def add_message(self, message: Dict[str, str], context_type: str = None, context_id: str = None):
        # 如果需要，可以在这里使用 context_type 和 context_id
        current_time = time.time()
        self.short_term_buffer.append(message)
        self.mid_term_buffer.append(message)

        # 短期记忆生成
        time_since_last_update = current_time - self.last_short_term_update
        if (time_since_last_update >= self.SHORT_TERM_INTERVAL and len(self.short_term_buffer) >= self.MIN_SHORT_TERM_MESSAGES) or \
           time_since_last_update >= self.MAX_SHORT_TERM_INTERVAL:
            await self.generate_short_term_memory()
            self.last_short_term_update = current_time

        # 中期记忆生成
        time_since_last_update = current_time - self.last_mid_term_update
        if (time_since_last_update >= self.MID_TERM_INTERVAL and len(self.mid_term_buffer) >= self.MIN_MID_TERM_MESSAGES) or \
           time_since_last_update >= self.MAX_MID_TERM_INTERVAL:
            await self.generate_mid_term_memory()
            self.last_mid_term_update = current_time

    # 生成短期记忆
    @async_timed()
    async def generate_short_term_memory(self):
        messages = list(self.short_term_buffer)
        logger.info(f"Generating short-term memory with {len(messages)} messages")
        summary = await self._generate_summary(messages[-self.MIN_SHORT_TERM_MESSAGES:], "short term")
        self.short_term_memory = summary
        logger.info(f"生成短期记忆: {summary}")

    # 生成中期记忆
    @async_timed()
    async def generate_mid_term_memory(self):
        messages = list(self.mid_term_buffer)
        logger.info(f"Generating mid-term memory with {len(messages)} messages")
        summary = await self._generate_summary(messages[-self.MIN_MID_TERM_MESSAGES:], "mid term")
        self.mid_term_memory = summary
        logger.info(f"生成中期记忆: {summary}")

    # 生成记忆摘要
    @async_timed()
    async def _generate_summary(self, messages: List[Dict[str, str]], memory_type: str) -> str:
        prompt = f"请将以下对话总结为简洁的{memory_type}记忆。重点放在关键点和整体上下文："
        for msg in messages:
            prompt += f"\n{msg['role']}: {msg['content']}"
        prompt += f"\nSummary:"

        response = await get_chat_response([{"role": "user", "content": prompt}])
        return response.strip()

    # 获取记忆
    def get_memories(self, context_type: str = None, context_id: str = None) -> Dict[str, str]:
        return {
            "short_term": self.short_term_memory,
            "mid_term": self.mid_term_memory
        }

# 创建记忆生成器实例
memory_generator = MemoryGenerator()
