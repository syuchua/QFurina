# process_festival.py

def should_include_lunar(user_input):
    lunar_keywords = ["农历", "阴历", "节日", "生肖", "春节", "元宵", "端午", "中秋", "重阳"]
    return any(keyword in user_input for keyword in lunar_keywords)

def should_include_festival(user_input):
    festival_keywords = ["元旦", "情人节", "妇女节", "愚人节", "劳动节", "儿童节", "国庆节", "圣诞节"]
    return any(keyword in user_input for keyword in festival_keywords)
