# *- split_message.py -*
"""
将长消息分割成多个短消息。
"""
def split_message(message, max_length=1000):
    """
    将长消息分割成多个短消息。
    每遇到一到两个换行符就进行分割，同时确保每条消息不超过最大长度。
    不截断Markdown代码块。
    """
    parts = []
    current_part = ""
    lines = message.split('\n')
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        if len(current_part) + len(line) + 1 > max_length and not in_code_block:
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
        
        current_part += line + '\n'

        if current_part.count('\n') >= 2 and not in_code_block:
            parts.append(current_part.strip())
            current_part = ""

    if current_part:
        parts.append(current_part.strip())

    return parts
