import time
import pymongo
import logging
import re,sys
#from app.config import Config
# 配置日志
logging.basicConfig(level=logging.INFO)
#config = Config.get_instance()
class MongoDBCleaner:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="chatbot_db"):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]

    def clean_empty_responses(self):
        messages_collection = self.db['messages']
        # 定义查询条件
        query = {"$or": [{"response_text": {"$exists": False}}, {"response_text": ""}]}
        result = messages_collection.delete_many(query)
        logging.info(f"Deleted {result.deleted_count} documents containing empty responses")

    def clean_old_messages(self, hours=2, exempt_user_ids=None, exempt_group_ids=None):
        if exempt_user_ids is None:
            exempt_user_ids = []
        if exempt_group_ids is None:
            exempt_group_ids = []

        messages_collection = self.db['messages']
        expiry_time = time.time() - hours * 1
        query = {
            "timestamp": {"$lt": expiry_time},
            "user_id": {"$nin": exempt_user_ids},
            "group_id": {"$nin": exempt_group_ids}
        }
        result = messages_collection.delete_many(query)
        logging.info(f"Deleted {result.deleted_count} documents older than {hours} hours")

    def clean_messages_by_keywords(self, keywords):
        """
        清理包含特定关键字的历史消息。

        参数:
            keywords (list): 要匹配的关键字列表。
        """
        messages_collection = self.db['messages']

        # 使用正则表达式构建查询条件，忽略大小写
        regex_pattern = '|'.join(re.escape(keyword) for keyword in keywords)
        regex = re.compile(regex_pattern, re.IGNORECASE)

        # 定义查询条件，匹配 user_input 和 response_text 中包含关键字的消息
        query = {
            "$or": [
                {"user_input": {"$regex": regex}},
                {"response_text": {"$regex": regex}}
            ]
        }

        result = messages_collection.delete_many(query)
        logging.info(f"Deleted {result.deleted_count} documents containing keywords: {keywords}")

if __name__ == "__main__":
    # 使用数据库连接 URI 和数据库名称初始化清理工具
    mongo_cleaner = MongoDBCleaner()
    # 清除包含空值的历史消息
    #mongo_cleaner.clean_empty_responses()
    # 清除一段时间前的消息记录
    #mongo_cleaner.clean_old_messages()
    # 定义要清除的关键字列表
    keywords_to_del = sys.argv[1:] # 从命令行参数获取关键字列表
    if keywords_to_del:
        # 清除包含特定关键字的消息
        mongo_cleaner.clean_messages_by_keywords(keywords_to_del)
    else:
        logging.error("Please provide keywords to delete as command line arguments.")