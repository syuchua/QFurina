# filters.py: 用于处理消息过滤和屏蔽词的模块
"""
过滤消息中的屏蔽词
主要特点和功能：
- 加载屏蔽词：从配置文件中加载屏蔽词。
- 更新模式：根据加载的屏蔽词更新正则表达式模式。
- 包含检查：检查消息中是否包含屏蔽词。
- 添加和删除：添加和删除屏蔽词。
- 重新加载：重新加载配置文件中的屏蔽词，实现热更新。
"""
import json
import re
from pathlib import Path
from ..logger import logger

class WordFilter:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / 'config' / 'blocked_words.json'
        self.blocked_words = self._load_blocked_words()
        self._update_pattern()

    def _load_blocked_words(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                words = set(json.load(f)['blocked_words'])
                logger.info(f"Loaded {len(words)} blocked words from {self.config_path}")
                return words
            
        except Exception as e:
            logger.error(f"Error loading blocked words: {e}")
            return set()

    def _save_blocked_words(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({'blocked_words': list(self.blocked_words)}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving blocked words: {e}")

    def _update_pattern(self):
        self.word_pattern = re.compile('|'.join(map(re.escape, self.blocked_words)))

    def contains_blocked_word(self, text):
        match = self.word_pattern.search(text)
        if match:
            return match.group()  # 返回匹配到的词
        return None

    def add_blocked_word(self, word):
        self.blocked_words.add(word)
        self._update_pattern()
        self._save_blocked_words()
        self.reload_config()

    def remove_blocked_word(self, word):
        self.blocked_words.discard(word)
        self._update_pattern()
        self._save_blocked_words()
        self.reload_config()

    def reload_config(self):
        """重新加载配置文件中的屏蔽词"""
        new_words = self._load_blocked_words()
        if new_words != self.blocked_words:
            self.blocked_words = new_words
            self._update_pattern()
            logger.info(f"Reloaded blocked words. New count: {len(self.blocked_words)}")
        else:
            logger.info("Blocked words unchanged after reload.")

word_filter = WordFilter()
