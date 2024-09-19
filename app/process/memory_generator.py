# memory_generator.py 记忆生成器
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
        self.short_term_buffer = deque(maxlen=20)
        self.mid_term_buffer = deque(maxlen=150)
        self.short_term_memory = ""
        self.mid_term_memory = ""
        self.long_term_memory = ""
        self.last_short_term_update = 0
        self.last_mid_term_update = 0

    async def add_message(self, message: Dict[str, str]):
        self.short_term_buffer.append(message)
        self.mid_term_buffer.append(message)

        current_time = time.time()
        if len(self.short_term_buffer) == 20: # or current_time - self.last_short_term_update > 3600:
            await self.generate_short_term_memory()
            self.last_short_term_update = current_time

        if len(self.mid_term_buffer) == 150: # or current_time - self.last_mid_term_update > 86400:
            await self.generate_mid_term_memory()
            self.last_mid_term_update = current_time

    # 生成短期记忆
    @async_timed()
    async def generate_short_term_memory(self):
        messages = list(self.short_term_buffer)
        summary = await self._generate_summary(messages, "short term", self.short_term_memory)
        self.short_term_memory = summary
        logger.info(f"生成短期记忆: {summary}")

    # 生成中期记忆
    @async_timed()
    async def generate_mid_term_memory(self):
        messages = list(self.mid_term_buffer)
        summary = await self._generate_summary(messages, "mid term", self.mid_term_memory)
        self.mid_term_memory = summary
        logger.info(f"生成中期记忆: {summary}")

    # 生成记忆摘要
    @async_timed()
    async def _generate_summary(self, messages: List[Dict[str, str]], memory_type: str, previous_summary: str) -> str:
        prompt = f"请将以下对话总结为简洁的{memory_type}记忆。请关注关键点和整体上下文。上次总结: {previous_summary}\n\n新对话:"
        for msg in messages:
            prompt += f"\n{msg['role']}: {msg['content']}"
        prompt += f"\nUpdated Summary:"

        response = await get_chat_response([{"role": "user", "content": prompt}])
        return response.strip()

    # 获取记忆
    def get_memories(self) -> Dict[str, str]:
        return {
            "short_term": self.short_term_memory,
            "mid_term": self.mid_term_memory,
            "long_term": self.long_term_memory
        }

# 创建记忆生成器实例
memory_generator = MemoryGenerator()
