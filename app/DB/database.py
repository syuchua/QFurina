# database.py
import os, time
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from ..logger import logger
from ..Core.config import Config
from bson import ObjectId

config = Config.get_instance()

class MongoDB:
    def __init__(self):
        self.client = self._create_client()
        self.db = self.client[self._get_db_name()]
        self.ensure_indexes()

    def _create_client(self):
        is_docker = os.environ.get('IS_DOCKER', 'false').lower() == 'true'
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017' if is_docker else 'mongodb://localhost:27017')
        return MongoClient(mongo_uri)

    def _get_db_name(self):
        return os.getenv('MONGO_DB_NAME', 'chatbot_db')

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def ensure_indexes(self):
        try:
            users_collection = self.get_collection('users')
            users_collection.create_index('user_id', unique=True)
            
            messages_collection = self.get_collection('messages')
            messages_collection.create_index([('timestamp', ASCENDING)])
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")

    def insert_user_info(self, user_info):
        try:
            users_collection = self.get_collection('users')
            users_collection.update_one(
                {'user_id': user_info['user_id']},
                {'$set': user_info},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error inserting/updating user info: {e}")

    def insert_chat_message(self, user_id, user_input, response_text, context_type, context_id):
        try:
            if response_text:
                messages_collection = self.get_collection('messages')
                message_data = {
                    'user_id': user_id,
                    'user_input': user_input,
                    'response_text': response_text,
                    'context_type': context_type,
                    'context_id': context_id,
                    #'username': username,
                    'timestamp': time.time()
                }
                messages_collection.insert_one(message_data)
        except Exception as e:
            logger.error(f"Error inserting chat message: {e}")

    def get_recent_messages(self, user_id, context_type, context_id, limit=10):
        try:
            messages_collection = self.get_collection('messages')
            query = {"context_type": context_type}
            
            if context_type == 'private':
                query["user_id"] = user_id
            elif context_type == 'group':
                query["context_id"] = context_id

            messages = messages_collection.find(query).sort("timestamp", -1).limit(limit)
            messages_list = []

            for msg in reversed(list(messages)):
                user_input = msg.get('user_input', '(no user input)')
                response_text = msg.get('response_text', '(no response)')
                if user_input and response_text and response_text != '(no response)':
                    msg["_id"] = str(msg["_id"])
                    messages_list.append({"role": "user", "content": user_input})
                    messages_list.append({"role": "assistant", "content": response_text})

            return messages_list
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []

    def get_user_historical_messages(self, user_id, context_type, context_id, limit=5):
        try:
            messages_collection = self.get_collection('messages')
            query = {
                "user_id": user_id,
                "context_type": context_type,
                "context_id": context_id
            }
            messages = messages_collection.find(query).sort("timestamp", -1).limit(limit * 2)
            messages_list = []

            for msg in reversed(list(messages)):
                user_input = msg.get('user_input', '(no user input)')
                response_text = msg.get('response_text', '(no response)')
                if user_input and response_text and response_text != '(no response)':
                    messages_list.append({"role": "user", "content": user_input})
                    messages_list.append({"role": "assistant", "content": response_text})

            return messages_list
        except Exception as e:
            logger.error(f"Error getting user historical messages: {e}")
            return []

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

    def delete_message(self, message_id):
        try:
            messages_collection = self.get_collection('messages')
            result = messages_collection.delete_one({'_id': ObjectId(message_id)})
            if result.deleted_count == 1:
                logger.info(f"Deleted message with _id {message_id}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    def delete_messages(self, messages_list):
        try:
            for message in messages_list:
                self.delete_message(message['_id'])
        except Exception as e:
            logger.error(f"Error deleting messages: {e}")
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
