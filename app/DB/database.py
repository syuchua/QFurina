# database.py
import os, time
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from ..logger import logger
from ..Core.config import Config
import motor.motor_asyncio

config = Config.get_instance()

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def init_async(self):
        self.client = self._create_client()
        self.db = self.client[self._get_db_name()]
        await self.ensure_indexes()  # 确保在事件循环中创建索引

    def _create_client(self):
        is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017' if is_docker else 'mongodb://localhost:27017')
        return motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)

    def _get_db_name(self):
        return os.getenv('MONGO_DB_NAME', 'chatbot_db')

    def get_collection(self, collection_name):
        return self.db[collection_name]

    async def ensure_indexes(self):
        try:
            users_collection = self.get_collection('users')
            await users_collection.create_index('user_id', unique=True)
            
            messages_collection = self.get_collection('messages')
            await messages_collection.create_index([('timestamp', ASCENDING)])
            await messages_collection.create_index([
                ('user_id', ASCENDING),
                ('context_type', ASCENDING),
                ('context_id', ASCENDING),
                ('platform', ASCENDING)
            ])
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")

    # 插入用户信息
    async def insert_user_info(self, user_info):
        try:
            users_collection = self.get_collection('users')
            await users_collection.update_one(
                {'user_id': user_info['user_id']},
                {'$set': user_info},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error inserting/updating user info: {e}")


    # 插入聊天信息
    async def insert_chat_message(self, user_id, user_input, response_text, context_type, context_id, platform):
        try:
            if response_text:
                messages_collection = self.get_collection('messages')
                message_data = {
                    'user_id': user_id,
                    'user_input': user_input,
                    'response_text': response_text,
                    'context_type': context_type,
                    'context_id': context_id,
                    'platform': platform,
                    'timestamp': time.time()
                }
                await messages_collection.insert_one(message_data)
        except Exception as e:
            logger.error(f"Error inserting chat message: {e}")

    

    # 获取最近的聊天信息
    #@async_timed()
    async def get_recent_messages(self, user_id, context_type, context_id, platform,limit=10):
        try:
            messages_collection = self.get_collection('messages')
            query = {"context_type": context_type,
                     "platform": platform
                    }
            
            if context_type == 'private':
                query["user_id"] = user_id
            elif context_type == 'group':
                query["context_id"] = context_id

            cursor = messages_collection.find(query).sort("timestamp", -1).limit(limit)
            messages = await cursor.to_list(length=limit)
            messages_list = []

            for msg in reversed(messages):
                user_input = msg.get('user_input', '(no user input)')
                response_text = msg.get('response_text', '(no response)')
                if user_input and response_text and response_text != '(no response)':
                    msg_id = str(msg["_id"])
                    messages_list.append({"_id": msg_id, "role": "user", "content": user_input})
                    messages_list.append({"_id": msg_id, "role": "assistant", "content": response_text})

            return messages_list
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []

    # 获取用户的历史聊天信息
    async def get_user_historical_messages(self, user_id, context_type, context_id, limit=5):
        try:
            messages_collection = self.get_collection('messages')
            query = {
                "user_id": user_id,
                "context_type": context_type,
                "context_id": context_id
            }
            cursor = messages_collection.find(query).sort("timestamp", -1).limit(limit * 2)
            messages = await cursor.to_list(length=limit)
            messages_list = []

            for msg in reversed(messages):
                user_input = msg.get('user_input', '(no user input)')
                response_text = msg.get('response_text', '(no response)')
                if user_input and response_text and response_text != '(no response)':
                    msg["_id"] = str(msg["_id"])
                    messages_list.append({"_id": msg["_id"], "role": "user", "content": user_input})
                    messages_list.append({"_id": msg["_id"], "role": "assistant", "content": response_text})

            return messages_list
        except Exception as e:
            logger.error(f"Error getting user historical messages: {e}")
            return []


    # 删除过期的聊天信息
    def clean_old_messages(self, days=1, exempt_user_ids=None, exempt_context_ids=None):
        try:
            exempt_user_ids = exempt_user_ids or [config.ADMIN_ID]
            exempt_context_ids = exempt_context_ids or []

            messages_collection = self.get_collection('messages')
            expiry_time = time.time() - days * 86400
            query = {
                "timestamp": {"$lt": expiry_time},
                "user_id": {"$nin": exempt_user_ids},
                "context_id": {"$nin": exempt_context_ids}
            }
            
            result = messages_collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} old messages")
        except Exception as e:
            logger.error(f"Error cleaning old messages: {e}")

    # 删除单条聊天信息
    def delete_message(self, message):
        try:
            messages_collection = self.get_collection('messages')
            if '_id' in message:
                result = messages_collection.delete_one({'_id': ObjectId(message['_id'])})
                if result.deleted_count == 1:
                    logger.info(f"Deleted message with _id: {message['_id']}")
                else:
                    logger.warning(f"No message found with _id: {message['_id']}")
            else:
                logger.warning(f"Message without _id: {message}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    # 删除多条聊天信息
    def delete_messages(self, messages_list):
        try:
            logger.info(f"Attempting to delete {len(messages_list)} messages")
            deleted_ids = set()
            for message in messages_list:
                #logger.info(f"Processing message: {message}")
                if isinstance(message, dict) and '_id' in message:
                    if message['_id'] not in deleted_ids:
                        self.delete_message(message)
                        deleted_ids.add(message['_id'])
                else:
                    logger.warning(f"Invalid message format: {message}")
            logger.info(f"Finished deleting messages. Deleted {len(deleted_ids)} unique messages.")
        except Exception as e:
            logger.error(f"Error deleting messages: {e}")

    # 获取聊天信息数量
    def get_message_count(self, start_time=None, end_time=None, user_id=None, context_type=None, context_id=None):
        try:
            messages_collection = self.get_collection('messages')
            
            match_condition = {}
            if start_time:
                match_condition['timestamp'] = {'$gte': start_time}
            if end_time:
                match_condition.setdefault('timestamp', {})['$lte'] = end_time
            if user_id:
                match_condition['user_id'] = user_id
            if context_type:
                match_condition['context_type'] = context_type
            if context_id:
                match_condition['context_id'] = context_id

            pipeline = [
                {'$match': match_condition},
                {'$group': {
                    '_id': None,
                    'count': {'$sum': 1}
                }}
            ]

            result = list(messages_collection.aggregate(pipeline))
            return result[0]['count'] if result else 0

        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0

    # 获取每日聊天信息数量
    def get_daily_message_count(self, days=7, user_id=None, context_type=None, context_id=None):
        try:
            messages_collection = self.get_collection('messages')
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            match_condition = {
                'timestamp': {'$gte': start_time.timestamp(), '$lte': end_time.timestamp()}
            }
            if user_id:
                match_condition['user_id'] = user_id
            if context_type:
                match_condition['context_type'] = context_type
            if context_id:
                match_condition['context_id'] = context_id

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

        except Exception as e:
            logger.error(f"Error getting daily message count: {e}")
            return {}

db = MongoDB()
