import time
import pymongo
import logging
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
if __name__ == "__main__":
    # 使用数据库连接 URI 和数据库名称初始化清理工具
    mongo_cleaner = MongoDBCleaner()
    # 清除包含空值的历史消息
    mongo_cleaner.clean_empty_responses()
    # 清除一段时间前的消息记录
    mongo_cleaner.clean_old_messages()