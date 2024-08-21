import csv
from pymongo import MongoClient
from datetime import datetime
import argparse

def export_messages_to_ai_csv(start_date, end_date, output_file, group_id=None):
    # 连接到 MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['chatbot_db']  # 替换为您的数据库名称
    messages_collection = db['messages']  # 消息集合

    # 转换日期字符串为 timestamp
    start_timestamp = datetime.strptime(start_date, "%Y-%m-%d").timestamp()
    end_timestamp = datetime.strptime(end_date, "%Y-%m-%d").timestamp() + 86400  # 加一天的秒数

    # 构建聚合管道
    pipeline = [
        {
            "$match": {
                "timestamp": {
                    "$gte": start_timestamp,
                    "$lt": end_timestamp
                }
            }
        },
        {
            "$project": {
                "user_input": { "$ifNull": ["$user_input", ""] },
                "response_text": { "$ifNull": ["$response_text", ""] },
                "timestamp": { "$ifNull": ["$timestamp", None] },
            }
        },
        { "$sort": { "timestamp": 1 } }
    ]

    # 如果指定了群组ID，添加到匹配条件中
    if group_id:
        pipeline[0]["$match"]["context_id"] = group_id

    # 执行聚合查询
    messages = messages_collection.aggregate(pipeline, allowDiskUse=True)

    # 准备 CSV 文件
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        # 写入表头
        writer.writerow(['User Input', 'Bot Response'])

        # 写入消息数据
        message_count = 0
        for msg in messages:
            user_input = msg.get('user_input', '').strip()
            bot_response = msg.get('response_text', '').strip()
            if user_input or bot_response:  # 只写入非空的对话
                writer.writerow([user_input, bot_response])
                message_count += 1

    print(f"数据已成功导出到 {output_file}")
    print(f"总共导出 {message_count} 条对话")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='导出指定时间段的聊天消息到 AI 训练用 CSV 文件')
    parser.add_argument('start_date', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('end_date', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('output_file', type=str, help='输出 CSV 文件的路径')
    parser.add_argument('--group_id', type=str, help='群组ID（可选）', default=None)

    args = parser.parse_args()

    export_messages_to_ai_csv(args.start_date, args.end_date, args.output_file, args.group_id)