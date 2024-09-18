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

    def remove_blocked_word(self, word):
        self.blocked_words.discard(word)
        self._update_pattern()
        self._save_blocked_words()

word_filter = WordFilter()
