# onebot v11.py
from enum import Enum
from typing import TypedDict, List, Union

# 定义消息类型枚举
class MessageType(Enum):
    PRIVATE = "private"  # 私聊消息
    GROUP = "group"  # 群聊消息

# 定义事件类型枚举
class EventType(Enum):
    MESSAGE = "message"  # 消息事件
    NOTICE = "notice"  # 通知事件
    REQUEST = "request"  # 请求事件
    META_EVENT = "meta_event"  # 元事件

# 定义通知类型枚举
class NoticeType(Enum):
    GROUP_UPLOAD = "group_upload"  # 群文件上传
    GROUP_ADMIN = "group_admin"  # 群管理员变动
    GROUP_DECREASE = "group_decrease"  # 群成员减少
    GROUP_INCREASE = "group_increase"  # 群成员增加
    GROUP_BAN = "group_ban"  # 群禁言
    FRIEND_ADD = "friend_add"  # 好友添加
    GROUP_RECALL = "group_recall"  # 群消息撤回
    FRIEND_RECALL = "friend_recall"  # 好友消息撤回
    POKE = "poke"  # 戳一戳
    LUCKY_KING = "lucky_king"  # 运气王
    HONOR = "honor"  # 群荣誉变更

# 定义请求类型枚举
class RequestType(Enum):
    FRIEND = "friend"  # 好友请求
    GROUP = "group"  # 群请求

# 定义消息段类型
class MessageSegment(TypedDict):
    type: str  # 消息段类型
    data: dict  # 消息段数据

# 定义发送者信息类型
class Sender(TypedDict):
    user_id: int  # 用户ID
    nickname: str  # 昵称
    sex: str  # 性别
    age: int  # 年龄
    card: str  # 群名片
    area: str  # 地区
    level: str  # 等级
    role: str  # 角色
    title: str  # 头衔

# 定义群消息事件类型
class GroupMessageEvent(TypedDict):
    post_type: str  # 上报类型
    message_type: str  # 消息类型
    time: int  # 事件发生的时间戳
    self_id: int  # 收到事件的机器人 QQ 号
    sub_type: str  # 消息子类型
    message_id: int  # 消息 ID
    user_id: int  # 发送者 QQ 号
    message: Union[str, List[MessageSegment]]  # 消息内容
    raw_message: str  # 原始消息内容
    font: int  # 字体
    sender: Sender  # 发送人信息
    group_id: int  # 群号

# 定义私聊消息事件类型
class PrivateMessageEvent(TypedDict):
    post_type: str  # 上报类型
    message_type: str  # 消息类型
    time: int  # 事件发生的时间戳
    self_id: int  # 收到事件的机器人 QQ 号
    sub_type: str  # 消息子类型
    message_id: int  # 消息 ID
    user_id: int  # 发送者 QQ 号
    message: Union[str, List[MessageSegment]]  # 消息内容
    raw_message: str  # 原始消息内容
    font: int  # 字体
    sender: Sender  # 发送人信息

# 可以继续添加其他事件类型的定义...

# 判断是否为群消息
def is_group_message(event: dict) -> bool:
    return event.get('message_type') == MessageType.GROUP.value

# 判断是否为私聊消息
def is_private_message(event: dict) -> bool:
    return event.get('message_type') == MessageType.PRIVATE.value

# 获取用户ID
def get_user_id(event: dict) -> int:
    return event.get('user_id', 0)

# 获取群ID
def get_group_id(event: dict) -> int:
    return event.get('group_id', 0)

# 获取消息内容
def get_message_content(event: dict) -> str:
    return event.get('raw_message', '')

def get_sender(event: dict) -> Sender:
    return event.get('sender', {})

def get_username(event: dict) -> str:
    return event.get('sender', {}).get('nickname', '')