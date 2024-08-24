# process_time.py
from utils.current_time import get_current_time, get_lunar_date_info
from .process_festival import should_include_lunar, should_include_festival

def get_time_info(user_input):
    # 检查是否需要包含农历信息和节日信息
    include_lunar = should_include_lunar(user_input)
    include_festival = should_include_festival(user_input)

    # 获取时间信息
    time_info = get_current_time()
    if include_lunar:
        lunar_info = get_lunar_date_info()
        time_info.update(lunar_info)

    # 构建时间信息字符串
    time_str = (f"今天是：{time_info['full_time']}，{time_info['weekday']}，"
                f"现在是{time_info['period']}，具体时间是{time_info['hour']}点{time_info['minute']}分。")
    
    if include_lunar:
        time_str += f"\n农历：{time_info['lunar_date']}，生肖：{time_info['zodiac']}"
        if time_info['festival']:
            time_str += f"，今天是{time_info['festival']}"
    
    if include_festival and time_info['solar_festival']:
        time_str += f"\n今天是{time_info['solar_festival']}"
    elif include_festival:
        time_str += "\n今天没有特殊的公历节日"

    return time_str