# dbcount.py

import pymongo
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MongoDBCounter:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="chatbot_db"):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]

    def get_message_count(self, hours=24, user_id=None, group_id=None):
        messages_collection = self.db['messages']
        
        start_time = datetime.now() - timedelta(hours=hours)
        query = {"timestamp": {"$gte": start_time.timestamp()}}
        
        if user_id:
            query["user_id"] = user_id
        if group_id:
            query["group_id"] = group_id

        count = messages_collection.count_documents(query)
        return count

    def get_daily_message_count(self, days=7, user_id=None, group_id=None):
        messages_collection = self.db['messages']
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        match_condition = {
            'timestamp': {'$gte': start_time.timestamp(), '$lte': end_time.timestamp()}
        }
        if user_id:
            match_condition['user_id'] = user_id
        if group_id:
            match_condition['group_id'] = group_id

        pipeline = [
            {'$match': match_condition},
            {'$group': {
                '_id': {
                    'year': {'$year': {'$toDate': {'$multiply': ['$timestamp', 1000]}}},
                    'month': {'$month': {'$toDate': {'$multiply': ['$timestamp', 1000]}}},
                    'day': {'$dayOfMonth': {'$toDate': {'$multiply': ['$timestamp', 1000]}}}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        result = list(messages_collection.aggregate(pipeline))
        daily_counts = {f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}": item['count'] for item in result}
        return daily_counts

    def get_user_statistics(self, user_id, days=30):
        messages_collection = self.db['messages']
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        pipeline = [
            {'$match': {
                'user_id': user_id,
                'timestamp': {'$gte': start_time.timestamp(), '$lte': end_time.timestamp()}
            }},
            {'$group': {
                '_id': None,
                'total_messages': {'$sum': 1},
                'avg_message_length': {'$avg': {'$strLenCP': '$user_input'}},
                'most_active_hour': {'$first': {'$hour': {'$toDate': {'$multiply': ['$timestamp', 1000]}}}},
            }}
        ]

        result = list(messages_collection.aggregate(pipeline))
        if result:
            stats = result[0]
            stats['avg_message_length'] = round(stats['avg_message_length'], 2)
            return stats
        else:
            return {'total_messages': 0, 'avg_message_length': 0, 'most_active_hour': None}

    def get_group_statistics(self, group_id, days=30):
        messages_collection = self.db['messages']
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        pipeline = [
            {'$match': {
                'group_id': group_id,
                'timestamp': {'$gte': start_time.timestamp(), '$lte': end_time.timestamp()}
            }},
            {'$group': {
                '_id': None,
                'total_messages': {'$sum': 1},
                'avg_message_length': {'$avg': {'$strLenCP': '$user_input'}},
                'most_active_hour': {'$first': {'$hour': {'$toDate': {'$multiply': ['$timestamp', 1000]}}}},
                'today_messages': {'$sum': {'$cond': [{'$gte': ['$timestamp', end_time.timestamp()]}, 1, 0]}}
            }}
        ]

        result = list(messages_collection.aggregate(pipeline))
        if result:
            stats = result[0]
            stats['avg_message_length'] = round(stats['avg_message_length'], 2)
            return stats
        else:
            return {'total_messages': 0, 'avg_message_length': 0, 'most_active_hour': None, 'today_messages': 0}

if __name__ == "__main__":
    # 使用数据库连接 URI 和数据库名称初始化计数工具
    mongo_counter = MongoDBCounter()

    # 获取过去24小时的消息数量
    total_count = mongo_counter.get_message_count(hours=24)
    logging.info(f"过去24小时内的总消息数: {total_count}")

    db_size = mongo_counter.db.command("dbstats")['dataSize']
    logging.info(f"数据库大小: {db_size / 1024 / 1024:.2f} MB")


    # 获取特定用户过去7天的每日消息数量
    # user_id = "example_user_id"  # 替换为实际的用户ID
    # daily_counts = mongo_counter.get_daily_message_count(days=7, user_id=user_id)
    # logging.info(f"用户 {user_id} 过去7天的每日消息数:")
    # for date, count in daily_counts.items():
    #     logging.info(f"{date}: {count}")

    # 获取用户统计信息
    # user_stats = mongo_counter.get_user_statistics(user_id)
    # logging.info(f"用户 {user_id} 的统计信息:")
    # logging.info(f"总消息数: {user_stats['total_messages']}")
    # logging.info(f"平均消息长度: {user_stats['avg_message_length']}")
    # logging.info(f"最活跃的小时: {user_stats['most_active_hour']}")

     # 统计机器人在特定群组今天发的消息
    # group_id = 310602383  # 替换为实际的群组ID
    # bot_messages_count = mongo_counter.get_message_count(hours=24, group_id=group_id)
    # logging.info(f"机器人今天在群组 {group_id} 中发送的消息数量: {bot_messages_count}")
    # group_stats = mongo_counter.get_group_statistics(group_id)
    # logging.info(f"群组 {group_id} 的统计信息:")
    # logging.info(f"总消息数: {group_stats['total_messages']}")
    # logging.info(f"平均消息长度: {group_stats['avg_message_length']}")
    # logging.info(f"最活跃的小时: {group_stats['most_active_hour']}")
    # logging.info(f"今天的消息数: {group_stats['today_messages']}")
