# database.py
import time
from bson import ObjectId
from pymongo import MongoClient
from app.logger import logger
import pymongo
from app.config import Config
import schedule

config = Config.get_instance()

class MongoDB:
    def __init__(self, uri="mongodb://mongo:27017/", db_name="chatbot_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.ensure_indexes()

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def ensure_indexes(self):
        try:
            users_collection = self.get_collection('users')
            users_collection.create_index('user_id', unique=True)
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")

    def insert_user_info(self, user_info):
        try:
            users_collection = self.get_collection('users')
            # 尝试找到已有的用户信息
            existing_user = users_collection.find_one({'user_id': user_info['user_id']})
            if existing_user:
                # 更新现有的用户信息
                result = users_collection.update_one(
                    {'user_id': user_info['user_id']},
                    {'$set': user_info}
                )
            else:
                # 插入新的用户信息
                result = users_collection.insert_one(user_info)
        except Exception as e:
            logger.error(f"Error inserting/updating user info: {e}")

    def deduplicate_users(self):
        try:
            users_collection = self.get_collection('users')
            pipeline = [
                {"$group": {
                    "_id": "$user_id",
                    "count": {"$sum": 1},
                    "ids": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = list(users_collection.aggregate(pipeline))
            for doc in duplicates:
                ids_to_remove = doc['ids'][1:]  # 保留一个文档，其余删除
                users_collection.delete_many({"_id": {"$in": ids_to_remove}})
            logger.info(f"Deduplicated {len(duplicates)} user records")
        except Exception as e:
            logger.error(f"Error deduplicating users: {e}")

    def insert_chat_message(self, user_id, user_input, response_text, context_type, context_id):
        try:
            if response_text:  # 仅保存有回复的消息
                messages_collection = self.get_collection('messages')
                message_data = {
                    'user_id': user_id,
                    'user_input': user_input,
                    'response_text': response_text,
                    'context_type': context_type,  # "group" 或 "private"
                    'context_id': context_id,
                    # 'username': username,
                    'timestamp': time.time()  # 添加时间戳
                }
                result = messages_collection.insert_one(message_data)
                # logger.info(f"Inserted chat message: {result.inserted_id}")
        except Exception as e:
            logger.error(f"Error inserting chat message: {e}")

    def get_context(self, context_type, context_id):
        try:
            contexts_collection = self.get_collection('contexts')
            context = contexts_collection.find_one({"context_type": context_type, "context_id": context_id})
            if context:
                return context['messages']
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return []

    def update_context(self, context_type, context_id, new_message):
        try:
            contexts_collection = self.get_collection('contexts')
            contexts_collection.update_one(
                {"context_type": context_type, "context_id": context_id},
                {"$push": {"messages": new_message}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating context: {e}")

    def get_recent_messages(self, user_id, context_type, context_id, limit=10):
        try:
            messages_collection = self.get_collection('messages')
            query = {"context_type": context_type}
            
            if context_type == 'private':
                query["user_id"] = user_id
            elif context_type == 'group':
                if context_id:
                    query["context_id"] = context_id
                else:
                    logger.warning("Context ID is required for group messages.")
                    return []

            messages = messages_collection.find(query).sort("timestamp", -1).limit(limit)
            messages_list = []

             # 确保字段存在默认值，并跳过未回复的消息
            for msg in reversed(list(messages)):
                user_input = msg.get('user_input', '(no user input)')
                response_text = msg.get('response_text', '(no response)')
                if user_input and response_text and response_text != '(no response)':
                    msg["_id"] = str(msg["_id"])  # 将 ObjectId 转换为字符串
                    messages_list.append({"_id": msg['_id'], "role": "user", "content": user_input})
                    messages_list.append({"_id": msg['_id'], "role": "assistant", "content": response_text})

            return messages_list
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []

    def clean_empty_responses(self):
        try:
            messages_collection = self.db['messages']
            query = {"$or": [{"response_text": {"$exists": False}}, {"response_text": ""}]}
            result = messages_collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} documents containing empty responses")
        except Exception as e:
            logger.error(f"Error cleaning empty responses: {e}")

    def clean_old_messages(self, days=1, exempt_user_ids=None, exempt_context_ids=None):
        try:
            if exempt_user_ids is None:
                exempt_user_ids = [config.ADMIN_ID]
            if exempt_context_ids is None:
                exempt_context_ids = []

            messages_collection = self.db['messages']

            # 首先补全缺失的 context_type 和 context_id
            update_ops = []
            for message in messages_collection.find({"context_type": {"$exists": False}}):
                message_type = 'private' if 'group_id' not in message else 'group'
                context_id = message['user_id'] if message_type == 'private' else message.get('group_id')
                update_ops.append(
                    pymongo.UpdateOne(
                        {'_id': message['_id']},
                        {'$set': {'context_type': message_type, 'context_id': context_id}}
                    )
                )
            if update_ops:
                result = messages_collection.bulk_write(update_ops)
                logger.info(f"Updated {result.matched_count} documents with context_type and context_id")

            expiry_time = time.time() - days * 86400  # 86400 seconds in a day
            query = {
                "timestamp": {"$lt": expiry_time},
                "user_id": {"$nin": exempt_user_ids},
                "context_id": {"$nin": exempt_context_ids}
            }
            
            result = messages_collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} old documents")
        except Exception as e:
            logger.error(f"Error cleaning old messages: {e}")

    def clean_old_contexts(self, days=1):
        try:
            contexts_collection = self.db['contexts']
            expiry_time = time.time() - days * 86400  # 86400 seconds in a day
            query = {
                "messages.timestamp": {"$lt": expiry_time}
            }
            
            result = contexts_collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} old contexts")
        except Exception as e:
            logger.error(f"Error cleaning old contexts: {e}")

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
