# current_time.py

import pytz
from datetime import datetime
from zhdate import ZhDate

def get_current_time():
    # 设置时区为中国标准时间
    china_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(china_tz)
    
    # 格式化时间字符串
    time_str = current_time.strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 获取星期几
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][current_time.weekday()]
    
    # 判断时间段
    hour = current_time.hour
    if 5 <= hour < 12:
        period = "早上"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 22:
        period = "晚上"
    else:
        period = "深夜"
    
    return {
        "full_time": time_str,
        "weekday": weekday,
        "period": period,
        "hour": hour,
        "minute": current_time.minute
    }

def get_lunar_date_info():
    today = datetime.now()
    lunar_date = ZhDate.from_datetime(today)
    zodiac = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"][(lunar_date.lunar_year - 1900) % 12]
    
    # 简单的节日判断，可以根据需要扩展
    festivals = {
        (1, 1): "春节",
        (5, 5): "端午节",
        (7, 7): "七夕节",
        (8, 15): "中秋节",
        (9, 9): "重阳节"
    }
    festival = festivals.get((lunar_date.lunar_month, lunar_date.lunar_day), "")
    
    return {
        "lunar_date": f"{lunar_date.lunar_year}年{lunar_date.lunar_month}月{lunar_date.lunar_day}日",
        "zodiac": zodiac,
        "festival": festival
    }

def get_solar_festival(date):
    solar_festivals = {
        (1, 1): "元旦",
        (2, 14): "情人节",
        (3, 8): "妇女节",
        (4, 1): "愚人节",
        (5, 1): "劳动节",
        (6, 1): "儿童节",
        (10, 1): "国庆节",
        (12, 25): "圣诞节",
        # 可以根据需要添加更多节日
    }
    return solar_festivals.get((date.month, date.day), "")

def get_current_time_with_lunar():
    current_time = get_current_time()
    lunar_info = get_lunar_date_info()
    
    current_time.update({
        "lunar_date": lunar_info["lunar_date"],
        "zodiac": lunar_info["zodiac"],
        "festival": lunar_info["festival"]
    })
    
    return current_time
